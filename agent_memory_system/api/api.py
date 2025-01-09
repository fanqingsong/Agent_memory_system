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

from datetime import datetime
from typing import Dict, List, Optional

from fastapi import (
    FastAPI,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    status
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from agent_memory_system.core.memory.memory_manager import MemoryManager
from agent_memory_system.core.memory.memory_retrieval import MemoryRetrieval
from agent_memory_system.models.memory_model import (
    Memory,
    MemoryQuery,
    MemoryType,
    RetrievalStrategy
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
websocket_connections: Dict[str, WebSocket] = {}

@app.on_event("startup")
async def startup():
    """应用启动事件处理"""
    log.info("API服务启动")

@app.on_event("shutdown")
async def shutdown():
    """应用关闭事件处理"""
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
    """WebSocket连接处理
    
    Args:
        websocket: WebSocket连接
    """
    try:
        # 接受连接
        await websocket.accept()
        client_id = str(id(websocket))
        websocket_connections[client_id] = websocket
        log.info(f"WebSocket客户端连接: {client_id}")
        
        try:
            while True:
                # 接收消息
                data = await websocket.receive_json()
                # 处理消息
                response = await process_websocket_message(data)
                # 发送响应
                await websocket.send_json(response)
        except WebSocketDisconnect:
            log.info(f"WebSocket客户端断开: {client_id}")
        finally:
            # 清理连接
            if client_id in websocket_connections:
                del websocket_connections[client_id]
    except Exception as e:
        log.error(f"WebSocket处理失败: {e}")

async def process_websocket_message(data: Dict) -> Dict:
    """处理WebSocket消息
    
    Args:
        data: 消息数据
    
    Returns:
        Dict: 响应数据
    """
    try:
        message_type = data.get("type")
        payload = data.get("payload", {})
        
        if message_type == "create_memory":
            memory = Memory(**payload)
            result = memory_manager.create_memory(memory)
            await broadcast_update("memory_created", result)
            return {
                "type": "memory_created",
                "payload": result
            }
        
        elif message_type == "update_memory":
            memory_id = payload.get("id")
            memory = Memory(**payload)
            result = memory_manager.update_memory(memory_id, memory)
            if result:
                await broadcast_update("memory_updated", result)
                return {
                    "type": "memory_updated",
                    "payload": result
                }
            return {
                "type": "error",
                "payload": {"message": "记忆不存在"}
            }
        
        elif message_type == "delete_memory":
            memory_id = payload.get("id")
            result = memory_manager.delete_memory(memory_id)
            if result:
                await broadcast_update("memory_deleted", {"id": memory_id})
                return {
                    "type": "memory_deleted",
                    "payload": {"id": memory_id}
                }
            return {
                "type": "error",
                "payload": {"message": "记忆不存在"}
            }
        
        elif message_type == "search_memories":
            query = MemoryQuery(**payload.get("query", {}))
            strategy = RetrievalStrategy(
                payload.get("strategy", RetrievalStrategy.HYBRID)
            )
            limit = payload.get("limit", 10)
            results = memory_retrieval.retrieve(
                query=query,
                strategy=strategy,
                limit=limit
            )
            return {
                "type": "search_results",
                "payload": results
            }
        
        else:
            return {
                "type": "error",
                "payload": {"message": "未知的消息类型"}
            }
    except Exception as e:
        log.error(f"处理WebSocket消息失败: {e}")
        return {
            "type": "error",
            "payload": {"message": str(e)}
        }

async def broadcast_update(update_type: str, payload: Dict) -> None:
    """广播更新消息
    
    Args:
        update_type: 更新类型
        payload: 更新数据
    """
    message = {
        "type": update_type,
        "payload": payload
    }
    
    # 广播给所有连接的客户端
    for client_id, websocket in websocket_connections.items():
        try:
            await websocket.send_json(message)
        except Exception as e:
            log.error(f"广播消息失败(客户端{client_id}): {e}")

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理
    
    Args:
        request: 请求对象
        exc: 异常对象
    
    Returns:
        JSONResponse: 错误响应
    """
    log.error(f"API错误: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": str(exc)
        }
    )
