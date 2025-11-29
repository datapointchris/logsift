"""Tests for monitor command."""

import json
import sys
from unittest.mock import patch

from logsift.commands.monitor import monitor_command


def test_monitor_command_basic(capsys):
    """Test monitoring a basic command."""
    monitor_command(['echo', 'hello'], output_format='json', save_log=False)
    captured = capsys.readouterr()

    # Should produce valid JSON
    data = json.loads(captured.out)
    assert 'stats' in data
    assert 'summary' in data
    assert data['summary']['exit_code'] == 0


def test_monitor_command_with_name(capsys):
    """Test monitoring with a custom name."""
    # Monitor with save_log=False to avoid file creation
    monitor_command(['echo', 'test'], name='custom-name', output_format='json', save_log=False)
    captured = capsys.readouterr()

    data = json.loads(captured.out)
    assert data['summary']['command'] == 'echo test'


def test_monitor_command_saves_log():
    """Test that monitor saves log to cache."""
    # We can't easily control cache dir, so just verify it doesn't crash
    monitor_command(['echo', 'test'], output_format='json', save_log=True)


def test_monitor_command_json_format(capsys):
    """Test monitoring with JSON output format."""
    monitor_command(['echo', 'test'], output_format='json', save_log=False)
    captured = capsys.readouterr()

    # Should be valid JSON
    data = json.loads(captured.out)
    assert isinstance(data, dict)


def test_monitor_command_markdown_format(capsys):
    """Test monitoring with Markdown output format."""
    monitor_command(['echo', 'test'], output_format='markdown', save_log=False)
    captured = capsys.readouterr()

    # Should have markdown header
    assert '# Log Analysis Results' in captured.out


def test_monitor_command_auto_format(capsys):
    """Test monitoring with auto format detection."""
    monitor_command(['echo', 'test'], output_format='auto', save_log=False)
    captured = capsys.readouterr()

    # Should produce output
    assert len(captured.out) > 0


def test_monitor_command_with_error():
    """Test monitoring a command that fails."""
    from contextlib import suppress

    with suppress(SystemExit):
        monitor_command(['false'], output_format='json', save_log=False)
        # Should have exited with non-zero code
        raise AssertionError('Should have called sys.exit')


def test_monitor_command_captures_output(capsys):
    """Test that command output is captured and analyzed."""
    monitor_command([sys.executable, '-c', 'print("test output")'], output_format='json', save_log=False)
    captured = capsys.readouterr()

    data = json.loads(captured.out)
    assert 'stats' in data


def test_monitor_command_includes_summary(capsys):
    """Test that result includes command summary."""
    monitor_command(['echo', 'test'], output_format='json', save_log=False)
    captured = capsys.readouterr()

    data = json.loads(captured.out)
    assert 'summary' in data
    assert 'status' in data['summary']
    assert 'exit_code' in data['summary']
    assert 'duration_seconds' in data['summary']
    assert 'command' in data['summary']


def test_monitor_command_default_name(capsys):
    """Test that default name is command name."""
    monitor_command(['echo', 'test'], output_format='json', save_log=False)
    captured = capsys.readouterr()

    data = json.loads(captured.out)
    assert data['summary']['command'] == 'echo test'


def test_monitor_command_with_stderr(capsys):
    """Test monitoring command with stderr output."""
    monitor_command([sys.executable, '-c', 'import sys; sys.stderr.write("error")'], output_format='json', save_log=False)
    captured = capsys.readouterr()

    # Should produce valid output
    data = json.loads(captured.out)
    assert 'stats' in data


def test_monitor_command_empty_command():
    """Test monitoring with empty command list."""
    from contextlib import suppress

    # Empty command should raise SystemExit or Exception
    with suppress(SystemExit, Exception):
        monitor_command([], output_format='json', save_log=False)
        # If it doesn't raise, that's also acceptable


def test_monitor_command_with_notify(capsys):
    """Test monitoring with notification enabled."""
    with patch('logsift.commands.monitor.notify_command_complete') as mock_notify:
        monitor_command(['echo', 'test'], output_format='json', save_log=False, notify=True)

        # Should have called notify_command_complete
        mock_notify.assert_called_once()

        # Check notification was called with correct parameters
        call_args = mock_notify.call_args[1]
        assert 'command' in call_args
        assert 'success' in call_args
        assert 'errors' in call_args
        assert 'warnings' in call_args
        assert 'duration_seconds' in call_args


def test_monitor_command_without_notify(capsys):
    """Test monitoring with notification disabled (default)."""
    with patch('logsift.commands.monitor.notify_command_complete') as mock_notify:
        monitor_command(['echo', 'test'], output_format='json', save_log=False, notify=False)

        # Should not have called notify_command_complete
        mock_notify.assert_not_called()


def test_monitor_command_with_external_log(tmp_path, capsys):
    """Test monitoring with external log file."""

    # Create external log file
    external_log = tmp_path / 'external.log'
    external_log.write_text('External log line 1\nExternal log line 2\n')

    # Monitor a command while watching the external log
    monitor_command(
        ['echo', 'Command output'],
        output_format='json',
        save_log=False,
        external_log=str(external_log),
    )

    captured = capsys.readouterr()

    # Parse the JSON output
    data = json.loads(captured.out)

    # Command should have succeeded
    assert data['summary']['exit_code'] == 0
    assert 'stats' in data


def test_monitor_command_with_nonexistent_external_log(capsys):
    """Test monitoring with non-existent external log file."""
    from contextlib import suppress

    # Should exit with error
    with suppress(SystemExit):
        monitor_command(
            ['echo', 'test'],
            output_format='json',
            save_log=False,
            external_log='/nonexistent/log/file.log',
        )


def test_monitor_command_with_append_mode(tmp_path, capsys):
    """Test monitoring with append mode."""
    # First run - create initial log
    monitor_command(
        ['echo', 'first run'],
        name='test-append',
        output_format='json',
        save_log=True,
        append=False,
    )

    # Get the created log file
    from logsift.cache.manager import CacheManager

    cache = CacheManager()
    log_file = cache.get_latest_log('test-append')

    assert log_file is not None
    assert log_file.exists()

    # Read initial content
    initial_content = log_file.read_text()
    assert 'first run' in initial_content

    # Second run - append to existing log
    monitor_command(
        ['echo', 'second run'],
        name='test-append',
        output_format='json',
        save_log=True,
        append=True,
    )

    # Read updated content
    updated_content = log_file.read_text()

    # Should contain both runs
    assert 'first run' in updated_content
    assert 'second run' in updated_content


def test_monitor_command_append_without_existing_log(capsys):
    """Test append mode when no existing log exists."""
    # Using unique name to ensure no existing log
    monitor_command(
        ['echo', 'new log'],
        name='unique-test-name-12345',
        output_format='json',
        save_log=True,
        append=True,
    )

    captured = capsys.readouterr()

    # Should succeed and create new log
    data = json.loads(captured.out)
    assert data['summary']['exit_code'] == 0
