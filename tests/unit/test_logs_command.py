"""Tests for logs command."""

import json
from unittest.mock import patch

from logsift.commands.logs import clean_logs
from logsift.commands.logs import list_logs


def test_list_logs_empty_cache(capsys, tmp_path):
    """Test listing logs when cache is empty."""
    from logsift.cache.manager import CacheManager

    # Use temporary cache directory
    def mock_init(self, cache_dir=None):
        self.cache_dir = tmp_path
        self.raw_dir = tmp_path / 'raw'
        self.json_dir = tmp_path / 'json'
        self.toon_dir = tmp_path / 'toon'
        self.md_dir = tmp_path / 'md'
        self.logs_dir = tmp_path / 'logs'
        self.analyzed_dir = tmp_path / 'analyzed'
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.json_dir.mkdir(parents=True, exist_ok=True)
        self.toon_dir.mkdir(parents=True, exist_ok=True)
        self.md_dir.mkdir(parents=True, exist_ok=True)

    with patch.object(CacheManager, '__init__', mock_init):
        list_logs(output_format='table')
        captured = capsys.readouterr()

        assert 'No cached logs found' in captured.out


def test_list_logs_with_files(capsys, tmp_path):
    """Test listing logs with files present."""
    # Create some test log files in raw/ subdirectory
    raw_dir = tmp_path / 'raw'
    raw_dir.mkdir(parents=True, exist_ok=True)

    log1 = raw_dir / '2024-01-01T12:00:00-test1.log'
    log1.write_text('log content 1')

    log2 = raw_dir / '2024-01-01T13:00:00-test2.log'
    log2.write_text('log content 2 with more data')

    from logsift.cache.manager import CacheManager

    def mock_init(self, cache_dir=None):
        self.cache_dir = tmp_path
        self.raw_dir = raw_dir
        self.json_dir = tmp_path / 'json'
        self.toon_dir = tmp_path / 'toon'
        self.md_dir = tmp_path / 'md'
        self.logs_dir = tmp_path / 'logs'
        self.analyzed_dir = tmp_path / 'analyzed'
        self.json_dir.mkdir(parents=True, exist_ok=True)

    with patch.object(CacheManager, '__init__', mock_init):
        list_logs(output_format='table')
        captured = capsys.readouterr()

        # Should show both files
        assert 'test1' in captured.out
        assert 'test2' in captured.out
        assert 'Total: 2 log file(s)' in captured.out


def test_list_logs_json_format(capsys, tmp_path):
    """Test listing logs with JSON output format."""
    # Create test log file in raw/ subdirectory
    raw_dir = tmp_path / 'raw'
    raw_dir.mkdir(parents=True, exist_ok=True)

    log_file = raw_dir / '2024-01-01T12:00:00-test.log'
    log_file.write_text('test log content')

    from logsift.cache.manager import CacheManager

    def mock_init(self, cache_dir=None):
        self.cache_dir = tmp_path
        self.raw_dir = raw_dir
        self.json_dir = tmp_path / 'json'
        self.toon_dir = tmp_path / 'toon'
        self.md_dir = tmp_path / 'md'
        self.logs_dir = tmp_path / 'logs'
        self.analyzed_dir = tmp_path / 'analyzed'
        self.json_dir.mkdir(parents=True, exist_ok=True)

    with patch.object(CacheManager, '__init__', mock_init):
        list_logs(output_format='json')
        captured = capsys.readouterr()

        # Should produce valid JSON
        data = json.loads(captured.out)
        assert isinstance(data, list)
        assert len(data) == 1
        assert '2024-01-01T12:00:00-test' in data[0]['name']


def test_list_logs_plain_format(capsys, tmp_path):
    """Test listing logs with plain output format."""
    # Create test log file in raw/ subdirectory
    raw_dir = tmp_path / 'raw'
    raw_dir.mkdir(parents=True, exist_ok=True)

    log_file = raw_dir / '2024-01-01T12:00:00-app.log'
    log_file.write_text('app log content')

    from logsift.cache.manager import CacheManager

    def mock_init(self, cache_dir=None):
        self.cache_dir = tmp_path
        self.raw_dir = raw_dir
        self.json_dir = tmp_path / 'json'
        self.toon_dir = tmp_path / 'toon'
        self.md_dir = tmp_path / 'md'
        self.logs_dir = tmp_path / 'logs'
        self.analyzed_dir = tmp_path / 'analyzed'
        self.json_dir.mkdir(parents=True, exist_ok=True)

    with patch.object(CacheManager, '__init__', mock_init):
        list_logs(output_format='plain')
        captured = capsys.readouterr()

        # Should show tab-separated values
        assert 'app' in captured.out
        assert str(log_file) in captured.out


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
    # Create recent log file in flat structure
    (tmp_path / '2024-01-01T12:00:00-recent.log').write_text('recent log')

    from logsift.cache.manager import CacheManager

    with patch.object(CacheManager, '__init__', lambda self, cache_dir=None: setattr(self, 'cache_dir', tmp_path)):
        clean_logs(days=1)  # Only delete files older than 1 day
        captured = capsys.readouterr()

        assert 'No log files older than 1 days' in captured.out


def test_clean_logs_dry_run(capsys, tmp_path):
    """Test cleaning logs with dry-run mode."""
    import time

    # Create an old log file in flat structure
    old_log = tmp_path / '2024-01-01T12:00:00-old.log'
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
        assert '2024-01-01T12:00:00-old.log' in captured.out
        assert 'Run without --dry-run to actually delete' in captured.out

        # File should still exist
        assert old_log.exists()


def test_clean_logs_actual_deletion(capsys, tmp_path):
    """Test actual deletion of old log files."""
    import time

    # Create an old log file in flat structure
    old_log = tmp_path / '2024-01-01T12:00:00-old.log'
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

    # Create old log in flat structure
    old_log = tmp_path / '2024-01-01T12:00:00-old.log'
    old_log.write_text('old log')
    old_time = time.time() - (100 * 24 * 60 * 60)
    import os

    os.utime(old_log, (old_time, old_time))

    # Create recent log
    recent_log = tmp_path / '2024-01-01T12:00:00-recent.log'
    recent_log.write_text('recent log')

    from logsift.cache.manager import CacheManager

    with patch.object(CacheManager, '__init__', lambda self, cache_dir=None: setattr(self, 'cache_dir', tmp_path)):
        clean_logs(days=30, dry_run=False)

        # Old should be deleted
        assert not old_log.exists()

        # Recent should be preserved
        assert recent_log.exists()
