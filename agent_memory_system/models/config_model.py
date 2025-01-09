"""配置数据模型

定义系统配置相关的数据模型。

主要功能：
    - 定义配置数据结构
    - 提供配置验证
    - 提供配置序列化

依赖：
    - pydantic: 用于数据验证和序列化

作者：Cursor_for_YansongW
创建日期：2025-01-09
"""

from typing import Dict, Optional

from pydantic import BaseModel, Field, HttpUrl, validator

class LLMConfig(BaseModel):
    """LLM配置模型
    
    属性说明：
        - model: 模型名称
        - temperature: 温度参数
        - max_tokens: 最大token数
        - api_key: API密钥
        - api_base: API基础URL
    """
    
    model: str = Field(
        default="gpt-3.5-turbo",
        description="LLM模型名称"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="生成温度，控制随机性"
    )
    max_tokens: int = Field(
        default=2000,
        gt=0,
        description="单次生成的最大token数"
    )
    api_key: Optional[str] = Field(
        default=None,
        description="API密钥"
    )
    api_base: Optional[HttpUrl] = Field(
        default=None,
        description="API基础URL"
    )

class VectorConfig(BaseModel):
    """向量配置模型
    
    属性说明：
        - dimension: 向量维度
        - similarity_threshold: 相似度阈值
        - max_return_count: 最大返回数量
    """
    
    dimension: int = Field(
        default=768,
        gt=0,
        description="向量维度"
    )
    similarity_threshold: float = Field(
        default=0.85,
        gt=0.0,
        le=1.0,
        description="相似度阈值"
    )
    max_return_count: int = Field(
        default=100,
        gt=0,
        description="最大返回数量"
    )

class MemoryConfig(BaseModel):
    """记忆配置模型
    
    属性说明：
        - max_size: 最大记忆数量
        - timeout: 记忆超时时间(秒)
        - importance_threshold: 重要性阈值
    """
    
    max_size: int = Field(
        default=1000,
        gt=0,
        description="最大记忆数量"
    )
    timeout: int = Field(
        default=7 * 24 * 3600,  # 7天
        gt=0,
        description="记忆超时时间(秒)"
    )
    importance_threshold: int = Field(
        default=7,
        ge=1,
        le=10,
        description="重要性阈值"
    )

class DatabaseConfig(BaseModel):
    """数据库配置模型
    
    属性说明：
        - database_url: 主数据库URL
        - redis_url: Redis URL
        - neo4j_url: Neo4j URL
        - username: 数据库用户名
        - password: 数据库密码
    """
    
    database_url: str = Field(
        default="sqlite:///memory.db",
        description="主数据库URL"
    )
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis URL"
    )
    neo4j_url: str = Field(
        default="bolt://localhost:7687",
        description="Neo4j URL"
    )
    username: Optional[str] = Field(
        default=None,
        description="数据库用户名"
    )
    password: Optional[str] = Field(
        default=None,
        description="数据库密码"
    )
    
    @validator("database_url")
    def validate_database_url(cls, v: str) -> str:
        """验证数据库URL"""
        if not v.startswith(("sqlite://", "postgresql://", "mysql://")):
            raise ValueError("不支持的数据库类型")
        return v
    
    @validator("redis_url")
    def validate_redis_url(cls, v: str) -> str:
        """验证Redis URL"""
        if not v.startswith("redis://"):
            raise ValueError("无效的Redis URL")
        return v
    
    @validator("neo4j_url")
    def validate_neo4j_url(cls, v: str) -> str:
        """验证Neo4j URL"""
        if not v.startswith(("bolt://", "neo4j://")):
            raise ValueError("无效的Neo4j URL")
        return v

class SystemConfig(BaseModel):
    """系统配置模型
    
    属性说明：
        - debug: 是否为调试模式
        - log_level: 日志级别
        - api_port: API端口
        - llm: LLM配置
        - vector: 向量配置
        - memory: 记忆配置
        - database: 数据库配置
    """
    
    debug: bool = Field(
        default=False,
        description="是否为调试模式"
    )
    log_level: str = Field(
        default="INFO",
        description="日志级别"
    )
    api_port: int = Field(
        default=8000,
        gt=0,
        lt=65536,
        description="API端口"
    )
    llm: LLMConfig = Field(
        default_factory=LLMConfig,
        description="LLM配置"
    )
    vector: VectorConfig = Field(
        default_factory=VectorConfig,
        description="向量配置"
    )
    memory: MemoryConfig = Field(
        default_factory=MemoryConfig,
        description="记忆配置"
    )
    database: DatabaseConfig = Field(
        default_factory=DatabaseConfig,
        description="数据库配置"
    )
    
    @validator("log_level")
    def validate_log_level(cls, v: str) -> str:
        """验证日志级别"""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"无效的日志级别，有效值为: {valid_levels}")
        return v.upper()
    
    class Config:
        """Pydantic配置"""
        validate_assignment = True  # 赋值时进行验证
        extra = "forbid"  # 禁止额外字段
