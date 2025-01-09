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

作者：Cursor_for_YansongW
创建日期：2024-01-09
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field

class Config:
    """配置管理类
    
    功能描述：
        负责管理系统的所有配置项，包括从环境变量和配置文件加载配置，
        验证配置的正确性，并提供配置的访问接口。
    
    属性说明：
        - _instance: 单例实例
        - _config: 配置字典
        - _env_file: 环境变量文件路径
    
    使用示例：
        config = Config()
        db_url = config.get("DATABASE_URL")
    """
    
    _instance = None
    _config: Dict[str, Any] = {}
    _env_file: Optional[Path] = None
    
    def __new__(cls) -> "Config":
        """实现单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        """初始化配置管理器"""
        if not self._config:
            self._load_config()
    
    def _load_config(self) -> None:
        """加载配置
        
        从环境变量和配置文件加载配置信息。
        优先级：环境变量 > .env文件 > 默认值
        """
        # 1. 加载默认配置
        self._config.update({
            # 系统配置
            "DEBUG": False,
            "LOG_LEVEL": "INFO",
            "API_PORT": 8000,
            
            # 向量存储配置
            "VECTOR_DIMENSION": 768,
            "SIMILARITY_THRESHOLD": 0.85,
            "MAX_RETURN_COUNT": 100,
            
            # 记忆配置
            "MAX_MEMORY_SIZE": 1000,
            "MEMORY_TIMEOUT": 7 * 24 * 3600,  # 7天
            "IMPORTANCE_THRESHOLD": 7,
            
            # 数据库配置
            "DATABASE_URL": "sqlite:///memory.db",
            "REDIS_URL": "redis://localhost:6379/0",
            "NEO4J_URL": "bolt://localhost:7687",
            
            # LLM配置
            "LLM_MODEL": "gpt-3.5-turbo",
            "LLM_TEMPERATURE": 0.7,
            "LLM_MAX_TOKENS": 2000,
        })
        
        # 2. 加载.env文件
        env_file = Path(".env")
        if env_file.exists():
            self._env_file = env_file
            load_dotenv(env_file)
        
        # 3. 从环境变量更新配置
        for key in self._config.keys():
            env_value = os.getenv(key)
            if env_value is not None:
                # 根据默认值类型进行类型转换
                default_value = self._config[key]
                if isinstance(default_value, bool):
                    self._config[key] = env_value.lower() in ("true", "1", "yes")
                elif isinstance(default_value, int):
                    self._config[key] = int(env_value)
                elif isinstance(default_value, float):
                    self._config[key] = float(env_value)
                else:
                    self._config[key] = env_value
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键名
            default: 默认值，当配置不存在时返回
        
        Returns:
            配置值
        
        Raises:
            KeyError: 当配置不存在且未提供默认值时
        """
        if key not in self._config and default is None:
            raise KeyError(f"Configuration key '{key}' not found")
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """设置配置值
        
        Args:
            key: 配置键名
            value: 配置值
        """
        self._config[key] = value
    
    def reload(self) -> None:
        """重新加载配置"""
        self._config.clear()
        self._load_config()
    
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
    def neo4j_url(self) -> str:
        """Neo4j连接URL"""
        return self.get("NEO4J_URL")
    
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

# 全局配置实例
config = Config()
