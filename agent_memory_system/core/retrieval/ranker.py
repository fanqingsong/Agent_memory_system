"""排序器模块

实现检索结果的排序功能。

主要功能：
    - 基于相似度排序
    - 基于重要性排序
    - 基于时间排序
    - 基于访问频率排序
    - 组合排序策略

依赖：
    - memory_model: 记忆数据模型
    - memory_utils: 记忆处理工具
    - config: 配置管理
    - logger: 日志记录

作者：Cursor_for_YansongW
创建日期：2025-01-09
"""

from datetime import datetime
from typing import Callable, Dict, List, Optional, Tuple, Union

import numpy as np
from sklearn.preprocessing import MinMaxScaler

from agent_memory_system.models.memory_model import (
    Memory,
    MemoryStatus,
    MemoryType,
    RetrievalResult
)
from agent_memory_system.utils.config import config
from agent_memory_system.utils.logger import log

class Ranker:
    """排序器
    
    功能描述：
        实现检索结果的排序功能，包括：
        1. 基于相似度排序
        2. 基于重要性排序
        3. 基于时间排序
        4. 基于访问频率排序
        5. 组合排序策略
    
    属性说明：
        - config: 配置管理器实例
        - scaler: 特征归一化器
    """
    
    def __init__(self) -> None:
        """初始化排序器"""
        self.config = config
        self.scaler = MinMaxScaler()
    
    def rank_by_similarity(
        self,
        results: List[RetrievalResult],
        reverse: bool = True
    ) -> List[RetrievalResult]:
        """基于相似度排序
        
        Args:
            results: 检索结果列表
            reverse: 是否降序排序
        
        Returns:
            List[RetrievalResult]: 排序后的结果列表
        """
        return sorted(results, key=lambda x: x.score, reverse=reverse)
    
    def rank_by_importance(
        self,
        results: List[RetrievalResult],
        reverse: bool = True
    ) -> List[RetrievalResult]:
        """基于重要性排序
        
        Args:
            results: 检索结果列表
            reverse: 是否降序排序
        
        Returns:
            List[RetrievalResult]: 排序后的结果列表
        """
        return sorted(results, key=lambda x: x.importance, reverse=reverse)
    
    def rank_by_time(
        self,
        results: List[RetrievalResult],
        use_access_time: bool = False,
        reverse: bool = True
    ) -> List[RetrievalResult]:
        """基于时间排序
        
        Args:
            results: 检索结果列表
            use_access_time: 是否使用访问时间而不是创建时间
            reverse: 是否降序排序
        
        Returns:
            List[RetrievalResult]: 排序后的结果列表
        """
        if use_access_time:
            return sorted(results, key=lambda x: x.accessed_at, reverse=reverse)
        return sorted(results, key=lambda x: x.created_at, reverse=reverse)
    
    def rank_by_access_count(
        self,
        results: List[RetrievalResult],
        reverse: bool = True
    ) -> List[RetrievalResult]:
        """基于访问频率排序
        
        Args:
            results: 检索结果列表
            reverse: 是否降序排序
        
        Returns:
            List[RetrievalResult]: 排序后的结果列表
        """
        return sorted(results, key=lambda x: x.access_count, reverse=reverse)
    
    def rank(
        self,
        results: List[RetrievalResult],
        weights: Optional[Dict[str, float]] = None,
        reverse: bool = True
    ) -> List[RetrievalResult]:
        """组合排序
        
        功能描述：
            基于多个特征的加权组合进行排序：
            1. 相似度得分
            2. 重要性
            3. 时间衰减
            4. 访问频率
        
        Args:
            results: 检索结果列表
            weights: 特征权重字典，包含以下键：
                - similarity: 相似度权重
                - importance: 重要性权重
                - time_decay: 时间衰减权重
                - access_count: 访问频率权重
            reverse: 是否降序排序
        
        Returns:
            List[RetrievalResult]: 排序后的结果列表
        """
        if not results:
            return []
        
        # 默认权重
        default_weights = {
            'similarity': 0.4,
            'importance': 0.3,
            'time_decay': 0.2,
            'access_count': 0.1
        }
        weights = weights or default_weights
        
        # 提取特征
        features = []
        for result in results:
            # 相似度得分
            similarity = result.score
            
            # 重要性
            importance = result.importance
            
            # 时间衰减
            now = datetime.now()
            time_diff = (now - result.created_at).total_seconds()
            time_decay = 1.0 / (1.0 + np.log1p(time_diff / 3600))  # 使用小时作为单位
            
            # 访问频率
            access_count = result.access_count
            
            features.append([similarity, importance, time_decay, access_count])
        
        # 特征归一化
        features = np.array(features)
        if len(features) > 1:  # 只有多于一个结果时才进行归一化
            features = self.scaler.fit_transform(features)
        
        # 计算加权得分
        scores = np.zeros(len(results))
        scores += weights['similarity'] * features[:, 0]
        scores += weights['importance'] * features[:, 1]
        scores += weights['time_decay'] * features[:, 2]
        scores += weights['access_count'] * features[:, 3]
        
        # 排序
        sorted_indices = np.argsort(scores)
        if reverse:
            sorted_indices = sorted_indices[::-1]
        
        return [results[i] for i in sorted_indices]
    
    def rerank(
        self,
        results: List[RetrievalResult],
        rerank_func: Callable[[List[RetrievalResult]], List[RetrievalResult]]
    ) -> List[RetrievalResult]:
        """重排序
        
        功能描述：
            使用自定义重排序函数对结果进行重排序
        
        Args:
            results: 检索结果列表
            rerank_func: 重排序函数
        
        Returns:
            List[RetrievalResult]: 重排序后的结果列表
        """
        return rerank_func(results)
