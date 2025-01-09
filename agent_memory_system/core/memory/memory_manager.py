"""记忆管理模块

负责管理系统的记忆存储和检索功能。

主要功能：
    - 记忆的存储和检索
    - 记忆的生命周期管理
    - 记忆的关系管理
    - 记忆的优化和清理

依赖：
    - memory_model: 记忆数据模型
    - storage: 存储引擎
    - retrieval: 检索引擎
    - config: 配置管理

作者：Cursor_for_YansongW
创建日期：2024-01-09
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from uuid import UUID

from agent_memory_system.core.storage.cache_store import CacheStore
from agent_memory_system.core.storage.graph_store import GraphStore
from agent_memory_system.core.storage.vector_store import VectorStore
from agent_memory_system.models.memory_model import (
    Memory,
    MemoryMetadata,
    MemoryRelationType,
    MemoryStatus,
    MemoryType,
    MemoryVector
)
from agent_memory_system.utils.config import config
from agent_memory_system.utils.logger import log
from tenacity import retry, stop_after_attempt, wait_exponential

class MemoryManager:
    """记忆管理器类
    
    功能描述：
        负责管理系统中所有的记忆操作，包括存储、检索、更新和删除。
        同时负责记忆的生命周期管理和关系管理。
    
    属性说明：
        - _storage: 存储引擎实例
        - _retrieval: 检索引擎实例
        - _cache: 记忆缓存字典
        - _config: 配置管理器实例
    
    依赖关系：
        - 依赖StorageEngine进行存储操作
        - 依赖RetrievalEngine进行检索操作
        - 依赖Config获取配置
        - 依赖Logger记录日志
    """
    
    def __init__(self) -> None:
        """初始化记忆管理器"""
        # 初始化存储引擎
        self._vector_store = VectorStore(
            dimension=config.vector_config["dimension"]
        )
        self._graph_store = GraphStore()
        self._cache_store = CacheStore()
        
        # 初始化本地缓存
        self._cache: Dict[UUID, Memory] = {}
        self._config = config
        
        log.info("记忆管理器初始化完成")
    
    def store_memory(
        self,
        content: str,
        memory_type: Union[MemoryType, str],
        importance: int = 5,
        metadata: Optional[Dict] = None,
        vector: Optional[List[float]] = None
    ) -> Memory:
        """存储新的记忆
        
        Args:
            content: 记忆内容
            memory_type: 记忆类型
            importance: 重要性评分(1-10)
            metadata: 记忆元数据
            vector: 记忆向量表示
        
        Returns:
            Memory: 新创建的记忆对象
        
        Raises:
            ValueError: 当参数无效时
            StorageError: 当存储操作失败时
        """
        # 参数验证和转换
        if isinstance(memory_type, str):
            memory_type = MemoryType(memory_type)
        
        # 创建记忆对象
        memory = Memory(
            content=content,
            memory_type=memory_type,
            importance=importance,
            metadata=MemoryMetadata(**(metadata or {})),
            vector=MemoryVector(
                vector=vector,
                model_name="default",
                dimension=len(vector) if vector else 0
            ) if vector else None
        )
        
        # 存储向量
        if memory.vector:
            self._vector_store.add_vector(
                memory.vector.vector,
                str(memory.id)
            )
        
        # 存储节点
        self._graph_store.add_node(
            str(memory.id),
            {
                "content": memory.content,
                "type": memory.memory_type.value,
                "importance": memory.importance,
                "status": memory.status.value,
                "created_at": memory.created_at.isoformat(),
                "updated_at": memory.updated_at.isoformat(),
                "accessed_at": memory.accessed_at.isoformat(),
                "access_count": memory.access_count
            }
        )
        
        # 存储缓存
        self._cache_store.set(
            str(memory.id),
            memory.dict(),
            ttl=self._get_cache_ttl(memory)
        )
        
        # 更新本地缓存
        self._cache[memory.id] = memory
        
        log.info(f"记忆存储成功: {memory.id}")
        return memory
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def retrieve_memory(
        self,
        memory_id: Union[UUID, str]
    ) -> Optional[Memory]:
        """检索指定ID的记忆
        
        Args:
            memory_id: 记忆ID
        
        Returns:
            Memory: 记忆对象，如果不存在则返回None
            
        Raises:
            StorageError: 当存储操作失败时
        """
        if isinstance(memory_id, str):
            memory_id = UUID(memory_id)
            
        try:
            # 获取分布式锁
            with self._cache_store.lock(f"memory_lock:{memory_id}", timeout=10.0):
                # 先从本地缓存中查找
                if memory_id in self._cache:
                    memory = self._cache[memory_id]
                    memory.update_access()
                    return memory
                
                # 从Redis缓存中查找
                memory_dict = self._cache_store.get(str(memory_id))
                if memory_dict:
                    memory = Memory(**memory_dict)
                    self._cache[memory.id] = memory
                    memory.update_access()
                    # 更新访问信息
                    self._update_access_info(memory)
                    return memory
                
                # 从图存储中查找
                node = self._graph_store.get_node(str(memory_id))
                if not node:
                    return None
                
                # 从向量存储中获取向量
                vector = self._vector_store.get(str(memory_id))
                
                # 构建记忆对象
                memory = Memory(
                    id=memory_id,
                    content=node["content"],
                    memory_type=MemoryType(node["type"]),
                    importance=node["importance"],
                    status=MemoryStatus(node["status"]),
                    vector=MemoryVector(
                        vector=vector.tolist(),
                        model_name="default",
                        dimension=len(vector)
                    ) if vector is not None else None,
                    created_at=datetime.fromisoformat(node["created_at"]),
                    updated_at=datetime.fromisoformat(node["updated_at"]),
                    accessed_at=datetime.fromisoformat(node["accessed_at"]),
                    access_count=node["access_count"]
                )
                
                # 更新缓存
                self._cache[memory.id] = memory
                self._cache_store.set(
                    str(memory.id),
                    memory.dict(),
                    ttl=self._get_cache_ttl(memory)
                )
                
                # 更新访问信息
                self._update_access_info(memory)
                return memory
                
        except Exception as e:
            log.error(f"检索记忆失败: {e}")
            raise StorageError(f"检索记忆失败: {e}")
    
    def _update_access_info(self, memory: Memory) -> None:
        """更新记忆访问信息
        
        Args:
            memory: 记忆对象
        """
        try:
            memory.update_access()
            
            # 更新图存储中的访问信息
            self._graph_store.update_node(
                str(memory.id),
                {
                    "accessed_at": memory.accessed_at.isoformat(),
                    "access_count": memory.access_count
                }
            )
            
            # 更新缓存
            self._cache_store.set(
                str(memory.id),
                memory.dict(),
                ttl=self._get_cache_ttl(memory)
            )
        except Exception as e:
            log.error(f"更新访问信息失败: {e}")
            # 这里我们不抛出异常,因为这不是关键操作
    
    def update_memory(
        self,
        memory_id: Union[UUID, str],
        content: Optional[str] = None,
        importance: Optional[int] = None,
        metadata: Optional[Dict] = None,
        status: Optional[MemoryStatus] = None
    ) -> Optional[Memory]:
        """更新记忆
        
        Args:
            memory_id: 记忆ID
            content: 新的记忆内容
            importance: 新的重要性评分
            metadata: 新的元数据
            status: 新的状态
        
        Returns:
            Memory: 更新后的记忆对象，如果记忆不存在则返回None
        """
        memory = self.retrieve_memory(memory_id)
        if not memory:
            return None
        
        # 更新字段
        if content is not None:
            memory.content = content
        if importance is not None:
            memory.importance = importance
        if metadata is not None:
            memory.metadata = MemoryMetadata(**metadata)
        if status is not None:
            memory.status = status
        
        memory.updated_at = datetime.utcnow()
        
        # 更新图存储
        self._graph_store.update_node(
            str(memory.id),
            {
                "content": memory.content,
                "importance": memory.importance,
                "status": memory.status.value,
                "updated_at": memory.updated_at.isoformat()
            }
        )
        
        # 更新缓存
        self._cache_store.set(
            str(memory.id),
            memory.dict(),
            ttl=self._get_cache_ttl(memory)
        )
        
        log.info(f"记忆更新成功: {memory.id}")
        return memory
    
    def delete_memory(
        self,
        memory_id: Union[UUID, str]
    ) -> bool:
        """删除记忆
        
        Args:
            memory_id: 记忆ID
        
        Returns:
            bool: 是否删除成功
        """
        if isinstance(memory_id, str):
            memory_id = UUID(memory_id)
        
        # 从本地缓存中删除
        memory = self._cache.pop(memory_id, None)
        
        # 从存储中删除
        success = True
        if memory and memory.vector:
            success &= self._vector_store.delete_vector(str(memory_id))
        success &= self._graph_store.delete_node(str(memory_id))
        success &= self._cache_store.delete(str(memory_id))
        
        if success:
            log.info(f"记忆删除成功: {memory_id}")
        else:
            log.error(f"记忆删除失败: {memory_id}")
        
        return success
    
    def add_relation(
        self,
        source_id: Union[UUID, str],
        target_id: Union[UUID, str],
        relation_type: Union[MemoryRelationType, str],
        weight: float = 1.0,
        metadata: Optional[Dict] = None
    ) -> bool:
        """添加记忆关系
        
        Args:
            source_id: 源记忆ID
            target_id: 目标记忆ID
            relation_type: 关系类型
            weight: 关系权重
            metadata: 关系元数据
        
        Returns:
            bool: 是否添加成功
        """
        source = self.retrieve_memory(source_id)
        if not source:
            return False
        
        target = self.retrieve_memory(target_id)
        if not target:
            return False
        
        # 添加关系到记忆对象
        source.add_relation(
            target_id=target_id,
            relation_type=relation_type,
            weight=weight,
            metadata=metadata
        )
        
        # 添加关系到图存储
        success = self._graph_store.add_relation(
            str(source_id),
            str(target_id),
            relation_type,
            {
                "weight": weight,
                **(metadata or {})
            }
        )
        
        # 更新缓存
        if success:
            self._cache_store.set(
                str(source.id),
                source.dict(),
                ttl=self._get_cache_ttl(source)
            )
            log.info(f"记忆关系添加成功: {source_id} -> {target_id}")
        else:
            log.error(f"记忆关系添加失败: {source_id} -> {target_id}")
        
        return success
    
    def remove_relation(
        self,
        source_id: Union[UUID, str],
        target_id: Union[UUID, str]
    ) -> bool:
        """移除记忆关系
        
        Args:
            source_id: 源记忆ID
            target_id: 目标记忆ID
        
        Returns:
            bool: 是否移除成功
        """
        source = self.retrieve_memory(source_id)
        if not source:
            return False
        
        # 从记忆对象移除关系
        source.remove_relation(target_id)
        
        # 从图存储移除关系
        success = self._graph_store.delete_relation(
            str(source_id),
            str(target_id)
        )
        
        # 更新缓存
        if success:
            self._cache_store.set(
                str(source.id),
                source.dict(),
                ttl=self._get_cache_ttl(source)
            )
            log.info(f"记忆关系移除成功: {source_id} -> {target_id}")
        else:
            log.error(f"记忆关系移除失败: {source_id} -> {target_id}")
        
        return success
    
    def cleanup(self) -> None:
        """清理过期和不重要的记忆
        
        根据配置的清理策略，清理：
        1. 超过存活时间的记忆
        2. 重要性低于阈值的记忆
        3. 长期未访问的记忆
        """
        now = datetime.utcnow()
        timeout = timedelta(seconds=self._config.memory_config["timeout"])
        importance_threshold = self._config.memory_config["importance_threshold"]
        
        # 获取所有记忆
        memories = list(self._cache.values())
        
        for memory in memories:
            should_delete = False
            
            # 检查存活时间
            if now - memory.created_at > timeout:
                should_delete = True
            
            # 检查重要性
            if memory.importance < importance_threshold:
                should_delete = True
            
            # 检查访问时间
            if now - memory.accessed_at > timeout:
                should_delete = True
            
            # 删除符合条件的记忆
            if should_delete:
                self.delete_memory(memory.id)
    
    def optimize(self) -> None:
        """优化记忆系统
        
        执行以下优化操作：
        1. 合并相似记忆
        2. 更新记忆关系
        3. 重新计算重要性
        4. 整理存储空间
        """
        # TODO: 实现优化逻辑
        pass
    
    def _get_cache_ttl(self, memory: Memory) -> int:
        """计算缓存过期时间
        
        根据记忆的重要性和访问频率计算合适的缓存时间
        
        Args:
            memory: 记忆对象
        
        Returns:
            int: 过期时间(秒)
        """
        base_ttl = 3600  # 基础过期时间1小时
        
        # 根据重要性调整
        importance_factor = memory.importance / 5.0  # 1-2
        
        # 根据访问频率调整
        access_factor = min(memory.access_count / 10.0 + 1, 2)  # 1-2
        
        return int(base_ttl * importance_factor * access_factor)
