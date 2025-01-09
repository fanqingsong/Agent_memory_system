"""API模型定义模块

定义API请求和响应的数据模型。

主要功能：
    - 请求模型定义
    - 响应模型定义
    - WebSocket消息模型
    - 错误响应模型
    - 版本信息模型

依赖：
    - pydantic: 用于数据验证和序列化

作者：Cursor_for_YansongW
创建日期：2025-01-09
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator

class ErrorResponse(BaseModel):
    """错误响应模型"""
    code: int = Field(..., description="错误代码")
    message: str = Field(..., description="错误消息")
    detail: Optional[Any] = Field(None, description="错误详情")

class SuccessResponse(BaseModel):
    """成功响应模型"""
    code: int = Field(200, description="状态代码")
    message: str = Field("success", description="状态消息")
    data: Optional[Any] = Field(None, description="响应数据")

class PaginationResponse(BaseModel):
    """分页响应模型"""
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")
    items: List[Any] = Field(..., description="数据列表")

class VersionInfo(BaseModel):
    """版本信息模型"""
    version: str = Field(..., description="API版本")
    build_date: str = Field(..., description="构建日期")
    supported_versions: List[str] = Field(..., description="支持的版本")

class WebSocketMessage(BaseModel):
    """WebSocket消息模型"""
    type: str = Field(..., description="消息类型")
    data: Dict[str, Any] = Field(default_factory=dict, description="消息数据")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="时间戳")
    
    @validator("type")
    def validate_type(cls, v: str) -> str:
        """验证消息类型"""
        valid_types = {
            "ping",
            "pong",
            "subscribe",
            "unsubscribe",
            "query",
            "error"
        }
        if v not in valid_types:
            raise ValueError(f"不支持的消息类型: {v}")
        return v

class WebSocketResponse(BaseModel):
    """WebSocket响应模型"""
    type: str = Field(..., description="响应类型")
    data: Dict[str, Any] = Field(default_factory=dict, description="响应数据")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="时间戳")
    
    @validator("type")
    def validate_type(cls, v: str) -> str:
        """验证响应类型"""
        valid_types = {
            "welcome",
            "pong",
            "subscribed",
            "unsubscribed",
            "query_result",
            "error"
        }
        if v not in valid_types:
            raise ValueError(f"不支持的响应类型: {v}")
        return v

class CreateMemoryRequest(BaseModel):
    """创建记忆请求模型"""
    content: str = Field(..., min_length=1, max_length=10000, description="记忆内容")
    memory_type: str = Field(..., description="记忆类型")
    importance: int = Field(5, ge=1, le=10, description="重要性评分")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")
    vector: Optional[List[float]] = Field(None, description="向量表示")

class UpdateMemoryRequest(BaseModel):
    """更新记忆请求模型"""
    content: Optional[str] = Field(None, min_length=1, max_length=10000, description="记忆内容")
    importance: Optional[int] = Field(None, ge=1, le=10, description="重要性评分")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")
    status: Optional[str] = Field(None, description="记忆状态")

class SearchMemoryRequest(BaseModel):
    """搜索记忆请求模型"""
    query: str = Field(..., min_length=1, max_length=1000, description="搜索查询")
    strategy: str = Field("hybrid", description="检索策略")
    filters: Optional[Dict[str, Any]] = Field(None, description="过滤条件")
    limit: int = Field(10, gt=0, le=100, description="返回数量限制")

class AddRelationRequest(BaseModel):
    """添加关系请求模型"""
    target_id: str = Field(..., description="目标记忆ID")
    relation_type: str = Field(..., description="关系类型")
    weight: float = Field(1.0, ge=0.0, le=1.0, description="关系权重")
    metadata: Optional[Dict[str, Any]] = Field(None, description="关系元数据")

class BatchOperationRequest(BaseModel):
    """批量操作请求模型"""
    operation: str = Field(..., description="操作类型")
    items: List[Dict[str, Any]] = Field(..., description="操作项目")
    
    @validator("operation")
    def validate_operation(cls, v: str) -> str:
        """验证操作类型"""
        valid_operations = {
            "create",
            "update",
            "delete",
            "retrieve"
        }
        if v not in valid_operations:
            raise ValueError(f"不支持的操作类型: {v}")
        return v

class BatchOperationResponse(BaseModel):
    """批量操作响应模型"""
    success_count: int = Field(..., description="成功数量")
    failed_count: int = Field(..., description="失败数量")
    results: List[Dict[str, Any]] = Field(..., description="操作结果")
    errors: List[Dict[str, Any]] = Field(..., description="错误信息") 