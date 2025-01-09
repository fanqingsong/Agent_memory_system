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
from pathlib import Path
from typing import Union

from loguru import logger

from agent_memory_system.utils.config import config

class Logger:
    """日志管理类
    
    功能描述：
        负责管理系统的日志记录，包括配置日志格式、级别，
        添加日志处理器，并提供统一的日志记录接口。
    
    属性说明：
        - _instance: 单例实例
        - _log_path: 日志文件路径
        - _format: 日志格式
    
    使用示例：
        logger = Logger()
        logger.info("这是一条信息日志")
    """
    
    _instance = None
    _log_path = Path("logs")
    _format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    def __new__(cls) -> "Logger":
        """实现单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        """初始化日志管理器"""
        # 创建日志目录
        self._log_path.mkdir(exist_ok=True)
        
        # 移除默认处理器
        logger.remove()
        
        # 添加控制台处理器
        logger.add(
            sys.stderr,
            format=self._format,
            level=config.log_level,
            colorize=True,
        )
        
        # 添加文件处理器
        logger.add(
            self._log_path / "app_{time}.log",
            format=self._format,
            level=config.log_level,
            rotation="1 day",
            retention="7 days",
            compression="zip",
            encoding="utf-8",
        )
        
        # 添加错误日志处理器
        logger.add(
            self._log_path / "error_{time}.log",
            format=self._format,
            level="ERROR",
            rotation="1 day",
            retention="30 days",
            compression="zip",
            encoding="utf-8",
            filter=lambda record: record["level"].name == "ERROR",
        )
    
    def debug(self, message: str, *args, **kwargs) -> None:
        """记录调试日志
        
        Args:
            message: 日志消息
            *args: 位置参数
            **kwargs: 关键字参数
        """
        logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs) -> None:
        """记录信息日志
        
        Args:
            message: 日志消息
            *args: 位置参数
            **kwargs: 关键字参数
        """
        logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs) -> None:
        """记录警告日志
        
        Args:
            message: 日志消息
            *args: 位置参数
            **kwargs: 关键字参数
        """
        logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs) -> None:
        """记录错误日志
        
        Args:
            message: 日志消息
            *args: 位置参数
            **kwargs: 关键字参数
        """
        logger.error(message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs) -> None:
        """记录严重错误日志
        
        Args:
            message: 日志消息
            *args: 位置参数
            **kwargs: 关键字参数
        """
        logger.critical(message, *args, **kwargs)
    
    def exception(self, message: str, *args, **kwargs) -> None:
        """记录异常日志
        
        Args:
            message: 日志消息
            *args: 位置参数
            **kwargs: 关键字参数
        """
        logger.exception(message, *args, **kwargs)
    
    def set_level(self, level: Union[str, int]) -> None:
        """设置日志级别
        
        Args:
            level: 日志级别，可以是字符串或整数
        """
        logger.remove()
        logger.add(sys.stderr, level=level)
    
    @property
    def log_path(self) -> Path:
        """获取日志路径"""
        return self._log_path

# 全局日志实例
log = Logger()
