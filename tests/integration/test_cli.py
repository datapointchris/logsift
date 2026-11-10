"""Integration tests for CLI interface."""

from importlib.metadata import version

import typer
from typer.testing import CliRunner

from logsift.cli import BROWSE_PANEL
from logsift.cli import app

runner = CliRunner()


def test_version_is_one_line_naming_the_tool_and_its_installed_version():
    result = runner.invoke(app, ['--version'])

    assert result.exit_code == 0
    assert result.stdout.startswith(f'logsift {version("logsift")}')
    assert result.stdout.count('\n') == 1


def test_help_command_prints_what_help_flag_prints():
    for command in ([], ['monitor']):
        flag = runner.invoke(app, [*command, '--help'])
        named = runner.invoke(app, ['help', *command])
        assert named.exit_code == 0
        assert named.stdout == flag.stdout


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


def test_every_saved_file_group_offers_list_latest_and_choose():
    root = typer.main.get_command(app)
    groups = [command for command in getattr(root, 'commands', {}).values() if getattr(command, 'rich_help_panel', None) == BROWSE_PANEL]

    assert groups
    for group in groups:
        assert {'list', 'latest', 'choose'} <= set(group.commands), group.name


def test_choose_without_a_terminal_exits_at_once_naming_the_command_that_needs_none():
    for args, instead in ((['logs', 'choose'], 'logsift logs latest'), (['analyze', '--choose'], 'logsift analyze --latest')):
        result = runner.invoke(app, args)

        assert result.exit_code == 2
        assert instead in ' '.join(result.stderr.split())
