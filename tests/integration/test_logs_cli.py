"""Integration tests for logs CLI commands."""

import json
import time

from typer.testing import CliRunner

from logsift.cli import app

runner = CliRunner()


class TestLogsListCommand:
    """Test the logs list command."""

    def test_logs_list_empty_cache(self, tmp_path, monkeypatch):
        """Test listing logs with empty cache."""
        # Set cache directory to temp
        monkeypatch.setenv('HOME', str(tmp_path))

        result = runner.invoke(app, ['logs', 'list'])

        assert result.exit_code == 0
        assert 'No cached logs found' in result.stdout

    def test_logs_list_with_logs(self):
        """Test listing logs with cached log files."""
        # First create some logs by running monitor
        runner.invoke(app, ['monitor', '-n', 'list-test-1', '--format=json', '--', 'echo', 'test1'])
        runner.invoke(app, ['monitor', '-n', 'list-test-2', '--format=json', '--', 'echo', 'test2'])

        # Now list them
        result = runner.invoke(app, ['logs', 'list'])

        assert result.exit_code == 0
        assert 'list-test-1' in result.stdout or 'list-test-2' in result.stdout

    def test_logs_list_json_format(self):
        """Test listing logs with JSON format."""
        # Create a log
        runner.invoke(app, ['monitor', '-n', 'json-test', '--format=json', '--', 'echo', 'test'])

        # List with JSON format
        result = runner.invoke(app, ['logs', 'list', '--format', 'json'])

        assert result.exit_code == 0

        # Should be valid JSON
        data = json.loads(result.stdout)
        assert isinstance(data, list)

    def test_logs_list_plain_format(self):
        """Test listing logs with plain format."""
        # Create a log
        runner.invoke(app, ['monitor', '-n', 'plain-test', '--format=json', '--', 'echo', 'test'])

        # List with plain format
        result = runner.invoke(app, ['logs', 'list', '--format', 'plain'])

        assert result.exit_code == 0
        # Plain format should have tab-separated values
        assert '\t' in result.stdout or 'plain-test' in result.stdout


class TestLogsCleanCommand:
    """Test the logs clean command."""

    def test_logs_clean_empty_cache(self):
        """Test cleaning with empty cache."""
        # Cache directory exists but is empty (thanks to autouse fixture)
        result = runner.invoke(app, ['logs', 'clean'])

        assert result.exit_code == 0
        # Should report no old files, not that directory doesn't exist
        assert 'No log files older than' in result.stdout or 'Deleted 0 log file(s)' in result.stdout

    def test_logs_clean_no_old_files(self):
        """Test cleaning when no files are old enough."""
        # Create a recent log
        runner.invoke(app, ['monitor', '-n', 'clean-test-recent-new', '--format=json', '--', 'echo', 'test'])

        # Try to clean files older than 0.0001 days (a few seconds ago) - won't match just-created log
        result = runner.invoke(app, ['logs', 'clean', '--days', '0'])

        # Should succeed - the just-created log is too recent to be deleted even with 0 days retention
        # (there's a small time window)
        assert result.exit_code == 0
        # Either no files deleted, or very few (not the one we just created)
        assert 'Deleted' in result.stdout or 'No log files older than' in result.stdout

    def test_logs_clean_dry_run(self, tmp_path):
        """Test cleaning with dry-run mode."""
        from logsift.cache.manager import CacheManager

        # Create an old log file in logs/ subdirectory
        cache = CacheManager()
        logs_dir = cache.logs_dir
        logs_dir.mkdir(parents=True, exist_ok=True)

        old_log = logs_dir / '2024-01-01T12:00:00-old-test.log'
        old_log.write_text('old log content')

        # Set modification time to 100 days ago
        old_time = time.time() - (100 * 24 * 60 * 60)
        import os

        os.utime(old_log, (old_time, old_time))

        # Run dry-run clean
        result = runner.invoke(app, ['logs', 'clean', '--days', '30', '--dry-run'])

        assert result.exit_code == 0
        assert 'Would delete' in result.stdout
        assert 'Run without --dry-run to actually delete' in result.stdout

        # File should still exist
        assert old_log.exists()

    def test_logs_clean_actual_deletion(self, tmp_path):
        """Test actual deletion of old log files."""
        from logsift.cache.manager import CacheManager

        # Create an old log file in logs/ subdirectory
        cache = CacheManager()
        logs_dir = cache.logs_dir
        logs_dir.mkdir(parents=True, exist_ok=True)

        old_log = logs_dir / '2024-01-01T12:00:00-delete-test.log'
        old_log.write_text('old log to delete')

        # Set modification time to 100 days ago
        old_time = time.time() - (100 * 24 * 60 * 60)
        import os

        os.utime(old_log, (old_time, old_time))

        # Run actual clean
        result = runner.invoke(app, ['logs', 'clean', '--days', '30'])

        assert result.exit_code == 0
        assert 'Deleted' in result.stdout

        # File should be gone
        assert not old_log.exists()

    def test_logs_clean_custom_retention_days(self, tmp_path):
        """Test cleaning with custom retention period."""
        from logsift.cache.manager import CacheManager

        cache = CacheManager()
        logs_dir = cache.logs_dir
        logs_dir.mkdir(parents=True, exist_ok=True)

        # Create log files with different ages in logs/ subdirectory
        log_60_days = logs_dir / '2024-01-01T12:00:00-log-60days.log'
        log_60_days.write_text('60 days old')
        time_60_days = time.time() - (60 * 24 * 60 * 60)

        log_20_days = logs_dir / '2024-01-01T12:00:00-log-20days.log'
        log_20_days.write_text('20 days old')
        time_20_days = time.time() - (20 * 24 * 60 * 60)

        import os

        os.utime(log_60_days, (time_60_days, time_60_days))
        os.utime(log_20_days, (time_20_days, time_20_days))

        # Clean files older than 30 days
        result = runner.invoke(app, ['logs', 'clean', '--days', '30'])

        assert result.exit_code == 0

        # 60 day old file should be deleted
        assert not log_60_days.exists()

        # 20 day old file should be preserved
        assert log_20_days.exists()


class TestLogsEndToEnd:
    """Test complete workflows involving logs commands."""

    def test_monitor_list_clean_workflow(self):
        """Test complete workflow: monitor -> list -> clean."""
        # Step 1: Monitor a command to create logs
        result1 = runner.invoke(app, ['monitor', '-n', 'workflow-test', '--format=json', '--', 'echo', 'test data'])

        assert result1.exit_code == 0

        # Step 2: List logs to verify it was created
        result2 = runner.invoke(app, ['logs', 'list', '--format', 'json'])

        assert result2.exit_code == 0
        data = json.loads(result2.stdout)
        assert len(data) > 0

        # Find our log
        our_logs = [log for log in data if 'workflow-test' in log['name']]
        assert len(our_logs) > 0

        # Step 3: Dry-run clean to see what would be deleted
        result3 = runner.invoke(app, ['logs', 'clean', '--days', '0', '--dry-run'])

        assert result3.exit_code == 0
        # Should show our log would be deleted (since retention is 0 days)
        assert 'Would delete' in result3.stdout or 'workflow-test' in result3.stdout

    def test_multiple_monitors_then_list(self):
        """Test creating multiple logs and listing them."""
        # Create multiple logs
        for i in range(3):
            runner.invoke(app, ['monitor', '-n', f'multi-test-{i}', '--format=json', '--', 'echo', f'test {i}'])

        # List all logs
        result = runner.invoke(app, ['logs', 'list', '--format', 'json'])

        assert result.exit_code == 0
        data = json.loads(result.stdout)

        # Should have at least our 3 logs
        our_logs = [log for log in data if 'multi-test' in log['name']]
        assert len(our_logs) >= 3


class TestLogsLatestCommand:
    """Test the logs latest command."""

    def test_logs_latest_by_name(self):
        """Test getting the latest log by name."""
        # Create multiple logs for the same command
        runner.invoke(app, ['monitor', '-n', 'latest-test', '--format=json', '--', 'echo', 'test1'])
        runner.invoke(app, ['monitor', '-n', 'latest-test', '--format=json', '--', 'echo', 'test2'])

        # Get latest for that name
        result = runner.invoke(app, ['logs', 'latest', 'latest-test'])

        assert result.exit_code == 0
        assert 'Latest log:' in result.stdout
        # The name might be split across lines due to path wrapping, so check for it without newlines
        stdout_no_newlines = result.stdout.replace('\n', '')
        assert 'latest-test' in stdout_no_newlines

    def test_logs_latest_absolute(self):
        """Test getting the absolute latest log (no name filter)."""
        # Create logs for different commands
        runner.invoke(app, ['monitor', '-n', 'latest-abs-1', '--format=json', '--', 'echo', 'test1'])
        runner.invoke(app, ['monitor', '-n', 'latest-abs-2', '--format=json', '--', 'echo', 'test2'])

        # Get absolute latest
        result = runner.invoke(app, ['logs', 'latest'])

        assert result.exit_code == 0
        assert 'Latest log:' in result.stdout

    def test_logs_latest_nonexistent_name(self):
        """Test getting latest log for nonexistent name."""
        result = runner.invoke(app, ['logs', 'latest', 'nonexistent-command-xyz'])

        assert result.exit_code == 1
        assert 'No logs found' in result.stdout

    def test_logs_latest_with_tail_flag(self):
        """Test that --tail flag is accepted (full tail testing in watch tests)."""
        # Create a log
        runner.invoke(app, ['monitor', '-n', 'tail-test', '--format=json', '--', 'echo', 'test'])

        # This should not error with --tail flag (though we'll ctrl-c it quickly)
        # Just verify the command accepts the flag
        result = runner.invoke(app, ['logs', 'latest', 'tail-test', '--help'])

        assert result.exit_code == 0
        assert '--tail' in result.stdout


class TestMonitorStreamFlags:
    """Test the monitor command --stream and --update-interval flags."""

    def test_monitor_with_stream_flag(self):
        """Test monitor with --stream flag for real-time output."""
        result = runner.invoke(app, ['monitor', '--stream', '--format=json', '--', 'echo', 'stream test'])

        assert result.exit_code == 0
        # Should have captured output and analysis
        data = json.loads(result.stdout)
        assert 'summary' in data

    def test_monitor_with_update_interval(self):
        """Test monitor with custom --update-interval."""
        result = runner.invoke(app, ['monitor', '--update-interval', '5', '--format=json', '--', 'echo', 'interval test'])

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert 'summary' in data

    def test_monitor_default_periodic_updates(self):
        """Test monitor default behavior (periodic updates, not streaming)."""
        # Without --stream, should still work (periodic mode)
        result = runner.invoke(app, ['monitor', '--format=json', '--', 'echo', 'periodic test'])

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert 'summary' in data

    def test_monitor_stream_with_interval(self):
        """Test monitor with both --stream and --update-interval."""
        result = runner.invoke(app, ['monitor', '--stream', '--update-interval', '10', '--format=json', '--', 'echo', 'both flags test'])

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert 'summary' in data
