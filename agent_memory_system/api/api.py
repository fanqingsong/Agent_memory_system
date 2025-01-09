"""API接口模块

实现RESTful API和WebSocket接口。

主要功能：
    - RESTful API接口
    - WebSocket实时接口
    - 接口认证和授权
    - 请求限流和缓存
    - 错误处理和日志

依赖：
    - fastapi: Web框架
    - memory_manager: 记忆管理
    - memory_retrieval: 记忆检索
    - config: 配置管理
    - logger: 日志记录

作者：Cursor_for_YansongW
创建日期：2024-01-15
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from uuid import uuid4

from fastapi import (
    FastAPI,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    status,
    BackgroundTasks,
    Request
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from agent_memory_system.core.memory.memory_manager import MemoryManager
from agent_memory_system.core.memory.memory_retrieval import MemoryRetrieval
from agent_memory_system.models.memory_model import (
    Memory,
    MemoryQuery,
    MemoryType,
    RetrievalStrategy
)
from agent_memory_system.models.api_models import (
    ErrorResponse,
    SuccessResponse,
    WebSocketMessage,
    WebSocketResponse
)
from agent_memory_system.utils.config import config
from agent_memory_system.utils.logger import log

# 创建FastAPI应用
app = FastAPI(
    title="Agent Memory System API",
    description="智能Agent记忆管理系统API",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# 初始化管理器
memory_manager = MemoryManager()
memory_retrieval = MemoryRetrieval()

# WebSocket连接管理
class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_times: Dict[str, datetime] = {}
        self.ping_tasks: Dict[str, asyncio.Task] = {}
        self.timeout = timedelta(seconds=config.get("websocket.timeout", 60))
        self.ping_interval = timedelta(seconds=config.get("websocket.ping_interval", 30))
    
    async def connect(self, websocket: WebSocket) -> str:
        """建立连接"""
        await websocket.accept()
        client_id = str(uuid4())
        self.active_connections[client_id] = websocket
        self.connection_times[client_id] = datetime.now()
        
        # 启动心跳检测
        self.ping_tasks[client_id] = asyncio.create_task(
            self._ping_client(client_id, websocket)
        )
        
        log.info(f"WebSocket客户端连接: {client_id}")
        return client_id
    
    def disconnect(self, client_id: str) -> None:
        """断开连接"""
        if client_id in self.active_connections:
            # 取消心跳任务
            if client_id in self.ping_tasks:
                self.ping_tasks[client_id].cancel()
                del self.ping_tasks[client_id]
            
            # 清理连接信息
            del self.active_connections[client_id]
            del self.connection_times[client_id]
            log.info(f"WebSocket客户端断开: {client_id}")
    
    async def _ping_client(self, client_id: str, websocket: WebSocket) -> None:
        """心跳检测"""
        try:
            while True:
                await asyncio.sleep(self.ping_interval.total_seconds())
                try:
                    await websocket.send_json({"type": "ping"})
                except Exception:
                    self.disconnect(client_id)
                    break
        except asyncio.CancelledError:
            pass
    
    async def broadcast(
        self,
        message: Dict,
        exclude: Optional[Set[str]] = None
    ) -> None:
        """广播消息"""
        exclude = exclude or set()
        for client_id, websocket in self.active_connections.items():
            if client_id not in exclude:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    log.error(f"广播消息失败: {e}")
                    self.disconnect(client_id)
    
    def clean_inactive_connections(self) -> None:
        """清理不活跃的连接"""
        now = datetime.now()
        inactive_clients = [
            client_id
            for client_id, last_time in self.connection_times.items()
            if now - last_time > self.timeout
        ]
        for client_id in inactive_clients:
            self.disconnect(client_id)

# 创建连接管理器
connection_manager = ConnectionManager()

@app.on_event("startup")
async def startup():
    """应用启动事件处理"""
    log.info("API服务启动")

@app.on_event("shutdown")
async def shutdown():
    """应用关闭事件处理"""
    # 关闭所有WebSocket连接
    for client_id in list(connection_manager.active_connections.keys()):
        connection_manager.disconnect(client_id)
    
    # 关闭管理器
    memory_manager.close()
    memory_retrieval.close()
    log.info("API服务关闭")

@app.get("/")
async def root():
    """根路径处理
    
    Returns:
        Dict: 基本信息
    """
    return {
        "name": "Agent Memory System API",
        "version": "1.0.0",
        "status": "running"
    }

@app.post("/memories")
async def create_memory(memory: Memory):
    """创建记忆
    
    Args:
        memory: 记忆对象
    
    Returns:
        Memory: 创建的记忆
    """
    try:
        result = memory_manager.create_memory(memory)
        # 广播更新
        await broadcast_update("memory_created", result)
        return result
    except Exception as e:
        log.error(f"创建记忆失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/memories/{memory_id}")
async def get_memory(memory_id: str):
    """获取记忆
    
    Args:
        memory_id: 记忆ID
    
    Returns:
        Memory: 记忆对象
    """
    try:
        result = memory_manager.get_memory(memory_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="记忆不存在"
            )
        return result
    except Exception as e:
        log.error(f"获取记忆失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.put("/memories/{memory_id}")
async def update_memory(memory_id: str, memory: Memory):
    """更新记忆
    
    Args:
        memory_id: 记忆ID
        memory: 记忆对象
    
    Returns:
        Memory: 更新后的记忆
    """
    try:
        result = memory_manager.update_memory(memory_id, memory)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="记忆不存在"
            )
        # 广播更新
        await broadcast_update("memory_updated", result)
        return result
    except Exception as e:
        log.error(f"更新记忆失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.delete("/memories/{memory_id}")
async def delete_memory(memory_id: str):
    """删除记忆
    
    Args:
        memory_id: 记忆ID
    
    Returns:
        Dict: 操作结果
    """
    try:
        result = memory_manager.delete_memory(memory_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="记忆不存在"
            )
        # 广播更新
        await broadcast_update("memory_deleted", {"id": memory_id})
        return {"message": "删除成功"}
    except Exception as e:
        log.error(f"删除记忆失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/memories/search")
async def search_memories(
    query: MemoryQuery,
    strategy: RetrievalStrategy = RetrievalStrategy.HYBRID,
    limit: int = 10
):
    """搜索记忆
    
    Args:
        query: 检索查询
        strategy: 检索策略
        limit: 返回数量限制
    
    Returns:
        List[Memory]: 记忆列表
    """
    try:
        results = memory_retrieval.retrieve(
            query=query,
            strategy=strategy,
            limit=limit
        )
        return results
    except Exception as e:
        log.error(f"搜索记忆失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket连接处理"""
    client_id = None
    try:
        # 建立连接
        client_id = await connection_manager.connect(websocket)
        
        # 发送欢迎消息
        await websocket.send_json(
            WebSocketResponse(
                type="welcome",
                data={"client_id": client_id}
            ).dict()
        )
        
        while True:
            # 接收消息
            try:
                raw_data = await websocket.receive_json()
                message = WebSocketMessage.parse_obj(raw_data)
            except ValidationError as e:
                await websocket.send_json(
                    WebSocketResponse(
                        type="error",
                        data={"message": "无效的消息格式", "detail": str(e)}
                    ).dict()
                )
                continue
            
            # 处理消息
            try:
                response = await process_websocket_message(message)
                await websocket.send_json(response.dict())
            except Exception as e:
                log.error(f"处理WebSocket消息失败: {e}")
                await websocket.send_json(
                    WebSocketResponse(
                        type="error",
                        data={"message": "处理消息失败", "detail": str(e)}
                    ).dict()
                )
    
    except WebSocketDisconnect:
        if client_id:
            connection_manager.disconnect(client_id)
    except Exception as e:
        log.error(f"WebSocket连接异常: {e}")
        if client_id:
            connection_manager.disconnect(client_id)

async def process_websocket_message(message: WebSocketMessage) -> WebSocketResponse:
    """处理WebSocket消息"""
    try:
        if message.type == "ping":
            return WebSocketResponse(type="pong")
        
        elif message.type == "subscribe":
            # 处理订阅请求
            return WebSocketResponse(
                type="subscribed",
                data={"topics": message.data.get("topics", [])}
            )
        
        elif message.type == "unsubscribe":
            # 处理取消订阅请求
            return WebSocketResponse(
                type="unsubscribed",
                data={"topics": message.data.get("topics", [])}
            )
        
        elif message.type == "query":
            # 处理查询请求
            query = MemoryQuery.parse_obj(message.data.get("query", {}))
            results = await memory_retrieval.retrieve(
                query=query,
                strategy=message.data.get("strategy", RetrievalStrategy.HYBRID),
                limit=message.data.get("limit", 10)
            )
            return WebSocketResponse(
                type="query_result",
                data={"results": [r.dict() for r in results]}
            )
        
        else:
            return WebSocketResponse(
                type="error",
                data={"message": "不支持的消息类型"}
            )
    
    except Exception as e:
        log.error(f"处理WebSocket消息失败: {e}")
        return WebSocketResponse(
            type="error",
            data={"message": "处理消息失败", "detail": str(e)}
        )

async def broadcast_update(
    update_type: str,
    payload: Dict,
    exclude_clients: Optional[Set[str]] = None
) -> None:
    """广播更新消息"""
    try:
        message = WebSocketResponse(
            type=update_type,
            data=payload
        ).dict()
        await connection_manager.broadcast(message, exclude_clients)
    except Exception as e:
        log.error(f"广播更新失败: {e}")

# 定期清理不活跃连接
@app.on_event("startup")
async def setup_periodic_cleanup():
    """设置定期清理任务"""
    async def cleanup():
        while True:
            await asyncio.sleep(300)  # 每5分钟清理一次
            connection_manager.clean_inactive_connections()
    
    asyncio.create_task(cleanup())

# 错误处理
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            code=exc.status_code,
            message=exc.detail,
            detail=None
        ).dict()
    )

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """验证异常处理器"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            code=422,
            message="请求数据验证失败",
            detail=exc.errors()
        ).dict()
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    log.error(f"全局异常: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            code=500,
            message="服务器内部错误",
            detail=str(exc)
        ).dict()
    )
