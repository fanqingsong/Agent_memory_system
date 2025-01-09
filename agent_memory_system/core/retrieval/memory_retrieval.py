"""记忆检索引擎模块

实现具体的记忆检索功能。

主要功能：
    - 基于内容的检索
    - 基于关系的检索
    - 基于时间的检索
    - 基于重要性的检索
    - 组合检索策略

依赖：
    - retrieval_engine: 检索引擎基类
    - memory_model: 记忆数据模型
    - memory_utils: 记忆处理工具
    - storage: 存储引擎
    - config: 配置管理
    - logger: 日志记录

作者：Cursor_for_YansongW
创建日期：2025-01-09
"""

from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Union

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from agent_memory_system.core.memory.memory_utils import (
    calculate_similarity,
    generate_memory_vectors
)
from agent_memory_system.core.retrieval.retrieval_engine import RetrievalEngine
from agent_memory_system.core.storage.cache_store import CacheStore
from agent_memory_system.core.storage.graph_store import GraphStore
from agent_memory_system.core.storage.vector_store import VectorStore
from agent_memory_system.models.memory_model import (
    Memory,
    MemoryStatus,
    MemoryType,
    MemoryVector,
    RetrievalResult
)
from agent_memory_system.utils.config import config
from agent_memory_system.utils.logger import log

class MemoryRetrieval(RetrievalEngine):
    """记忆检索引擎
    
    功能描述：
        实现具体的记忆检索功能，包括：
        1. 向量相似度检索
        2. 图关系检索
        3. 时间范围检索
        4. 重要性过滤
        5. 缓存加速
    
    属性说明：
        - vector_store: 向量存储引擎
        - graph_store: 图存储引擎
        - cache_store: 缓存存储引擎
    """
    
    def __init__(
        self,
        vector_store: VectorStore,
        graph_store: GraphStore,
        cache_store: CacheStore
    ) -> None:
        """初始化检索引擎
        
        Args:
            vector_store: 向量存储引擎
            graph_store: 图存储引擎
            cache_store: 缓存存储引擎
        """
        super().__init__()
        self.vector_store = vector_store
        self.graph_store = graph_store
        self.cache_store = cache_store
        
        # 支持所有记忆类型
        self.memory_types = {
            MemoryType.SHORT_TERM,
            MemoryType.LONG_TERM,
            MemoryType.WORKING,
            MemoryType.SKILL
        }
    
    def retrieve_by_content(
        self,
        query: str,
        memory_type: Optional[MemoryType] = None,
        top_k: int = 10,
        threshold: float = 0.5
    ) -> List[RetrievalResult]:
        """基于内容检索记忆
        
        实现说明：
            1. 生成查询向量
            2. 在向量存储中检索
            3. 过滤和排序结果
            4. 后处理结果
        
        Args:
            query: 检索查询
            memory_type: 记忆类型过滤
            top_k: 返回结果数量
            threshold: 相似度阈值
        
        Returns:
            List[RetrievalResult]: 检索结果列表
        """
        # 生成查询向量
        query_vectors = generate_memory_vectors(Memory(
            content=query,
            memory_type=memory_type or MemoryType.WORKING
        ))
        
        # 在向量存储中检索
        results = []
        for vector in query_vectors:
            # 检索相似向量
            similar_vectors = self.vector_store.search(
                vector=vector.vector,
                top_k=top_k * 2,  # 预取更多结果用于过滤
                threshold=threshold
            )
            
            # 获取完整记忆
            for vec_id, score in similar_vectors:
                memory = self.graph_store.get_memory(vec_id)
                if memory:
                    # 应用记忆类型过滤
                    if memory_type and memory.memory_type != memory_type:
                        continue
                    
                    # 创建检索结果
                    result = RetrievalResult(
                        memory_id=memory.id,
                        memory=memory,
                        score=score,
                        memory_type=memory.memory_type,
                        importance=memory.importance,
                        created_at=memory.created_at,
                        accessed_at=memory.accessed_at,
                        access_count=memory.access_count
                    )
                    results.append(result)
        
        # 合并和排序结果
        merged_results = self._merge_results(results)
        
        # 后处理结果
        processed_results = self.postprocess_results(merged_results)
        
        return processed_results[:top_k]
    
    def retrieve_by_relation(
        self,
        memory_id: str,
        relation_types: Optional[List[str]] = None,
        depth: int = 1,
        top_k: int = 10
    ) -> List[RetrievalResult]:
        """基于关系检索记忆
        
        实现说明：
            1. 在图存储中检索关系
            2. 递归获取指定深度的关系
            3. 过滤关系类型
            4. 计算关系强度得分
        
        Args:
            memory_id: 起始记忆ID
            relation_types: 关系类型过滤
            depth: 关系深度
            top_k: 返回结果数量
        
        Returns:
            List[RetrievalResult]: 检索结果列表
        """
        # 在图存储中检索关系
        related_memories = self.graph_store.get_related_memories(
            memory_id=memory_id,
            relation_types=relation_types,
            depth=depth
        )
        
        # 转换为检索结果
        results = []
        for memory, relations in related_memories.items():
            # 计算关系强度得分
            score = sum(r.strength for r in relations) / len(relations)
            
            # 创建检索结果
            result = RetrievalResult(
                memory_id=memory.id,
                memory=memory,
                score=score,
                memory_type=memory.memory_type,
                importance=memory.importance,
                created_at=memory.created_at,
                accessed_at=memory.accessed_at,
                access_count=memory.access_count
            )
            results.append(result)
        
        # 排序结果
        results.sort(key=lambda x: x.score, reverse=True)
        
        # 后处理结果
        processed_results = self.postprocess_results(results)
        
        return processed_results[:top_k]
    
    def retrieve_by_time(
        self,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        memory_type: Optional[MemoryType] = None,
        top_k: int = 10
    ) -> List[RetrievalResult]:
        """基于时间检索记忆
        
        实现说明：
            1. 在图存储中检索时间范围内的记忆
            2. 应用记忆类型过滤
            3. 计算时间相关性得分
            4. 排序和返回结果
        
        Args:
            start_time: 起始时间
            end_time: 结束时间
            memory_type: 记忆类型过滤
            top_k: 返回结果数量
        
        Returns:
            List[RetrievalResult]: 检索结果列表
        """
        # 在图存储中检索时间范围内的记忆
        memories = self.graph_store.get_memories_by_time(
            start_time=start_time,
            end_time=end_time,
            memory_type=memory_type
        )
        
        # 转换为检索结果
        results = []
        for memory in memories:
            # 计算时间相关性得分
            if end_time:
                time_range = (end_time - start_time).total_seconds()
                time_diff = (memory.created_at - start_time).total_seconds()
                score = 1 - (time_diff / time_range)
            else:
                time_diff = (datetime.utcnow() - memory.created_at).total_seconds()
                score = np.exp(-time_diff / (24 * 3600))  # 24小时衰减
            
            # 创建检索结果
            result = RetrievalResult(
                memory_id=memory.id,
                memory=memory,
                score=score,
                memory_type=memory.memory_type,
                importance=memory.importance,
                created_at=memory.created_at,
                accessed_at=memory.accessed_at,
                access_count=memory.access_count
            )
            results.append(result)
        
        # 排序结果
        results.sort(key=lambda x: x.score, reverse=True)
        
        # 后处理结果
        processed_results = self.postprocess_results(results)
        
        return processed_results[:top_k]
    
    def retrieve_by_importance(
        self,
        min_importance: int = 1,
        max_importance: int = 10,
        memory_type: Optional[MemoryType] = None,
        top_k: int = 10
    ) -> List[RetrievalResult]:
        """基于重要性检索记忆
        
        实现说明：
            1. 在图存储中检索指定重要性范围的记忆
            2. 应用记忆类型过滤
            3. 计算重要性得分
            4. 排序和返回结果
        
        Args:
            min_importance: 最小重要性
            max_importance: 最大重要性
            memory_type: 记忆类型过滤
            top_k: 返回结果数量
        
        Returns:
            List[RetrievalResult]: 检索结果列表
        """
        # 在图存储中检索指定重要性范围的记忆
        memories = self.graph_store.get_memories_by_importance(
            min_importance=min_importance,
            max_importance=max_importance,
            memory_type=memory_type
        )
        
        # 转换为检索结果
        results = []
        for memory in memories:
            # 计算重要性得分
            importance_range = max_importance - min_importance
            score = (memory.importance - min_importance) / importance_range
            
            # 创建检索结果
            result = RetrievalResult(
                memory_id=memory.id,
                memory=memory,
                score=score,
                memory_type=memory.memory_type,
                importance=memory.importance,
                created_at=memory.created_at,
                accessed_at=memory.accessed_at,
                access_count=memory.access_count
            )
            results.append(result)
        
        # 排序结果
        results.sort(key=lambda x: x.score, reverse=True)
        
        # 后处理结果
        processed_results = self.postprocess_results(results)
        
        return processed_results[:top_k]
    
    def optimize_retrieval(self) -> None:
        """优化检索性能
        
        功能描述：
            定期优化检索性能：
            1. 更新向量索引
            2. 优化图结构
            3. 清理过期缓存
            4. 更新检索策略
        """
        # 更新向量索引
        self.vector_store.optimize_index()
        
        # 优化图结构
        self.graph_store.optimize_graph()
        
        # 清理过期缓存
        self.cache_store.clear_expired()
        
        # 记录优化日志
        log.info("检索引擎优化完成") 