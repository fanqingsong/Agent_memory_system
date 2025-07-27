"""
Agent Memory System Utils Module

This module provides utility functions and helper classes used throughout the system,
including configuration management, logging, and common utilities.
"""

__version__ = "0.1.0"

from .config import (
    init_config
)
from .logger import (
    setup_logging,
    get_logger,
    init_logger,
    log,
    LogLevel
)
from .openai_client import LLMClient
# from .encryption import (
#     encrypt_data,
#     decrypt_data,
#     generate_key
# )

__all__ = [
    # Config utilities
    "init_config",
    
    # Logging utilities
    "setup_logging",
    "get_logger",
    "init_logger",
    "log",
    "LogLevel",
    
    # LLM client
    "LLMClient",
    
    # Encryption utilities
    # "encrypt_data",
    # "decrypt_data",
    # "generate_key"
]
