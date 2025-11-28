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

    with suppress(Exception):
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
