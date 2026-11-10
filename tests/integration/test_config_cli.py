"""A bad config.toml stops the run."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from logsift.cli import app

runner = CliRunner()


def write_config(home: Path, content: str) -> Path:
    config_file = home / 'logsift' / 'config.toml'
    config_file.parent.mkdir(parents=True)
    config_file.write_text(content)
    return config_file


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
