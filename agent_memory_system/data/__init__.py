"""
Agent Memory System Data Module

This module handles data management and persistence,
including data loading, saving, and preprocessing functionality.
"""

__version__ = "0.1.0"

from pathlib import Path

# Set up data directories
DATA_DIR = Path(__file__).parent
CACHE_DIR = DATA_DIR / "cache"
VECTOR_DIR = DATA_DIR / "vectors"
MODEL_DIR = DATA_DIR / "models"

# Ensure directories exist
CACHE_DIR.mkdir(exist_ok=True)
VECTOR_DIR.mkdir(exist_ok=True)
MODEL_DIR.mkdir(exist_ok=True)

__all__ = [
    "DATA_DIR",
    "CACHE_DIR",
    "VECTOR_DIR",
    "MODEL_DIR"
] 