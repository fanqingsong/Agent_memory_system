"""WebSocket处理模块

提供WebSocket连接的处理逻辑。

主要功能：
    - WebSocket连接管理
    - 消息处理
    - 实时通信
    - 状态同步

作者：Cursor_for_YansongW
创建日期：2025-01-09
"""

from typing import Dict, List, Optional
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from agent_memory_system.core.memory.memory_manager import MemoryManager
from agent_memory_system.models.memory_model import Memory, MemoryType
from agent_memory_system.utils.logger import log

class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.memory_manager = MemoryManager()
    
    async def connect(self, websocket: WebSocket):
        """建立WebSocket连接"""
        await websocket.accept()
        self.active_connections.append(websocket)
        log.info(f"新的WebSocket连接: {len(self.active_connections)}个活动连接")
    
    def disconnect(self, websocket: WebSocket):
        """断开WebSocket连接"""
        self.active_connections.remove(websocket)
        log.info(f"WebSocket连接断开: {len(self.active_connections)}个活动连接")
    
    async def broadcast(self, message: dict):
        """广播消息到所有连接"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                log.error(f"广播消息失败: {str(e)}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """发送个人消息"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            log.error(f"发送个人消息失败: {str(e)}")

# 创建连接管理器实例
manager = ConnectionManager()

async def websocket_endpoint(websocket: WebSocket):
    """WebSocket端点处理函数"""
    await manager.connect(websocket)
    try:
        while True:
            # 接收消息
            data = await websocket.receive_json()
            
            try:
                # 处理消息
                if data["type"] == "message":
                    # 处理聊天消息
                    response = await process_message(data)
                    await manager.send_personal_message(response, websocket)
                
                elif data["type"] == "memory_create":
                    # 创建新记忆
                    memory = await create_memory(data)
                    # 广播新记忆到所有连接
                    await manager.broadcast({
                        "type": "memory_created",
                        "memory": memory.dict()
                    })
                
                elif data["type"] == "memory_access":
                    # 访问记忆
                    memory = await access_memory(data["memory_id"])
                    await manager.send_personal_message({
                        "type": "memory_accessed",
                        "memory": memory.dict()
                    }, websocket)
                
                elif data["type"] == "settings":
                    # 更新设置
                    await update_settings(data["settings"])
                    await manager.send_personal_message({
                        "type": "settings_updated",
                        "settings": data["settings"]
                    }, websocket)
                
            except Exception as e:
                # 发送错误消息
                await manager.send_personal_message({
                    "type": "error",
                    "message": str(e)
                }, websocket)
                log.error(f"处理WebSocket消息失败: {str(e)}")
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        log.error(f"WebSocket连接异常: {str(e)}")
        manager.disconnect(websocket)

async def process_message(data: dict) -> dict:
    """处理聊天消息"""
    try:
        # 这里可以添加消息处理逻辑
        # 例如：调用LLM、生成回复等
        return {
            "type": "message",
            "content": f"收到消息: {data['content']}"
        }
    except Exception as e:
        log.error(f"处理消息失败: {str(e)}")
        raise

async def create_memory(data: dict) -> Memory:
    """创建新记忆"""
    try:
        memory = Memory(
            content=data["content"],
            memory_type=MemoryType(data["memory_type"]),
            importance=data.get("importance", 5)
        )
        return manager.memory_manager.store_memory(memory)
    except Exception as e:
        log.error(f"创建记忆失败: {str(e)}")
        raise

async def access_memory(memory_id: str) -> Memory:
    """访问记忆"""
    try:
        return manager.memory_manager.get_memory(memory_id)
    except Exception as e:
        log.error(f"访问记忆失败: {str(e)}")
        raise

async def update_settings(settings: dict):
    """更新设置"""
    try:
        # 这里可以添加设置更新逻辑
        pass
    except Exception as e:
        log.error(f"更新设置失败: {str(e)}")
        raise 