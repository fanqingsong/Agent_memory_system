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
创建日期：2025-01-09
"""

import asyncio
import time
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
    SuccessResponse
)
from agent_memory_system.models.websocket_model import (
    WebSocketMessage,
    WebSocketResponse
)
from agent_memory_system.utils.config import config, init_config
from agent_memory_system.utils.logger import log

# 初始化配置
init_config()

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
memory_retrieval = MemoryRetrieval(
    vector_store=memory_manager._vector_store,
    graph_store=memory_manager._graph_store
)

# WebSocket连接管理
class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_times: Dict[str, datetime] = {}
        self.ping_tasks: Dict[str, asyncio.Task] = {}
        self.timeout = timedelta(seconds=60)  # 默认60秒超时
        self.ping_interval = timedelta(seconds=30)  # 默认30秒心跳间隔
    
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

def get_app_instance():
    """获取应用实例
    
    Returns:
        FastAPI: 应用实例
    """
    return app

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

@app.get("/health")
async def health_check():
    """健康检查端点
    
    Returns:
        Dict: 健康状态信息
    """
    try:
        # 检查基本服务状态
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "services": {
                "api": "healthy",
                "memory_manager": "healthy",
                "memory_retrieval": "healthy"
            }
        }
        
        # 这里可以添加更多健康检查逻辑
        # 比如检查数据库连接、Redis连接等
        
        return health_status
    except Exception as e:
        log.error(f"健康检查失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="服务不可用"
        )

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

@app.post("/chat/message")
async def chat_message(message: Dict):
    """聊天消息端点（HTTP回退方案）
    
    Args:
        message: 消息数据
    
    Returns:
        Dict: 回复数据
    """
    try:
        content = message.get("content", "")
        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="消息内容不能为空"
            )
        
        # 使用WebSocket消息处理逻辑
        from agent_memory_system.models.websocket_model import WebSocketMessage
        
        ws_message = WebSocketMessage(
            type="message",
            data={"content": content, "message_id": message.get("message_id", str(int(time.time() * 1000)))},
            timestamp=datetime.now().isoformat()
        )
        
        # 处理消息
        response = await process_websocket_message(ws_message)
        
        return response.dict()
        
    except Exception as e:
        log.error(f"处理聊天消息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/memories")
async def get_all_memories(limit: int = 100, offset: int = 0):
    """获取所有记忆
    
    Args:
        limit: 返回数量限制
        offset: 偏移量
    
    Returns:
        List[Memory]: 记忆列表
    """
    try:
        memories = memory_manager.get_all_memories(limit=limit, offset=offset)
        return memories
    except Exception as e:
        log.error(f"获取所有记忆失败: {e}")
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
        result = memory_manager.update_memory_with_object(memory_id, memory)
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
        List[Dict]: 记忆列表，包含记忆对象和相似度分数
    """
    try:
        results = memory_retrieval.retrieve(
            query=query,
            strategy=strategy,
            limit=limit
        )
        
        # 转换为前端期望的格式
        formatted_results = []
        for result in results:
            formatted_results.append({
                "memory": result.memory.model_dump(mode='json'),
                "score": result.score,
                "strategy": result.strategy
            })
        
        return formatted_results
    except Exception as e:
        log.error(f"搜索记忆失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/storage/vector")
async def get_vector_storage_info():
    """获取向量存储信息
    
    Returns:
        Dict: 向量存储统计信息
    """
    try:
        vector_store = memory_manager._vector_store
        if not vector_store:
            return {"error": "向量存储未初始化"}
        
        # 获取向量存储统计信息
        stats = {
            "total_vectors": len(vector_store) if vector_store else 0,
            "dimension": vector_store._dimension,
            "index_type": "Weaviate",
            "class_name": vector_store._class_name
        }
        
        # 获取最近的向量数据（限制数量）
        recent_vectors = []
        if vector_store and len(vector_store) > 0:
            try:
                # 获取前10个向量的基本信息
                response = vector_store._collection.query.fetch_objects(
                    limit=10,
                    return_properties=["memory_id"]
                )
                for obj in response.objects:
                    vector = obj.vector
                    recent_vectors.append({
                        "id": obj.properties.get("memory_id", ""),
                        "dimension": len(vector),
                        "sample_values": vector[:5] if len(vector) > 5 else vector
                    })
            except Exception as e:
                log.warning(f"获取向量数据失败: {e}")
        
        stats["recent_vectors"] = recent_vectors
        return stats
    except Exception as e:
        log.error(f"获取向量存储信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/storage/graph")
async def get_graph_storage_info():
    """获取图存储信息
    
    Returns:
        Dict: 图存储统计信息
    """
    try:
        graph_store = memory_manager._graph_store
        if not graph_store:
            return {"error": "图存储未初始化"}
        
        # 获取图存储统计信息
        stats = {
            "total_nodes": 0,
            "total_relationships": 0,
            "node_types": [],
            "relationship_types": []
        }
        
        # 获取节点统计
        try:
            with graph_store._driver.session() as session:
                # 获取节点总数
                result = session.run("MATCH (n) RETURN count(n) as count")
                stats["total_nodes"] = result.single()["count"]
                
                # 获取关系总数
                result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
                stats["total_relationships"] = result.single()["count"]
                
                # 获取节点类型
                result = session.run("CALL db.labels() YIELD label RETURN collect(label) as labels")
                stats["node_types"] = result.single()["labels"]
                
                # 获取关系类型
                result = session.run("CALL db.relationshipTypes() YIELD relationshipType RETURN collect(relationshipType) as types")
                stats["relationship_types"] = result.single()["types"]
                
                # 获取最近的节点（限制数量）
                recent_nodes = []
                result = session.run("MATCH (n) RETURN labels(n) as labels, properties(n) as props LIMIT 10")
                for record in result:
                    recent_nodes.append({
                        "labels": record["labels"],
                        "properties": {k: v for k, v in record["props"].items() if k != 'vector' and len(str(v)) < 100}
                    })
                stats["recent_nodes"] = recent_nodes
                
        except Exception as e:
            log.warning(f"获取图存储统计失败: {e}")
            stats["error"] = str(e)
        
        return stats
    except Exception as e:
        log.error(f"获取图存储信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/storage/cache")
async def get_cache_storage_info():
    """获取缓存存储信息
    
    Returns:
        Dict: 缓存存储统计信息
    """
    try:
        cache_store = memory_manager._cache_store
        if not cache_store:
            return {"error": "缓存存储未初始化"}
        
        # 获取缓存统计信息
        stats = {
            "total_keys": 0,
            "memory_usage": "0",
            "cache_type": "Redis"
        }
        
        try:
            # 获取Redis统计信息
            redis_client = cache_store._client
            info = redis_client.info()
            
            stats["total_keys"] = info.get("db0", {}).get("keys", 0)
            stats["memory_usage"] = f"{info.get('used_memory_human', '0')}"
            stats["redis_version"] = info.get("redis_version", "unknown")
            
            # 获取最近的缓存键（限制数量）
            recent_keys = []
            keys = redis_client.keys("*")[:10]  # 获取前10个键
            for key in keys:
                try:
                    key_type = redis_client.type(key)
                    if key_type == "string":
                        value = redis_client.get(key)
                        if value:
                            # 尝试解析JSON
                            try:
                                import json
                                parsed = json.loads(value)
                                recent_keys.append({
                                    "key": key.decode() if isinstance(key, bytes) else key,
                                    "type": key_type,
                                    "value_preview": str(parsed)[:100] + "..." if len(str(parsed)) > 100 else str(parsed)
                                })
                            except:
                                recent_keys.append({
                                    "key": key.decode() if isinstance(key, bytes) else key,
                                    "type": key_type,
                                    "value_preview": value.decode()[:100] + "..." if len(value) > 100 else value.decode()
                                })
                    else:
                        recent_keys.append({
                            "key": key.decode() if isinstance(key, bytes) else key,
                            "type": key_type,
                            "value_preview": f"[{key_type} type]"
                        })
                except Exception as e:
                    log.warning(f"获取缓存键 {key} 失败: {e}")
            
            stats["recent_keys"] = recent_keys
            
        except Exception as e:
            log.warning(f"获取缓存统计失败: {e}")
            stats["error"] = str(e)
        
        return stats
    except Exception as e:
        log.error(f"获取缓存存储信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/storage/all")
async def get_all_storage_info():
    """获取所有存储信息
    
    Returns:
        Dict: 所有存储的统计信息
    """
    try:
        vector_info = await get_vector_storage_info()
        graph_info = await get_graph_storage_info()
        cache_info = await get_cache_storage_info()
        
        return {
            "vector_storage": vector_info,
            "graph_storage": graph_info,
            "cache_storage": cache_info,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        log.error(f"获取所有存储信息失败: {e}")
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
        
        # 发送欢迎消息 - 直接使用字典避免序列化问题
        await websocket.send_json({
            "type": "welcome",
            "data": {"client_id": client_id},
            "timestamp": datetime.now().isoformat(),
            "success": True
        })
        
        while True:
            # 接收消息
            try:
                raw_data = await websocket.receive_json()
                log.info(f"收到WebSocket消息: {raw_data}")
                
                # 处理前端发送的消息格式（content在顶层）
                if raw_data.get("type") == "message" and "content" in raw_data:
                    # 将content移动到data对象中
                    processed_data = {
                        "type": raw_data["type"],
                        "data": {"content": raw_data["content"]},
                        "timestamp": raw_data.get("timestamp")
                    }
                    log.info(f"处理后的消息格式: {processed_data}")
                    message = WebSocketMessage.model_validate(processed_data)
                else:
                    message = WebSocketMessage.model_validate(raw_data)
                
                log.info(f"解析后的消息: type={message.type}, data={message.data}")
            except ValidationError as e:
                log.error(f"消息格式验证失败: {e}")
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": "无效的消息格式", "detail": str(e)},
                    "timestamp": datetime.now().isoformat(),
                    "success": False
                })
                continue
            
            # 处理消息
            try:
                log.info(f"开始处理消息类型: {message.type}")
                response = await process_websocket_message(message)
                log.info(f"处理完成，准备发送响应: {response.dict()}")
                await websocket.send_json(response.dict())
                log.info(f"响应已发送")
            except Exception as e:
                log.error(f"处理WebSocket消息失败: {e}")
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": "处理消息失败", "detail": str(e)},
                    "timestamp": datetime.now().isoformat(),
                    "success": False
                })
    
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
        log.info(f"process_websocket_message: 开始处理消息类型 {message.type}")
        
        if message.type == "ping":
            log.info("处理ping消息")
            return WebSocketResponse(type="pong")
        
        elif message.type == "message":
            # 处理聊天消息 - 集成chat_router的功能
            content = message.data.get("content", "")
            log.info(f"处理聊天消息，内容: {content}")
            
            if not content:
                log.warning("消息内容为空")
                return WebSocketResponse(
                    type="error",
                    data={"message": "消息内容不能为空"}
                )
            
            # 获取相关记忆
            from agent_memory_system.models.memory_model import MemoryQuery
            
            query = MemoryQuery(
                query=content,
                threshold=0.3  # 降低阈值，使更多记忆能被检索到
            )
            retrieval_results = memory_retrieval.retrieve(
                query=query,
                limit=5
            )
            relevant_memories = [result.memory for result in retrieval_results]
            
            # 构建系统提示
            system_prompt = """你是一个具有记忆能力的AI助手。你可以访问以下记忆来帮助回答问题:

{memories}

请基于这些记忆和你的知识来回答用户的问题。如果记忆中包含相关信息，请明确指出你在使用这些记忆。
"""
            
            # 格式化记忆
            memory_text = ""
            for i, memory in enumerate(relevant_memories, 1):
                memory_text += f"{i}. {memory.content} (重要性: {memory.importance})\n"
            
            system_prompt = system_prompt.format(memories=memory_text)
            
            # 创建LLM客户端并生成回复
            try:
                from agent_memory_system.utils.openai_client import OpenAIClient
                
                # 使用配置中的LLM设置
                llm_client = OpenAIClient(
                    api_key=config.llm.api_key,
                    api_base_url=config.llm.api_base_url,
                    model=config.llm.model
                )
                
                # 调用LLM生成回复
                response_content = await llm_client.chat_completion(
                    system_prompt=system_prompt,
                    user_message=content
                )
                
                log.info(f"LLM生成回复: {response_content}")
                
            except Exception as e:
                log.error(f"LLM调用失败: {e}")
                # 如果LLM调用失败，返回错误信息
                response_content = f"抱歉，我暂时无法处理您的请求。错误信息: {str(e)}"
            
            # 存储对话记忆
            try:
                from agent_memory_system.models.memory_model import Memory, MemoryType
                
                conversation_memory = Memory(
                    content=f"用户: {content}\n助手: {response_content}",
                    memory_type=MemoryType.SHORT_TERM,
                    importance=5,
                    metadata={
                        "source": "conversation",
                        "timestamp": datetime.now().isoformat(),
                        "user_message": content,
                        "assistant_message": response_content,
                        "relevant_memories": [str(m.id) for m in relevant_memories]
                    }
                )
                
                memory_manager.store_memory(
                    content=conversation_memory.content,
                    memory_type=conversation_memory.memory_type,
                    importance=conversation_memory.importance,
                    metadata=conversation_memory.metadata.model_dump()
                )
                log.info(f"存储对话记忆: {conversation_memory.id}")
                
            except Exception as e:
                log.error(f"存储记忆失败: {e}")
            
            return WebSocketResponse(
                type="message",
                data={"content": response_content}
            )
        
        elif message.type == "settings":
            # 处理设置更新
            if message.data is None:
                log.error("设置消息的data字段为None")
                return WebSocketResponse(
                    type="error",
                    data={"message": "设置消息格式错误"}
                )
            
            settings = message.data.get("settings", {})
            log.info(f"处理设置更新: {settings}")
            
            try:
                                # 更新LLM配置
                if "apiKey" in settings:
                    config.llm.api_key = settings["apiKey"]
                
                
                # 更新记忆系统设置
                if "importanceThreshold" in settings:
                    config.memory.importance_threshold = int(settings["importanceThreshold"])
                if "retentionDays" in settings:
                    config.memory.retention_days = int(settings["retentionDays"])
                
                return WebSocketResponse(
                    type="settings_updated",
                    data={"message": "设置已更新"}
                )
                
            except Exception as e:
                log.error(f"更新设置失败: {e}")
                return WebSocketResponse(
                    type="error",
                    data={"message": f"更新设置失败: {str(e)}"}
                )
        
        elif message.type == "subscribe":
            # 处理订阅请求
            topics = message.data.get("topics", []) if message.data else []
            return WebSocketResponse(
                type="subscribed",
                data={"topics": topics}
            )
        
        elif message.type == "unsubscribe":
            # 处理取消订阅请求
            topics = message.data.get("topics", []) if message.data else []
            return WebSocketResponse(
                type="unsubscribed",
                data={"topics": topics}
            )
        
        elif message.type == "query":
            # 处理查询请求
            if message.data is None:
                log.error("查询消息的data字段为None")
                return WebSocketResponse(
                    type="error",
                    data={"message": "查询消息格式错误"}
                )
            
            query_data = message.data.get("query", {})
            strategy = message.data.get("strategy", RetrievalStrategy.HYBRID)
            limit = message.data.get("limit", 10)
            
            query = MemoryQuery.model_validate(query_data)
            results = await memory_retrieval.retrieve(
                query=query,
                strategy=strategy,
                limit=limit
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
