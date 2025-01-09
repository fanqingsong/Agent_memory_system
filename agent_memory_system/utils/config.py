"""配置管理模块

负责系统配置的加载、验证和管理。

主要功能：
    - 从环境变量和配置文件加载配置
    - 验证配置的正确性
    - 提供配置的访问接口
    - 管理配置的更新

依赖：
    - python-dotenv: 用于加载环境变量
    - pydantic: 用于配置验证
    - cryptography: 用于配置加密

作者：Cursor_for_YansongW
创建日期：2024-01-09
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from cryptography.fernet import Fernet
from dotenv import load_dotenv
from pydantic import BaseModel, Field, validator

class DatabaseConfig(BaseModel):
    """数据库配置模型"""
    database_url: str = Field(..., description="数据库连接URL")
    redis_url: str = Field(..., description="Redis连接URL")
    neo4j_uri: str = Field(..., description="Neo4j连接URI")
    neo4j_user: str = Field(default="neo4j", description="Neo4j用户名")
    neo4j_password: str = Field(..., description="Neo4j密码")
    
    @validator("database_url")
    def validate_database_url(cls, v: str) -> str:
        if not v.startswith(("sqlite://", "postgresql://", "mysql://")):
            raise ValueError("不支持的数据库类型")
        return v
    
    @validator("redis_url")
    def validate_redis_url(cls, v: str) -> str:
        if not v.startswith("redis://"):
            raise ValueError("无效的Redis URL")
        return v
    
    @validator("neo4j_uri")
    def validate_neo4j_uri(cls, v: str) -> str:
        if not v.startswith(("bolt://", "neo4j://")):
            raise ValueError("无效的Neo4j URI")
        return v

class LLMConfig(BaseModel):
    """LLM配置模型"""
    model: str = Field(..., description="模型名称")
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="温度参数"
    )
    max_tokens: int = Field(
        default=2000,
        gt=0,
        description="最大token数"
    )

class MemoryConfig(BaseModel):
    """记忆配置模型"""
    max_size: int = Field(
        default=1000,
        gt=0,
        description="最大记忆数量"
    )
    timeout: int = Field(
        default=7 * 24 * 3600,
        gt=0,
        description="记忆超时时间(秒)"
    )
    importance_threshold: int = Field(
        default=7,
        ge=1,
        le=10,
        description="重要性阈值"
    )

class VectorConfig(BaseModel):
    """向量配置模型"""
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

class SystemConfig(BaseModel):
    """系统配置模型"""
    debug: bool = Field(default=False, description="调试模式")
    log_level: str = Field(default="INFO", description="日志级别")
    api_port: int = Field(default=8000, gt=0, description="API端口")
    data_dir: Path = Field(default=Path("data"), description="数据目录")
    log_dir: Path = Field(default=Path("logs"), description="日志目录")
    
    @validator("log_level")
    def validate_log_level(cls, v: str) -> str:
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"无效的日志级别,有效值为: {valid_levels}")
        return v.upper()

class Config:
    """配置管理类"""
    
    _instance = None
    _config: Dict[str, Any] = {}
    _env_file: Optional[Path] = None
    _observers: Set[callable] = set()
    
    def __new__(cls) -> "Config":
        """实现单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        """初始化配置管理器"""
        if not self._config:
            self._load_config()
            self._encrypt_sensitive_data()
    
    def _load_config(self) -> None:
        """加载配置"""
        # 1. 加载默认配置
        self._config.update({
            "DEBUG": False,
            "LOG_LEVEL": "INFO",
            "API_PORT": 8000,
            "DATA_DIR": "data",
            "LOG_DIR": "logs",
            
            "VECTOR_DIMENSION": 768,
            "SIMILARITY_THRESHOLD": 0.85,
            "MAX_RETURN_COUNT": 100,
            
            "MAX_MEMORY_SIZE": 1000,
            "MEMORY_TIMEOUT": 7 * 24 * 3600,
            "IMPORTANCE_THRESHOLD": 7,
            
            "DATABASE_URL": "sqlite:///memory.db",
            "REDIS_URL": "redis://localhost:6379/0",
            "NEO4J_URL": "bolt://localhost:7687",
            "NEO4J_USER": "neo4j",
            "NEO4J_PASSWORD": "password",
            
            "LLM_MODEL": "gpt-3.5-turbo",
            "LLM_TEMPERATURE": 0.7,
            "LLM_MAX_TOKENS": 2000,
        })
        
        # 2. 加载.env文件
        env_files = [".env", ".env.local", ".env.development"]
        for env_file in env_files:
            env_path = Path(env_file)
            if env_path.exists():
                self._env_file = env_path
                load_dotenv(env_path)
                break
        
        # 3. 从环境变量更新配置
        for key in self._config.keys():
            env_value = os.getenv(key)
            if env_value is not None:
                self._config[key] = self._convert_value(
                    env_value,
                    self._config[key]
                )
        
        # 4. 验证配置
        self._validate_config()
    
    def _convert_value(self, value: str, default_value: Any) -> Any:
        """转换配置值类型"""
        if isinstance(default_value, bool):
            return value.lower() in ("true", "1", "yes")
        elif isinstance(default_value, int):
            return int(value)
        elif isinstance(default_value, float):
            return float(value)
        elif isinstance(default_value, Path):
            return Path(value)
        return value
    
    def _validate_config(self) -> None:
        """验证配置"""
        # 验证系统配置
        SystemConfig(
            debug=self._config["DEBUG"],
            log_level=self._config["LOG_LEVEL"],
            api_port=self._config["API_PORT"],
            data_dir=self._config["DATA_DIR"],
            log_dir=self._config["LOG_DIR"]
        )
        
        # 验证数据库配置
        DatabaseConfig(
            database_url=self._config["DATABASE_URL"],
            redis_url=self._config["REDIS_URL"],
            neo4j_uri=self._config["NEO4J_URL"],
            neo4j_user=self._config["NEO4J_USER"],
            neo4j_password=self._config["NEO4J_PASSWORD"]
        )
        
        # 验证LLM配置
        LLMConfig(
            model=self._config["LLM_MODEL"],
            temperature=self._config["LLM_TEMPERATURE"],
            max_tokens=self._config["LLM_MAX_TOKENS"]
        )
        
        # 验证记忆配置
        MemoryConfig(
            max_size=self._config["MAX_MEMORY_SIZE"],
            timeout=self._config["MEMORY_TIMEOUT"],
            importance_threshold=self._config["IMPORTANCE_THRESHOLD"]
        )
        
        # 验证向量配置
        VectorConfig(
            dimension=self._config["VECTOR_DIMENSION"],
            similarity_threshold=self._config["SIMILARITY_THRESHOLD"],
            max_return_count=self._config["MAX_RETURN_COUNT"]
        )
    
    def _encrypt_sensitive_data(self) -> None:
        """加密敏感数据"""
        # 生成加密密钥
        key = Fernet.generate_key()
        cipher_suite = Fernet(key)
        
        # 加密敏感配置
        sensitive_keys = {
            "NEO4J_PASSWORD",
            "DATABASE_URL",
            "REDIS_URL",
            "NEO4J_URL"
        }
        
        for key in sensitive_keys:
            if key in self._config:
                value = str(self._config[key]).encode()
                self._config[key] = cipher_suite.encrypt(value)
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        if key not in self._config and default is None:
            raise KeyError(f"配置项'{key}'不存在")
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """设置配置值"""
        old_value = self._config.get(key)
        self._config[key] = value
        
        # 通知观察者
        if old_value != value:
            self._notify_observers(key, old_value, value)
    
    def add_observer(self, observer: callable) -> None:
        """添加配置变更观察者"""
        self._observers.add(observer)
    
    def remove_observer(self, observer: callable) -> None:
        """移除配置变更观察者"""
        self._observers.discard(observer)
    
    def _notify_observers(
        self,
        key: str,
        old_value: Any,
        new_value: Any
    ) -> None:
        """通知配置变更"""
        for observer in self._observers:
            observer(key, old_value, new_value)
    
    def reload(self) -> None:
        """重新加载配置"""
        old_config = self._config.copy()
        self._config.clear()
        self._load_config()
        
        # 通知配置变更
        for key, new_value in self._config.items():
            old_value = old_config.get(key)
            if old_value != new_value:
                self._notify_observers(key, old_value, new_value)
    
    @property
    def debug(self) -> bool:
        """是否为调试模式"""
        return self.get("DEBUG", False)
    
    @property
    def log_level(self) -> str:
        """日志级别"""
        return self.get("LOG_LEVEL", "INFO")
    
    @property
    def database_url(self) -> str:
        """数据库连接URL"""
        return self.get("DATABASE_URL")
    
    @property
    def redis_url(self) -> str:
        """Redis连接URL"""
        return self.get("REDIS_URL")
    
    @property
    def neo4j_uri(self) -> str:
        """Neo4j连接URI"""
        return self.get("NEO4J_URL")
    
    @property
    def neo4j_user(self) -> str:
        """Neo4j用户名"""
        return self.get("NEO4J_USER", "neo4j")
    
    @property
    def neo4j_password(self) -> str:
        """Neo4j密码"""
        return self.get("NEO4J_PASSWORD", "password")
    
    @property
    def llm_config(self) -> Dict[str, Any]:
        """LLM配置"""
        return {
            "model": self.get("LLM_MODEL"),
            "temperature": self.get("LLM_TEMPERATURE"),
            "max_tokens": self.get("LLM_MAX_TOKENS"),
        }
    
    @property
    def memory_config(self) -> Dict[str, Any]:
        """记忆配置"""
        return {
            "max_size": self.get("MAX_MEMORY_SIZE"),
            "timeout": self.get("MEMORY_TIMEOUT"),
            "importance_threshold": self.get("IMPORTANCE_THRESHOLD"),
        }
    
    @property
    def vector_config(self) -> Dict[str, Any]:
        """向量配置"""
        return {
            "dimension": self.get("VECTOR_DIMENSION"),
            "similarity_threshold": self.get("SIMILARITY_THRESHOLD"),
            "max_return_count": self.get("MAX_RETURN_COUNT"),
        }
    
    @property
    def data_dir(self) -> Path:
        """数据目录"""
        return Path(self.get("DATA_DIR", "data"))
    
    @property
    def log_dir(self) -> Path:
        """日志目录"""
        return Path(self.get("LOG_DIR", "logs"))
    
    @property
    def faiss_index_path(self) -> Path:
        """FAISS索引路径"""
        return self.data_dir / "faiss_index"

# 全局配置实例
config = Config()
