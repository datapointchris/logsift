"""Tests for what --format auto prints."""

import io

from typer.testing import CliRunner

from logsift.cli import app
from logsift.output.analysis_format import AnalysisFormat
from logsift.output.analysis_format import resolve_format


class Terminal(io.StringIO):
    def isatty(self) -> bool:
        return True


def test_auto_is_markdown_on_a_terminal_and_toon_on_a_pipe():
    assert resolve_format('auto', Terminal()) is AnalysisFormat.MARKDOWN
    assert resolve_format('auto', io.StringIO()) is AnalysisFormat.TOON


def test_analyze_with_no_format_prints_toon_to_a_pipe(tmp_path):
    log_file = tmp_path / 'build.log'
    log_file.write_text('ERROR: boom\n')

    result = CliRunner().invoke(app, ['analyze', '--no-save', str(log_file)])

    assert result.exit_code == 0
    assert result.stdout.startswith('stats:\n  total_errors: 1\n')
