"""Which shipped pattern `logsift analyze` reports a tool's output line under, with its severity and code."""

from pathlib import Path

import pytest

from logsift.core.analyzer import Analyzer

TOOL_LINES = [
    ('    ^---^ SC2086 (info): Double quote to prevent globbing and word splitting.', 'shellcheck_info', 'warning', 'SC2086'),
    ('^--------^ SC2034 (warning): UNUSED_VAR appears unused.', 'shellcheck_warning', 'warning', 'SC2034'),
    ('In script.sh line 5:', 'shellcheck_file_location', 'error', None),
    ("src/main.py:10:1: F401 'sys' imported but unused", 'ruff_error', 'error', 'F401'),
    ('src/refurb_pathlib.py:6:1 [FURB101]: Replace `with open(x) as f: y = f.read()`', 'refurb_suggestion', 'warning', 'FURB101'),
    ('src/mypy_types.py:10: error: Argument 1 to', 'mypy_error_no_code', 'error', None),
    ('  in "bad.yaml", line 7, column 10', 'check_yaml_error', 'error', None),
    ("bad.toml: Expected '=' after a key in a key/value pair (at line 3, column 9)", 'check_toml_error', 'error', None),
    ('bad.json: Failed to json decode (Expecting value: line 4 column 14 (char 53))', 'check_json_error', 'error', None),
    ('>> Issue: [B307:blacklist] Use of possibly insecure function.', 'bandit_issue_header', 'warning', 'B307'),
    (
        'docs/x.md:1 MD041/first-line-heading/first-line-h1 First line in a file should be a top-level heading',
        'markdownlint_error',
        'error',
        'MD041',
    ),
    ("ModuleNotFoundError: No module named 'requests'", 'module_not_found', 'error', None),
    ('SyntaxError: invalid syntax', 'syntax_error_python', 'error', None),
    ('bash: unzip: command not found', 'shell_command_not_found', 'error', None),
    ('An unexpected error has occurred: CalledProcessError', 'pre_commit_called_process_error', 'error', None),
    ('failed to connect to the docker API at unix:///x/docker.sock', 'docker_socket_connection_failure', 'error', None),
]


@pytest.mark.parametrize(('line', 'pattern_name', 'severity', 'code'), TOOL_LINES)
def test_analyze_reports_a_tool_line_under_its_own_pattern(line, pattern_name, severity, code):
    result = Analyzer().analyze(line)

    [issue] = result['errors'] + result['warnings']
    assert (issue['pattern_name'], issue['severity'], issue.get('code')) == (pattern_name, severity, code)


def test_analyze_reports_each_line_of_captured_codespell_output():
    captured = (Path(__file__).parents[1] / 'fixtures/pre-commit-violations/codespell_output.txt').read_text()

    result = Analyzer().analyze(captured)

    assert [warning['pattern_name'] for warning in result['warnings']] == ['codespell_typo', 'codespell_typo']
