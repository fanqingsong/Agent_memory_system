"""
Agent Memory System API Module

This module provides the API interface for the Agent Memory System,
including REST endpoints and WebSocket communication.
"""

__version__ = "0.1.0"

from .api import app, get_app_instance
from .chat import ConnectionManager, ChatMessage, websocket_endpoint
from .routes import app as api_app
from .memory_api import (
    create_memory,
    get_memory,
    update_memory,
    delete_memory
)

__all__ = [
    "app",
    "get_app_instance",
    "ConnectionManager",
    "ChatMessage",
    "websocket_endpoint",
    "api_app",
    "create_memory",
    "get_memory",
    "update_memory",
    "delete_memory"
]
