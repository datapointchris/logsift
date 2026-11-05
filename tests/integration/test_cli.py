"""Integration tests for CLI interface."""

from typer.testing import CliRunner

from logsift.cli import app

runner = CliRunner()


def test_cli_version():
    """Test --version flag."""
    result = runner.invoke(app, ['--version'])
    assert result.exit_code == 0
    assert 'logsift version' in result.stdout


def test_cli_help():
    """Test --help flag."""
    result = runner.invoke(app, ['--help'])
    assert result.exit_code == 0
    assert 'logsift' in result.stdout.lower()


def test_help_for_an_unknown_command_is_a_usage_error():
    """A mistyped command name exits 2, apart from a command that ran and failed."""
    result = runner.invoke(app, ['help', 'no-such-command'])
    assert result.exit_code == 2


def test_monitor_command():
    """Test that monitor command works."""
    result = runner.invoke(app, ['monitor', '--format=json', '--', 'echo', 'test'])
    # Command should execute successfully
    assert result.exit_code == 0
    assert 'summary' in result.stdout


def test_analyze_command():
    """Test that analyze command works with nonexistent file."""
    result = runner.invoke(app, ['analyze', '/nonexistent/file.log'])
    # Should handle error gracefully
    assert result.exit_code == 1
