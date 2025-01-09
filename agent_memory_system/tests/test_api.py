"""API接口单元测试

测试API接口的各项功能。

测试内容：
    - 记忆创建接口
    - 记忆获取接口
    - 记忆更新接口
    - 记忆删除接口
    - 记忆检索接口
    - 记忆关系管理接口

作者：Cursor_for_YansongW
创建日期：2025-01-09
"""

import json
import unittest
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from fastapi.testclient import TestClient

from agent_memory_system.api.memory_api import app
from agent_memory_system.models.memory_model import (
    Memory,
    MemoryRelation,
    MemoryStatus,
    MemoryType,
    RetrievalResult
)

class TestAPI(unittest.TestCase):
    """API接口测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建测试客户端
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
    
    def test_create_memory(self):
        """测试创建记忆接口"""
        # 发送请求
        response = self.client.post(
            "/memories",
            json=self.memory_data
        )
        
        # 验证响应
        self.assertEqual(response.status_code, 200)
        
        # 验证响应数据
        data = response.json()
        self.assertIsNotNone(data["memory_id"])
        self.assertEqual(data["content"], self.memory_data["content"])
        self.assertEqual(data["memory_type"], self.memory_data["memory_type"])
        self.assertEqual(data["importance"], self.memory_data["importance"])
        self.assertEqual(data["status"], "active")
        self.assertEqual(len(data["relations"]), 1)
        
        # 保存记忆ID用于后续测试
        self.memory_id = data["memory_id"]
    
    def test_get_memory(self):
        """测试获取记忆接口"""
        # 先创建记忆
        response = self.client.post(
            "/memories",
            json=self.memory_data
        )
        memory_id = response.json()["memory_id"]
        
        # 获取记忆
        response = self.client.get(f"/memories/{memory_id}")
        
        # 验证响应
        self.assertEqual(response.status_code, 200)
        
        # 验证响应数据
        data = response.json()
        self.assertEqual(data["memory_id"], memory_id)
        self.assertEqual(data["content"], self.memory_data["content"])
    
    def test_get_nonexistent_memory(self):
        """测试获取不存在的记忆"""
        response = self.client.get("/memories/nonexistent_id")
        self.assertEqual(response.status_code, 404)
    
    def test_update_memory(self):
        """测试更新记忆接口"""
        # 先创建记忆
        response = self.client.post(
            "/memories",
            json=self.memory_data
        )
        memory_id = response.json()["memory_id"]
        
        # 更新数据
        update_data = self.memory_data.copy()
        update_data["content"] = "这是更新后的记忆"
        
        # 更新记忆
        response = self.client.put(
            f"/memories/{memory_id}",
            json=update_data
        )
        
        # 验证响应
        self.assertEqual(response.status_code, 200)
        
        # 验证响应数据
        data = response.json()
        self.assertEqual(data["content"], "这是更新后的记忆")
    
    def test_update_nonexistent_memory(self):
        """测试更新不存在的记忆"""
        response = self.client.put(
            "/memories/nonexistent_id",
            json=self.memory_data
        )
        self.assertEqual(response.status_code, 404)
    
    def test_delete_memory(self):
        """测试删除记忆接口"""
        # 先创建记忆
        response = self.client.post(
            "/memories",
            json=self.memory_data
        )
        memory_id = response.json()["memory_id"]
        
        # 删除记忆
        response = self.client.delete(f"/memories/{memory_id}")
        
        # 验证响应
        self.assertEqual(response.status_code, 200)
        
        # 验证记忆已删除
        response = self.client.get(f"/memories/{memory_id}")
        self.assertEqual(response.status_code, 404)
    
    def test_retrieve_memories(self):
        """测试检索记忆接口"""
        # 先创建多个记忆
        memories = []
        for i in range(5):
            data = self.memory_data.copy()
            data["content"] = f"这是测试记忆{i}"
            response = self.client.post(
                "/memories",
                json=data
            )
            memories.append(response.json())
        
        # 构建检索请求
        retrieval_data = {
            "query": "这是测试记忆0",
            "memory_type": "short_term",
            "top_k": 3,
            "threshold": 0.5
        }
        
        # 检索记忆
        response = self.client.post(
            "/memories/retrieve",
            json=retrieval_data
        )
        
        # 验证响应
        self.assertEqual(response.status_code, 200)
        
        # 验证响应数据
        data = response.json()
        self.assertIsNotNone(data["results"])
        self.assertTrue(len(data["results"]) <= 3)
        self.assertEqual(data["total"], len(data["results"]))
    
    def test_retrieve_with_filters(self):
        """测试带过滤条件的检索"""
        # 先创建多个记忆
        memories = []
        now = datetime.utcnow()
        for i in range(5):
            data = self.memory_data.copy()
            data["content"] = f"这是测试记忆{i}"
            data["importance"] = i + 3
            response = self.client.post(
                "/memories",
                json=data
            )
            memories.append(response.json())
        
        # 构建检索请求
        retrieval_data = {
            "query": "这是测试记忆",
            "memory_type": "short_term",
            "importance_filter": {
                "min_importance": 5,
                "max_importance": 7
            },
            "time_filter": {
                "start_time": (now - timedelta(hours=1)).isoformat(),
                "end_time": now.isoformat()
            },
            "top_k": 3,
            "threshold": 0.5
        }
        
        # 检索记忆
        response = self.client.post(
            "/memories/retrieve",
            json=retrieval_data
        )
        
        # 验证响应
        self.assertEqual(response.status_code, 200)
        
        # 验证响应数据
        data = response.json()
        self.assertIsNotNone(data["results"])
        for result in data["results"]:
            self.assertTrue(5 <= result["importance"] <= 7)
    
    def test_add_memory_relation(self):
        """测试添加记忆关系接口"""
        # 先创建两个记忆
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
        
        # 构建关系数据
        relation_data = {
            "relation_type": "test",
            "target_id": memory2_id,
            "strength": 5
        }
        
        # 添加关系
        response = self.client.post(
            f"/memories/{memory1_id}/relations",
            json=relation_data
        )
        
        # 验证响应
        self.assertEqual(response.status_code, 200)
        
        # 验证响应数据
        data = response.json()
        self.assertTrue(
            any(
                r["target_id"] == memory2_id
                for r in data["relations"]
            )
        )
    
    def test_delete_memory_relation(self):
        """测试删除记忆关系接口"""
        # 先创建带关系的记忆
        response = self.client.post(
            "/memories",
            json=self.memory_data
        )
        memory_id = response.json()["memory_id"]
        relation_id = "test_memory_2"
        
        # 删除关系
        response = self.client.delete(
            f"/memories/{memory_id}/relations/{relation_id}"
        )
        
        # 验证响应
        self.assertEqual(response.status_code, 200)
        
        # 验证响应数据
        data = response.json()
        self.assertFalse(
            any(
                r["target_id"] == relation_id
                for r in data["relations"]
            )
        )
    
    def test_invalid_memory_type(self):
        """测试无效的记忆类型"""
        data = self.memory_data.copy()
        data["memory_type"] = "invalid_type"
        
        response = self.client.post(
            "/memories",
            json=data
        )
        self.assertEqual(response.status_code, 422)
    
    def test_invalid_importance(self):
        """测试无效的重要性值"""
        data = self.memory_data.copy()
        data["importance"] = 11  # 超出范围
        
        response = self.client.post(
            "/memories",
            json=data
        )
        self.assertEqual(response.status_code, 422)
    
    def test_missing_required_fields(self):
        """测试缺少必填字段"""
        data = {
            "content": "这是一条测试记忆"
            # 缺少memory_type
        }
        
        response = self.client.post(
            "/memories",
            json=data
        )
        self.assertEqual(response.status_code, 422)

if __name__ == "__main__":
    unittest.main() 