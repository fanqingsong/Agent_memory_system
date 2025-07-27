"""记忆工具模块单元测试

测试记忆工具模块的各项功能。

测试内容：
    - 记忆预处理
    - 记忆后处理
    - 向量生成
    - 相似度计算
    - 记忆合并

作者：Cursor_for_YansongW
创建日期：2025-01-09
"""

import unittest
from datetime import datetime, timedelta

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from agent_memory_system.core.memory.memory_utils import (
    calculate_content_similarity,
    calculate_initial_importance,
    calculate_relation_similarity,
    calculate_similarity,
    calculate_time_similarity,
    calculate_vector_similarity,
    clean_relations,
    generate_memory_vectors,
    merge_memories,
    merge_memory_group,
    optimize_vectors,
    postprocess_memory,
    preprocess_memory,
    update_importance
)
from agent_memory_system.models.memory_model import (
    Memory,
    MemoryRelation,
    MemoryStatus,
    MemoryType,
    MemoryVector
)

class TestMemoryUtils(unittest.TestCase):
    """记忆工具模块测试类"""
    
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
    
    def test_preprocess_memory(self):
        """测试记忆预处理"""
        # 预处理记忆
        processed = preprocess_memory(self.memory)
        
        # 验证ID生成
        self.assertIsNotNone(processed.id)
        self.assertTrue(processed.id.startswith("short_term_"))
        
        # 验证时间戳
        self.assertIsNotNone(processed.created_at)
        self.assertIsNotNone(processed.accessed_at)
        self.assertIsNotNone(processed.updated_at)
        
        # 验证状态
        self.assertEqual(processed.status, MemoryStatus.ACTIVE)
        self.assertEqual(processed.access_count, 0)
        
        # 验证向量生成
        self.assertIsNotNone(processed.vectors)
        self.assertTrue(len(processed.vectors) > 0)
        
        # 验证重要性
        self.assertIsNotNone(processed.importance)
        self.assertTrue(1 <= processed.importance <= 10)
    
    def test_postprocess_memory(self):
        """测试记忆后处理"""
        # 预处理记忆
        memory = preprocess_memory(self.memory)
        
        # 记录原始访问时间
        original_accessed_at = memory.accessed_at
        
        # 等待一段时间
        import time
        time.sleep(1)
        
        # 后处理记忆
        processed = postprocess_memory(memory)
        
        # 验证访问信息更新
        self.assertGreater(processed.accessed_at, original_accessed_at)
        self.assertEqual(processed.access_count, 1)
        
        # 验证重要性更新
        self.assertIsNotNone(processed.importance)
        self.assertTrue(1 <= processed.importance <= 10)
        
        # 验证向量优化
        self.assertIsNotNone(processed.vectors)
        self.assertTrue(len(processed.vectors) > 0)
        
        # 验证关系清理
        self.assertIsNotNone(processed.relations)
    
    def test_generate_memory_vectors(self):
        """测试向量生成"""
        # 生成向量
        vectors = generate_memory_vectors(self.memory)
        
        # 验证向量列表
        self.assertIsNotNone(vectors)
        self.assertTrue(len(vectors) > 0)
        
        # 验证向量属性
        for vector in vectors:
            self.assertIsInstance(vector, MemoryVector)
            self.assertIsNotNone(vector.vector_type)
            self.assertIsNotNone(vector.vector)
            self.assertIsNotNone(vector.dimension)
            self.assertEqual(len(vector.vector), vector.dimension)
    

    
    def test_calculate_initial_importance(self):
        """测试初始重要性计算"""
        # 计算重要性
        importance = calculate_initial_importance(self.memory)
        
        # 验证重要性范围
        self.assertTrue(1 <= importance <= 10)
        
        # 测试不同情况
        # 长内容
        memory = Memory(
            content="x" * 1000,
            memory_type=MemoryType.SHORT_TERM
        )
        importance = calculate_initial_importance(memory)
        self.assertTrue(importance > 5)
        
        # 多关系
        memory = Memory(
            content="test",
            memory_type=MemoryType.SHORT_TERM,
            relations=[MemoryRelation(
                relation_type="test",
                target_id=f"test_{i}",
                strength=5
            ) for i in range(5)]
        )
        importance = calculate_initial_importance(memory)
        self.assertTrue(importance > 5)
    
    def test_update_importance(self):
        """测试重要性更新"""
        # 预处理记忆
        memory = preprocess_memory(self.memory)
        
        # 更新重要性
        importance = update_importance(memory)
        
        # 验证重要性范围
        self.assertTrue(1 <= importance <= 10)
        
        # 测试访问频率影响
        memory.access_count = 20
        importance = update_importance(memory)
        self.assertTrue(importance > memory.importance)
        
        # 测试时间衰减
        memory.created_at = datetime.utcnow() - timedelta(days=2)
        importance = update_importance(memory)
        self.assertTrue(importance < memory.importance)
    
    def test_optimize_vectors(self):
        """测试向量优化"""
        # 生成向量
        vectors = generate_memory_vectors(self.memory)
        
        # 优化向量
        optimized = optimize_vectors(vectors)
        
        # 验证向量数量
        self.assertEqual(len(optimized), len(vectors))
        
        # 验证向量归一化
        for vector in optimized:
            norm = np.linalg.norm(vector.vector)
            self.assertAlmostEqual(norm, 1.0, places=6)
    
    def test_clean_relations(self):
        """测试关系清理"""
        # 创建测试关系
        relations = [
            MemoryRelation(
                relation_type="test",
                target_id="test_1",
                strength=5
            ),
            MemoryRelation(
                relation_type="test",
                target_id="test_1",  # 重复关系
                strength=3
            ),
            MemoryRelation(
                relation_type="test",
                target_id="test_2",
                strength=0.5  # 弱关系
            )
        ]
        
        # 清理关系
        cleaned = clean_relations(relations)
        
        # 验证去重
        self.assertEqual(len(cleaned), 1)
        
        # 验证关系强度
        self.assertEqual(cleaned[0].target_id, "test_1")
        self.assertTrue(cleaned[0].strength > 0)
    
    def test_calculate_similarity(self):
        """测试相似度计算"""
        # 创建相似记忆
        similar_memory = Memory(
            content="这也是一条测试记忆",
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
        
        # 预处理记忆
        memory1 = preprocess_memory(self.memory)
        memory2 = preprocess_memory(similar_memory)
        
        # 计算相似度
        similarity = calculate_similarity(memory1, memory2)
        
        # 验证相似度范围
        self.assertTrue(0 <= similarity <= 1)
        self.assertTrue(similarity > 0.5)  # 应该相似
        
        # 创建不相似记忆
        different_memory = Memory(
            content="这是一条完全不同的记忆",
            memory_type=MemoryType.LONG_TERM,
            importance=8,
            relations=[]
        )
        
        # 计算相似度
        memory3 = preprocess_memory(different_memory)
        similarity = calculate_similarity(memory1, memory3)
        
        # 验证相似度
        self.assertTrue(similarity < 0.5)  # 应该不相似
    
    def test_calculate_content_similarity(self):
        """测试内容相似度计算"""
        # 计算相似内容
        similarity = calculate_content_similarity(
            "这是一条测试记忆",
            "这也是一条测试记忆"
        )
        
        # 验证相似度范围
        self.assertTrue(0 <= similarity <= 1)
        self.assertTrue(similarity > 0.5)  # 应该相似
        
        # 计算不相似内容
        similarity = calculate_content_similarity(
            "这是一条测试记忆",
            "这是一条完全不同的记忆"
        )
        
        # 验证相似度
        self.assertTrue(similarity < 0.5)  # 应该不相似
    
    def test_calculate_vector_similarity(self):
        """测试向量相似度计算"""
        # 生成向量
        vectors1 = generate_memory_vectors(self.memory)
        
        # 创建相似记忆
        similar_memory = Memory(
            content="这也是一条测试记忆",
            memory_type=MemoryType.SHORT_TERM
        )
        vectors2 = generate_memory_vectors(similar_memory)
        
        # 计算相似度
        similarity = calculate_vector_similarity(vectors1, vectors2)
        
        # 验证相似度范围
        self.assertTrue(0 <= similarity <= 1)
        self.assertTrue(similarity > 0.5)  # 应该相似
    
    def test_calculate_relation_similarity(self):
        """测试关系相似度计算"""
        # 创建相似关系
        relations1 = [
            MemoryRelation(
                relation_type="test",
                target_id="test_1",
                strength=5
            ),
            MemoryRelation(
                relation_type="test",
                target_id="test_2",
                strength=3
            )
        ]
        
        relations2 = [
            MemoryRelation(
                relation_type="test",
                target_id="test_1",
                strength=4
            ),
            MemoryRelation(
                relation_type="test",
                target_id="test_3",
                strength=2
            )
        ]
        
        # 计算相似度
        similarity = calculate_relation_similarity(relations1, relations2)
        
        # 验证相似度范围
        self.assertTrue(0 <= similarity <= 1)
        self.assertEqual(similarity, 1/3)  # 一个共同关系
    
    def test_calculate_time_similarity(self):
        """测试时间相似度计算"""
        # 计算相近时间
        now = datetime.utcnow()
        time1 = now
        time2 = now + timedelta(hours=1)
        
        similarity = calculate_time_similarity(time1, time2)
        
        # 验证相似度范围
        self.assertTrue(0 <= similarity <= 1)
        self.assertTrue(similarity > 0.5)  # 应该相似
        
        # 计算远离时间
        time3 = now + timedelta(days=7)
        similarity = calculate_time_similarity(time1, time3)
        
        # 验证相似度
        self.assertTrue(similarity < 0.5)  # 应该不相似
    
    def test_merge_memories(self):
        """测试记忆合并"""
        # 创建相似记忆
        memories = [
            preprocess_memory(Memory(
                content=f"这是测试记忆{i}",
                memory_type=MemoryType.SHORT_TERM,
                importance=5,
                relations=[
                    MemoryRelation(
                        relation_type="test",
                        target_id=f"test_{i}",
                        strength=5
                    )
                ]
            ))
            for i in range(3)
        ]
        
        # 合并记忆
        merged = merge_memories(memories, threshold=0.3)
        
        # 验证合并结果
        self.assertTrue(len(merged) <= len(memories))
        
        # 验证合并记忆的属性
        for memory in merged:
            self.assertIsNotNone(memory.id)
            self.assertIsNotNone(memory.content)
            self.assertIsNotNone(memory.vectors)
            self.assertTrue(len(memory.relations) > 0)
    
    def test_merge_memory_group(self):
        """测试记忆组合并"""
        # 创建记忆组
        memories = [
            preprocess_memory(Memory(
                content=f"这是测试记忆{i}",
                memory_type=MemoryType.SHORT_TERM,
                importance=5,
                relations=[
                    MemoryRelation(
                        relation_type="test",
                        target_id=f"test_{i}",
                        strength=5
                    )
                ]
            ))
            for i in range(2)
        ]
        
        # 合并记忆组
        merged = merge_memory_group(memories)
        
        # 验证合并结果
        self.assertIsNotNone(merged)
        self.assertTrue("\n" in merged.content)
        self.assertTrue(len(merged.relations) >= len(memories[0].relations))
        self.assertEqual(
            merged.importance,
            max(m.importance for m in memories)
        )
        self.assertEqual(
            merged.access_count,
            sum(m.access_count for m in memories)
        )

if __name__ == "__main__":
    unittest.main() 