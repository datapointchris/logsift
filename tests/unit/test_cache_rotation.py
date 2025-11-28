"""Tests for cache rotation."""

import tempfile
from datetime import UTC
from datetime import datetime
from datetime import timedelta
from pathlib import Path

from logsift.cache.rotation import clean_old_logs


def test_clean_old_logs_no_files():
    """Test cleaning directory with no files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir)
        deleted = clean_old_logs(cache_dir, retention_days=7)
        assert deleted == 0


def test_clean_old_logs_only_recent_files():
    """Test that recent files are not deleted."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir)

        # Create a recent file
        log_file = cache_dir / 'recent.log'
        log_file.write_text('test')

        deleted = clean_old_logs(cache_dir, retention_days=7)
        assert deleted == 0
        assert log_file.exists()


def test_clean_old_logs_deletes_old_files():
    """Test that old files are deleted."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir)

        # Create an old file
        old_file = cache_dir / 'old.log'
        old_file.write_text('test')

        # Set modification time to 100 days ago
        old_time = (datetime.now(tz=UTC) - timedelta(days=100)).timestamp()
        old_file.touch()
        # Update the modification time
        import os

        os.utime(old_file, (old_time, old_time))

        deleted = clean_old_logs(cache_dir, retention_days=90)
        assert deleted == 1
        assert not old_file.exists()


def test_clean_old_logs_preserves_recent_deletes_old():
    """Test that recent files are preserved while old files are deleted."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir)

        # Create a recent file
        recent_file = cache_dir / 'recent.log'
        recent_file.write_text('recent')

        # Create an old file
        old_file = cache_dir / 'old.log'
        old_file.write_text('old')

        # Set old file modification time to 100 days ago
        old_time = (datetime.now(tz=UTC) - timedelta(days=100)).timestamp()
        import os

        os.utime(old_file, (old_time, old_time))

        deleted = clean_old_logs(cache_dir, retention_days=90)
        assert deleted == 1
        assert recent_file.exists()
        assert not old_file.exists()


def test_clean_old_logs_with_subdirectories():
    """Test cleaning logs in subdirectories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir)
        subdir = cache_dir / 'context'
        subdir.mkdir()

        # Create old file in subdirectory
        old_file = subdir / 'old.log'
        old_file.write_text('test')

        old_time = (datetime.now(tz=UTC) - timedelta(days=100)).timestamp()
        import os

        os.utime(old_file, (old_time, old_time))

        deleted = clean_old_logs(cache_dir, retention_days=90)
        assert deleted == 1
        assert not old_file.exists()


def test_clean_old_logs_nonexistent_directory():
    """Test cleaning nonexistent directory."""
    deleted = clean_old_logs(Path('/nonexistent/path'), retention_days=90)
    assert deleted == 0


def test_clean_old_logs_custom_retention():
    """Test with custom retention period."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir)

        # Create file 5 days old
        old_file = cache_dir / 'file.log'
        old_file.write_text('test')

        old_time = (datetime.now(tz=UTC) - timedelta(days=5)).timestamp()
        import os

        os.utime(old_file, (old_time, old_time))

        # Should not delete with 7 day retention
        deleted = clean_old_logs(cache_dir, retention_days=7)
        assert deleted == 0
        assert old_file.exists()

        # Should delete with 3 day retention
        deleted = clean_old_logs(cache_dir, retention_days=3)
        assert deleted == 1
        assert not old_file.exists()


def test_clean_old_logs_returns_count():
    """Test that function returns correct count of deleted files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir)

        # Create multiple old files
        old_time = (datetime.now(tz=UTC) - timedelta(days=100)).timestamp()
        import os

        for i in range(5):
            old_file = cache_dir / f'old_{i}.log'
            old_file.write_text('test')
            os.utime(old_file, (old_time, old_time))

        deleted = clean_old_logs(cache_dir, retention_days=90)
        assert deleted == 5


def test_clean_old_logs_only_log_files():
    """Test that only .log files are considered."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir)

        # Create old .log file
        old_log = cache_dir / 'old.log'
        old_log.write_text('test')

        # Create old .txt file
        old_txt = cache_dir / 'old.txt'
        old_txt.write_text('test')

        old_time = (datetime.now(tz=UTC) - timedelta(days=100)).timestamp()
        import os

        os.utime(old_log, (old_time, old_time))
        os.utime(old_txt, (old_time, old_time))

        deleted = clean_old_logs(cache_dir, retention_days=90)

        # Should only delete .log file
        assert deleted == 1
        assert not old_log.exists()
        assert old_txt.exists()
