"""Pytest configuration and fixtures.

Common fixtures used across all tests.
"""

from pathlib import Path

import pytest


@pytest.fixture
def sample_log_content() -> str:
    """Sample log content for testing."""
    return """\
2025-11-27T14:30:22Z [INFO] Starting installation
2025-11-27T14:30:23Z [ERROR] Package tmux already installed
2025-11-27T14:30:24Z [INFO] Continuing...
2025-11-27T14:30:25Z [WARNING] Deprecated flag used
2025-11-27T14:30:26Z [INFO] Installation complete"""


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


@pytest.fixture(autouse=True)
def isolate_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Automatically isolate all tests to use a temporary cache directory.

    This prevents tests from polluting the user's real cache directory
    at ~/.cache/logsift/. Every test gets its own isolated cache.
    """
    test_cache = tmp_path / 'logsift_test_cache'
    test_cache.mkdir(parents=True, exist_ok=True)

    # Override the cache directory via environment variable
    monkeypatch.setenv('HOME', str(tmp_path))

    # Also patch the default cache location
    from logsift.cache.manager import CacheManager

    original_init = CacheManager.__init__

    def patched_init(self, cache_dir=None):
        if cache_dir is None:
            cache_dir = test_cache
        original_init(self, cache_dir=cache_dir)

    monkeypatch.setattr(CacheManager, '__init__', patched_init)

    return test_cache
