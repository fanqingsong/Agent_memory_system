"""
Agent Memory System Core Memory Module

This module provides the core memory management functionality,
including memory storage, retrieval, and type definitions.
"""

__version__ = "0.1.0"

from .memory_manager import MemoryManager
from .memory_retrieval import MemoryRetrieval
from .memory_types import (
    Memory,
    EpisodicMemory,
    SemanticMemory,
    ProceduralMemory,
    MemoryType,
    EmotionType
)
from .memory_utils import (
    calculate_memory_importance,
    generate_memory_embedding,
    validate_memory_data,
    create_memory_context
)

__all__ = [
    "MemoryManager",
    "MemoryRetrieval",
    "Memory",
    "EpisodicMemory",
    "SemanticMemory",
    "ProceduralMemory",
    "MemoryType",
    "EmotionType",
    "calculate_memory_importance",
    "generate_memory_embedding",
    "validate_memory_data",
    "create_memory_context"
]
