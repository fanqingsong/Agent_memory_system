"""存储引擎单元测试

测试存储引擎的各项功能。

测试内容：
    - 向量存储引擎
    - 图存储引擎
    - 缓存存储引擎

作者：Cursor_for_YansongW
创建日期：2025-01-09
"""

import unittest
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple

import numpy as np
from neo4j import GraphDatabase
from redis import Redis

from agent_memory_system.core.storage.cache_store import CacheStore
from agent_memory_system.core.storage.graph_store import GraphStore
from agent_memory_system.core.storage.vector_store import VectorStore
from agent_memory_system.models.memory_model import (
    Memory,
    MemoryRelation,
    MemoryStatus,
    MemoryType,
    MemoryVector
)
from agent_memory_system.utils.config import config

class TestVectorStore(unittest.TestCase):
    """向量存储引擎测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建向量存储引擎
        self.vector_store = VectorStore()
        
        # 创建测试用向量
        self.test_vector = np.random.rand(128)
        self.test_id = "test_vector_1"
    
    def tearDown(self):
        """测试后清理"""
        # 清理测试数据
        self.vector_store.clear()
    
    def test_add_vector(self):
        """测试添加向量"""
        # 添加向量
        self.vector_store.add(
            id=self.test_id,
            vector=self.test_vector
        )
        
        # 验证向量是否存在
        self.assertTrue(self.test_id in self.vector_store)
        
        # 验证向量内容
        stored_vector = self.vector_store.get(self.test_id)
        self.assertTrue(np.allclose(stored_vector, self.test_vector))
    
    def test_get_vector(self):
        """测试获取向量"""
        # 添加向量
        self.vector_store.add(
            id=self.test_id,
            vector=self.test_vector
        )
        
        # 获取向量
        vector = self.vector_store.get(self.test_id)
        
        # 验证向量
        self.assertIsNotNone(vector)
        self.assertTrue(np.allclose(vector, self.test_vector))
    
    def test_delete_vector(self):
        """测试删除向量"""
        # 添加向量
        self.vector_store.add(
            id=self.test_id,
            vector=self.test_vector
        )
        
        # 删除向量
        success = self.vector_store.delete(self.test_id)
        
        # 验证删除结果
        self.assertTrue(success)
        self.assertFalse(self.test_id in self.vector_store)
    
    def test_search_vectors(self):
        """测试搜索向量"""
        # 添加多个向量
        vectors = [
            (f"test_vector_{i}", np.random.rand(128))
            for i in range(5)
        ]
        for vec_id, vector in vectors:
            self.vector_store.add(id=vec_id, vector=vector)

        # 搜索向量
        query_vector = vectors[0][1]
        results = self.vector_store.search(
            vector=query_vector,
            k=3,
            threshold=0.5
        )
        
        # 验证结果
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0][0], vectors[0][0])
    
    def test_update_vector(self):
        """测试更新向量"""
        # 添加向量
        self.vector_store.add(
            id=self.test_id,
            vector=self.test_vector
        )
        
        # 更新向量
        new_vector = np.random.rand(128)
        success = self.vector_store.update(
            id=self.test_id,
            vector=new_vector
        )
        
        # 验证更新结果
        self.assertTrue(success)
        stored_vector = self.vector_store.get(self.test_id)
        self.assertTrue(np.allclose(stored_vector, new_vector))
    
    def test_optimize_index(self):
        """测试优化索引"""
        # 添加多个向量
        for i in range(10):
            self.vector_store.add(
                id=f"test_vector_{i}",
                vector=np.random.rand(128)
            )

class TestGraphStore(unittest.TestCase):
    """图存储引擎测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建图存储引擎
        self.graph_store = GraphStore()
        
        # 创建测试用记忆
        self.memory = Memory(
            id="test_memory_1",
            content="这是一条测试记忆",
            memory_type=MemoryType.SHORT_TERM,
            importance=5,
            relations=[
                MemoryRelation(
                    relation_type="test",
                    target_id="test_memory_2",
                    strength=5
                )
            ]
        )
    
    def tearDown(self):
        """测试后清理"""
        # 清理测试数据
        self.graph_store.clear()
    
    def test_add_memory(self):
        """测试添加记忆"""
        # 添加记忆
        self.graph_store.add_memory(self.memory)
        
        # 验证记忆存在
        memory = self.graph_store.get_memory(self.memory.id)
        self.assertIsNotNone(memory)
        self.assertEqual(memory.id, self.memory.id)
    
    def test_get_memory(self):
        """测试获取记忆"""
        # 添加记忆
        self.graph_store.add_memory(self.memory)
        
        # 获取记忆
        memory = self.graph_store.get_memory(self.memory.id)
        
        # 验证记忆
        self.assertIsNotNone(memory)
        self.assertEqual(memory.content, self.memory.content)
        self.assertEqual(memory.memory_type, self.memory.memory_type)
        self.assertEqual(memory.importance, self.memory.importance)
    
    def test_update_memory(self):
        """测试更新记忆"""
        # 添加记忆
        self.graph_store.add_memory(self.memory)
        
        # 更新记忆
        self.memory.content = "这是更新后的记忆"
        self.graph_store.update_memory(self.memory)
        
        # 验证更新
        memory = self.graph_store.get_memory(self.memory.id)
        self.assertEqual(memory.content, "这是更新后的记忆")
    
    def test_delete_memory(self):
        """测试删除记忆"""
        # 添加记忆
        self.graph_store.add_memory(self.memory)
        
        # 删除记忆
        self.graph_store.delete_memory(self.memory.id)
        
        # 验证记忆不存在
        memory = self.graph_store.get_memory(self.memory.id)
        self.assertIsNone(memory)
    
    def test_get_related_memories(self):
        """测试获取相关记忆"""
        # 添加多个记忆
        memories = [
            Memory(
                id=f"test_memory_{i}",
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
            )
            for i in range(3)
        ]
        for memory in memories:
            self.graph_store.add_memory(memory)
        
        # 获取相关记忆
        related = self.graph_store.get_related_memories(
            memory_id="test_memory_1",
            relation_types=["test"],
            depth=2
        )
        
        # 验证结果
        self.assertTrue(len(related) > 0)
        for memory, relations in related.items():
            self.assertIsNotNone(memory)
            self.assertTrue(len(relations) > 0)
    
    def test_get_memories_by_time(self):
        """测试按时间获取记忆"""
        # 添加多个记忆
        now = datetime.utcnow()
        memories = [
            Memory(
                id=f"test_memory_{i}",
                content=f"这是测试记忆{i}",
                memory_type=MemoryType.SHORT_TERM,
                importance=5,
                created_at=now - timedelta(hours=i)
            )
            for i in range(5)
        ]
        for memory in memories:
            self.graph_store.add_memory(memory)
        
        # 获取时间范围内的记忆
        results = self.graph_store.get_memories_by_time(
            start_time=now - timedelta(hours=3),
            end_time=now
        )
        
        # 验证结果
        self.assertTrue(len(results) > 0)
        self.assertTrue(len(results) <= 4)
    
    def test_get_memories_by_importance(self):
        """测试按重要性获取记忆"""
        # 添加多个记忆
        memories = [
            Memory(
                id=f"test_memory_{i}",
                content=f"这是测试记忆{i}",
                memory_type=MemoryType.SHORT_TERM,
                importance=i
            )
            for i in range(1, 11)
        ]
        for memory in memories:
            self.graph_store.add_memory(memory)
        
        # 获取重要性范围内的记忆
        results = self.graph_store.get_memories_by_importance(
            min_importance=5,
            max_importance=8
        )
        
        # 验证结果
        self.assertTrue(len(results) > 0)
        for memory in results:
            self.assertTrue(5 <= memory.importance <= 8)
    
    def test_optimize_graph(self):
        """测试优化图结构"""
        # 添加多个记忆和关系
        for i in range(10):
            memory = Memory(
                id=f"test_memory_{i}",
                content=f"这是测试记忆{i}",
                memory_type=MemoryType.SHORT_TERM,
                importance=5,
                relations=[
                    MemoryRelation(
                        relation_type="test",
                        target_id=f"test_memory_{j}",
                        strength=5
                    )
                    for j in range(max(0, i-2), min(10, i+3))
                    if j != i
                ]
            )
            self.graph_store.add_memory(memory)
        
        # 优化图结构
        self.graph_store.optimize_graph()

@unittest.skip("Redis not available")
class TestCacheStore(unittest.TestCase):
    """缓存存储引擎测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建缓存存储引擎
        self.cache_store = CacheStore()
        
        # 创建测试数据
        self.test_key = "test_key"
        self.test_value = "test_value"
    
    def tearDown(self):
        """测试后清理"""
        # 清理测试数据
        self.cache_store.clear_all()
    
    def test_set_get(self):
        """测试设置和获取缓存"""
        # 设置缓存
        self.cache_store.set(
            key=self.test_key,
            value=self.test_value,
            ttl=300
        )
        
        # 获取缓存
        value = self.cache_store.get(self.test_key)
        
        # 验证缓存
        self.assertEqual(value, self.test_value)
    
    def test_delete(self):
        """测试删除缓存"""
        # 设置缓存
        self.cache_store.set(
            key=self.test_key,
            value=self.test_value
        )
        
        # 删除缓存
        self.cache_store.delete(self.test_key)
        
        # 验证缓存不存在
        value = self.cache_store.get(self.test_key)
        self.assertIsNone(value)
    
    def test_exists(self):
        """测试缓存存在性"""
        # 设置缓存
        self.cache_store.set(
            key=self.test_key,
            value=self.test_value
        )
        
        # 验证存在性
        self.assertTrue(
            self.cache_store.exists(self.test_key)
        )
        
        # 验证不存在
        self.assertFalse(
            self.cache_store.exists("non_existent_key")
        )
    
    def test_ttl(self):
        """测试缓存过期"""
        # 设置短期缓存
        self.cache_store.set(
            key=self.test_key,
            value=self.test_value,
            ttl=1
        )
        
        # 验证缓存存在
        self.assertTrue(
            self.cache_store.exists(self.test_key)
        )
        
        # 等待过期
        import time
        time.sleep(2)
        
        # 验证缓存过期
        self.assertFalse(
            self.cache_store.exists(self.test_key)
        )
    
    def test_clear_expired(self):
        """测试清理过期缓存"""
        # 设置多个缓存
        for i in range(5):
            self.cache_store.set(
                key=f"test_key_{i}",
                value=f"test_value_{i}",
                ttl=1 if i < 3 else 300
            )
        
        # 等待部分过期
        import time
        time.sleep(2)
        
        # 清理过期缓存
        self.cache_store.clear_expired()
        
        # 验证结果
        for i in range(5):
            exists = self.cache_store.exists(f"test_key_{i}")
            if i < 3:
                self.assertFalse(exists)
            else:
                self.assertTrue(exists)
    
    def test_clear_all(self):
        """测试清理所有缓存"""
        # 设置多个缓存
        for i in range(5):
            self.cache_store.set(
                key=f"test_key_{i}",
                value=f"test_value_{i}"
            )
        
        # 清理所有缓存
        self.cache_store.clear_all()
        
        # 验证所有缓存不存在
        for i in range(5):
            self.assertFalse(
                self.cache_store.exists(f"test_key_{i}")
            )

if __name__ == "__main__":
    unittest.main() 