"""
Agent Memory System Tests Module

This module contains all test cases for the system,
including unit tests, integration tests, and performance tests.
"""

__version__ = "0.1.0"

import pytest
from pathlib import Path

# Set up test constants
TEST_DIR = Path(__file__).parent
TEST_DATA_DIR = TEST_DIR / "test_data"
TEST_CONFIG_PATH = TEST_DIR / "test_config.yaml"

# Ensure test directories exist
TEST_DATA_DIR.mkdir(exist_ok=True)

__all__ = [
    "TEST_DIR",
    "TEST_DATA_DIR",
    "TEST_CONFIG_PATH"
]
