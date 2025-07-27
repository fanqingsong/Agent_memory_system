"""
WebSocket 模型定义

该模块定义了 WebSocket 通信相关的数据模型，包括消息格式和响应格式。

主要功能：
- WebSocket 消息模型
- WebSocket 响应模型
- 消息类型枚举
- 数据验证和序列化

作者：Cursor_for_YansongW
创建日期：2025-01-09
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum


class MessageType(str, Enum):
    """消息类型枚举"""
    PING = "ping"
    PONG = "pong"
    MESSAGE = "message"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    QUERY = "query"
    SETTINGS = "settings"
    ERROR = "error"
    WELCOME = "welcome"
    SUBSCRIBED = "subscribed"
    UNSUBSCRIBED = "unsubscribed"
    QUERY_RESULT = "query_result"
    MEMORY_CREATED = "memory_created"
    MEMORY_UPDATED = "memory_updated"
    MEMORY_DELETED = "memory_deleted"
    MEMORY_ACCESSED = "memory_accessed"


class WebSocketMessage(BaseModel):
    """WebSocket 消息模型"""
    type: MessageType = Field(..., description="消息类型")
    data: Optional[Dict[str, Any]] = Field(default=None, description="消息数据")
    timestamp: Optional[str] = Field(default=None, description="时间戳")
    client_id: Optional[str] = Field(default=None, description="客户端ID")

    class Config:
        json_encoders = {
            MessageType: lambda v: v.value
        }
    
    def dict(self, **kwargs):
        """重写dict方法，处理datetime序列化"""
        # 先获取原始数据
        data = super().dict(**kwargs)
        
        # 使用json序列化然后反序列化来确保所有对象都是JSON兼容的
        try:
            json_str = json.dumps(data, default=self._json_serializer)
            return json.loads(json_str)
        except Exception:
            # 如果json序列化失败，回退到原始方法
            return self._serialize_data(data)
    
    def _json_serializer(self, obj):
        """JSON序列化器，处理特殊对象"""
        if hasattr(obj, 'isoformat'):  # datetime对象
            return obj.isoformat()
        elif hasattr(obj, 'value'):  # Enum对象
            return obj.value
        else:
            return str(obj)
    
    def _serialize_data(self, obj):
        """序列化数据，处理datetime对象"""
        if isinstance(obj, dict):
            return {k: self._serialize_data(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_data(item) for item in obj]
        elif hasattr(obj, 'isoformat'):  # datetime对象
            return obj.isoformat()
        elif hasattr(obj, 'value'):  # Enum对象
            return obj.value
        else:
            return obj


class WebSocketResponse(BaseModel):
    """WebSocket 响应模型"""
    type: MessageType = Field(..., description="响应类型")
    data: Optional[Dict[str, Any]] = Field(default=None, description="响应数据")
    timestamp: Optional[str] = Field(default_factory=lambda: datetime.now().isoformat(), description="时间戳")
    success: bool = Field(default=True, description="是否成功")
    error: Optional[str] = Field(default=None, description="错误信息")

    class Config:
        json_encoders = {
            MessageType: lambda v: v.value
        }
    
    def model_dump(self, **kwargs):
        """重写model_dump方法，处理datetime序列化"""
        # 先获取原始数据
        data = super().model_dump(**kwargs)
        
        # 使用json序列化然后反序列化来确保所有对象都是JSON兼容的
        try:
            json_str = json.dumps(data, default=self._json_serializer)
            return json.loads(json_str)
        except Exception:
            # 如果json序列化失败，回退到原始方法
            return self._serialize_data(data)
    
    def dict(self, **kwargs):
        """兼容性方法，调用model_dump"""
        return self.model_dump(**kwargs)
    
    def _json_serializer(self, obj):
        """JSON序列化器，处理特殊对象"""
        if hasattr(obj, 'isoformat'):  # datetime对象
            return obj.isoformat()
        elif hasattr(obj, 'value'):  # Enum对象
            return obj.value
        else:
            return str(obj)
    
    def _serialize_data(self, obj):
        """序列化数据，处理datetime对象"""
        if isinstance(obj, dict):
            return {k: self._serialize_data(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_data(item) for item in obj]
        elif hasattr(obj, 'isoformat'):  # datetime对象
            return obj.isoformat()
        elif hasattr(obj, 'value'):  # Enum对象
            return obj.value
        else:
            return obj


class ChatMessage(BaseModel):
    """聊天消息模型"""
    content: str = Field(..., description="消息内容")
    sender: str = Field(..., description="发送者")
    timestamp: str = Field(..., description="时间戳")
    message_id: Optional[str] = Field(default=None, description="消息ID")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")


class ConnectionInfo(BaseModel):
    """连接信息模型"""
    client_id: str = Field(..., description="客户端ID")
    connected_at: str = Field(..., description="连接时间")
    last_activity: str = Field(..., description="最后活动时间")
    user_agent: Optional[str] = Field(default=None, description="用户代理")
    ip_address: Optional[str] = Field(default=None, description="IP地址")


class SubscriptionRequest(BaseModel):
    """订阅请求模型"""
    topics: list[str] = Field(..., description="订阅主题列表")
    client_id: Optional[str] = Field(default=None, description="客户端ID")


class BroadcastMessage(BaseModel):
    """广播消息模型"""
    type: MessageType = Field(..., description="消息类型")
    data: Dict[str, Any] = Field(..., description="消息数据")
    exclude_clients: Optional[list[str]] = Field(default=None, description="排除的客户端列表")
    topic: Optional[str] = Field(default=None, description="主题")


# 预定义的响应消息
def create_welcome_response(client_id: str) -> WebSocketResponse:
    """创建欢迎响应"""
    return WebSocketResponse(
        type=MessageType.WELCOME,
        data={"client_id": client_id, "message": "欢迎连接到 Agent Memory System"}
    )


def create_error_response(message: str, detail: Optional[str] = None) -> WebSocketResponse:
    """创建错误响应"""
    return WebSocketResponse(
        type=MessageType.ERROR,
        data={"message": message, "detail": detail},
        success=False,
        error=message
    )


def create_pong_response() -> WebSocketResponse:
    """创建 Pong 响应"""
    return WebSocketResponse(type=MessageType.PONG)


def create_subscribed_response(topics: list[str]) -> WebSocketResponse:
    """创建订阅成功响应"""
    return WebSocketResponse(
        type=MessageType.SUBSCRIBED,
        data={"topics": topics, "message": "订阅成功"}
    )


def create_unsubscribed_response(topics: list[str]) -> WebSocketResponse:
    """创建取消订阅成功响应"""
    return WebSocketResponse(
        type=MessageType.UNSUBSCRIBED,
        data={"topics": topics, "message": "取消订阅成功"}
    ) 