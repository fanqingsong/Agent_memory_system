"""聊天API模块

处理对话和LLM集成。

主要功能：
    - WebSocket对话接口
    - LLM集成(OpenAI/Ollama)
    - 对话记忆管理
    - 实时记忆检索

依赖：
    - fastapi: Web框架
    - openai: OpenAI API
    - httpx: HTTP客户端
    - memory_manager: 记忆管理
    - memory_retrieval: 记忆检索

作者：Cursor_for_YansongW
创建日期：2025-01-09
"""

import json
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
from pydantic import BaseModel

from agent_memory_system.core.memory.memory_manager import MemoryManager
from agent_memory_system.core.memory.memory_retrieval import MemoryRetrieval
from agent_memory_system.models.memory_model import Memory, MemoryType
from agent_memory_system.utils.config import config
from agent_memory_system.utils.logger import log
from agent_memory_system.utils.openai_client import LLMClient

router = APIRouter()

# 连接管理器
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.memory_manager = MemoryManager()
        self.memory_retrieval = MemoryRetrieval()
        self.llm_clients: Dict[str, LLMClient] = {}
    
    async def connect(self, client_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        log.info(f"WebSocket客户端连接: {client_id}")
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            if client_id in self.llm_clients:
                del self.llm_clients[client_id]
            log.info(f"WebSocket客户端断开: {client_id}")
    
    async def send_message(self, client_id: str, message: Dict):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)
    
    async def process_message(self, client_id: str, message: Dict):
        try:
            if message["type"] == "message":
                # 处理用户消息
                await self.handle_user_message(client_id, message)
            elif message["type"] == "settings":
                # 处理设置更新
                await self.handle_settings_update(client_id, message)
        except Exception as e:
            log.error(f"处理消息失败: {e}")
            await self.send_message(client_id, {
                "type": "error",
                "message": str(e)
            })
    
    async def handle_user_message(self, client_id: str, message: Dict):
        # 检查是否已配置LLM客户端
        if client_id not in self.llm_clients:
            await self.send_message(client_id, {
                "type": "error",
                "message": "请先配置LLM设置"
            })
            return
        
        # 获取相关记忆
        relevant_memories = self.memory_retrieval.search_memories(
            query=message["content"],
            limit=5,
            min_similarity=0.7
        )
        
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
        
        # 调用LLM生成回复
        llm_client = self.llm_clients[client_id]
        response = await llm_client.chat_completion(
            system_prompt=system_prompt,
            user_message=message["content"]
        )
        
        # 发送回复
        await self.send_message(client_id, {
            "type": "message",
            "content": response
        })
        
        # 存储对话记忆
        conversation_memory = Memory(
            content=f"用户: {message['content']}\n助手: {response}",
            memory_type=MemoryType.SHORT_TERM,
            importance=5,
            metadata={
                "source": "conversation",
                "timestamp": datetime.utcnow().isoformat(),
                "user_message": message["content"],
                "assistant_message": response,
                "relevant_memories": [str(m.id) for m in relevant_memories]
            }
        )
        
        self.memory_manager.store_memory(conversation_memory)
        
        # 通知前端更新记忆可视化
        await self.send_message(client_id, {
            "type": "memory_created",
            "memory": conversation_memory.dict()
        })
        
        # 高亮相关记忆
        for memory in relevant_memories:
            await self.send_message(client_id, {
                "type": "memory_accessed",
                "memory_id": str(memory.id)
            })
    
    async def handle_settings_update(self, client_id: str, message: Dict):
        settings = message["settings"]
        
        # 创建新的LLM客户端
        if settings["provider"] == "openai":
            if not settings.get("apiKey"):
                await self.send_message(client_id, {
                    "type": "error",
                    "message": "请提供OpenAI API密钥"
                })
                return
            
            llm_client = LLMClient(
                provider="openai",
                api_key=settings["apiKey"]
            )
        else:
            if not settings.get("ollamaModel"):
                await self.send_message(client_id, {
                    "type": "error",
                    "message": "请选择Ollama模型"
                })
                return
            
            llm_client = LLMClient(
                provider="ollama",
                model=settings["ollamaModel"],
                ollama_base_url=settings.get("ollamaBaseUrl", "http://localhost:11434")
            )
        
        # 验证LLM客户端配置
        if not await llm_client.validate_api_key():
            await self.send_message(client_id, {
                "type": "error",
                "message": "LLM配置验证失败"
            })
            return
        
        # 更新LLM客户端
        self.llm_clients[client_id] = llm_client
        
        # 更新记忆系统设置
        if "importanceThreshold" in settings:
            config.memory_config["importance_threshold"] = int(settings["importanceThreshold"])
        
        if "retentionDays" in settings:
            config.memory_config["retention_days"] = int(settings["retentionDays"])
        
        # 如果是Ollama,获取可用模型列表
        if settings["provider"] == "ollama":
            models = await llm_client.list_models()
            await self.send_message(client_id, {
                "type": "models_list",
                "models": models
            })
        
        await self.send_message(client_id, {
            "type": "settings_updated",
            "message": "设置已更新"
        })

manager = ConnectionManager()

@router.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    client_id = str(UUID.uuid4())
    await manager.connect(client_id, websocket)
    
    try:
        while True:
            message = await websocket.receive_json()
            await manager.process_message(client_id, message)
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        log.error(f"WebSocket错误: {e}")
        manager.disconnect(client_id)

class ChatMessage(BaseModel):
    """聊天消息模型"""
    content: str
    timestamp: datetime

@router.post("/chat/message")
async def send_message(message: ChatMessage):
    """发送聊天消息(HTTP接口)"""
    try:
        # 创建默认LLM客户端
        llm_client = LLMClient(
            provider=config.llm_config.get("provider", "openai"),
            api_key=config.llm_config.get("api_key"),
            model=config.llm_config.get("model"),
            ollama_base_url=config.llm_config.get("ollama_base_url")
        )
        
        # 处理消息
        response = await llm_client.chat_completion(
            system_prompt="你是一个有帮助的AI助手。",
            user_message=message.content
        )
        
        # 存储对话记忆
        conversation_memory = Memory(
            content=f"用户: {message.content}\n助手: {response}",
            memory_type=MemoryType.SHORT_TERM,
            importance=5,
            metadata={
                "source": "conversation",
                "timestamp": message.timestamp.isoformat(),
                "user_message": message.content,
                "assistant_message": response
            }
        )
        
        manager.memory_manager.store_memory(conversation_memory)
        
        return {
            "response": response,
            "memory_id": str(conversation_memory.id)
        }
    except Exception as e:
        log.error(f"处理消息失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        ) 