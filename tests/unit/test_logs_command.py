"""Tests for logs command."""

import json
from unittest.mock import patch

from logsift.commands.logs import clean_logs
from logsift.commands.logs import list_logs


def test_list_logs_empty_cache(capsys, tmp_path):
    """Test listing logs when cache is empty."""
    from logsift.cache.manager import CacheManager

    # Use temporary cache directory
    with patch.object(CacheManager, '__init__', lambda self, cache_dir=None: setattr(self, 'cache_dir', tmp_path)):
        list_logs(output_format='table')
        captured = capsys.readouterr()

        assert 'No cached logs found' in captured.out


def test_list_logs_with_files(capsys, tmp_path):
    """Test listing logs with files present."""
    # Create some test log files
    context_dir = tmp_path / 'monitor'
    context_dir.mkdir(parents=True)

    log1 = context_dir / 'test1-20240101_120000_000000.log'
    log1.write_text('log content 1')

    log2 = context_dir / 'test2-20240101_130000_000000.log'
    log2.write_text('log content 2 with more data')

    from logsift.cache.manager import CacheManager

    with patch.object(CacheManager, '__init__', lambda self, cache_dir=None: setattr(self, 'cache_dir', tmp_path)):
        list_logs(output_format='table')
        captured = capsys.readouterr()

        # Should show both files
        assert 'test1' in captured.out
        assert 'test2' in captured.out
        assert 'monitor' in captured.out
        assert 'Total: 2 log file(s)' in captured.out


def test_list_logs_json_format(capsys, tmp_path):
    """Test listing logs with JSON output format."""
    # Create test log file
    context_dir = tmp_path / 'analyze'
    context_dir.mkdir(parents=True)

    log_file = context_dir / 'test-20240101_120000_000000.log'
    log_file.write_text('test log content')

    from logsift.cache.manager import CacheManager

    with patch.object(CacheManager, '__init__', lambda self, cache_dir=None: setattr(self, 'cache_dir', tmp_path)):
        list_logs(output_format='json')
        captured = capsys.readouterr()

        # Should produce valid JSON
        data = json.loads(captured.out)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]['context'] == 'analyze'
        assert 'test-20240101_120000_000000' in data[0]['name']


def test_list_logs_plain_format(capsys, tmp_path):
    """Test listing logs with plain output format."""
    # Create test log file
    context_dir = tmp_path / 'watch'
    context_dir.mkdir(parents=True)

    log_file = context_dir / 'app-20240101_120000_000000.log'
    log_file.write_text('watch log content')

    from logsift.cache.manager import CacheManager

    with patch.object(CacheManager, '__init__', lambda self, cache_dir=None: setattr(self, 'cache_dir', tmp_path)):
        list_logs(output_format='plain')
        captured = capsys.readouterr()

        # Should show tab-separated values
        assert 'watch' in captured.out
        assert str(log_file) in captured.out


def test_list_logs_with_context_filter(capsys, tmp_path):
    """Test listing logs with context filter."""
    # Create logs in multiple contexts
    monitor_dir = tmp_path / 'monitor'
    monitor_dir.mkdir(parents=True)
    (monitor_dir / 'test1-20240101_120000_000000.log').write_text('monitor log')

    analyze_dir = tmp_path / 'analyze'
    analyze_dir.mkdir(parents=True)
    (analyze_dir / 'test2-20240101_120000_000000.log').write_text('analyze log')

    from logsift.cache.manager import CacheManager

    with patch.object(CacheManager, '__init__', lambda self, cache_dir=None: setattr(self, 'cache_dir', tmp_path)):
        list_logs(context='monitor', output_format='table')
        captured = capsys.readouterr()

        # Should only show monitor logs
        assert 'test1' in captured.out
        assert 'test2' not in captured.out
        assert 'monitor' in captured.out


def test_list_logs_nonexistent_context(capsys, tmp_path):
    """Test listing logs with non-existent context."""
    from logsift.cache.manager import CacheManager

    with patch.object(CacheManager, '__init__', lambda self, cache_dir=None: setattr(self, 'cache_dir', tmp_path)):
        list_logs(context='nonexistent', output_format='table')
        captured = capsys.readouterr()

        assert 'No logs found for context: nonexistent' in captured.out


def test_clean_logs_empty_cache(capsys, tmp_path):
    """Test cleaning logs when cache is empty."""
    from logsift.cache.manager import CacheManager

    # Use a non-existent directory
    nonexistent_dir = tmp_path / 'nonexistent'

    with patch.object(CacheManager, '__init__', lambda self, cache_dir=None: setattr(self, 'cache_dir', nonexistent_dir)):
        clean_logs(days=30)
        captured = capsys.readouterr()

        assert 'No cache directory found' in captured.out


def test_clean_logs_no_old_files(capsys, tmp_path):
    """Test cleaning logs when no files are old enough."""
    # Create recent log file
    context_dir = tmp_path / 'monitor'
    context_dir.mkdir(parents=True)
    (context_dir / 'recent-20240101_120000_000000.log').write_text('recent log')

    from logsift.cache.manager import CacheManager

    with patch.object(CacheManager, '__init__', lambda self, cache_dir=None: setattr(self, 'cache_dir', tmp_path)):
        clean_logs(days=1)  # Only delete files older than 1 day
        captured = capsys.readouterr()

        assert 'No log files older than 1 days' in captured.out


def test_clean_logs_dry_run(capsys, tmp_path):
    """Test cleaning logs with dry-run mode."""
    import time

    # Create an old log file by creating and modifying its timestamp
    context_dir = tmp_path / 'monitor'
    context_dir.mkdir(parents=True)

    old_log = context_dir / 'old-20240101_120000_000000.log'
    old_log.write_text('old log')

    # Set modification time to 100 days ago
    old_time = time.time() - (100 * 24 * 60 * 60)
    old_log.touch()
    import os

    os.utime(old_log, (old_time, old_time))

    from logsift.cache.manager import CacheManager

    with patch.object(CacheManager, '__init__', lambda self, cache_dir=None: setattr(self, 'cache_dir', tmp_path)):
        clean_logs(days=30, dry_run=True)
        captured = capsys.readouterr()

        # Should show what would be deleted
        assert 'Would delete' in captured.out
        assert 'old-20240101_120000_000000.log' in captured.out
        assert 'Run without --dry-run to actually delete' in captured.out

        # File should still exist
        assert old_log.exists()


def test_clean_logs_actual_deletion(capsys, tmp_path):
    """Test actual deletion of old log files."""
    import time

    # Create an old log file
    context_dir = tmp_path / 'monitor'
    context_dir.mkdir(parents=True)

    old_log = context_dir / 'old-20240101_120000_000000.log'
    old_log.write_text('old log')

    # Set modification time to 100 days ago
    old_time = time.time() - (100 * 24 * 60 * 60)
    import os

    os.utime(old_log, (old_time, old_time))

    from logsift.cache.manager import CacheManager

    with patch.object(CacheManager, '__init__', lambda self, cache_dir=None: setattr(self, 'cache_dir', tmp_path)):
        clean_logs(days=30, dry_run=False)
        captured = capsys.readouterr()

        # Should show deletion message
        assert 'Deleted 1 log file(s)' in captured.out

        # File should be gone
        assert not old_log.exists()


def test_clean_logs_preserves_recent_files(tmp_path):
    """Test that clean_logs preserves recent files."""
    import time

    context_dir = tmp_path / 'monitor'
    context_dir.mkdir(parents=True)

    # Create old log
    old_log = context_dir / 'old-20240101_120000_000000.log'
    old_log.write_text('old log')
    old_time = time.time() - (100 * 24 * 60 * 60)
    import os

    os.utime(old_log, (old_time, old_time))

    # Create recent log
    recent_log = context_dir / 'recent-20240101_120000_000000.log'
    recent_log.write_text('recent log')

    from logsift.cache.manager import CacheManager

    with patch.object(CacheManager, '__init__', lambda self, cache_dir=None: setattr(self, 'cache_dir', tmp_path)):
        clean_logs(days=30, dry_run=False)

        # Old should be deleted
        assert not old_log.exists()

        # Recent should be preserved
        assert recent_log.exists()
