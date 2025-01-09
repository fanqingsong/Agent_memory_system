"""检索引擎基类模块

定义检索引擎的基本接口和功能。

主要功能：
    - 定义检索引擎接口
    - 实现基本检索逻辑
    - 提供检索结果处理
    - 支持多种检索策略

依赖：
    - memory_model: 记忆数据模型
    - memory_utils: 记忆处理工具
    - config: 配置管理
    - logger: 日志记录

作者：Cursor_for_YansongW
创建日期：2024-01-09
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Union

from agent_memory_system.core.memory.memory_utils import (
    calculate_similarity,
    postprocess_memory
)
from agent_memory_system.models.memory_model import (
    Memory,
    MemoryStatus,
    MemoryType,
    RetrievalResult
)
from agent_memory_system.utils.config import config
from agent_memory_system.utils.logger import log

class RetrievalEngine(ABC):
    """检索引擎基类
    
    功能描述：
        定义检索引擎的基本接口和功能，包括：
        1. 基于内容的检索
        2. 基于关系的检索
        3. 基于时间的检索
        4. 基于重要性的检索
        5. 组合检索策略
    
    属性说明：
        - config: 配置管理器实例
        - memory_types: 支持的记忆类型集合
    """
    
    def __init__(self) -> None:
        """初始化检索引擎"""
        self.config = config
        self.memory_types = set()
    
    @abstractmethod
    def retrieve_by_content(
        self,
        query: str,
        memory_type: Optional[MemoryType] = None,
        top_k: int = 10,
        threshold: float = 0.5
    ) -> List[RetrievalResult]:
        """基于内容检索记忆
        
        Args:
            query: 检索查询
            memory_type: 记忆类型过滤
            top_k: 返回结果数量
            threshold: 相似度阈值
        
        Returns:
            List[RetrievalResult]: 检索结果列表
        """
        pass
    
    @abstractmethod
    def retrieve_by_relation(
        self,
        memory_id: str,
        relation_types: Optional[List[str]] = None,
        depth: int = 1,
        top_k: int = 10
    ) -> List[RetrievalResult]:
        """基于关系检索记忆
        
        Args:
            memory_id: 起始记忆ID
            relation_types: 关系类型过滤
            depth: 关系深度
            top_k: 返回结果数量
        
        Returns:
            List[RetrievalResult]: 检索结果列表
        """
        pass
    
    @abstractmethod
    def retrieve_by_time(
        self,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        memory_type: Optional[MemoryType] = None,
        top_k: int = 10
    ) -> List[RetrievalResult]:
        """基于时间检索记忆
        
        Args:
            start_time: 起始时间
            end_time: 结束时间
            memory_type: 记忆类型过滤
            top_k: 返回结果数量
        
        Returns:
            List[RetrievalResult]: 检索结果列表
        """
        pass
    
    @abstractmethod
    def retrieve_by_importance(
        self,
        min_importance: int = 1,
        max_importance: int = 10,
        memory_type: Optional[MemoryType] = None,
        top_k: int = 10
    ) -> List[RetrievalResult]:
        """基于重要性检索记忆
        
        Args:
            min_importance: 最小重要性
            max_importance: 最大重要性
            memory_type: 记忆类型过滤
            top_k: 返回结果数量
        
        Returns:
            List[RetrievalResult]: 检索结果列表
        """
        pass
    
    def retrieve(
        self,
        query: Optional[str] = None,
        memory_type: Optional[MemoryType] = None,
        relation_filter: Optional[Dict[str, List[str]]] = None,
        time_filter: Optional[Tuple[datetime, datetime]] = None,
        importance_filter: Optional[Tuple[int, int]] = None,
        top_k: int = 10,
        threshold: float = 0.5
    ) -> List[RetrievalResult]:
        """组合检索记忆
        
        功能描述：
            支持多条件组合检索，包括：
            1. 内容相关性
            2. 记忆类型
            3. 关系过滤
            4. 时间范围
            5. 重要性范围
        
        Args:
            query: 检索查询
            memory_type: 记忆类型过滤
            relation_filter: 关系过滤条件
            time_filter: 时间范围过滤
            importance_filter: 重要性范围过滤
            top_k: 返回结果数量
            threshold: 相似度阈值
        
        Returns:
            List[RetrievalResult]: 检索结果列表
        """
        results = []
        
        # 基于内容检索
        if query:
            content_results = self.retrieve_by_content(
                query,
                memory_type,
                top_k=top_k * 2,  # 预取更多结果用于过滤
                threshold=threshold
            )
            results.extend(content_results)
        
        # 基于关系检索
        if relation_filter:
            for memory_id, relation_types in relation_filter.items():
                relation_results = self.retrieve_by_relation(
                    memory_id,
                    relation_types,
                    top_k=top_k
                )
                results.extend(relation_results)
        
        # 基于时间检索
        if time_filter:
            start_time, end_time = time_filter
            time_results = self.retrieve_by_time(
                start_time,
                end_time,
                memory_type,
                top_k=top_k
            )
            results.extend(time_results)
        
        # 基于重要性检索
        if importance_filter:
            min_importance, max_importance = importance_filter
            importance_results = self.retrieve_by_importance(
                min_importance,
                max_importance,
                memory_type,
                top_k=top_k
            )
            results.extend(importance_results)
        
        # 如果没有指定任何条件，返回空列表
        if not any([query, relation_filter, time_filter, importance_filter]):
            return []
        
        # 合并和排序结果
        merged_results = self._merge_results(results)
        
        # 应用过滤条件
        filtered_results = self._filter_results(
            merged_results,
            memory_type=memory_type,
            time_filter=time_filter,
            importance_filter=importance_filter
        )
        
        # 返回top_k个结果
        return filtered_results[:top_k]
    
    def _merge_results(
        self,
        results: List[RetrievalResult]
    ) -> List[RetrievalResult]:
        """合并检索结果
        
        功能描述：
            合并多个来源的检索结果：
            1. 去重
            2. 合并分数
            3. 排序
        
        Args:
            results: 检索结果列表
        
        Returns:
            List[RetrievalResult]: 合并后的结果列表
        """
        # 使用字典去重并合并分数
        merged = {}
        for result in results:
            if result.memory_id in merged:
                # 取最高分数
                merged[result.memory_id].score = max(
                    merged[result.memory_id].score,
                    result.score
                )
            else:
                merged[result.memory_id] = result
        
        # 转换为列表并排序
        merged_list = list(merged.values())
        merged_list.sort(key=lambda x: x.score, reverse=True)
        
        return merged_list
    
    def _filter_results(
        self,
        results: List[RetrievalResult],
        memory_type: Optional[MemoryType] = None,
        time_filter: Optional[Tuple[datetime, datetime]] = None,
        importance_filter: Optional[Tuple[int, int]] = None
    ) -> List[RetrievalResult]:
        """过滤检索结果
        
        功能描述：
            根据条件过滤结果：
            1. 记忆类型
            2. 时间范围
            3. 重要性范围
        
        Args:
            results: 检索结果列表
            memory_type: 记忆类型过滤
            time_filter: 时间范围过滤
            importance_filter: 重要性范围过滤
        
        Returns:
            List[RetrievalResult]: 过滤后的结果列表
        """
        filtered = results
        
        # 记忆类型过滤
        if memory_type:
            filtered = [
                r for r in filtered
                if r.memory_type == memory_type
            ]
        
        # 时间范围过滤
        if time_filter:
            start_time, end_time = time_filter
            filtered = [
                r for r in filtered
                if start_time <= r.created_at
                and (not end_time or r.created_at <= end_time)
            ]
        
        # 重要性范围过滤
        if importance_filter:
            min_importance, max_importance = importance_filter
            filtered = [
                r for r in filtered
                if min_importance <= r.importance <= max_importance
            ]
        
        return filtered
    
    def postprocess_results(
        self,
        results: List[RetrievalResult]
    ) -> List[RetrievalResult]:
        """后处理检索结果
        
        功能描述：
            对检索结果进行后处理：
            1. 更新访问信息
            2. 更新重要性
            3. 优化向量
            4. 清理关系
        
        Args:
            results: 检索结果列表
        
        Returns:
            List[RetrievalResult]: 处理后的结果列表
        """
        for result in results:
            # 更新记忆
            result.memory = postprocess_memory(result.memory)
            
            # 更新结果属性
            result.importance = result.memory.importance
            result.accessed_at = result.memory.accessed_at
            result.access_count = result.memory.access_count
        
        return results 