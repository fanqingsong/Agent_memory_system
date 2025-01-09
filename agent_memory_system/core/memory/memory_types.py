"""记忆类型处理模块

定义和处理不同类型记忆的特性和行为。

主要功能：
    - 记忆类型的特性定义
    - 记忆类型的处理策略
    - 记忆类型的转换规则
    - 记忆类型的优化方法

依赖：
    - memory_model: 记忆数据模型
    - config: 配置管理
    - logger: 日志记录

作者：Cursor_for_YansongW
创建日期：2025-01-09
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Union

from agent_memory_system.models.memory_model import (
    Memory,
    MemoryStatus,
    MemoryType
)
from agent_memory_system.utils.config import config
from agent_memory_system.utils.logger import log

class MemoryTypeHandler(ABC):
    """记忆类型处理器基类
    
    功能描述：
        定义记忆类型处理器的基本接口，包括：
        1. 记忆的生命周期管理
        2. 记忆的重要性评估
        3. 记忆的关系处理
        4. 记忆的优化策略
    
    属性说明：
        - memory_type: 处理的记忆类型
        - config: 配置管理器实例
    """
    
    def __init__(self, memory_type: MemoryType) -> None:
        """初始化处理器
        
        Args:
            memory_type: 处理的记忆类型
        """
        self.memory_type = memory_type
        self.config = config
    
    @abstractmethod
    def should_store(self, memory: Memory) -> bool:
        """判断记忆是否应该存储
        
        Args:
            memory: 记忆对象
        
        Returns:
            bool: 是否应该存储
        """
        pass
    
    @abstractmethod
    def calculate_importance(self, memory: Memory) -> int:
        """计算记忆的重要性
        
        Args:
            memory: 记忆对象
        
        Returns:
            int: 重要性评分(1-10)
        """
        pass
    
    @abstractmethod
    def should_forget(self, memory: Memory) -> bool:
        """判断记忆是否应该遗忘
        
        Args:
            memory: 记忆对象
        
        Returns:
            bool: 是否应该遗忘
        """
        pass
    
    @abstractmethod
    def optimize(self, memory: Memory) -> Memory:
        """优化记忆
        
        Args:
            memory: 记忆对象
        
        Returns:
            Memory: 优化后的记忆对象
        """
        pass

class ShortTermMemoryHandler(MemoryTypeHandler):
    """短期记忆处理器
    
    功能描述：
        处理短期记忆的特性，包括：
        1. 较短的保留时间
        2. 较低的重要性阈值
        3. 频繁的更新和清理
        4. 简单的关系处理
    """
    
    def __init__(self) -> None:
        """初始化短期记忆处理器"""
        super().__init__(MemoryType.SHORT_TERM)
    
    def should_store(self, memory: Memory) -> bool:
        """判断短期记忆是否应该存储
        
        短期记忆的存储条件：
        1. 内容长度适中
        2. 重要性不太高
        3. 近期没有类似记忆
        """
        # 检查内容长度
        if len(memory.content) > 1000:
            return False
        
        # 检查重要性
        if memory.importance > 7:
            return False  # 重要性过高应该存为长期记忆
        
        return True
    
    def calculate_importance(self, memory: Memory) -> int:
        """计算短期记忆的重要性
        
        短期记忆的重要性评分依据：
        1. 基础重要性(1-5)
        2. 访问频率影响(0-2)
        3. 关系数量影响(0-2)
        4. 时间衰减(-2-0)
        """
        importance = memory.importance
        
        # 访问频率影响
        access_bonus = min(memory.access_count / 5, 2)
        importance += access_bonus
        
        # 关系数量影响
        relation_bonus = min(len(memory.relations) / 3, 2)
        importance += relation_bonus
        
        # 时间衰减
        age = datetime.utcnow() - memory.created_at
        decay = min(age.total_seconds() / 3600, 2)  # 每小时衰减1分，最多衰减2分
        importance -= decay
        
        return max(1, min(10, round(importance)))
    
    def should_forget(self, memory: Memory) -> bool:
        """判断短期记忆是否应该遗忘
        
        短期记忆的遗忘条件：
        1. 存在时间超过阈值
        2. 重要性低于阈值
        3. 长期未访问
        4. 无重要关系
        """
        now = datetime.utcnow()
        
        # 检查存在时间
        age = now - memory.created_at
        if age > timedelta(hours=24):  # 短期记忆默认保留24小时
            return True
        
        # 检查重要性
        if memory.importance < 3:  # 短期记忆重要性阈值
            return True
        
        # 检查访问时间
        if now - memory.accessed_at > timedelta(hours=12):  # 12小时未访问
            return True
        
        # 检查关系
        if not memory.relations:  # 无关系的记忆更容易遗忘
            return True
        
        return False
    
    def optimize(self, memory: Memory) -> Memory:
        """优化短期记忆
        
        短期记忆的优化策略：
        1. 合并相似记忆
        2. 提取关键信息
        3. 更新重要性
        4. 考虑转换为长期记忆
        """
        # 更新重要性
        memory.importance = self.calculate_importance(memory)
        
        # 考虑转换为长期记忆
        if memory.importance >= 7:
            memory.memory_type = MemoryType.LONG_TERM
            log.info(f"记忆{memory.id}转换为长期记忆")
        
        return memory

class LongTermMemoryHandler(MemoryTypeHandler):
    """长期记忆处理器
    
    功能描述：
        处理长期记忆的特性，包括：
        1. 较长的保留时间
        2. 较高的重要性阈值
        3. 复杂的关系网络
        4. 定期的巩固和优化
    """
    
    def __init__(self) -> None:
        """初始化长期记忆处理器"""
        super().__init__(MemoryType.LONG_TERM)
    
    def should_store(self, memory: Memory) -> bool:
        """判断长期记忆是否应该存储
        
        长期记忆的存储条件：
        1. 重要性达到阈值
        2. 具有复杂的关系
        3. 内容完整且有价值
        """
        # 检查重要性
        if memory.importance < 7:
            return False
        
        # 检查关系
        if len(memory.relations) < 2:
            return False
        
        # 检查内容
        if len(memory.content) < 50:  # 长期记忆应该包含足够的信息
            return False
        
        return True
    
    def calculate_importance(self, memory: Memory) -> int:
        """计算长期记忆的重要性
        
        长期记忆的重要性评分依据：
        1. 基础重要性(5-10)
        2. 关系网络影响(0-3)
        3. 访问价值(0-2)
        4. 时间价值(-1-0)
        """
        importance = memory.importance
        
        # 关系网络影响
        relation_bonus = min(len(memory.relations) / 2, 3)
        importance += relation_bonus
        
        # 访问价值
        access_value = min(memory.access_count / 10, 2)
        importance += access_value
        
        # 时间价值
        age = datetime.utcnow() - memory.created_at
        time_decay = min(age.total_seconds() / (30 * 24 * 3600), 1)  # 每30天衰减1分
        importance -= time_decay
        
        return max(5, min(10, round(importance)))
    
    def should_forget(self, memory: Memory) -> bool:
        """判断长期记忆是否应该遗忘
        
        长期记忆的遗忘条件：
        1. 重要性显著降低
        2. 极长时间未访问
        3. 关系网络弱化
        4. 内容过时或无效
        """
        now = datetime.utcnow()
        
        # 检查重要性
        if memory.importance < 5:  # 长期记忆重要性最低阈值
            return True
        
        # 检查访问时间
        if now - memory.accessed_at > timedelta(days=90):  # 90天未访问
            return True
        
        # 检查关系网络
        if len(memory.relations) < 2:  # 关系网络弱化
            return True
        
        return False
    
    def optimize(self, memory: Memory) -> Memory:
        """优化长期记忆
        
        长期记忆的优化策略：
        1. 强化重要关系
        2. 整合相关信息
        3. 更新重要性
        4. 定期巩固
        """
        # 更新重要性
        memory.importance = self.calculate_importance(memory)
        
        # 如果重要性降低，考虑转换为短期记忆
        if memory.importance < 5:
            memory.memory_type = MemoryType.SHORT_TERM
            log.info(f"记忆{memory.id}转换为短期记忆")
        
        return memory

class WorkingMemoryHandler(MemoryTypeHandler):
    """工作记忆处理器
    
    功能描述：
        处理工作记忆的特性，包括：
        1. 非常短的保留时间
        2. 高频的访问和更新
        3. 临时的关系网络
        4. 快速的清理机制
    """
    
    def __init__(self) -> None:
        """初始化工作记忆处理器"""
        super().__init__(MemoryType.WORKING)
    
    def should_store(self, memory: Memory) -> bool:
        """判断工作记忆是否应该存储
        
        工作记忆的存储条件：
        1. 当前任务相关
        2. 临时重要性高
        3. 内容简洁
        """
        # 检查内容长度
        if len(memory.content) > 500:  # 工作记忆应该简洁
            return False
        
        # 检查关系
        if len(memory.relations) > 5:  # 工作记忆关系不应太复杂
            return False
        
        return True
    
    def calculate_importance(self, memory: Memory) -> int:
        """计算工作记忆的重要性
        
        工作记忆的重要性评分依据：
        1. 当前相关性(1-5)
        2. 访问频率(0-3)
        3. 时间衰减(-3-0)
        """
        importance = memory.importance
        
        # 访问频率
        access_bonus = min(memory.access_count, 3)
        importance += access_bonus
        
        # 时间衰减（工作记忆衰减很快）
        age = datetime.utcnow() - memory.created_at
        decay = min(age.total_seconds() / 300, 3)  # 每5分钟衰减1分
        importance -= decay
        
        return max(1, min(10, round(importance)))
    
    def should_forget(self, memory: Memory) -> bool:
        """判断工作记忆是否应该遗忘
        
        工作记忆的遗忘条件：
        1. 存在时间超过阈值
        2. 重要性降低
        3. 短时间未访问
        """
        now = datetime.utcnow()
        
        # 检查存在时间
        age = now - memory.created_at
        if age > timedelta(hours=1):  # 工作记忆默认保留1小时
            return True
        
        # 检查重要性
        if memory.importance < 2:
            return True
        
        # 检查访问时间
        if now - memory.accessed_at > timedelta(minutes=30):  # 30分钟未访问
            return True
        
        return False
    
    def optimize(self, memory: Memory) -> Memory:
        """优化工作记忆
        
        工作记忆的优化策略：
        1. 保持内容简洁
        2. 更新重要性
        3. 及时清理
        4. 必要时转换类型
        """
        # 更新重要性
        memory.importance = self.calculate_importance(memory)
        
        # 根据重要性决定是否转换类型
        if memory.importance >= 7:
            memory.memory_type = MemoryType.LONG_TERM
            log.info(f"记忆{memory.id}转换为长期记忆")
        elif memory.importance >= 4:
            memory.memory_type = MemoryType.SHORT_TERM
            log.info(f"记忆{memory.id}转换为短期记忆")
        
        return memory

class SkillMemoryHandler(MemoryTypeHandler):
    """技能记忆处理器
    
    功能描述：
        处理技能记忆的特性，包括：
        1. 永久保留
        2. 高度结构化
        3. 复杂的依赖关系
        4. 渐进式优化
    """
    
    def __init__(self) -> None:
        """初始化技能记忆处理器"""
        super().__init__(MemoryType.SKILL)
    
    def should_store(self, memory: Memory) -> bool:
        """判断技能记忆是否应该存储
        
        技能记忆的存储条件：
        1. 包含明确的步骤或规则
        2. 具有可重复性
        3. 有清晰的目标
        """
        # 检查内容结构
        if len(memory.content) < 100:  # 技能记忆应该足够详细
            return False
        
        # 检查关系
        if len(memory.relations) < 3:  # 技能记忆应该有足够的关联
            return False
        
        return True
    
    def calculate_importance(self, memory: Memory) -> int:
        """计算技能记忆的重要性
        
        技能记忆的重要性评分依据：
        1. 使用频率(1-4)
        2. 依赖关系(0-3)
        3. 完整性(0-3)
        """
        importance = memory.importance
        
        # 使用频率
        usage_value = min(memory.access_count / 20, 4)
        importance += usage_value
        
        # 依赖关系
        dependency_value = min(len(memory.relations) / 2, 3)
        importance += dependency_value
        
        # 完整性（基于内容长度）
        completeness = min(len(memory.content) / 500, 3)
        importance += completeness
        
        return max(1, min(10, round(importance)))
    
    def should_forget(self, memory: Memory) -> bool:
        """判断技能记忆是否应该遗忘
        
        技能记忆的遗忘条件：
        1. 极长时间未使用
        2. 依赖关系全部失效
        3. 内容严重过时
        """
        now = datetime.utcnow()
        
        # 检查使用时间
        if now - memory.accessed_at > timedelta(days=365):  # 一年未使用
            return True
        
        # 检查重要性
        if memory.importance < 3:  # 技能记忆最低重要性
            return True
        
        return False
    
    def optimize(self, memory: Memory) -> Memory:
        """优化技能记忆
        
        技能记忆的优化策略：
        1. 提取核心步骤
        2. 更新依赖关系
        3. 合并相似技能
        4. 分解复杂技能
        """
        # 更新重要性
        memory.importance = self.calculate_importance(memory)
        
        # 技能记忆通常不会改变类型
        return memory

class MemoryTypeRegistry:
    """记忆类型注册表
    
    功能描述：
        管理所有记忆类型的处理器，提供统一的访问接口
    
    属性说明：
        - _handlers: 类型处理器字典
    """
    
    _instance = None
    
    def __new__(cls) -> "MemoryTypeRegistry":
        """实现单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        """初始化注册表"""
        if not hasattr(self, "_handlers"):
            self._handlers = {
                MemoryType.SHORT_TERM: ShortTermMemoryHandler(),
                MemoryType.LONG_TERM: LongTermMemoryHandler(),
                MemoryType.WORKING: WorkingMemoryHandler(),
                MemoryType.SKILL: SkillMemoryHandler()
            }
    
    def get_handler(
        self,
        memory_type: Union[MemoryType, str]
    ) -> MemoryTypeHandler:
        """获取指定类型的处理器
        
        Args:
            memory_type: 记忆类型
        
        Returns:
            MemoryTypeHandler: 类型处理器
        
        Raises:
            ValueError: 当类型无效时
        """
        if isinstance(memory_type, str):
            memory_type = MemoryType(memory_type)
        
        handler = self._handlers.get(memory_type)
        if not handler:
            raise ValueError(f"无效的记忆类型: {memory_type}")
        
        return handler

# 全局注册表实例
memory_type_registry = MemoryTypeRegistry()
