"""
Legal Spend MCP Server Test Suite

This package contains comprehensive tests for the Legal Spend MCP Server,
including unit tests, integration tests, and fixtures.
"""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path for testing
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Test configuration
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")
TEST_API_KEY = os.getenv("TEST_API_KEY", "test_api_key")

# Disable logging during tests unless explicitly enabled
import logging
if not os.getenv("ENABLE_TEST_LOGGING"):
    logging.disable(logging.CRITICAL)