"""Pytest configuration for integration tests.

These tests require actual Google Sheets credentials and network access.
They are separated from unit tests to allow fast test runs during development.
"""

import os
import sys
import pytest

# Add backend directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires credentials/network)"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
