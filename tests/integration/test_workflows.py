"""Comprehensive integration tests for logsift workflows.

Tests end-to-end functionality with real commands and log files.
"""

import json
import sys
from pathlib import Path

from typer.testing import CliRunner

from logsift.cli import app

runner = CliRunner()


class TestMonitorWorkflow:
    """Test the complete monitor command workflow."""

    def test_monitor_successful_command(self):
        """Test monitoring a successful command produces expected output."""
        result = runner.invoke(app, ['monitor', '--format=json', '--', 'echo', 'hello world'])

        assert result.exit_code == 0

        # Parse JSON output
        data = json.loads(result.stdout)

        # Verify structure
        assert 'summary' in data
        assert 'stats' in data
        assert 'errors' in data

        # Verify summary
        assert data['summary']['status'] == 'success'
        assert data['summary']['exit_code'] == 0
        assert data['summary']['command'] == 'echo hello world'
        assert 'duration_seconds' in data['summary']

        # Verify stats
        assert data['stats']['total_errors'] == 0
        assert data['stats']['total_warnings'] == 0

    def test_monitor_failing_command(self):
        """Test monitoring a failing command produces expected output."""
        result = runner.invoke(app, ['monitor', '--format=json', '--', 'false'])

        # Command should fail with non-zero exit
        assert result.exit_code != 0

        # Parse JSON output
        data = json.loads(result.stdout)

        # Verify failure is captured
        assert data['summary']['status'] == 'failed'
        assert data['summary']['exit_code'] != 0

    def test_monitor_command_with_stderr(self):
        """Test monitoring a command that writes to stderr."""
        result = runner.invoke(
            app,
            ['monitor', '--format=json', '--', sys.executable, '-c', 'import sys; sys.stderr.write("error message")'],
        )

        assert result.exit_code == 0

        # Output should be captured
        data = json.loads(result.stdout)
        assert 'summary' in data

    def test_monitor_with_custom_name(self, tmp_path):
        """Test monitoring with a custom session name."""
        result = runner.invoke(
            app,
            ['monitor', '-n', 'test-session', '--format=json', '--', 'echo', 'test'],
        )

        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data['summary']['command'] == 'echo test'
        assert data['summary']['log_file'] is not None

    def test_monitor_markdown_format(self):
        """Test monitoring with markdown output format."""
        result = runner.invoke(app, ['monitor', '--format=markdown', '--', 'echo', 'test'])

        assert result.exit_code == 0
        assert '# Log Analysis Results' in result.stdout
        assert 'Status' in result.stdout

    def test_monitor_with_notification_flag(self):
        """Test monitoring with notification flag doesn't crash."""
        result = runner.invoke(
            app,
            ['monitor', '--notify', '--format=json', '--', 'echo', 'test'],
        )

        # Should succeed even if notifications aren't available
        assert result.exit_code == 0


class TestAnalyzeWorkflow:
    """Test the complete analyze command workflow."""

    def test_analyze_existing_log_file(self, tmp_path):
        """Test analyzing an existing log file with errors."""
        # Create a log file with errors using simple text format
        log_file = tmp_path / 'test.log'
        log_file.write_text("""Starting application
error: Failed to connect to database
warning: Retrying connection
error: Connection timeout after 30s
Shutting down
        """)

        result = runner.invoke(app, ['analyze', str(log_file), '--format=json'])

        assert result.exit_code == 0

        data = json.loads(result.stdout)

        # Should detect errors (case-insensitive)
        assert data['stats']['total_errors'] >= 2
        assert data['stats']['total_warnings'] >= 1

        # Should have error entries
        assert len(data['errors']) > 0

    def test_analyze_clean_log_file(self, tmp_path):
        """Test analyzing a log file with no errors."""
        log_file = tmp_path / 'clean.log'
        log_file.write_text("""
2024-01-01 10:00:00 INFO Starting application
2024-01-01 10:00:01 INFO Processing request
2024-01-01 10:00:02 INFO Request completed
2024-01-01 10:00:03 INFO Shutting down
        """)

        result = runner.invoke(app, ['analyze', str(log_file), '--format=json'])

        assert result.exit_code == 0

        data = json.loads(result.stdout)

        # Should have no errors
        assert data['stats']['total_errors'] == 0
        assert data['stats']['total_warnings'] == 0

    def test_analyze_nonexistent_file(self):
        """Test analyzing a file that doesn't exist."""
        result = runner.invoke(app, ['analyze', '/nonexistent/file.log'])

        assert result.exit_code == 1

    def test_analyze_with_file_references(self, tmp_path):
        """Test analyzing log with file:line references."""
        log_file = tmp_path / 'test.log'
        log_file.write_text("""error: File not found at src/main.py:42
warning: Deprecated function in lib/utils.js:123
error: Syntax error in config.yaml:15
        """)

        result = runner.invoke(app, ['analyze', str(log_file), '--format=json'])

        assert result.exit_code == 0

        data = json.loads(result.stdout)

        # Should extract errors and warnings
        assert data['stats']['total_errors'] >= 2
        assert data['stats']['total_warnings'] >= 1


class TestWatchWorkflow:
    """Test the complete watch command workflow."""

    def test_watch_existing_file(self, tmp_path, monkeypatch):
        """Test watching an existing log file."""
        import time
        from contextlib import suppress

        from logsift.commands.watch import watch_log

        log_file = tmp_path / 'watch.log'
        log_file.write_text('Initial line\n')

        # Mock the infinite loop to exit after one iteration
        original_sleep = time.sleep
        call_count = {'count': 0}

        def mock_sleep(seconds):
            call_count['count'] += 1
            if call_count['count'] >= 2:  # Exit after first watch iteration
                raise KeyboardInterrupt()
            original_sleep(0.01)  # Very short sleep for test

        monkeypatch.setattr(time, 'sleep', mock_sleep)

        # Should handle KeyboardInterrupt gracefully
        with suppress(KeyboardInterrupt, SystemExit):
            watch_log(str(log_file), interval=1)

    def test_watch_nonexistent_file(self):
        """Test watching a file that doesn't exist."""
        result = runner.invoke(app, ['watch', '/nonexistent/file.log'], catch_exceptions=False)

        # Should exit with error (may be 0 or 1 depending on how CliRunner handles sys.exit)
        # Check that error message is shown
        assert 'Error' in result.stdout or result.exit_code != 0


class TestEndToEndWorkflows:
    """Test complete end-to-end workflows combining multiple commands."""

    def test_monitor_then_analyze(self, tmp_path):
        """Test monitoring a command and then analyzing the saved log."""
        # Monitor a command that produces errors
        result1 = runner.invoke(
            app,
            [
                'monitor',
                '-n',
                'e2e-test',
                '--format=json',
                '--',
                sys.executable,
                '-c',
                'import sys; print("INFO: Starting"); print("ERROR: Failed"); sys.exit(1)',
            ],
        )

        # Monitor should fail (exit code 1 from command)
        assert result1.exit_code == 1

        # Parse output
        data1 = json.loads(result1.stdout)

        # Should have saved log file
        assert data1['summary']['log_file'] is not None
        log_path = Path(data1['summary']['log_file'])

        # Verify log file exists
        assert log_path.exists()

        # Now analyze the saved log
        result2 = runner.invoke(app, ['analyze', str(log_path), '--format=json'])

        assert result2.exit_code == 0

        data2 = json.loads(result2.stdout)

        # Should detect the error
        assert data2['stats']['total_errors'] >= 1

    def test_monitor_with_append_mode(self, tmp_path):
        """Test monitoring multiple times with append mode."""
        # First run
        result1 = runner.invoke(
            app,
            ['monitor', '-n', 'append-test', '--format=json', '--', 'echo', 'first run'],
        )

        assert result1.exit_code == 0
        data1 = json.loads(result1.stdout)
        log_path = Path(data1['summary']['log_file'])

        # Second run with append
        result2 = runner.invoke(
            app,
            ['monitor', '-n', 'append-test', '--append', '--format=json', '--', 'echo', 'second run'],
        )

        assert result2.exit_code == 0

        # Read the log file
        log_content = log_path.read_text()

        # Should contain both runs
        assert 'first run' in log_content
        assert 'second run' in log_content

    def test_monitor_with_external_log(self, tmp_path):
        """Test monitoring with external log file."""
        # Create external log
        external_log = tmp_path / 'external.log'
        external_log.write_text('External log entry 1\nExternal log entry 2\n')

        # Monitor command with external log
        result = runner.invoke(
            app,
            [
                'monitor',
                f'--external-log={external_log}',
                '--format=json',
                '--',
                'echo',
                'Command output',
            ],
        )

        assert result.exit_code == 0

        data = json.loads(result.stdout)

        # Command should succeed
        assert data['summary']['exit_code'] == 0


class TestPatternMatching:
    """Test pattern matching in real-world scenarios."""

    def test_common_error_patterns(self, tmp_path):
        """Test detection of common error patterns."""
        log_file = tmp_path / 'patterns.log'
        log_file.write_text("""
Error: Permission denied
Error: File not found: /path/to/file
Error: Connection refused
Warning: Deprecated API usage
Error: Out of memory
Fatal error: Segmentation fault
        """)

        result = runner.invoke(app, ['analyze', str(log_file), '--format=json'])

        assert result.exit_code == 0

        data = json.loads(result.stdout)

        # Should detect multiple errors
        assert data['stats']['total_errors'] >= 4
        assert data['stats']['total_warnings'] >= 1

    def test_json_log_parsing(self, tmp_path):
        """Test parsing JSON-formatted logs."""
        log_file = tmp_path / 'json.log'
        log_file.write_text("""
{"level": "info", "message": "Starting application"}
{"level": "error", "message": "Failed to connect", "code": 500}
{"level": "warn", "message": "Slow query detected"}
{"level": "error", "message": "Unhandled exception", "stack": "..."}
        """)

        result = runner.invoke(app, ['analyze', str(log_file), '--format=json'])

        assert result.exit_code == 0

        data = json.loads(result.stdout)

        # Should detect errors in JSON logs
        assert data['stats']['total_errors'] >= 2


class TestCacheManagement:
    """Test log cache management workflows."""

    def test_multiple_monitoring_sessions(self):
        """Test that multiple monitoring sessions create separate logs."""
        # Run multiple monitoring sessions
        result1 = runner.invoke(
            app,
            ['monitor', '-n', 'session1', '--format=json', '--', 'echo', 'test1'],
        )

        result2 = runner.invoke(
            app,
            ['monitor', '-n', 'session2', '--format=json', '--', 'echo', 'test2'],
        )

        assert result1.exit_code == 0
        assert result2.exit_code == 0

        data1 = json.loads(result1.stdout)
        data2 = json.loads(result2.stdout)

        # Should have different log files
        assert data1['summary']['log_file'] != data2['summary']['log_file']


class TestErrorHandling:
    """Test error handling in various scenarios."""

    def test_invalid_command(self):
        """Test monitoring an invalid command."""
        result = runner.invoke(
            app,
            ['monitor', '--format=json', '--', 'nonexistent-command-12345'],
        )

        # Should handle error gracefully
        assert result.exit_code != 0

    def test_command_timeout(self):
        """Test handling of long-running commands."""
        # This is a basic test - actual timeout handling would need more sophisticated testing
        result = runner.invoke(
            app,
            ['monitor', '--format=json', '--', 'echo', 'test'],
        )

        assert result.exit_code == 0

    def test_empty_log_file(self, tmp_path):
        """Test analyzing an empty log file."""
        log_file = tmp_path / 'empty.log'
        log_file.write_text('')

        result = runner.invoke(app, ['analyze', str(log_file), '--format=json'])

        assert result.exit_code == 0

        data = json.loads(result.stdout)

        # Should handle empty file gracefully
        assert data['stats']['total_errors'] == 0
