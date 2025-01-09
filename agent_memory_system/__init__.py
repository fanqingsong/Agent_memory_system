"""Agent Memory System

一个基于双轨记忆机制的智能Agent记忆管理系统。

主要功能：
    - 记忆的存储和检索
    - 记忆的关联和演化
    - 记忆的遗忘和强化
    - 记忆的情感标注

作者：Cursor_for_YansongW
创建日期：2024-01-15
"""

__version__ = "0.1.0"

from agent_memory_system.core.memory.memory_manager import MemoryManager
from agent_memory_system.core.memory.memory_retrieval import MemoryRetrieval
from agent_memory_system.models.memory_model import Memory, MemoryType, MemoryQuery
from agent_memory_system.api.api import app

__all__ = [
    "MemoryManager",
    "MemoryRetrieval",
    "Memory",
    "MemoryType",
    "MemoryQuery",
    "app"
]
