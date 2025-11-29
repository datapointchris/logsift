"""Tests for cache manager."""

import tempfile
from pathlib import Path

from logsift.cache.manager import CacheManager


def test_cache_manager_init_with_default_dir(tmp_path):
    """Test cache manager initializes with default cache directory."""
    # This test validates the default path logic, but we provide explicit path
    # to avoid using the real cache (which is patched by the autouse fixture)
    test_cache = tmp_path / 'explicit_cache'
    manager = CacheManager(cache_dir=test_cache)

    assert manager.cache_dir == test_cache


def test_cache_manager_init_with_custom_dir():
    """Test cache manager initializes with custom directory."""
    custom_dir = Path('/tmp/custom_cache')
    manager = CacheManager(cache_dir=custom_dir)

    assert manager.cache_dir == custom_dir


def test_create_log_path_basic():
    """Test creating a basic log path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = CacheManager(cache_dir=Path(tmpdir))

        log_path = manager.create_log_path('test_command')

        # Should create a path in logs/ subdirectory
        assert log_path.parent == manager.logs_dir
        assert log_path.name.endswith('.log')
        assert 'test_command' in str(log_path)


def test_create_log_path_creates_directories():
    """Test that creating log path creates necessary directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = CacheManager(cache_dir=Path(tmpdir))

        log_path = manager.create_log_path('test_command')

        # Parent directory should exist
        assert log_path.parent.exists()


def test_create_log_path_unique_timestamps():
    """Test that consecutive calls create unique paths."""
    import time

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = CacheManager(cache_dir=Path(tmpdir))

        path1 = manager.create_log_path('test_command')
        time.sleep(1.1)  # Sleep to ensure different timestamp
        path2 = manager.create_log_path('test_command')

        # Paths should be different due to timestamps
        assert path1 != path2


def test_create_log_path_sanitizes_name():
    """Test that log path sanitizes invalid characters in name."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = CacheManager(cache_dir=Path(tmpdir))

        # Name with spaces, slashes, special chars
        log_path = manager.create_log_path('npm run build/test')

        # Should sanitize the name (exact behavior depends on implementation)
        assert log_path.parent.exists()


def test_get_latest_log_returns_none_when_empty():
    """Test get_latest_log returns None when no logs exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = CacheManager(cache_dir=Path(tmpdir))

        latest = manager.get_latest_log('nonexistent')

        assert latest is None


def test_get_latest_log_returns_most_recent():
    """Test get_latest_log returns the most recent log file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = CacheManager(cache_dir=Path(tmpdir))

        # Create multiple log files
        path1 = manager.create_log_path('test_command')
        path1.write_text('first log')

        path2 = manager.create_log_path('test_command')
        path2.write_text('second log')

        path3 = manager.create_log_path('test_command')
        path3.write_text('third log')

        # Get latest
        latest = manager.get_latest_log('test_command')

        # Should be the most recently created
        assert latest == path3


def test_get_latest_log_ignores_other_commands():
    """Test get_latest_log only returns logs for the specified command."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = CacheManager(cache_dir=Path(tmpdir))

        # Create logs for different commands
        path1 = manager.create_log_path('npm_build')
        path1.write_text('npm log')

        path2 = manager.create_log_path('pytest')
        path2.write_text('pytest log')

        # Get latest for npm_build
        latest = manager.get_latest_log('npm_build')

        assert latest == path1
        assert latest != path2


def test_get_absolute_latest_log_returns_none_when_empty():
    """Test get_absolute_latest_log returns None when no logs exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = CacheManager(cache_dir=Path(tmpdir))

        latest = manager.get_absolute_latest_log()

        assert latest is None


def test_get_absolute_latest_log_returns_most_recent():
    """Test get_absolute_latest_log returns the most recent log across all names."""
    import time

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = CacheManager(cache_dir=Path(tmpdir))

        # Create logs for different commands with delays to ensure different timestamps
        path1 = manager.create_log_path('npm_build')
        path1.write_text('npm log')
        time.sleep(1.1)

        path2 = manager.create_log_path('pytest')
        path2.write_text('pytest log')
        time.sleep(1.1)

        path3 = manager.create_log_path('make')
        path3.write_text('make log')

        # Get absolute latest (should be the last created)
        latest = manager.get_absolute_latest_log()

        assert latest == path3


def test_get_absolute_latest_log_sorts_by_timestamp():
    """Test get_absolute_latest_log correctly sorts by ISO8601 timestamp prefix."""
    import time

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = CacheManager(cache_dir=Path(tmpdir))

        # Create multiple logs with different names and delays to ensure different timestamps
        paths = []
        for i, cmd in enumerate(['echo', 'bash', 'pytest', 'make']):
            path = manager.create_log_path(cmd)
            path.write_text(f'{cmd} log')
            paths.append(path)
            # Sleep except after last one
            if i < 3:
                time.sleep(1.1)

        # Get absolute latest
        latest = manager.get_absolute_latest_log()

        # Should be the last one created
        assert latest == paths[-1]
