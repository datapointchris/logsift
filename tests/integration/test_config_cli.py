"""`logsift config` names the layer behind every value logsift resolves, and a bad config.toml stops the run."""

import re
from pathlib import Path

import pytest
import typer
from typer.testing import CliRunner

from logsift import xdg_dirs
from logsift.cli import app
from logsift.config.loader import FILE_KEYS

runner = CliRunner()


def option_variables() -> set[str]:
    """Every environment variable a logsift option reads, read from the command tree."""
    found: set[str] = set()

    def walk(command) -> None:
        for param in command.params:
            found.update([param.envvar] if isinstance(param.envvar, str) else list(param.envvar or []))
        for subcommand in getattr(command, 'commands', {}).values():
            walk(subcommand)

    walk(typer.main.get_command(app))
    return found


def config_rows(output: str) -> list[list[str]]:
    return [re.split(r'\s{2,}', line) for line in output.splitlines() if line]


def write_config(home: Path, content: str) -> Path:
    config_file = home / 'logsift' / 'config.toml'
    config_file.parent.mkdir(parents=True)
    config_file.write_text(content)
    return config_file


XDG_VARIABLES = {variable for variable, _ in xdg_dirs.BASE_DIRS.values()}


@pytest.mark.parametrize('variable', sorted(option_variables() | XDG_VARIABLES))
def test_every_variable_logsift_reads_is_named_by_a_row(variable, monkeypatch, tmp_path):
    # An XDG variable is honored only as an absolute path. Every option variable takes an int or any string.
    monkeypatch.setenv(variable, str(tmp_path / variable) if variable in XDG_VARIABLES else '7')

    result = runner.invoke(app, ['config'])

    assert result.exit_code == 0, result.output
    assert any(row[2] == f'${variable}' for row in config_rows(result.stdout)), (
        f'No row names ${variable} as the layer that answered. Add its option to RESOLVED_OPTIONS '
        f'in src/logsift/config/resolved_values.py.\n{result.stdout}'
    )


@pytest.mark.parametrize('key', FILE_KEYS)
def test_every_file_key_is_named_by_a_row_for_each_option_it_sets(key, monkeypatch, tmp_path):
    monkeypatch.setenv('XDG_CONFIG_HOME', str(tmp_path))
    write_config(tmp_path, f'{key} = {7 if FILE_KEYS[key].toml_type is int else '"json"'}\n')

    result = runner.invoke(app, ['config'])

    assert result.exit_code == 0, result.output
    from_file = [row for row in config_rows(result.stdout) if row[-1] == key and row[2] == 'config.toml']
    assert len(from_file) == len(FILE_KEYS[key].sets), result.stdout


@pytest.mark.parametrize(
    ('content', 'named'),
    [
        ('print_analysis_as = \n', 'Invalid value'),
        ('[output]\ndefault_format = "json"\n', 'unknown key(s) output.default_format; known: print_analysis_as,'),
        ('monitor.report_progress_every_seconds = "60"\n', "must be a TOML int, not '60'"),
    ],
)
def test_a_config_file_logsift_cannot_honor_stops_the_run(content, named, monkeypatch, tmp_path):
    monkeypatch.setenv('XDG_CONFIG_HOME', str(tmp_path))
    config_file = write_config(tmp_path, content)

    result = runner.invoke(app, ['monitor', '--', 'echo', 'ran anyway'])

    assert result.exit_code == 1
    assert f'{config_file}: ' in result.output
    assert named in result.output
    assert 'ran anyway' not in result.output
