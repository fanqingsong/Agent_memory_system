"""检索引擎单元测试

测试检索引擎的各项功能。

测试内容：
    - 检索引擎基类
    - 内容检索
    - 关系检索
    - 时间检索
    - 重要性检索
    - 组合检索

作者：Cursor_for_YansongW
创建日期：2025-01-09
"""

import unittest
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple

import numpy as np

from agent_memory_system.core.memory.memory_utils import (
    generate_memory_vectors,
    preprocess_memory
)
from agent_memory_system.core.retrieval.memory_retrieval import MemoryRetrieval
from agent_memory_system.core.storage.cache_store import CacheStore
from agent_memory_system.core.storage.graph_store import GraphStore
from agent_memory_system.core.storage.vector_store import VectorStore
from agent_memory_system.models.memory_model import (
    Memory,
    MemoryRelation,
    MemoryStatus,
    MemoryType,
    RetrievalResult
)

class TestRetrieval(unittest.TestCase):
    """检索引擎测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建存储引擎
        self.vector_store = VectorStore()
        self.graph_store = GraphStore()
        self.cache_store = CacheStore()
        
        # 创建检索引擎
        self.retrieval = MemoryRetrieval(
            vector_store=self.vector_store,
            graph_store=self.graph_store,
            cache_store=self.cache_store
        )
        
        # 创建测试用记忆
        self.memories = [
            preprocess_memory(Memory(
                content=f"这是测试记忆{i}",
                memory_type=MemoryType.SHORT_TERM,
                importance=5,
                relations=[
                    MemoryRelation(
                        relation_type="test",
                        target_id=f"test_memory_{i+1}",
                        strength=5
                    )
                ]
            ))
            for i in range(5)
        ]
        
        # 存储测试记忆
        for memory in self.memories:
            # 存储向量
            for vector in memory.vectors:
                self.vector_store.add(memory.id, vector.vector)
            
            # 存储记忆
            self.graph_store.add_memory(memory)
    
    def tearDown(self):
        """测试后清理"""
        # 清理测试数据
        self.vector_store.clear()
        self.graph_store.clear()
        self.cache_store.clear_all()
    
    def test_retrieve_by_content(self):
        """测试基于内容检索"""
        # 检索记忆
        results = self.retrieval.retrieve_by_content(
            query="这是测试记忆0",
            top_k=3,
            threshold=0.5
        )
        
        # 验证结果
        self.assertTrue(len(results) > 0)
        self.assertTrue(len(results) <= 3)
        
        # 验证结果排序
        for i in range(len(results) - 1):
            self.assertGreaterEqual(
                results[i].score,
                results[i + 1].score
            )
        
        # 验证相似度阈值
        for result in results:
            self.assertGreaterEqual(result.score, 0.5)
    
    def test_retrieve_by_relation(self):
        """测试基于关系检索"""
        # 检索记忆
        results = self.retrieval.retrieve_by_relation(
            memory_id=self.memories[0].id,
            relation_types=["test"],
            depth=2,
            top_k=3
        )
        
        # 验证结果
        self.assertTrue(len(results) > 0)
        self.assertTrue(len(results) <= 3)
        
        # 验证关系
        for result in results:
            self.assertTrue(
                any(r.relation_type == "test" for r in result.memory.relations)
            )
    
    def test_retrieve_by_time(self):
        """测试基于时间检索"""
        # 设置不同时间
        now = datetime.utcnow()
        for i, memory in enumerate(self.memories):
            memory.created_at = now - timedelta(hours=i)
            self.graph_store.update_memory(memory)
        
        # 检索记忆
        results = self.retrieval.retrieve_by_time(
            start_time=now - timedelta(hours=3),
            end_time=now,
            top_k=3
        )
        
        # 验证结果
        self.assertTrue(len(results) > 0)
        self.assertTrue(len(results) <= 3)
        
        # 验证时间范围
        for result in results:
            self.assertTrue(
                now - timedelta(hours=3) <= result.created_at <= now
            )
    
    def test_retrieve_by_importance(self):
        """测试基于重要性检索"""
        # 设置不同重要性
        for i, memory in enumerate(self.memories):
            memory.importance = i + 3
            self.graph_store.update_memory(memory)
        
        # 检索记忆
        results = self.retrieval.retrieve_by_importance(
            min_importance=5,
            max_importance=7,
            top_k=3
        )
        
        # 验证结果
        self.assertTrue(len(results) > 0)
        self.assertTrue(len(results) <= 3)
        
        # 验证重要性范围
        for result in results:
            self.assertTrue(5 <= result.importance <= 7)
    
    def test_retrieve_combined(self):
        """测试组合检索"""
        # 设置不同属性
        now = datetime.utcnow()
        for i, memory in enumerate(self.memories):
            memory.importance = i + 3
            memory.created_at = now - timedelta(hours=i)
            self.graph_store.update_memory(memory)
        
        # 组合检索
        results = self.retrieval.retrieve(
            query="这是测试记忆",
            memory_type=MemoryType.SHORT_TERM,
            relation_filter={
                self.memories[0].id: ["test"]
            },
            time_filter=(now - timedelta(hours=3), now),
            importance_filter=(5, 7),
            top_k=3,
            threshold=0.5
        )
        
        # 验证结果
        self.assertTrue(len(results) > 0)
        self.assertTrue(len(results) <= 3)
        
        # 验证结果属性
        for result in results:
            # 验证记忆类型
            self.assertEqual(
                result.memory_type,
                MemoryType.SHORT_TERM
            )
            
            # 验证时间范围
            self.assertTrue(
                now - timedelta(hours=3) <= result.created_at <= now
            )
            
            # 验证重要性范围
            self.assertTrue(5 <= result.importance <= 7)
            
            # 验证相似度阈值
            self.assertGreaterEqual(result.score, 0.5)
    
    def test_merge_results(self):
        """测试结果合并"""
        # 创建重复结果
        results = [
            RetrievalResult(
                memory_id=self.memories[0].id,
                memory=self.memories[0],
                score=0.8,
                memory_type=MemoryType.SHORT_TERM,
                importance=5,
                created_at=datetime.utcnow(),
                accessed_at=datetime.utcnow(),
                access_count=0
            ),
            RetrievalResult(
                memory_id=self.memories[0].id,
                memory=self.memories[0],
                score=0.6,
                memory_type=MemoryType.SHORT_TERM,
                importance=5,
                created_at=datetime.utcnow(),
                accessed_at=datetime.utcnow(),
                access_count=0
            )
        ]
        
        # 合并结果
        merged = self.retrieval._merge_results(results)
        
        # 验证去重
        self.assertEqual(len(merged), 1)
        
        # 验证分数
        self.assertEqual(merged[0].score, 0.8)
    
    def test_filter_results(self):
        """测试结果过滤"""
        # 创建测试结果
        now = datetime.utcnow()
        results = [
            RetrievalResult(
                memory_id=memory.id,
                memory=memory,
                score=0.8,
                memory_type=memory.memory_type,
                importance=i + 3,
                created_at=now - timedelta(hours=i),
                accessed_at=now,
                access_count=0
            )
            for i, memory in enumerate(self.memories)
        ]
        
        # 过滤结果
        filtered = self.retrieval._filter_results(
            results=results,
            memory_type=MemoryType.SHORT_TERM,
            time_filter=(now - timedelta(hours=3), now),
            importance_filter=(5, 7)
        )
        
        # 验证过滤结果
        for result in filtered:
            # 验证记忆类型
            self.assertEqual(
                result.memory_type,
                MemoryType.SHORT_TERM
            )
            
            # 验证时间范围
            self.assertTrue(
                now - timedelta(hours=3) <= result.created_at <= now
            )
            
            # 验证重要性范围
            self.assertTrue(5 <= result.importance <= 7)
    
    def test_postprocess_results(self):
        """测试结果后处理"""
        # 创建测试结果
        results = [
            RetrievalResult(
                memory_id=memory.id,
                memory=memory,
                score=0.8,
                memory_type=memory.memory_type,
                importance=memory.importance,
                created_at=memory.created_at,
                accessed_at=memory.accessed_at,
                access_count=memory.access_count
            )
            for memory in self.memories[:2]
        ]
        
        # 记录原始访问信息
        original_accessed_at = results[0].accessed_at
        original_access_count = results[0].access_count
        
        # 后处理结果
        processed = self.retrieval.postprocess_results(results)
        
        # 验证访问信息更新
        self.assertGreater(
            processed[0].accessed_at,
            original_accessed_at
        )
        self.assertEqual(
            processed[0].access_count,
            original_access_count + 1
        )
    
    def test_optimize_retrieval(self):
        """测试检索优化"""
        # 执行优化
        self.retrieval.optimize_retrieval()

if __name__ == "__main__":
    unittest.main() 