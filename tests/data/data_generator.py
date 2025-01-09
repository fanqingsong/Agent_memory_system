"""测试数据生成器模块

实现测试数据的生成功能。

主要功能：
    - 常规记忆生成
    - 技能记忆生成
    - 记忆关系生成
    - 数据初始化
    - 数据清理

依赖：
    - numpy: 数值计算
    - datetime: 时间处理
    - random: 随机数生成
    - typing: 类型注解
    - logger: 日志记录

作者：Cursor_for_YansongW
创建日期：2024-01-09
"""

import random
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np

from agent_memory_system.models.memory_model import (
    Memory,
    MemoryRelation,
    MemoryStatus,
    MemoryType
)
from agent_memory_system.utils.logger import log

class MemoryDataGenerator:
    """记忆数据生成器
    
    功能描述：
        生成测试用的记忆数据，包括：
        1. 常规记忆
        2. 技能记忆
        3. 记忆关系
    
    属性说明：
        - embedding_dim: 向量维度
        - content_templates: 内容模板
    """
    
    def __init__(self, embedding_dim: int = 768) -> None:
        """初始化生成器
        
        Args:
            embedding_dim: 向量维度
        """
        self.embedding_dim = embedding_dim
        self.content_templates = {
            'regular': [
                "这是一个关于{topic}的记忆，发生在{time}，涉及到{entity}。",
                "在{time}，{entity}进行了{action}，给人留下了深刻印象。",
                "{entity}在{time}展示了{attribute}的特点，这让我想到了{topic}。",
                "关于{topic}的一个观察：{entity}在{time}表现出了{attribute}。",
                "记录一下{time}发生的事：{entity}在{topic}方面表现出{attribute}。"
            ],
            'skill': [
                "掌握了一个关于{domain}的技能：{skill_name}",
                "学会了如何在{domain}中使用{skill_name}来解决问题",
                "{domain}领域的{skill_name}技能已经掌握",
                "通过实践掌握了{domain}中的{skill_name}技能",
                "成功学习了{domain}相关的{skill_name}技能"
            ]
        }
    
    def generate_regular_memory(
        self,
        count: int,
        min_importance: int = 1,
        max_importance: int = 10
    ) -> List[Memory]:
        """生成常规记忆
        
        Args:
            count: 生成数量
            min_importance: 最小重要性
            max_importance: 最大重要性
        
        Returns:
            List[Memory]: 记忆列表
        """
        memories = []
        topics = ["技术", "生活", "工作", "学习", "娱乐"]
        entities = ["用户", "系统", "项目", "团队", "客户"]
        actions = ["开发", "测试", "部署", "维护", "优化"]
        attributes = ["高效", "创新", "稳定", "灵活", "可靠"]
        
        for i in range(count):
            # 生成内容
            template = random.choice(self.content_templates['regular'])
            content = template.format(
                topic=random.choice(topics),
                time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                entity=random.choice(entities),
                action=random.choice(actions),
                attribute=random.choice(attributes)
            )
            
            # 创建记忆
            memory = Memory(
                content=content,
                memory_type=MemoryType.REGULAR,
                importance=random.randint(min_importance, max_importance),
                embedding=np.random.rand(self.embedding_dim),
                status=MemoryStatus.ACTIVE,
                created_at=datetime.now(),
                accessed_at=datetime.now(),
                updated_at=datetime.now(),
                access_count=random.randint(0, 100)
            )
            memories.append(memory)
        
        return memories
    
    def generate_skill_memory(
        self,
        count: int,
        min_importance: int = 1,
        max_importance: int = 10
    ) -> List[Memory]:
        """生成技能记忆
        
        Args:
            count: 生成数量
            min_importance: 最小重要性
            max_importance: 最大重要性
        
        Returns:
            List[Memory]: 记忆列表
        """
        memories = []
        domains = ["编程", "设计", "测试", "运维", "管理"]
        skills = ["Python开发", "UI设计", "自动化测试", "系统部署", "项目管理"]
        
        for i in range(count):
            # 生成内容
            template = random.choice(self.content_templates['skill'])
            content = template.format(
                domain=random.choice(domains),
                skill_name=random.choice(skills)
            )
            
            # 创建记忆
            memory = Memory(
                content=content,
                memory_type=MemoryType.SKILL,
                importance=random.randint(min_importance, max_importance),
                embedding=np.random.rand(self.embedding_dim),
                status=MemoryStatus.ACTIVE,
                created_at=datetime.now(),
                accessed_at=datetime.now(),
                updated_at=datetime.now(),
                access_count=random.randint(0, 100)
            )
            memories.append(memory)
        
        return memories

class RelationGenerator:
    """关系生成器
    
    功能描述：
        生成记忆之间的关系，包括：
        1. 相似关系
        2. 依赖关系
        3. 引用关系
    
    属性说明：
        - relation_types: 关系类型
        - relation_weights: 关系权重
    """
    
    def __init__(self) -> None:
        """初始化生成器"""
        self.relation_types = ["SIMILAR", "DEPENDS", "REFERENCES"]
        self.relation_weights = {
            "SIMILAR": (0.7, 1.0),
            "DEPENDS": (0.6, 0.9),
            "REFERENCES": (0.5, 0.8)
        }
    
    def generate_relations(
        self,
        memories: List[Memory],
        density: float = 0.3
    ) -> List[MemoryRelation]:
        """生成记忆关系
        
        Args:
            memories: 记忆列表
            density: 关系密度(0-1)
        
        Returns:
            List[MemoryRelation]: 关系列表
        """
        relations = []
        memory_count = len(memories)
        
        # 计算关系数量
        total_relations = int(memory_count * memory_count * density)
        
        # 生成关系
        for _ in range(total_relations):
            # 随机选择两个不同的记忆
            source_idx = random.randint(0, memory_count - 1)
            target_idx = random.randint(0, memory_count - 1)
            while target_idx == source_idx:
                target_idx = random.randint(0, memory_count - 1)
            
            # 随机选择关系类型
            relation_type = random.choice(self.relation_types)
            
            # 生成关系权重
            min_weight, max_weight = self.relation_weights[relation_type]
            weight = random.uniform(min_weight, max_weight)
            
            # 创建关系
            relation = MemoryRelation(
                source_id=memories[source_idx].id,
                target_id=memories[target_idx].id,
                relation_type=relation_type,
                weight=weight,
                created_at=datetime.now()
            )
            relations.append(relation)
        
        return relations

class TestDataInitializer:
    """测试数据初始化器
    
    功能描述：
        初始化测试数据，包括：
        1. 生成记忆数据
        2. 生成关系数据
        3. 数据清理
    
    属性说明：
        - memory_generator: 记忆生成器
        - relation_generator: 关系生成器
    """
    
    def __init__(self) -> None:
        """初始化"""
        self.memory_generator = MemoryDataGenerator()
        self.relation_generator = RelationGenerator()
    
    def initialize_test_data(
        self,
        regular_count: int = 100,
        skill_count: int = 20,
        relation_density: float = 0.3
    ) -> Tuple[List[Memory], List[Memory], List[MemoryRelation]]:
        """初始化测试数据
        
        Args:
            regular_count: 常规记忆数量
            skill_count: 技能记忆数量
            relation_density: 关系密度
        
        Returns:
            Tuple[List[Memory], List[Memory], List[MemoryRelation]]:
                常规记忆列表, 技能记忆列表, 关系列表
        """
        try:
            # 生成记忆数据
            regular_memories = self.memory_generator.generate_regular_memory(
                regular_count
            )
            skill_memories = self.memory_generator.generate_skill_memory(
                skill_count
            )
            
            # 生成关系数据
            all_memories = regular_memories + skill_memories
            relations = self.relation_generator.generate_relations(
                all_memories,
                relation_density
            )
            
            return regular_memories, skill_memories, relations
            
        except Exception as e:
            log.error(f"测试数据初始化失败: {str(e)}")
            raise 