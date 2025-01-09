"""记忆检索模块

实现基于向量和图的混合检索功能。

主要功能：
    - 向量相似度检索
    - 图关系检索
    - 混合检索策略
    - 检索结果排序
    - 检索结果优化

依赖：
    - memory_model: 记忆数据模型
    - memory_types: 记忆类型处理
    - memory_utils: 记忆工具函数
    - vector_store: 向量存储
    - graph_store: 图存储
    - config: 配置管理
    - logger: 日志记录

作者：Cursor_for_YansongW
创建日期：2024-01-15
"""

from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Union

import numpy as np
from sklearn.preprocessing import normalize

from agent_memory_system.core.memory.memory_utils import (
    calculate_similarity,
    generate_memory_vectors,
    postprocess_memory
)
from agent_memory_system.core.storage.graph_store import GraphStore
from agent_memory_system.core.storage.vector_store import VectorStore
from agent_memory_system.models.memory_model import (
    Memory,
    MemoryQuery,
    MemoryType,
    MemoryVector,
    RetrievalResult,
    RetrievalStrategy
)
from agent_memory_system.utils.config import config
from agent_memory_system.utils.logger import log


class MemoryRetrieval:
    """记忆检索类
    
    功能描述：
        实现基于向量和图的混合检索功能，支持：
        1. 基于向量相似度的检索
        2. 基于图关系的检索
        3. 混合检索策略
        4. 检索结果的排序和优化
    
    属性说明：
        - _vector_store: 向量存储实例
        - _graph_store: 图存储实例
        - _cache: 检索缓存
    
    依赖关系：
        - 依赖VectorStore进行向量检索
        - 依赖GraphStore进行图检索
        - 依赖MemoryUtils进行记忆处理
    """
    
    def __init__(
        self,
        vector_store: VectorStore = None,
        graph_store: GraphStore = None
    ) -> None:
        """初始化记忆检索
        
        Args:
            vector_store: 向量存储实例
            graph_store: 图存储实例
        """
        self._vector_store = vector_store or VectorStore()
        self._graph_store = graph_store or GraphStore()
        self._cache = {}
    
    def retrieve(
        self,
        query: MemoryQuery,
        strategy: RetrievalStrategy = RetrievalStrategy.HYBRID,
        limit: int = 10
    ) -> List[RetrievalResult]:
        """检索记忆
        
        Args:
            query: 检索查询
            strategy: 检索策略
            limit: 返回结果数量限制
        
        Returns:
            List[RetrievalResult]: 检索结果列表
        """
        try:
            # 根据策略选择检索方法
            if strategy == RetrievalStrategy.VECTOR:
                results = self._vector_retrieval(query, limit)
            elif strategy == RetrievalStrategy.GRAPH:
                results = self._graph_retrieval(query, limit)
            else:  # HYBRID
                results = self._hybrid_retrieval(query, limit)
            
            # 后处理结果
            results = self._postprocess_results(results)
            
            # 更新缓存
            self._update_cache(query, results)
            
            return results[:limit]
        except Exception as e:
            log.error(f"检索记忆失败: {e}")
            return []
    
    def _vector_retrieval(
        self,
        query: MemoryQuery,
        limit: int
    ) -> List[RetrievalResult]:
        """向量检索
        
        使用向量相似度进行记忆检索。
        
        Args:
            query: 检索查询
            limit: 结果数量限制
        
        Returns:
            List[RetrievalResult]: 检索结果列表
        """
        try:
            # 生成查询向量
            query_vectors = generate_memory_vectors(Memory(
                content=query.content,
                memory_type=query.memory_type
            ))
            
            results = []
            for vector in query_vectors:
                # 向量检索
                similar_vectors = self._vector_store.search(
                    vector=vector.vector,
                    k=limit * 2,  # 获取更多结果用于后续过滤
                    threshold=query.threshold
                )
                
                # 转换结果
                for memory_id, similarity in similar_vectors:
                    memory = self._get_memory(memory_id)
                    if memory and self._filter_memory(memory, query):
                        results.append(RetrievalResult(
                            memory=memory,
                            similarity=similarity,
                            source="vector"
                        ))
            
            return self._merge_results(results)
        except Exception as e:
            log.error(f"向量检索失败: {e}")
            return []
    
    def _graph_retrieval(
        self,
        query: MemoryQuery,
        limit: int
    ) -> List[RetrievalResult]:
        """图检索
        
        使用图关系进行记忆检索。
        
        Args:
            query: 检索查询
            limit: 结果数量限制
        
        Returns:
            List[RetrievalResult]: 检索结果列表
        """
        try:
            results = []
            
            # 获取相关节点
            if query.memory_ids:
                for memory_id in query.memory_ids:
                    # 获取邻居节点
                    neighbors = self._graph_store.get_neighbors(
                        node_id=memory_id,
                        relationship_type=query.relation_type,
                        limit=limit
                    )
                    
                    # 转换结果
                    for neighbor in neighbors:
                        memory = self._get_memory(neighbor["id"])
                        if memory and self._filter_memory(memory, query):
                            # 计算相似度
                            similarity = calculate_similarity(
                                memory1=memory,
                                memory2=Memory(
                                    content=query.content,
                                    memory_type=query.memory_type
                                )
                            )
                            results.append(RetrievalResult(
                                memory=memory,
                                similarity=similarity,
                                source="graph"
                            ))
            
            return self._merge_results(results)
        except Exception as e:
            log.error(f"图检索失败: {e}")
            return []
    
    def _hybrid_retrieval(
        self,
        query: MemoryQuery,
        limit: int
    ) -> List[RetrievalResult]:
        """混合检索
        
        结合向量相似度和图关系进行检索。
        
        Args:
            query: 检索查询
            limit: 结果数量限制
        
        Returns:
            List[RetrievalResult]: 检索结果列表
        """
        try:
            # 获取向量检索结果
            vector_results = self._vector_retrieval(
                query,
                limit=limit * 2
            )
            
            # 获取图检索结果
            graph_results = self._graph_retrieval(
                query,
                limit=limit * 2
            )
            
            # 合并结果
            results = vector_results + graph_results
            
            # 重新计算混合相似度
            for result in results:
                if result.source == "vector":
                    result.similarity *= 0.7  # 向量相似度权重
                else:  # graph
                    result.similarity *= 0.3  # 图关系权重
            
            return self._merge_results(results)
        except Exception as e:
            log.error(f"混合检索失败: {e}")
            return []
    
    def _get_memory(self, memory_id: str) -> Optional[Memory]:
        """获取记忆
        
        Args:
            memory_id: 记忆ID
        
        Returns:
            Memory: 记忆对象，如果不存在则返回None
        """
        try:
            # 从缓存获取
            if memory_id in self._cache:
                return self._cache[memory_id]
            
            # 获取节点数据
            node = self._graph_store.get_node(memory_id)
            if not node:
                return None
            
            # 获取向量数据
            vectors = []
            for vector_id in node["properties"].get("vector_ids", []):
                vector = self._vector_store.get(vector_id)
                if vector is not None:
                    vectors.append(MemoryVector(
                        vector_type="unknown",
                        vector=vector,
                        dimension=len(vector)
                    ))
            
            # 构建记忆对象
            memory = Memory(
                id=memory_id,
                content=node["properties"]["content"],
                memory_type=MemoryType(node["properties"]["memory_type"]),
                vectors=vectors,
                created_at=datetime.fromisoformat(
                    node["properties"]["created_at"]
                ),
                importance=node["properties"]["importance"]
            )
            
            # 更新缓存
            self._cache[memory_id] = memory
            
            return memory
        except Exception as e:
            log.error(f"获取记忆失败: {e}")
            return None
    
    def _filter_memory(
        self,
        memory: Memory,
        query: MemoryQuery
    ) -> bool:
        """过滤记忆
        
        Args:
            memory: 记忆对象
            query: 检索查询
        
        Returns:
            bool: 是否通过过滤
        """
        # 检查记忆类型
        if query.memory_type and memory.memory_type != query.memory_type:
            return False
        
        # 检查时间范围
        if query.start_time and memory.created_at < query.start_time:
            return False
        if query.end_time and memory.created_at > query.end_time:
            return False
        
        # 检查重要性
        if query.min_importance and memory.importance < query.min_importance:
            return False
        
        return True
    
    def _merge_results(
        self,
        results: List[RetrievalResult]
    ) -> List[RetrievalResult]:
        """合并检索结果
        
        Args:
            results: 检索结果列表
        
        Returns:
            List[RetrievalResult]: 合并后的结果列表
        """
        # 按记忆ID去重
        unique_results = {}
        for result in results:
            memory_id = result.memory.id
            if memory_id not in unique_results:
                unique_results[memory_id] = result
            else:
                # 保留相似度更高的结果
                if result.similarity > unique_results[memory_id].similarity:
                    unique_results[memory_id] = result
        
        # 按相似度排序
        sorted_results = sorted(
            unique_results.values(),
            key=lambda x: x.similarity,
            reverse=True
        )
        
        return sorted_results
    
    def _postprocess_results(
        self,
        results: List[RetrievalResult]
    ) -> List[RetrievalResult]:
        """后处理检索结果
        
        Args:
            results: 检索结果列表
        
        Returns:
            List[RetrievalResult]: 处理后的结果列表
        """
        # 更新记忆状态
        for result in results:
            result.memory = postprocess_memory(result.memory)
        
        return results
    
    def _update_cache(
        self,
        query: MemoryQuery,
        results: List[RetrievalResult]
    ) -> None:
        """更新检索缓存
        
        Args:
            query: 检索查询
            results: 检索结果列表
        """
        # 更新缓存
        for result in results:
            self._cache[result.memory.id] = result.memory
        
        # 清理过期缓存
        current_time = datetime.utcnow()
        expired_keys = []
        for memory_id, memory in self._cache.items():
            if (current_time - memory.accessed_at).total_seconds() > 3600:
                expired_keys.append(memory_id)
        
        for key in expired_keys:
            del self._cache[key]
    
    def close(self) -> None:
        """关闭检索器"""
        self._vector_store.close()
        self._graph_store.close()
    
    def __enter__(self) -> "MemoryRetrieval":
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close() 