"""Tests for cache manager."""

import tempfile
import time
from pathlib import Path

import pytest

from logsift.cache.manager import CacheManager


def test_cache_manager_init():
    """Test cache manager initializes with custom directory."""
    custom_dir = Path('/tmp/custom_cache')
    manager = CacheManager(cache_dir=custom_dir)

    assert manager.cache_dir == custom_dir


def test_create_log_path_basic():
    """Test creating a basic log path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = CacheManager(cache_dir=Path(tmpdir))

        log_path = manager.create_log_path('test_command')

        # Should create a path in raw/ subdirectory
        assert log_path.parent == manager.raw_dir
        assert log_path.name.endswith('.log')
        assert 'test_command' in str(log_path)
        assert log_path.parent.exists()


def test_create_log_path_unique_timestamps():
    """Test that consecutive calls create unique paths."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = CacheManager(cache_dir=Path(tmpdir))

        path1 = manager.create_log_path('test_command')
        time.sleep(1.1)  # Sleep to ensure different timestamp
        path2 = manager.create_log_path('test_command')

        # Paths should be different due to timestamps
        assert path1 != path2


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


def test_get_absolute_latest_log_returns_most_recent():
    """Test get_absolute_latest_log returns the most recent log across all names."""
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


def test_create_paths_returns_all_formats():
    """Test create_paths returns paths for all 4 formats."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = CacheManager(cache_dir=Path(tmpdir))

        paths = manager.create_paths('test_command')

        # Should return dict with all 4 formats
        assert isinstance(paths, dict)
        assert set(paths.keys()) == {'raw', 'json', 'toon', 'md'}

        # All paths should have the same stem
        assert paths['raw'].stem == paths['json'].stem
        assert paths['raw'].stem == paths['toon'].stem
        assert paths['raw'].stem == paths['md'].stem

        # Correct extensions
        assert paths['raw'].suffix == '.log'
        assert paths['json'].suffix == '.json'
        assert paths['toon'].suffix == '.toon'
        assert paths['md'].suffix == '.md'


def test_list_all_in_format():
    """Test list_all_in_format lists files in a specific format directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = CacheManager(cache_dir=Path(tmpdir))

        # Create multiple log sessions
        paths1 = manager.create_paths('session1')
        paths2 = manager.create_paths('session2')

        # Create raw files
        paths1['raw'].write_text('session1 log')
        paths2['raw'].write_text('session2 log')

        # List raw files
        raw_files = manager.list_all_in_format('raw')
        assert len(raw_files) == 2
        assert all(f['name'].endswith('.log') for f in raw_files)


def test_list_all_in_format_invalid_format():
    """Test list_all_in_format raises error for invalid format."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = CacheManager(cache_dir=Path(tmpdir))

        with pytest.raises(ValueError, match='Invalid format'):
            manager.list_all_in_format('invalid')


def test_migration_from_old_structure():
    """Test migration from old logs/ and analyzed/ structure to new format-based structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir)

        # Create old structure manually
        logs_dir = cache_dir / 'logs'
        analyzed_dir = cache_dir / 'analyzed'
        logs_dir.mkdir(parents=True)
        analyzed_dir.mkdir(parents=True)

        # Create old files
        old_log = logs_dir / '2025-01-15T10:00:00-test.log'
        old_log.write_text('old log content')

        old_json = analyzed_dir / '2025-01-15T10:00:00-test.json'
        old_json.write_text('{"old": "data"}')

        # Initialize manager (should trigger migration)
        manager = CacheManager(cache_dir=cache_dir)

        # Old files should be moved to new structure
        new_raw = manager.raw_dir / '2025-01-15T10:00:00-test.log'
        new_json = manager.json_dir / '2025-01-15T10:00:00-test.json'

        assert new_raw.exists()
        assert new_json.exists()
        assert new_raw.read_text() == 'old log content'
        assert new_json.read_text() == '{"old": "data"}'

        # Old directories should be removed if empty
        assert not logs_dir.exists()
        assert not analyzed_dir.exists()
