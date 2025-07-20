"""记忆数据模型

定义系统中记忆相关的数据模型。

主要功能：
    - 定义记忆数据结构
    - 提供记忆验证
    - 提供记忆序列化
    - 定义记忆关系模型
    - 提供版本控制

依赖：
    - pydantic: 用于数据验证和序列化
    - datetime: 用于时间处理

作者：Cursor_for_YansongW
创建日期：2025-01-09
"""

from datetime import datetime, timezone
from enum import Enum
import re
from typing import Dict, List, Optional, Set, Union, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator, model_validator

class ModelVersion(str, Enum):
    """模型版本枚举
    
    用于记录模型的版本信息,便于后续升级和迁移。
    """
    
    V1_0_0 = "1.0.0"  # 初始版本
    V1_1_0 = "1.1.0"  # 添加版本控制
    V1_2_0 = "1.2.0"  # 添加关系验证

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

class RetrievalStrategy(str, Enum):
    """检索策略枚举
    
    属性说明：
        - VECTOR: 向量检索
        - KEYWORD: 关键词检索
        - HYBRID: 混合检索
        - GRAPH: 图检索
        - SEMANTIC: 语义检索
    """
    
    VECTOR = "vector"
    KEYWORD = "keyword"
    HYBRID = "hybrid"
    GRAPH = "graph"
    SEMANTIC = "semantic"

class MemoryMetadata(BaseModel):
    """记忆元数据模型
    
    属性说明：
        - source: 记忆来源
        - context: 上下文信息
        - emotion: 情感标签
        - tags: 标签列表
        - custom_data: 自定义数据
        - version: 模型版本
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
    version: ModelVersion = Field(
        default=ModelVersion.V1_2_0,
        description="模型版本"
    )
    
    @validator("tags")
    def validate_tags(cls, v: List[str]) -> List[str]:
        """验证标签列表
        
        - 标签不能为空
        - 标签长度不超过50
        - 标签只能包含字母、数字、下划线
        """
        pattern = re.compile(r"^[a-zA-Z0-9_]+$")
        for tag in v:
            if not tag:
                raise ValueError("标签不能为空")
            if len(tag) > 50:
                raise ValueError(f"标签长度不能超过50: {tag}")
            if not pattern.match(tag):
                raise ValueError(f"标签只能包含字母、数字、下划线: {tag}")
        return v
    
    @validator("emotion")
    def validate_emotion(cls, v: Optional[str]) -> Optional[str]:
        """验证情感标签
        
        - 情感标签只能是预定义的值
        """
        if v is not None:
            valid_emotions = {
                "positive", "negative", "neutral",
                "happy", "sad", "angry", "fear", "surprise"
            }
            if v.lower() not in valid_emotions:
                raise ValueError(f"无效的情感标签: {v}")
            return v.lower()
        return v

class MemoryVector(BaseModel):
    """记忆向量模型
    
    属性说明：
        - vector: 向量数据
        - model_name: 编码模型名称
        - dimension: 向量维度
        - version: 模型版本
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
    version: ModelVersion = Field(
        default=ModelVersion.V1_2_0,
        description="模型版本"
    )
    
    @validator("vector")
    def validate_vector_dimension(cls, v: List[float], values: Dict) -> List[float]:
        """验证向量维度"""
        if "dimension" in values and len(v) != values["dimension"]:
            raise ValueError(f"向量维度不匹配，期望{values['dimension']}，实际{len(v)}")
        return v
    
    @validator("model_name")
    def validate_model_name(cls, v: str) -> str:
        """验证模型名称
        
        - 模型名称不能为空
        - 模型名称长度不超过100
        - 模型名称只能包含字母、数字、下划线、横线和斜杠
        """
        if not v:
            raise ValueError("模型名称不能为空")
        if len(v) > 100:
            raise ValueError("模型名称长度不能超过100")
        pattern = re.compile(r"^[a-zA-Z0-9_\-/]+$")
        if not pattern.match(v):
            raise ValueError("模型名称只能包含字母、数字、下划线、横线和斜杠")
        return v

class MemoryRelation(BaseModel):
    """记忆关系模型
    
    属性说明：
        - source_id: 源记忆ID
        - target_id: 目标记忆ID
        - relation_type: 关系类型
        - weight: 关系权重
        - metadata: 关系元数据
        - version: 模型版本
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
    version: ModelVersion = Field(
        default=ModelVersion.V1_2_0,
        description="模型版本"
    )
    
    @validator("target_id")
    def validate_target_id(cls, v: UUID, values: Dict) -> UUID:
        """验证目标ID不能等于源ID"""
        if "source_id" in values and v == values["source_id"]:
            raise ValueError("目标ID不能等于源ID")
        return v
    
    @model_validator(mode='after')
    def validate_relation(self) -> 'MemoryRelation':
        """验证关系
        
        - TEMPORAL关系必须包含时间信息
        - CAUSAL关系必须包含原因和结果
        - HIERARCHICAL关系必须指定层级
        """
        if self.relation_type == MemoryRelationType.TEMPORAL:
            if "timestamp" not in self.metadata:
                raise ValueError("TEMPORAL关系必须包含时间信息")
        elif self.relation_type == MemoryRelationType.CAUSAL:
            if "cause" not in self.metadata or "effect" not in self.metadata:
                raise ValueError("CAUSAL关系必须包含原因和结果")
        elif self.relation_type == MemoryRelationType.HIERARCHICAL:
            if "level" not in self.metadata:
                raise ValueError("HIERARCHICAL关系必须指定层级")
        
        return self

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
        - version: 模型版本
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
        default_factory=lambda: datetime.now(timezone.utc),
        description="创建时间"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="更新时间"
    )
    accessed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="最后访问时间"
    )
    access_count: int = Field(
        default=0,
        ge=0,
        description="访问次数"
    )
    version: ModelVersion = Field(
        default=ModelVersion.V1_2_0,
        description="模型版本"
    )
    
    def update_access(self) -> None:
        """更新访问信息"""
        self.accessed_at = datetime.now(timezone.utc)
        self.access_count += 1
    
    def add_relation(
        self,
        target_id: Union[UUID, str],
        relation_type: Union[MemoryRelationType, str],
        weight: float = 1.0,
        metadata: Optional[Dict] = None
    ) -> None:
        """添加关系
        
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
    
    def remove_relation(self, target_id: Union[UUID, str]) -> None:
        """移除关系
        
        Args:
            target_id: 目标记忆ID
        """
        if isinstance(target_id, str):
            target_id = UUID(target_id)
        
        self.relations = [
            r for r in self.relations
            if r.target_id != target_id
        ]
    
    @model_validator(mode='after')
    def validate_memory(self) -> 'Memory':
        """验证记忆
        
        - 重要性高的记忆必须有向量表示
        - 技能记忆必须包含步骤信息
        - 删除状态的记忆不能添加新关系
        """
        if self.importance >= 8 and self.vector is None:
            raise ValueError("重要性高的记忆必须有向量表示")
        
        if self.memory_type == MemoryType.SKILL:
            if "steps" not in self.metadata.custom_data:
                raise ValueError("技能记忆必须包含步骤信息")
        
        if self.status == MemoryStatus.DELETED and self.relations:
            raise ValueError("删除状态的记忆不能添加新关系")
        
        return self
    
    class Config:
        """Pydantic配置"""
        validate_assignment = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }
        
        @classmethod
        def json_schema_extra(cls, schema: Dict) -> None:
            """添加模型版本信息到schema"""
            schema["version"] = ModelVersion.V1_2_0.value

class MemoryQuery(BaseModel):
    """记忆查询模型
    
    属性说明：
        - query: 查询文本
        - strategy: 检索策略
        - filters: 过滤条件
        - limit: 返回数量限制
        - threshold: 相似度阈值
        - metadata: 查询元数据
    """
    
    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="查询文本"
    )
    strategy: str = Field(
        default="hybrid",
        description="检索策略"
    )
    filters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="过滤条件"
    )
    limit: int = Field(
        default=10,
        gt=0,
        le=100,
        description="返回数量限制"
    )
    threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="相似度阈值"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="查询元数据"
    )
    
    @validator("strategy")
    def validate_strategy(cls, v: str) -> str:
        """验证检索策略"""
        valid_strategies = {"vector", "keyword", "hybrid", "semantic"}
        if v not in valid_strategies:
            raise ValueError(f"不支持的检索策略，有效值为: {valid_strategies}")
        return v

class RetrievalResult(BaseModel):
    """检索结果模型
    
    属性说明：
        - memory: 记忆对象
        - score: 相关性得分
        - strategy: 检索策略
        - metadata: 检索元数据
    """
    
    memory: Memory = Field(
        ...,
        description="记忆对象"
    )
    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="相关性得分"
    )
    strategy: str = Field(
        default="hybrid",
        description="检索策略"
    )
    metadata: Dict = Field(
        default_factory=dict,
        description="检索元数据"
    )
