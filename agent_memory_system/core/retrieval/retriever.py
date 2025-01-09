"""检索器模块

实现具体的检索策略。

主要功能：
    - 向量检索
    - 图检索
    - 混合检索
    - 检索优化
    - 缓存管理

依赖：
    - memory_model: 记忆数据模型
    - memory_utils: 记忆处理工具
    - storage: 存储引擎
    - config: 配置管理
    - logger: 日志记录

作者：Cursor_for_YansongW
创建日期：2024-01-09
"""

from typing import Dict, List, Optional, Set, Tuple, Union

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from agent_memory_system.core.memory.memory_utils import (
    calculate_similarity,
    generate_memory_vectors
)
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

class Retriever:
    """检索器
    
    功能描述：
        实现具体的检索策略，包括：
        1. 向量检索
        2. 图检索
        3. 混合检索
        4. 检索优化
        5. 缓存管理
    
    属性说明：
        - vector_store: 向量存储引擎
        - graph_store: 图存储引擎
        - cache_store: 缓存存储引擎
        - config: 配置管理器实例
    """
    
    def __init__(
        self,
        vector_store: VectorStore,
        graph_store: GraphStore,
        cache_store: CacheStore
    ) -> None:
        """初始化检索器
        
        Args:
            vector_store: 向量存储引擎
            graph_store: 图存储引擎
            cache_store: 缓存存储引擎
        """
        self.vector_store = vector_store
        self.graph_store = graph_store
        self.cache_store = cache_store
        self.config = config
    
    def vector_search(
        self,
        query_vector: np.ndarray,
        top_k: int = 10,
        threshold: float = 0.5,
        memory_type: Optional[MemoryType] = None
    ) -> List[Tuple[str, float]]:
        """向量检索
        
        功能描述：
            基于向量相似度的检索：
            1. 在向量存储中检索相似向量
            2. 应用相似度阈值过滤
            3. 应用记忆类型过滤
            4. 返回结果ID和得分
        
        Args:
            query_vector: 查询向量
            top_k: 返回结果数量
            threshold: 相似度阈值
            memory_type: 记忆类型过滤
        
        Returns:
            List[Tuple[str, float]]: 结果ID和得分列表
        """
        # 检查缓存
        cache_key = f"vector_search_{hash(str(query_vector))}_{top_k}_{threshold}_{memory_type}"
        cached_results = self.cache_store.get(cache_key)
        if cached_results is not None:
            return cached_results
        
        # 在向量存储中检索
        results = self.vector_store.search(
            vector=query_vector,
            top_k=top_k * 2,  # 预取更多结果用于过滤
            threshold=threshold
        )
        
        # 应用记忆类型过滤
        if memory_type:
            filtered_results = []
            for memory_id, score in results:
                memory = self.graph_store.get_memory(memory_id)
                if memory and memory.memory_type == memory_type:
                    filtered_results.append((memory_id, score))
            results = filtered_results
        
        # 取top_k个结果
        results = results[:top_k]
        
        # 更新缓存
        self.cache_store.set(cache_key, results)
        
        return results
    
    def graph_search(
        self,
        start_id: str,
        relation_types: Optional[List[str]] = None,
        depth: int = 1,
        max_nodes: int = 100
    ) -> Dict[str, List[str]]:
        """图检索
        
        功能描述：
            基于图关系的检索：
            1. 在图存储中检索关系
            2. 递归获取指定深度的关系
            3. 应用关系类型过滤
            4. 限制返回节点数量
        
        Args:
            start_id: 起始节点ID
            relation_types: 关系类型过滤
            depth: 关系深度
            max_nodes: 最大节点数量
        
        Returns:
            Dict[str, List[str]]: 节点关系字典
        """
        # 检查缓存
        cache_key = f"graph_search_{start_id}_{relation_types}_{depth}_{max_nodes}"
        cached_results = self.cache_store.get(cache_key)
        if cached_results is not None:
            return cached_results
        
        # 在图存储中检索
        results = self.graph_store.get_related_nodes(
            node_id=start_id,
            relation_types=relation_types,
            depth=depth,
            max_nodes=max_nodes
        )
        
        # 更新缓存
        self.cache_store.set(cache_key, results)
        
        return results
    
    def hybrid_search(
        self,
        query_vector: np.ndarray,
        relation_boost: Optional[Dict[str, float]] = None,
        top_k: int = 10,
        threshold: float = 0.5,
        memory_type: Optional[MemoryType] = None
    ) -> List[Tuple[str, float]]:
        """混合检索
        
        功能描述：
            结合向量相似度和图关系的混合检索：
            1. 首先进行向量检索
            2. 获取结果节点的相关节点
            3. 基于关系提升相关节点的得分
            4. 重新排序并返回结果
        
        Args:
            query_vector: 查询向量
            relation_boost: 关系提升权重字典
            top_k: 返回结果数量
            threshold: 相似度阈值
            memory_type: 记忆类型过滤
        
        Returns:
            List[Tuple[str, float]]: 结果ID和得分列表
        """
        # 检查缓存
        cache_key = f"hybrid_search_{hash(str(query_vector))}_{relation_boost}_{top_k}_{threshold}_{memory_type}"
        cached_results = self.cache_store.get(cache_key)
        if cached_results is not None:
            return cached_results
        
        # 默认关系提升权重
        default_boost = {
            'SIMILAR': 0.3,
            'RELATED': 0.2,
            'REFERENCED': 0.1
        }
        relation_boost = relation_boost or default_boost
        
        # 进行向量检索
        vector_results = self.vector_search(
            query_vector=query_vector,
            top_k=top_k,
            threshold=threshold,
            memory_type=memory_type
        )
        
        # 获取相关节点
        related_nodes = {}
        for memory_id, score in vector_results:
            # 获取相关节点
            relations = self.graph_search(
                start_id=memory_id,
                depth=1,
                max_nodes=10
            )
            
            # 基于关系类型提升得分
            for node_id, relation_types in relations.items():
                boost = 0.0
                for relation in relation_types:
                    if relation in relation_boost:
                        boost = max(boost, relation_boost[relation])
                
                # 如果节点已存在，取最大提升
                if node_id in related_nodes:
                    related_nodes[node_id] = max(related_nodes[node_id], score * (1 + boost))
                else:
                    related_nodes[node_id] = score * (1 + boost)
        
        # 合并结果
        merged_results = []
        seen_nodes = set()
        
        # 首先添加向量检索结果
        for memory_id, score in vector_results:
            merged_results.append((memory_id, score))
            seen_nodes.add(memory_id)
        
        # 添加相关节点
        for node_id, score in sorted(related_nodes.items(), key=lambda x: x[1], reverse=True):
            if node_id not in seen_nodes and len(merged_results) < top_k:
                merged_results.append((node_id, score))
                seen_nodes.add(node_id)
        
        # 更新缓存
        self.cache_store.set(cache_key, merged_results)
        
        return merged_results[:top_k]
    
    def optimize_cache(self) -> None:
        """优化缓存
        
        功能描述：
            优化检索缓存：
            1. 清理过期缓存
            2. 预热热点数据
            3. 调整缓存大小
        """
        # 清理过期缓存
        self.cache_store.clear_expired()
        
        # 预热热点数据
        hot_memories = self.graph_store.get_hot_memories(
            min_access_count=self.config.get('cache.hot_memory_threshold', 10),
            limit=self.config.get('cache.hot_memory_limit', 1000)
        )
        
        for memory in hot_memories:
            # 生成向量
            vectors = generate_memory_vectors(memory)
            
            # 预热向量检索缓存
            for vector in vectors:
                self.vector_search(
                    query_vector=vector.vector,
                    top_k=10,
                    threshold=0.5,
                    memory_type=memory.memory_type
                )
            
            # 预热图检索缓存
            self.graph_search(
                start_id=memory.id,
                depth=1,
                max_nodes=10
            )
        
        # 调整缓存大小
        current_size = self.cache_store.get_size()
        max_size = self.config.get('cache.max_size', 1024 * 1024 * 1024)  # 默认1GB
        
        if current_size > max_size:
            # 清理最旧的缓存直到大小合适
            self.cache_store.shrink_to(max_size)
