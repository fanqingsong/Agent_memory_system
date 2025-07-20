"""配置管理模块

管理应用程序配置。

主要功能：
    - 加载环境变量
    - 配置验证
    - 配置访问

依赖：
    - pydantic: 数据验证
    - dotenv: 环境变量

作者：Cursor_for_YansongW
创建日期：2025-01-09
"""

import os
from typing import Optional, Dict, Any, Literal, cast
from pydantic import BaseModel, Field

class ServiceConfig(BaseModel):
    """服务配置"""
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

class Neo4jConfig(BaseModel):
    """Neo4j配置"""
    uri: str = "bolt://localhost:7687"
    user: str = "neo4j"
    password: str = "password"

class RedisConfig(BaseModel):
    """Redis配置"""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None

class FAISSConfig(BaseModel):
    """FAISS配置"""
    index_path: str = "data/faiss_index"
    use_gpu: bool = False

class ModelConfig(BaseModel):
    """模型配置"""
    device: Literal["cpu", "cuda"] = "cpu"
    precision: Literal["float32", "float16"] = "float32"

class LLMConfig(BaseModel):
    """LLM配置"""
    provider: Literal["openai", "ollama"] = "ollama"
    api_key: Optional[str] = None
    api_base_url: Optional[str] = None
    model: str = "gpt-3.5-turbo"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:0.5b"
    temperature: float = 0.7
    max_tokens: int = 1000

class MemoryConfig(BaseModel):
    """记忆系统配置"""
    importance_threshold: int = 5
    retention_days: int = 7
    max_size: int = 10000

class EmbeddingConfig(BaseModel):
    """Embedding配置"""
    model_name: str = "all-MiniLM-L6-v2"
    device: Optional[str] = None  # None表示自动选择
    max_length: int = 512
    dimension: int = 384  # all-MiniLM-L6-v2的默认维度

class PerformanceConfig(BaseModel):
    """性能配置"""
    batch_size: int = 32
    num_workers: int = 4
    cache_size: int = 1000

class LogConfig(BaseModel):
    """日志配置"""
    level: str = "INFO"
    file: str = "logs/app.log"
    format: str = "{time} | {level} | {message}"

class SecurityConfig(BaseModel):
    """安全配置"""
    encryption_key: str = Field(default="your-secret-encryption-key", description="用于加密敏感数据")
    api_key: str = Field(default="your-secret-api-key", description="API访问密钥")
    allowed_origins: str = "*"

class OtherConfig(BaseModel):
    """其他配置"""
    timezone: str = "UTC"
    language: str = "zh-CN"

class Config:
    """应用程序配置"""
    def __init__(self, **kwargs):
        # 初始化配置对象
        self.service = ServiceConfig()
        self.neo4j = Neo4jConfig()
        self.redis = RedisConfig()
        self.faiss = FAISSConfig()
        self.model = ModelConfig()
        self.llm = LLMConfig()
        self.memory = MemoryConfig()
        self.embedding = EmbeddingConfig()
        self.performance = PerformanceConfig()
        self.log = LogConfig()
        self.security = SecurityConfig()
        self.other = OtherConfig()
        
        # 从环境变量加载配置
        self.service.host = os.getenv("SERVICE_HOST", self.service.host)
        self.service.port = int(os.getenv("SERVICE_PORT", str(self.service.port)))
        self.service.debug = os.getenv("DEBUG", str(self.service.debug)).lower() == "true"
        
        self.neo4j.uri = os.getenv("NEO4J_URI", self.neo4j.uri)
        self.neo4j.user = os.getenv("NEO4J_USER", self.neo4j.user)
        self.neo4j.password = os.getenv("NEO4J_PASSWORD", self.neo4j.password)
        
        self.redis.host = os.getenv("REDIS_HOST", self.redis.host)
        self.redis.port = int(os.getenv("REDIS_PORT", str(self.redis.port)))
        self.redis.db = int(os.getenv("REDIS_DB", str(self.redis.db)))
        self.redis.password = os.getenv("REDIS_PASSWORD", self.redis.password)
        
        self.faiss.index_path = os.getenv("FAISS_INDEX_PATH", self.faiss.index_path)
        self.faiss.use_gpu = os.getenv("FAISS_USE_GPU", str(self.faiss.use_gpu)).lower() == "true"
        
        self.model.device = cast(Literal["cpu", "cuda"], os.getenv("MODEL_DEVICE", self.model.device))
        self.model.precision = cast(Literal["float32", "float16"], os.getenv("MODEL_PRECISION", self.model.precision))
        
        self.llm.provider = cast(Literal["openai", "ollama"], os.getenv("LLM_PROVIDER", self.llm.provider))
        self.llm.api_key = os.getenv("OPENAI_API_KEY", self.llm.api_key)
        self.llm.api_base_url = os.getenv("OPENAI_API_BASE_URL", self.llm.api_base_url)
        self.llm.model = os.getenv("OPENAI_MODEL", self.llm.model)
        self.llm.ollama_base_url = os.getenv("OLLAMA_BASE_URL", self.llm.ollama_base_url)
        self.llm.ollama_model = os.getenv("OLLAMA_MODEL", self.llm.ollama_model)
        
        # 根据提供者设置正确的模型名称
        if self.llm.provider == "ollama":
            self.llm.model = self.llm.ollama_model
        
        self.memory.importance_threshold = int(os.getenv("MEMORY_IMPORTANCE_THRESHOLD", str(self.memory.importance_threshold)))
        self.memory.retention_days = int(os.getenv("MEMORY_RETENTION_DAYS", str(self.memory.retention_days)))
        self.memory.max_size = int(os.getenv("MEMORY_MAX_SIZE", str(self.memory.max_size)))
        
        self.embedding.model_name = os.getenv("EMBEDDING_MODEL_NAME", self.embedding.model_name)
        self.embedding.device = os.getenv("EMBEDDING_DEVICE", self.embedding.device)
        self.embedding.max_length = int(os.getenv("EMBEDDING_MAX_LENGTH", str(self.embedding.max_length)))
        self.embedding.dimension = int(os.getenv("EMBEDDING_DIMENSION", str(self.embedding.dimension)))
        
        self.performance.batch_size = int(os.getenv("BATCH_SIZE", str(self.performance.batch_size)))
        self.performance.num_workers = int(os.getenv("NUM_WORKERS", str(self.performance.num_workers)))
        self.performance.cache_size = int(os.getenv("CACHE_SIZE", str(self.performance.cache_size)))
        
        self.log.level = os.getenv("LOG_LEVEL", self.log.level)
        self.log.file = os.getenv("LOG_FILE", self.log.file)
        self.log.format = os.getenv("LOG_FORMAT", self.log.format)
        
        self.security.encryption_key = os.getenv("ENCRYPTION_KEY", self.security.encryption_key)
        self.security.api_key = os.getenv("API_KEY", self.security.api_key)
        self.security.allowed_origins = os.getenv("ALLOWED_ORIGINS", self.security.allowed_origins)
        
        self.other.timezone = os.getenv("TIMEZONE", self.other.timezone)
        self.other.language = os.getenv("LANGUAGE", self.other.language)

# 全局配置实例
config = Config()

def init_config():
    """初始化配置"""
    global config
    config = Config()
    return config

load_config = init_config
