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


def test_monitor_command_placeholder():
    """Test that monitor command exists (placeholder)."""
    result = runner.invoke(app, ['monitor', '--', 'echo', 'test'])
    # Should not crash, even if not fully implemented
    assert 'Monitor command not yet implemented' in result.stdout


def test_analyze_command_placeholder():
    """Test that analyze command exists (placeholder)."""
    result = runner.invoke(app, ['analyze', '/tmp/test.log'])
    # Should not crash, even if not fully implemented
    assert 'Analyze command not yet implemented' in result.stdout
