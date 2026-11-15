"""Integration tests for CLI interface."""

import re
from importlib.metadata import version
from pathlib import Path

import typer
from typer.testing import CliRunner

from logsift.cli import BROWSE_PANEL
from logsift.cli import app

runner = CliRunner()

REPO = Path(__file__).parents[2]

# A command printed for a person to run. In the source: a code span, single quotes or rich bold,
# or an indented example line in a docstring or epilog string. In the README: a code span, or a
# line of a shell fence. A word running into a `/` or a `.` is a path argument, not a subcommand.
WORDS = r'((?: [a-z][\w-]*(?![\w/.-]))+)'
QUOTED = re.compile(rf"(?:\[b\]|`|')logsift{WORDS}")
EXAMPLE_LINE = re.compile(rf"^[ \t]+'?[ \t]*logsift{WORDS}", re.MULTILINE)
SHELL_FENCE = re.compile(r'^```(?:bash|sh|console)\n(.*?)^```', re.MULTILINE | re.DOTALL)
FENCE_LINE = re.compile(rf'^logsift{WORDS}', re.MULTILINE)


def printed_commands():
    for source in sorted((REPO / 'src' / 'logsift').rglob('*.py')):
        text = source.read_text()
        for pattern in (QUOTED, EXAMPLE_LINE):
            for match in pattern.finditer(text):
                yield source.name, match.group(1).split()
    readme = (REPO / 'README.md').read_text()
    for fence in SHELL_FENCE.finditer(readme):
        for match in FENCE_LINE.finditer(fence.group(1)):
            yield 'README.md', match.group(1).split()
    for match in QUOTED.finditer(readme):
        yield 'README.md', match.group(1).split()


def test_every_command_it_prints_is_in_the_command_tree():
    """A hint naming a command that does not exist sends its reader to an error.

    The walk stops at a command with no subcommands, so what follows it is that command's argument.
    """
    tree = typer.main.get_command(app)
    missing = []
    walked = 0
    for source, words in printed_commands():
        walked += 1
        command = tree
        for word in words:
            subcommands = getattr(command, 'commands', None)
            if subcommands is None:
                break
            if word not in subcommands:
                missing.append(f'{source}: logsift {" ".join(words)}')
                break
            command = subcommands[word]

    assert walked > 40
    assert missing == []


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


def test_choose_without_a_terminal_exits_at_once():
    for args in (['logs', 'choose'], ['analyze', '--choose']):
        result = runner.invoke(app, args)

        assert result.exit_code == 2
