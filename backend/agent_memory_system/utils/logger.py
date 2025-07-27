"""日志管理模块

负责系统日志的配置和管理。

主要功能：
    - 配置日志格式
    - 设置日志级别
    - 添加日志处理器
    - 提供日志记录接口

依赖：
    - loguru: 用于日志管理
    - config: 用于获取配置

作者：Cursor_for_YansongW
创建日期：2024-01-09
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Union

from loguru import logger

from agent_memory_system.utils.config import config
import os

class LogConfig:
    """日志配置类"""
    
    def __init__(
        self,
        log_path: Optional[Union[str, Path]] = None,
        log_level: str = "INFO",
        rotation: str = "1 day",
        retention: str = "7 days",
        compression: str = "zip",
        max_size: str = "100 MB",
        encoding: str = "utf-8",
        format: Optional[str] = None
    ) -> None:
        # Use the directory of config.log.file as the log path
        log_file_path = Path(config.log.file)
        log_dir = log_file_path.parent
        self.log_path = Path(log_path or log_dir)
        self.log_level = log_level
        self.rotation = rotation
        self.retention = retention
        self.compression = compression
        self.max_size = max_size
        self.encoding = encoding
        self.format = format or (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )

class Logger:
    """日志管理类"""
    
    _instance = None
    _handlers: Dict[str, int] = {}
    
    def __new__(cls) -> "Logger":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self._config = LogConfig()
            self._setup_logger()
    
    def _setup_logger(self) -> None:
        # 创建日志目录
        if self._config.log_path is None:
            self._config.log_path = Path("logs")
        self._config.log_path.mkdir(exist_ok=True)
        
        # 设置默认格式
        if self._config.format is None:
            self._config.format = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}"
        
        # 移除默认处理器
        logger.remove()
        
        # 添加控制台处理器
        self._add_console_handler()
        
        # 添加文件处理器
        self._add_file_handler()
        
        # 添加错误日志处理器
        self._add_error_handler()
    
    def _add_console_handler(self) -> None:
        handler_id = logger.add(
            sys.stderr,
            format=self._config.format,
            level=self._config.log_level,
            colorize=True,
            backtrace=True,
            diagnose=True
        )
        self._handlers["console"] = handler_id
    
    def _add_file_handler(self) -> None:
        handler_id = logger.add(
            self._config.log_path / "app_{time}.log",
            format=self._config.format,
            level=self._config.log_level,
            rotation=self._config.rotation,
            retention=self._config.retention,
            compression=self._config.compression,
            encoding=self._config.encoding,
            backtrace=True,
            diagnose=True,
            enqueue=True,
            catch=True
        )
        self._handlers["file"] = handler_id
    
    def _add_error_handler(self) -> None:
        handler_id = logger.add(
            self._config.log_path / "error_{time}.log",
            format=self._config.format,
            level="ERROR",
            rotation=self._config.rotation,
            retention=self._config.retention,
            compression=self._config.compression,
            encoding=self._config.encoding,
            backtrace=True,
            diagnose=True,
            enqueue=True,
            catch=True,
            filter=lambda record: record["level"].name == "ERROR"
        )
        self._handlers["error"] = handler_id
    
    def update_config(self, **kwargs) -> None:
        # 更新配置
        for key, value in kwargs.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)
        
        # 重新设置日志记录器
        self._remove_handlers()
        self._setup_logger()
    
    def _remove_handlers(self) -> None:
        for handler_id in self._handlers.values():
            logger.remove(handler_id)
        self._handlers.clear()
    
    def cleanup_old_logs(
        self,
        days: int = 7,
        pattern: str = "*.log*"
    ) -> None:
        cutoff = datetime.now() - timedelta(days=days)
        
        for file in self._config.log_path.glob(pattern):
            if file.stat().st_mtime < cutoff.timestamp():
                try:
                    file.unlink()
                except Exception as e:
                    self.error(f"清理日志文件失败: {e}")
    
    def debug(self, message: str, *args, **kwargs) -> None:
        logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs) -> None:
        logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs) -> None:
        logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs) -> None:
        logger.error(message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs) -> None:
        logger.critical(message, *args, **kwargs)
    
    def exception(self, message: str, *args, **kwargs) -> None:
        logger.exception(message, *args, **kwargs)
    
    def set_level(self, level: Union[str, int]) -> None:
        self.update_config(log_level=level)
    
    @property
    def log_path(self) -> Path:
        return self._config.log_path

# 全局日志实例
log = Logger()

def init_logger(
    log_path: Optional[Union[str, Path]] = None,
    log_level: str = "INFO",
    rotation: str = "1 day",
    retention: str = "7 days",
    compression: str = "zip",
    max_size: str = "100 MB",
    encoding: str = "utf-8",
    format: Optional[str] = None
) -> Logger:
    """初始化日志配置
    
    Args:
        log_path: 日志文件路径
        log_level: 日志级别
        rotation: 日志轮转策略
        retention: 日志保留策略
        compression: 压缩格式
        max_size: 最大文件大小
        encoding: 文件编码
        format: 日志格式
        
    Returns:
        Logger: 日志实例
    """
    return setup_logging(
        log_path=log_path,
        log_level=log_level,
        rotation=rotation,
        retention=retention,
        compression=compression,
        max_size=max_size,
        encoding=encoding,
        format=format
    )

# 添加缺失的函数和类定义
def setup_logging(
    log_path: Optional[Union[str, Path]] = None,
    log_level: str = "INFO",
    rotation: str = "1 day",
    retention: str = "7 days",
    compression: str = "zip",
    max_size: str = "100 MB",
    encoding: str = "utf-8",
    format: Optional[str] = None
) -> Logger:
    """设置日志配置
    
    Args:
        log_path: 日志文件路径
        log_level: 日志级别
        rotation: 日志轮转策略
        retention: 日志保留策略
        compression: 压缩格式
        max_size: 最大文件大小
        encoding: 文件编码
        format: 日志格式
        
    Returns:
        Logger: 日志实例
    """
    log.update_config(
        log_path=log_path,
        log_level=log_level,
        rotation=rotation,
        retention=retention,
        compression=compression,
        max_size=max_size,
        encoding=encoding,
        format=format
    )
    return log

def get_logger(name: Optional[str] = None) -> Logger:
    """获取日志实例
    
    Args:
        name: 日志器名称（可选）
        
    Returns:
        Logger: 日志实例
    """
    return log

class LogLevel:
    """日志级别枚举"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
