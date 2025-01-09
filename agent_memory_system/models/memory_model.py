"""记忆数据模型

定义系统中记忆相关的数据模型。

主要功能：
    - 定义记忆数据结构
    - 提供记忆验证
    - 提供记忆序列化
    - 定义记忆关系模型

依赖：
    - pydantic: 用于数据验证和序列化
    - datetime: 用于时间处理

作者：Cursor_for_YansongW
创建日期：2024-01-09
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator

class MemoryType(str, Enum):
    """记忆类型枚举
    
    属性说明：
        - SHORT_TERM: 短期记忆
        - LONG_TERM: 长期记忆
        - WORKING: 工作记忆
        - SKILL: 技能记忆
    """
    
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    WORKING = "working"
    SKILL = "skill"

class MemoryStatus(str, Enum):
    """记忆状态枚举
    
    属性说明：
        - ACTIVE: 活跃状态
        - INACTIVE: 非活跃状态
        - ARCHIVED: 已归档
        - DELETED: 已删除
    """
    
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    DELETED = "deleted"

class MemoryRelationType(str, Enum):
    """记忆关系类型枚举
    
    属性说明：
        - TEMPORAL: 时间关系
        - CAUSAL: 因果关系
        - SEMANTIC: 语义关系
        - HIERARCHICAL: 层级关系
        - ASSOCIATIVE: 联想关系
    """
    
    TEMPORAL = "temporal"
    CAUSAL = "causal"
    SEMANTIC = "semantic"
    HIERARCHICAL = "hierarchical"
    ASSOCIATIVE = "associative"

class MemoryMetadata(BaseModel):
    """记忆元数据模型
    
    属性说明：
        - source: 记忆来源
        - context: 上下文信息
        - emotion: 情感标签
        - tags: 标签列表
        - custom_data: 自定义数据
    """
    
    source: str = Field(
        default="user_input",
        description="记忆来源"
    )
    context: Optional[str] = Field(
        default=None,
        description="上下文信息"
    )
    emotion: Optional[str] = Field(
        default=None,
        description="情感标签"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="标签列表"
    )
    custom_data: Dict = Field(
        default_factory=dict,
        description="自定义数据"
    )

class MemoryVector(BaseModel):
    """记忆向量模型
    
    属性说明：
        - vector: 向量数据
        - model_name: 编码模型名称
        - dimension: 向量维度
    """
    
    vector: List[float] = Field(
        ...,
        description="向量数据"
    )
    model_name: str = Field(
        default="sentence-transformers",
        description="编码模型名称"
    )
    dimension: int = Field(
        ...,
        gt=0,
        description="向量维度"
    )
    
    @validator("vector")
    def validate_vector_dimension(cls, v: List[float], values: Dict) -> List[float]:
        """验证向量维度"""
        if "dimension" in values and len(v) != values["dimension"]:
            raise ValueError(f"向量维度不匹配，期望{values['dimension']}，实际{len(v)}")
        return v

class MemoryRelation(BaseModel):
    """记忆关系模型
    
    属性说明：
        - source_id: 源记忆ID
        - target_id: 目标记忆ID
        - relation_type: 关系类型
        - weight: 关系权重
        - metadata: 关系元数据
    """
    
    source_id: UUID = Field(
        ...,
        description="源记忆ID"
    )
    target_id: UUID = Field(
        ...,
        description="目标记忆ID"
    )
    relation_type: MemoryRelationType = Field(
        ...,
        description="关系类型"
    )
    weight: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="关系权重"
    )
    metadata: Dict = Field(
        default_factory=dict,
        description="关系元数据"
    )

class Memory(BaseModel):
    """记忆模型
    
    属性说明：
        - id: 记忆ID
        - content: 记忆内容
        - memory_type: 记忆类型
        - importance: 重要性评分
        - status: 记忆状态
        - vector: 向量表示
        - metadata: 元数据
        - relations: 关系列表
        - created_at: 创建时间
        - updated_at: 更新时间
        - accessed_at: 最后访问时间
        - access_count: 访问次数
    """
    
    id: UUID = Field(
        default_factory=uuid4,
        description="记忆ID"
    )
    content: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="记忆内容"
    )
    memory_type: MemoryType = Field(
        ...,
        description="记忆类型"
    )
    importance: int = Field(
        default=5,
        ge=1,
        le=10,
        description="重要性评分"
    )
    status: MemoryStatus = Field(
        default=MemoryStatus.ACTIVE,
        description="记忆状态"
    )
    vector: Optional[MemoryVector] = Field(
        default=None,
        description="向量表示"
    )
    metadata: MemoryMetadata = Field(
        default_factory=MemoryMetadata,
        description="元数据"
    )
    relations: List[MemoryRelation] = Field(
        default_factory=list,
        description="关系列表"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="创建时间"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="更新时间"
    )
    accessed_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="最后访问时间"
    )
    access_count: int = Field(
        default=0,
        ge=0,
        description="访问次数"
    )
    
    def update_access(self) -> None:
        """更新访问信息"""
        self.accessed_at = datetime.utcnow()
        self.access_count += 1
    
    def add_relation(
        self,
        target_id: Union[UUID, str],
        relation_type: Union[MemoryRelationType, str],
        weight: float = 1.0,
        metadata: Optional[Dict] = None
    ) -> None:
        """添加记忆关系
        
        Args:
            target_id: 目标记忆ID
            relation_type: 关系类型
            weight: 关系权重
            metadata: 关系元数据
        """
        if isinstance(target_id, str):
            target_id = UUID(target_id)
        if isinstance(relation_type, str):
            relation_type = MemoryRelationType(relation_type)
        
        relation = MemoryRelation(
            source_id=self.id,
            target_id=target_id,
            relation_type=relation_type,
            weight=weight,
            metadata=metadata or {}
        )
        self.relations.append(relation)
        self.updated_at = datetime.utcnow()
    
    def remove_relation(self, target_id: Union[UUID, str]) -> None:
        """移除记忆关系
        
        Args:
            target_id: 目标记忆ID
        """
        if isinstance(target_id, str):
            target_id = UUID(target_id)
        
        self.relations = [r for r in self.relations if r.target_id != target_id]
        self.updated_at = datetime.utcnow()
    
    class Config:
        """Pydantic配置"""
        validate_assignment = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }
