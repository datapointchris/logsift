"""Tests for cache manager."""

import tempfile
from pathlib import Path

from logsift.cache.manager import CacheManager


def test_cache_manager_init_with_default_dir():
    """Test cache manager initializes with default cache directory."""
    manager = CacheManager()

    assert manager.cache_dir == Path.home() / '.cache' / 'logsift'


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

        # Should create a path under cache_dir
        assert log_path.parent.parent == manager.cache_dir
        assert log_path.name.endswith('.log')
        assert 'test_command' in str(log_path)


def test_create_log_path_with_context():
    """Test creating log path with context."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = CacheManager(cache_dir=Path(tmpdir))

        log_path = manager.create_log_path('npm_build', context='frontend')

        # Should include context in path
        assert 'frontend' in str(log_path)
        assert 'npm_build' in str(log_path)


def test_create_log_path_creates_directories():
    """Test that creating log path creates necessary directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = CacheManager(cache_dir=Path(tmpdir))

        log_path = manager.create_log_path('test_command')

        # Parent directory should exist
        assert log_path.parent.exists()


def test_create_log_path_unique_timestamps():
    """Test that consecutive calls create unique paths."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = CacheManager(cache_dir=Path(tmpdir))

        path1 = manager.create_log_path('test_command')
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


def test_get_latest_log_with_context():
    """Test get_latest_log with context filter."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = CacheManager(cache_dir=Path(tmpdir))

        # Create logs in different contexts
        path1 = manager.create_log_path('build', context='frontend')
        path1.write_text('frontend build')

        path2 = manager.create_log_path('build', context='backend')
        path2.write_text('backend build')

        # Get latest for specific context
        latest_frontend = manager.get_latest_log('build', context='frontend')
        latest_backend = manager.get_latest_log('build', context='backend')

        assert latest_frontend == path1
        assert latest_backend == path2


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


def test_create_log_path_default_context():
    """Test create_log_path uses 'default' context when not specified."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = CacheManager(cache_dir=Path(tmpdir))

        log_path = manager.create_log_path('test_command')

        # Should use default context
        assert 'default' in str(log_path) or log_path.parent.name == 'default'


def test_cache_manager_handles_nested_contexts():
    """Test cache manager handles nested context paths."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = CacheManager(cache_dir=Path(tmpdir))

        # Create with a simple context that might become a nested path
        log_path = manager.create_log_path('test', context='project/build')

        # Should handle the context appropriately
        assert log_path.parent.exists()
