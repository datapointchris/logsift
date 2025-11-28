"""Tests for process monitor."""

import sys

from logsift.monitor.process import ProcessMonitor


def test_process_monitor_initialization():
    """Test ProcessMonitor initialization."""
    monitor = ProcessMonitor(['echo', 'test'])
    assert monitor.command == ['echo', 'test']


def test_run_simple_command():
    """Test running a simple command."""
    monitor = ProcessMonitor(['echo', 'hello world'])
    result = monitor.run()

    assert result['exit_code'] == 0
    assert 'hello world' in result['output']
    assert result['success'] is True


def test_run_command_with_exit_code():
    """Test running command that exits with non-zero code."""
    # Use 'false' command which always exits with 1
    monitor = ProcessMonitor(['false'])
    result = monitor.run()

    assert result['exit_code'] == 1
    assert result['success'] is False


def test_run_command_captures_stderr():
    """Test that stderr is captured in output."""
    # Python command that writes to stderr
    monitor = ProcessMonitor([sys.executable, '-c', 'import sys; sys.stderr.write("error message")'])
    result = monitor.run()

    assert 'error message' in result['output']


def test_run_command_captures_stdout():
    """Test that stdout is captured in output."""
    monitor = ProcessMonitor([sys.executable, '-c', 'print("stdout message")'])
    result = monitor.run()

    assert 'stdout message' in result['output']


def test_run_command_with_multiple_lines():
    """Test capturing multi-line output."""
    monitor = ProcessMonitor([sys.executable, '-c', 'print("line1"); print("line2"); print("line3")'])
    result = monitor.run()

    assert 'line1' in result['output']
    assert 'line2' in result['output']
    assert 'line3' in result['output']


def test_run_command_includes_command_in_result():
    """Test that result includes the command that was run."""
    monitor = ProcessMonitor(['echo', 'test'])
    result = monitor.run()

    assert result['command'] == 'echo test'


def test_run_command_includes_duration():
    """Test that result includes execution duration."""
    monitor = ProcessMonitor(['echo', 'test'])
    result = monitor.run()

    assert 'duration_seconds' in result
    assert isinstance(result['duration_seconds'], float)
    assert result['duration_seconds'] >= 0


def test_run_command_with_shell_special_chars():
    """Test running command with shell special characters."""
    # Command with quotes - should be properly handled
    monitor = ProcessMonitor(['echo', 'hello "world"'])
    result = monitor.run()

    assert result['exit_code'] == 0
    assert 'hello' in result['output']


def test_run_nonexistent_command():
    """Test running a command that doesn't exist."""
    monitor = ProcessMonitor(['nonexistent_command_12345'])
    result = monitor.run()

    assert result['success'] is False
    assert result['exit_code'] != 0


def test_run_command_with_timeout():
    """Test running command with timeout."""
    # Command that takes long time
    monitor = ProcessMonitor(['sleep', '0.1'], timeout=5)
    result = monitor.run()

    # Should complete successfully
    assert result['exit_code'] == 0
    assert result['success'] is True


def test_run_command_empty_output():
    """Test running command with no output."""
    monitor = ProcessMonitor(['true'])  # Command that produces no output
    result = monitor.run()

    assert result['exit_code'] == 0
    assert result['success'] is True
    assert result['output'] == ''
