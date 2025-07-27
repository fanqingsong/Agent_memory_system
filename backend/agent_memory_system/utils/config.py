"""配置管理模块

提供系统配置的统一管理。

主要功能：
    - 环境变量加载
    - 配置验证
    - 默认值设置
    - 配置热更新

依赖：
    - pydantic: 数据验证
    - os: 环境变量
    - dotenv: 环境变量文件

作者：Cursor_for_YansongW
创建日期：2025-01-09
"""

import os
from typing import Optional
from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    """LLM配置"""
    provider: str = "openai"
    api_key: Optional[str] = None
    api_base_url: Optional[str] = None
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: int = 1000


class EmbeddingConfig(BaseModel):
    """Embedding配置"""
    model_name: str = "BAAI/bge-large-zh-v1.5"
    device: Optional[str] = None
    max_length: int = 512
    dimension: int = 1024


class MemoryConfig(BaseModel):
    """记忆系统配置"""
    importance_threshold: int = 5
    retention_days: int = 7
    max_size: int = 10000


class StorageConfig(BaseModel):
    """存储配置"""
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    faiss_index_path: str = "./data/faiss_index"


class PerformanceConfig(BaseModel):
    """性能配置"""
    batch_size: int = 32
    num_workers: int = 4
    cache_size: int = 1000


class LogConfig(BaseModel):
    """日志配置"""
    level: str = "INFO"
    file: str = "./logs/app.log"
    format: str = "{time} | {level} | {message}"


class SecurityConfig(BaseModel):
    """安全配置"""
    encryption_key: str = "your-secret-encryption-key"
    api_key: str = "your-secret-api-key"
    allowed_origins: str = "*"


class Config(BaseModel):
    """主配置类"""
    llm: LLMConfig = Field(default_factory=LLMConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    log: LogConfig = Field(default_factory=LogConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)


# 全局配置实例
config = Config()


def init_config():
    """初始化配置"""
    global config
    
    # LLM配置
    config.llm.provider = os.getenv("LLM_PROVIDER", "openai")
    config.llm.api_key = os.getenv("OPENAI_API_KEY")
    config.llm.api_base_url = os.getenv("OPENAI_API_BASE_URL")
    config.llm.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    config.llm.temperature = float(os.getenv("TEMPERATURE", "0.7"))
    config.llm.max_tokens = int(os.getenv("MAX_TOKENS", "1000"))
    
    # Embedding配置
    config.embedding.model_name = os.getenv("OPENAI_EMBEDDING_MODEL", "BAAI/bge-large-zh-v1.5")
    config.embedding.device = os.getenv("MODEL_DEVICE")
    config.embedding.max_length = int(os.getenv("MAX_LENGTH", "512"))
    config.embedding.dimension = int(os.getenv("EMBEDDING_DIMENSION", "1024"))
    
    # 记忆系统配置
    config.memory.importance_threshold = int(os.getenv("MEMORY_IMPORTANCE_THRESHOLD", "5"))
    config.memory.retention_days = int(os.getenv("MEMORY_RETENTION_DAYS", "7"))
    config.memory.max_size = int(os.getenv("MEMORY_MAX_SIZE", "10000"))
    
    # 存储配置
    config.storage.neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    config.storage.neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    config.storage.neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
    config.storage.redis_host = os.getenv("REDIS_HOST", "localhost")
    config.storage.redis_port = int(os.getenv("REDIS_PORT", "6379"))
    config.storage.redis_db = int(os.getenv("REDIS_DB", "0"))
    config.storage.redis_password = os.getenv("REDIS_PASSWORD")
    config.storage.faiss_index_path = os.getenv("FAISS_INDEX_PATH", "./data/faiss_index")
    
    # 性能配置
    config.performance.batch_size = int(os.getenv("BATCH_SIZE", "32"))
    config.performance.num_workers = int(os.getenv("NUM_WORKERS", "4"))
    config.performance.cache_size = int(os.getenv("CACHE_SIZE", "1000"))
    
    # 日志配置
    config.log.level = os.getenv("LOG_LEVEL", "INFO")
    config.log.file = os.getenv("LOG_FILE", "./logs/app.log")
    config.log.format = os.getenv("LOG_FORMAT", "{time} | {level} | {message}")
    
    # 安全配置
    config.security.encryption_key = os.getenv("ENCRYPTION_KEY", "your-secret-encryption-key")
    config.security.api_key = os.getenv("API_KEY", "your-secret-api-key")
    config.security.allowed_origins = os.getenv("ALLOWED_ORIGINS", "*")
