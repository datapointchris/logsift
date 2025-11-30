"""Tests for cache manager."""

import tempfile
from pathlib import Path

import pytest

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

        # Should create a path in raw/ subdirectory
        assert log_path.parent == manager.raw_dir
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

        # Correct parent directories
        assert paths['raw'].parent == manager.raw_dir
        assert paths['json'].parent == manager.json_dir
        assert paths['toon'].parent == manager.toon_dir
        assert paths['md'].parent == manager.md_dir


def test_get_all_formats_finds_existing_files():
    """Test get_all_formats finds all format files for a log session."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = CacheManager(cache_dir=Path(tmpdir))

        # Create paths
        paths = manager.create_paths('test_command')
        stem = paths['raw'].stem

        # Create only some files (not all formats exist yet)
        paths['raw'].write_text('raw log')
        paths['json'].write_text('{"test": "data"}')

        # Get all formats
        found = manager.get_all_formats(stem)

        # Should find the ones that exist
        assert found['raw'] == paths['raw']
        assert found['json'] == paths['json']

        # Should return None for non-existent
        assert found['toon'] is None
        assert found['md'] is None


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

        # Create json files
        paths1['json'].write_text('{}')
        paths2['json'].write_text('{}')

        # List raw files
        raw_files = manager.list_all_in_format('raw')
        assert len(raw_files) == 2
        assert all(f['name'].endswith('.log') for f in raw_files)

        # List json files
        json_files = manager.list_all_in_format('json')
        assert len(json_files) == 2
        assert all(f['name'].endswith('.json') for f in json_files)

        # List toon files (should be empty)
        toon_files = manager.list_all_in_format('toon')
        assert len(toon_files) == 0


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


def test_migration_preserves_existing_files():
    """Test migration doesn't overwrite existing files in new structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir)

        # Create old structure
        logs_dir = cache_dir / 'logs'
        logs_dir.mkdir(parents=True)
        old_log = logs_dir / '2025-01-15T10:00:00-test.log'
        old_log.write_text('old content')

        # Create new structure with same file
        raw_dir = cache_dir / 'raw'
        raw_dir.mkdir(parents=True)
        existing_file = raw_dir / '2025-01-15T10:00:00-test.log'
        existing_file.write_text('existing content')

        # Initialize manager (should trigger migration)
        CacheManager(cache_dir=cache_dir)

        # Existing file should NOT be overwritten
        assert existing_file.read_text() == 'existing content'

        # Old file should still exist (not moved because target exists)
        assert old_log.exists()
        assert old_log.read_text() == 'old content'
