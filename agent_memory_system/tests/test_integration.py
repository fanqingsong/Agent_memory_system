"""系统集成测试

测试整个系统的功能集成。

测试内容：
    - 记忆存储和检索流程
    - 记忆关系管理流程
    - 记忆类型转换流程
    - 记忆优化流程
    - 系统性能测试

作者：Cursor_for_YansongW
创建日期：2024-01-09
"""

import time
import unittest
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set

import numpy as np
from fastapi.testclient import TestClient

from agent_memory_system.api.memory_api import app
from agent_memory_system.core.memory.memory_manager import MemoryManager
from agent_memory_system.core.memory.memory_types import (
    LongTermMemoryHandler,
    MemoryTypeRegistry,
    ShortTermMemoryHandler,
    SkillMemoryHandler,
    WorkingMemoryHandler
)
from agent_memory_system.core.memory.memory_utils import (
    calculate_similarity,
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

class TestIntegration(unittest.TestCase):
    """系统集成测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建存储引擎
        self.vector_store = VectorStore()
        self.graph_store = GraphStore()
        self.cache_store = CacheStore()
        
        # 创建记忆管理器
        self.memory_manager = MemoryManager()
        
        # 创建API客户端
        self.client = TestClient(app)
        
        # 创建测试数据
        self.memory_data = {
            "content": "这是一条测试记忆",
            "memory_type": "short_term",
            "importance": 5,
            "relations": [
                {
                    "relation_type": "test",
                    "target_id": "test_memory_2",
                    "strength": 5
                }
            ]
        }
    
    def tearDown(self):
        """测试后清理"""
        # 清理测试数据
        self.vector_store.clear()
        self.graph_store.clear()
        self.cache_store.clear_all()
    
    def test_memory_lifecycle(self):
        """测试记忆生命周期"""
        # 1. 创建记忆
        response = self.client.post(
            "/memories",
            json=self.memory_data
        )
        self.assertEqual(response.status_code, 200)
        memory_id = response.json()["memory_id"]
        
        # 2. 获取记忆
        response = self.client.get(f"/memories/{memory_id}")
        self.assertEqual(response.status_code, 200)
        memory = response.json()
        
        # 3. 更新记忆
        memory["content"] = "这是更新后的记忆"
        response = self.client.put(
            f"/memories/{memory_id}",
            json=memory
        )
        self.assertEqual(response.status_code, 200)
        
        # 4. 检索记忆
        response = self.client.post(
            "/memories/retrieve",
            json={
                "query": "这是更新后的记忆",
                "memory_type": "short_term",
                "top_k": 1
            }
        )
        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        
        # 5. 删除记忆
        response = self.client.delete(f"/memories/{memory_id}")
        self.assertEqual(response.status_code, 200)
        
        # 6. 验证删除
        response = self.client.get(f"/memories/{memory_id}")
        self.assertEqual(response.status_code, 404)
    
    def test_memory_relation_management(self):
        """测试记忆关系管理"""
        # 1. 创建两个记忆
        response1 = self.client.post(
            "/memories",
            json=self.memory_data
        )
        memory1_id = response1.json()["memory_id"]
        
        data2 = self.memory_data.copy()
        data2["content"] = "这是第二条测试记忆"
        response2 = self.client.post(
            "/memories",
            json=data2
        )
        memory2_id = response2.json()["memory_id"]
        
        # 2. 添加关系
        relation = {
            "relation_type": "reference",
            "target_id": memory2_id,
            "strength": 8
        }
        response = self.client.post(
            f"/memories/{memory1_id}/relations",
            json=relation
        )
        self.assertEqual(response.status_code, 200)
        
        # 3. 基于关系检索
        response = self.client.post(
            "/memories/retrieve",
            json={
                "relation_filter": {
                    memory1_id: ["reference"]
                },
                "top_k": 1
            }
        )
        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        
        # 4. 删除关系
        response = self.client.delete(
            f"/memories/{memory1_id}/relations/{memory2_id}"
        )
        self.assertEqual(response.status_code, 200)
        
        # 5. 验证关系删除
        response = self.client.get(f"/memories/{memory1_id}")
        memory = response.json()
        self.assertFalse(
            any(r["target_id"] == memory2_id for r in memory["relations"])
        )
    
    def test_memory_type_conversion(self):
        """测试记忆类型转换"""
        # 1. 创建工作记忆
        data = self.memory_data.copy()
        data["memory_type"] = "working"
        data["importance"] = 3
        response = self.client.post(
            "/memories",
            json=data
        )
        memory_id = response.json()["memory_id"]
        
        # 2. 增加访问次数和重要性
        for _ in range(10):
            response = self.client.get(f"/memories/{memory_id}")
            memory = response.json()
            memory["importance"] += 1
            if memory["importance"] > 10:
                memory["importance"] = 10
            response = self.client.put(
                f"/memories/{memory_id}",
                json=memory
            )
        
        # 3. 验证类型转换
        response = self.client.get(f"/memories/{memory_id}")
        memory = response.json()
        self.assertEqual(memory["memory_type"], "long_term")
    
    def test_memory_optimization(self):
        """测试记忆优化"""
        # 1. 创建多个相似记忆
        memories = []
        for i in range(3):
            data = self.memory_data.copy()
            data["content"] = f"这是一条关于优化的测试记忆 版本{i}"
            response = self.client.post(
                "/memories",
                json=data
            )
            memories.append(response.json())
        
        # 2. 检索并合并相似记忆
        response = self.client.post(
            "/memories/retrieve",
            json={
                "query": "关于优化的测试记忆",
                "memory_type": "short_term",
                "top_k": 10,
                "threshold": 0.7
            }
        )
        results = response.json()["results"]
        
        # 3. 验证记忆合并
        self.assertTrue(len(results) < 3)
    
    def test_system_performance(self):
        """测试系统性能"""
        # 1. 批量创建记忆
        start_time = time.time()
        memories = []
        for i in range(100):
            data = self.memory_data.copy()
            data["content"] = f"这是性能测试记忆{i}"
            response = self.client.post(
                "/memories",
                json=data
            )
            memories.append(response.json())
        create_time = time.time() - start_time
        
        # 2. 批量检索记忆
        start_time = time.time()
        for i in range(10):
            response = self.client.post(
                "/memories/retrieve",
                json={
                    "query": f"性能测试记忆{i}",
                    "top_k": 5
                }
            )
        retrieve_time = time.time() - start_time
        
        # 3. 验证性能指标
        self.assertLess(create_time / 100, 0.1)  # 平均创建时间小于0.1秒
        self.assertLess(retrieve_time / 10, 0.2)  # 平均检索时间小于0.2秒
    
    def test_error_handling(self):
        """测试错误处理"""
        # 1. 测试无效的记忆类型
        data = self.memory_data.copy()
        data["memory_type"] = "invalid_type"
        response = self.client.post(
            "/memories",
            json=data
        )
        self.assertEqual(response.status_code, 422)
        
        # 2. 测试无效的重要性值
        data = self.memory_data.copy()
        data["importance"] = 11
        response = self.client.post(
            "/memories",
            json=data
        )
        self.assertEqual(response.status_code, 422)
        
        # 3. 测试不存在的记忆ID
        response = self.client.get("/memories/nonexistent_id")
        self.assertEqual(response.status_code, 404)
        
        # 4. 测试无效的关系
        response = self.client.post(
            "/memories/invalid_id/relations",
            json={
                "relation_type": "test",
                "target_id": "invalid_target",
                "strength": 5
            }
        )
        self.assertEqual(response.status_code, 404)
    
    def test_concurrent_access(self):
        """测试并发访问"""
        import threading
        
        # 1. 创建测试记忆
        response = self.client.post(
            "/memories",
            json=self.memory_data
        )
        memory_id = response.json()["memory_id"]
        
        # 2. 定义并发操作
        def concurrent_update():
            data = self.memory_data.copy()
            data["importance"] += 1
            self.client.put(
                f"/memories/{memory_id}",
                json=data
            )
        
        # 3. 启动多个线程
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=concurrent_update)
            threads.append(thread)
            thread.start()
        
        # 4. 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 5. 验证数据一致性
        response = self.client.get(f"/memories/{memory_id}")
        memory = response.json()
        self.assertTrue(5 <= memory["importance"] <= 15)
    
    def test_cache_effectiveness(self):
        """测试缓存效果"""
        # 1. 创建测试记忆
        response = self.client.post(
            "/memories",
            json=self.memory_data
        )
        memory_id = response.json()["memory_id"]
        
        # 2. 首次访问
        start_time = time.time()
        response1 = self.client.get(f"/memories/{memory_id}")
        first_access_time = time.time() - start_time
        
        # 3. 再次访问
        start_time = time.time()
        response2 = self.client.get(f"/memories/{memory_id}")
        second_access_time = time.time() - start_time
        
        # 4. 验证缓存加速
        self.assertLess(second_access_time, first_access_time)
    
    def test_memory_decay(self):
        """测试记忆衰减"""
        # 1. 创建测试记忆
        data = self.memory_data.copy()
        data["importance"] = 10
        response = self.client.post(
            "/memories",
            json=data
        )
        memory_id = response.json()["memory_id"]
        
        # 2. 等待一段时间
        time.sleep(2)
        
        # 3. 检查重要性衰减
        response = self.client.get(f"/memories/{memory_id}")
        memory = response.json()
        self.assertLess(memory["importance"], 10)

if __name__ == "__main__":
    unittest.main() 