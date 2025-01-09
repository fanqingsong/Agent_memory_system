"""缓存存储模块

使用Redis实现高性能的缓存存储。

主要功能：
    - 记忆数据的缓存
    - 缓存的过期管理
    - 缓存的更新策略
    - 分布式锁支持

依赖：
    - redis: Redis Python客户端
    - config: 配置管理
    - logger: 日志记录

作者：Cursor_for_YansongW
创建日期：2024-01-09
"""

import json
from typing import Any, Dict, List, Optional, Set, Union

import redis
from redis.exceptions import RedisError

from agent_memory_system.utils.config import config
from agent_memory_system.utils.logger import log

class CacheStore:
    """缓存存储类
    
    功能描述：
        使用Redis实现高性能的缓存存储功能，支持：
        1. 记忆数据的缓存管理
        2. 缓存的过期策略
        3. 缓存的更新机制
        4. 分布式锁机制
    
    属性说明：
        - _client: Redis客户端实例
        - _prefix: 键前缀
        - _default_ttl: 默认过期时间
    
    依赖关系：
        - 依赖Redis进行缓存操作
        - 依赖Config获取配置
        - 依赖Logger记录日志
    """
    
    def __init__(
        self,
        url: str = None,
        prefix: str = "memory:",
        default_ttl: int = 3600
    ) -> None:
        """初始化缓存存储
        
        Args:
            url: Redis连接URL
            prefix: 键前缀
            default_ttl: 默认过期时间(秒)
        """
        self._url = url or config.redis_url
        self._prefix = prefix
        self._default_ttl = default_ttl
        
        # 连接Redis
        self._client = redis.from_url(self._url)
        
        # 测试连接
        try:
            self._client.ping()
            log.info("缓存存储初始化完成")
        except RedisError as e:
            log.error(f"连接Redis失败: {e}")
            raise
    
    def _make_key(self, key: str) -> str:
        """生成带前缀的键名
        
        Args:
            key: 原始键名
        
        Returns:
            str: 带前缀的键名
        """
        return f"{self._prefix}{key}"
    
    def get(
        self,
        key: str,
        default: Any = None
    ) -> Any:
        """获取缓存值
        
        Args:
            key: 键名
            default: 默认值
        
        Returns:
            Any: 缓存值，如果不存在则返回默认值
        """
        try:
            value = self._client.get(self._make_key(key))
            if value is None:
                return default
            return json.loads(value)
        except (RedisError, json.JSONDecodeError) as e:
            log.error(f"获取缓存失败: {e}")
            return default
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: int = None
    ) -> bool:
        """设置缓存值
        
        Args:
            key: 键名
            value: 值
            ttl: 过期时间(秒)
        
        Returns:
            bool: 是否设置成功
        """
        try:
            value_json = json.dumps(value)
            return self._client.set(
                self._make_key(key),
                value_json,
                ex=ttl or self._default_ttl
            )
        except (RedisError, TypeError) as e:
            log.error(f"设置缓存失败: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """删除缓存
        
        Args:
            key: 键名
        
        Returns:
            bool: 是否删除成功
        """
        try:
            return bool(self._client.delete(self._make_key(key)))
        except RedisError as e:
            log.error(f"删除缓存失败: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """检查键是否存在
        
        Args:
            key: 键名
        
        Returns:
            bool: 是否存在
        """
        try:
            return bool(self._client.exists(self._make_key(key)))
        except RedisError as e:
            log.error(f"检查缓存失败: {e}")
            return False
    
    def expire(
        self,
        key: str,
        ttl: int
    ) -> bool:
        """设置过期时间
        
        Args:
            key: 键名
            ttl: 过期时间(秒)
        
        Returns:
            bool: 是否设置成功
        """
        try:
            return bool(self._client.expire(
                self._make_key(key),
                ttl
            ))
        except RedisError as e:
            log.error(f"设置过期时间失败: {e}")
            return False
    
    def ttl(self, key: str) -> int:
        """获取剩余过期时间
        
        Args:
            key: 键名
        
        Returns:
            int: 剩余时间(秒)，-1表示永不过期，-2表示不存在
        """
        try:
            return self._client.ttl(self._make_key(key))
        except RedisError as e:
            log.error(f"获取过期时间失败: {e}")
            return -2
    
    def incr(
        self,
        key: str,
        amount: int = 1
    ) -> Optional[int]:
        """增加计数器
        
        Args:
            key: 键名
            amount: 增加量
        
        Returns:
            int: 新的值，如果失败则返回None
        """
        try:
            return self._client.incrby(
                self._make_key(key),
                amount
            )
        except RedisError as e:
            log.error(f"增加计数失败: {e}")
            return None
    
    def decr(
        self,
        key: str,
        amount: int = 1
    ) -> Optional[int]:
        """减少计数器
        
        Args:
            key: 键名
            amount: 减少量
        
        Returns:
            int: 新的值，如果失败则返回None
        """
        try:
            return self._client.decrby(
                self._make_key(key),
                amount
            )
        except RedisError as e:
            log.error(f"减少计数失败: {e}")
            return None
    
    def sadd(
        self,
        key: str,
        *values: str
    ) -> Optional[int]:
        """向集合添加元素
        
        Args:
            key: 键名
            *values: 要添加的值
        
        Returns:
            int: 新添加的元素数量，如果失败则返回None
        """
        try:
            return self._client.sadd(
                self._make_key(key),
                *values
            )
        except RedisError as e:
            log.error(f"添加集合元素失败: {e}")
            return None
    
    def srem(
        self,
        key: str,
        *values: str
    ) -> Optional[int]:
        """从集合移除元素
        
        Args:
            key: 键名
            *values: 要移除的值
        
        Returns:
            int: 移除的元素数量，如果失败则返回None
        """
        try:
            return self._client.srem(
                self._make_key(key),
                *values
            )
        except RedisError as e:
            log.error(f"移除集合元素失败: {e}")
            return None
    
    def smembers(self, key: str) -> Set[str]:
        """获取集合所有元素
        
        Args:
            key: 键名
        
        Returns:
            Set[str]: 元素集合
        """
        try:
            return self._client.smembers(self._make_key(key))
        except RedisError as e:
            log.error(f"获取集合元素失败: {e}")
            return set()
    
    def sismember(
        self,
        key: str,
        value: str
    ) -> bool:
        """检查元素是否在集合中
        
        Args:
            key: 键名
            value: 要检查的值
        
        Returns:
            bool: 是否存在
        """
        try:
            return bool(self._client.sismember(
                self._make_key(key),
                value
            ))
        except RedisError as e:
            log.error(f"检查集合元素失败: {e}")
            return False
    
    def lock(
        self,
        name: str,
        timeout: float = 10.0,
        blocking: bool = True,
        blocking_timeout: float = None
    ) -> redis.Lock:
        """获取分布式锁
        
        Args:
            name: 锁名称
            timeout: 锁超时时间(秒)
            blocking: 是否阻塞等待
            blocking_timeout: 阻塞超时时间(秒)
        
        Returns:
            redis.Lock: 锁对象
        """
        return self._client.lock(
            self._make_key(f"lock:{name}"),
            timeout=timeout,
            blocking=blocking,
            blocking_timeout=blocking_timeout
        )
    
    def clear(self, pattern: str = "*") -> bool:
        """清空缓存
        
        Args:
            pattern: 键模式
        
        Returns:
            bool: 是否清空成功
        """
        try:
            keys = self._client.keys(
                self._make_key(pattern)
            )
            if keys:
                self._client.delete(*keys)
            return True
        except RedisError as e:
            log.error(f"清空缓存失败: {e}")
            return False
    
    def close(self) -> None:
        """关闭连接"""
        try:
            self._client.close()
        except RedisError as e:
            log.error(f"关闭连接失败: {e}")
    
    def __enter__(self) -> "CacheStore":
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """上下文管理器出口"""
        self.close()
