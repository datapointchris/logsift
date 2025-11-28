"""Pytest configuration and fixtures.

Common fixtures used across all tests.
"""

from pathlib import Path

import pytest


@pytest.fixture
def sample_log_content() -> str:
    """Sample log content for testing."""
    return """
2025-11-27T14:30:22Z [INFO] Starting installation
2025-11-27T14:30:23Z [ERROR] Package tmux already installed
2025-11-27T14:30:24Z [INFO] Continuing...
2025-11-27T14:30:25Z [WARNING] Deprecated flag used
2025-11-27T14:30:26Z [INFO] Installation complete
    """.strip()


@pytest.fixture
def sample_log_file(tmp_path: Path, sample_log_content: str) -> Path:
    """Create a temporary log file for testing."""
    log_file = tmp_path / 'test.log'
    log_file.write_text(sample_log_content)
    return log_file


@pytest.fixture
def cache_dir(tmp_path: Path) -> Path:
    """Create a temporary cache directory for testing."""
    cache = tmp_path / 'cache'
    cache.mkdir()
    return cache
