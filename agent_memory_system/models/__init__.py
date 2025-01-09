"""
Agent Memory System Models Module

This module provides the data models and schemas used throughout the system,
including memory models, API models, and configuration models.
"""

__version__ = "0.1.0"

from .memory_model import (
    Memory,
    MemoryType,
    MemoryStatus,
    MemoryRelationType,
    ModelVersion
)
from .api_models import (
    APIResponse,
    CreateMemoryRequest,
    UpdateMemoryRequest,
    SearchMemoryRequest,
    MemoryResponse
)
from .config_model import (
    SystemConfig,
    StorageConfig,
    APIConfig,
    LoggingConfig
)

__all__ = [
    # Memory models
    "Memory",
    "MemoryType",
    "MemoryStatus",
    "MemoryRelationType",
    "ModelVersion",
    
    # API models
    "APIResponse",
    "CreateMemoryRequest",
    "UpdateMemoryRequest",
    "SearchMemoryRequest",
    "MemoryResponse",
    
    # Config models
    "SystemConfig",
    "StorageConfig",
    "APIConfig",
    "LoggingConfig"
]
