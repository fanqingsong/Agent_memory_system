"""记忆类型处理模块单元测试

测试记忆类型处理模块的各项功能。

测试内容：
    - 记忆类型处理器基类
    - 短期记忆处理器
    - 长期记忆处理器
    - 工作记忆处理器
    - 技能记忆处理器
    - 记忆类型注册表

作者：Cursor_for_YansongW
创建日期：2024-01-09
"""

import unittest
from datetime import datetime, timedelta
from typing import List

from agent_memory_system.core.memory.memory_types import (
    LongTermMemoryHandler,
    MemoryTypeHandler,
    MemoryTypeRegistry,
    ShortTermMemoryHandler,
    SkillMemoryHandler,
    WorkingMemoryHandler
)
from agent_memory_system.models.memory_model import (
    Memory,
    MemoryRelation,
    MemoryStatus,
    MemoryType
)

class TestMemoryTypes(unittest.TestCase):
    """记忆类型处理模块测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建测试用记忆
        self.memory = Memory(
            content="这是一条测试记忆",
            memory_type=MemoryType.SHORT_TERM,
            importance=5,
            relations=[
                MemoryRelation(
                    relation_type="test",
                    target_id="test_id",
                    strength=5
                )
            ]
        )
        
        # 创建各类型处理器
        self.short_term_handler = ShortTermMemoryHandler()
        self.long_term_handler = LongTermMemoryHandler()
        self.working_handler = WorkingMemoryHandler()
        self.skill_handler = SkillMemoryHandler()
    
    def test_short_term_memory_handler(self):
        """测试短期记忆处理器"""
        handler = self.short_term_handler
        
        # 测试存储判断
        self.assertTrue(handler.should_store(self.memory))
        
        # 测试重要性过高的情况
        self.memory.importance = 8
        self.assertFalse(handler.should_store(self.memory))
        
        # 测试内容过长的情况
        self.memory.content = "x" * 1500
        self.assertFalse(handler.should_store(self.memory))
        
        # 测试重要性计算
        self.memory.content = "这是一条测试记忆"
        self.memory.importance = 5
        importance = handler.calculate_importance(self.memory)
        self.assertTrue(1 <= importance <= 10)
        
        # 测试遗忘判断
        self.assertFalse(handler.should_forget(self.memory))
        
        # 测试长时间未访问的情况
        self.memory.accessed_at = datetime.utcnow() - timedelta(hours=13)
        self.assertTrue(handler.should_forget(self.memory))
        
        # 测试优化
        optimized = handler.optimize(self.memory)
        self.assertIsNotNone(optimized)
        self.assertEqual(optimized.memory_type, MemoryType.SHORT_TERM)
    
    def test_long_term_memory_handler(self):
        """测试长期记忆处理器"""
        handler = self.long_term_handler
        
        # 测试存储判断
        self.memory.importance = 8
        self.memory.relations = [
            MemoryRelation(
                relation_type="test",
                target_id=f"test_{i}",
                strength=5
            )
            for i in range(3)
        ]
        self.assertTrue(handler.should_store(self.memory))
        
        # 测试重要性过低的情况
        self.memory.importance = 5
        self.assertFalse(handler.should_store(self.memory))
        
        # 测试关系过少的情况
        self.memory.importance = 8
        self.memory.relations = []
        self.assertFalse(handler.should_store(self.memory))
        
        # 测试重要性计算
        self.memory.relations = [
            MemoryRelation(
                relation_type="test",
                target_id=f"test_{i}",
                strength=5
            )
            for i in range(3)
        ]
        importance = handler.calculate_importance(self.memory)
        self.assertTrue(5 <= importance <= 10)
        
        # 测试遗忘判断
        self.assertFalse(handler.should_forget(self.memory))
        
        # 测试长时间未访问的情况
        self.memory.accessed_at = datetime.utcnow() - timedelta(days=91)
        self.assertTrue(handler.should_forget(self.memory))
        
        # 测试优化
        optimized = handler.optimize(self.memory)
        self.assertIsNotNone(optimized)
        self.assertEqual(optimized.memory_type, MemoryType.LONG_TERM)
    
    def test_working_memory_handler(self):
        """测试工作记忆处理器"""
        handler = self.working_handler
        
        # 测试存储判断
        self.memory.memory_type = MemoryType.WORKING
        self.assertTrue(handler.should_store(self.memory))
        
        # 测试内容过长的情况
        self.memory.content = "x" * 600
        self.assertFalse(handler.should_store(self.memory))
        
        # 测试关系过多的情况
        self.memory.content = "这是一条测试记忆"
        self.memory.relations = [
            MemoryRelation(
                relation_type="test",
                target_id=f"test_{i}",
                strength=5
            )
            for i in range(6)
        ]
        self.assertFalse(handler.should_store(self.memory))
        
        # 测试重要性计算
        self.memory.relations = [
            MemoryRelation(
                relation_type="test",
                target_id="test_id",
                strength=5
            )
        ]
        importance = handler.calculate_importance(self.memory)
        self.assertTrue(1 <= importance <= 10)
        
        # 测试遗忘判断
        self.assertFalse(handler.should_forget(self.memory))
        
        # 测试短时间未访问的情况
        self.memory.accessed_at = datetime.utcnow() - timedelta(minutes=31)
        self.assertTrue(handler.should_forget(self.memory))
        
        # 测试优化
        optimized = handler.optimize(self.memory)
        self.assertIsNotNone(optimized)
        self.assertEqual(optimized.memory_type, MemoryType.WORKING)
    
    def test_skill_memory_handler(self):
        """测试技能记忆处理器"""
        handler = self.skill_handler
        
        # 测试存储判断
        self.memory.memory_type = MemoryType.SKILL
        self.memory.content = "步骤1: xxx\n步骤2: xxx\n步骤3: xxx"
        self.memory.relations = [
            MemoryRelation(
                relation_type="test",
                target_id=f"test_{i}",
                strength=5
            )
            for i in range(3)
        ]
        self.assertTrue(handler.should_store(self.memory))
        
        # 测试内容过短的情况
        self.memory.content = "简单步骤"
        self.assertFalse(handler.should_store(self.memory))
        
        # 测试关系过少的情况
        self.memory.content = "步骤1: xxx\n步骤2: xxx\n步骤3: xxx"
        self.memory.relations = []
        self.assertFalse(handler.should_store(self.memory))
        
        # 测试重要性计算
        self.memory.relations = [
            MemoryRelation(
                relation_type="test",
                target_id=f"test_{i}",
                strength=5
            )
            for i in range(3)
        ]
        importance = handler.calculate_importance(self.memory)
        self.assertTrue(1 <= importance <= 10)
        
        # 测试遗忘判断
        self.assertFalse(handler.should_forget(self.memory))
        
        # 测试长时间未访问的情况
        self.memory.accessed_at = datetime.utcnow() - timedelta(days=366)
        self.assertTrue(handler.should_forget(self.memory))
        
        # 测试优化
        optimized = handler.optimize(self.memory)
        self.assertIsNotNone(optimized)
        self.assertEqual(optimized.memory_type, MemoryType.SKILL)
    
    def test_memory_type_registry(self):
        """测试记忆类型注册表"""
        registry = MemoryTypeRegistry()
        
        # 测试单例模式
        registry2 = MemoryTypeRegistry()
        self.assertIs(registry, registry2)
        
        # 测试获取处理器
        handler = registry.get_handler(MemoryType.SHORT_TERM)
        self.assertIsInstance(handler, ShortTermMemoryHandler)
        
        handler = registry.get_handler(MemoryType.LONG_TERM)
        self.assertIsInstance(handler, LongTermMemoryHandler)
        
        handler = registry.get_handler(MemoryType.WORKING)
        self.assertIsInstance(handler, WorkingMemoryHandler)
        
        handler = registry.get_handler(MemoryType.SKILL)
        self.assertIsInstance(handler, SkillMemoryHandler)
        
        # 测试字符串类型
        handler = registry.get_handler("short_term")
        self.assertIsInstance(handler, ShortTermMemoryHandler)
        
        # 测试无效类型
        with self.assertRaises(ValueError):
            registry.get_handler("invalid_type")

if __name__ == "__main__":
    unittest.main() 