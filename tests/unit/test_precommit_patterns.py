"""Tests for pre-commit hook patterns.

This test file verifies that patterns in pre-commit.toml correctly match
real pre-commit hook output. Each test uses actual violation files and
captured hook output to ensure patterns work in practice.
"""

import re
from pathlib import Path


def test_shellcheck_file_location_pattern(builtin_pattern):
    """Test shellcheck file location header pattern."""
    pattern = builtin_pattern('shellcheck_file_location')

    # Real shellcheck output line
    test_line = 'In tests/pre-commit-testing/violations/shellcheck_unquoted.sh line 5:'
    match = re.search(pattern['regex'], test_line)
    assert match is not None, f"Pattern didn't match: {test_line}"
    assert match.group(1) == 'tests/pre-commit-testing/violations/shellcheck_unquoted.sh'
    assert match.group(2) == '5'


def test_shellcheck_info_pattern(builtin_pattern):
    """Test shellcheck info/style pattern."""
    pattern = builtin_pattern('shellcheck_info')

    # Real shellcheck output (info severity)
    test_line = '    ^---^ SC2086 (info): Double quote to prevent globbing and word splitting.'
    match = re.search(pattern['regex'], test_line)
    assert match is not None, f"Pattern didn't match: {test_line}"
    assert match.group('code') == 'SC2086'
    assert 'Double quote' in match.group(2)


def test_shellcheck_warning_pattern(builtin_pattern):
    """Test shellcheck warning pattern."""
    pattern = builtin_pattern('shellcheck_warning')

    # Real shellcheck output (warning severity)
    test_line1 = '^--------^ SC2034 (warning): UNUSED_VAR appears unused. Verify use (or export if used externally).'
    match1 = re.search(pattern['regex'], test_line1)
    assert match1 is not None, f"Pattern didn't match: {test_line1}"
    assert match1.group('code') == 'SC2034'

    test_line2 = '^----------------^ SC2154 (warning): undefined_command is referenced but not assigned.'
    match2 = re.search(pattern['regex'], test_line2)
    assert match2 is not None, f"Pattern didn't match: {test_line2}"
    assert match2.group('code') == 'SC2154'


def test_refurb_suggestion_pattern(builtin_pattern):
    """Test refurb suggestion pattern."""
    pattern = builtin_pattern('refurb_suggestion')

    # Real refurb output lines
    test_line1 = (
        'tests/pre-commit-testing/violations/refurb_pathlib.py:6:1 [FURB101]: '
        'Replace `with open(x) as f: y = f.read()` with `y = Path(x).read_text()`'
    )
    match1 = re.search(pattern['regex'], test_line1)
    assert match1 is not None, f"Pattern didn't match: {test_line1}"
    assert match1.group(1) == 'tests/pre-commit-testing/violations/refurb_pathlib.py'
    assert match1.group(2) == '6'
    assert match1.group(3) == '1'
    assert match1.group('code') == 'FURB101'
    assert 'Replace' in match1.group(5)

    test_line2 = (
        'tests/pre-commit-testing/violations/refurb_pathlib.py:10:1 [FURB103]: '
        'Replace `with open(x, ...) as f: f.write(y)` with `Path(x).write_text(y)`'
    )
    match2 = re.search(pattern['regex'], test_line2)
    assert match2 is not None, f"Pattern didn't match: {test_line2}"
    assert match2.group('code') == 'FURB103'


def test_mypy_error_pattern(builtin_pattern):
    """Test mypy error pattern (first line of multi-line error)."""
    pattern = builtin_pattern('mypy_error_no_code')

    # Real mypy output - first line of error (message wraps to next line)
    test_line1 = 'tests/pre-commit-testing/violations/mypy_types.py:10: error: Argument 1 to'
    match1 = re.search(pattern['regex'], test_line1)
    assert match1 is not None, f"Pattern didn't match: {test_line1}"
    assert match1.group(1) == 'tests/pre-commit-testing/violations/mypy_types.py'
    assert match1.group(2) == '10'
    assert 'Argument' in match1.group(3)

    test_line2 = 'tests/pre-commit-testing/violations/mypy_types.py:15: error: Incompatible'
    match2 = re.search(pattern['regex'], test_line2)
    assert match2 is not None, f"Pattern didn't match: {test_line2}"
    assert match2.group(2) == '15'


def test_ruff_error_pattern(builtin_pattern):
    """Test ruff linting error pattern."""
    pattern = builtin_pattern('ruff_error')

    # Real ruff output lines
    test_line1 = 'tests/pre-commit-testing/violations/ruff_errors.py:9:141: E501 Line too long (142 > 140)'
    match1 = re.search(pattern['regex'], test_line1)
    assert match1 is not None, f"Pattern didn't match: {test_line1}"
    assert match1.group(1) == 'tests/pre-commit-testing/violations/ruff_errors.py'
    assert match1.group(2) == '9'
    assert match1.group(3) == '141'
    assert match1.group(4) == 'E501'
    assert 'Line too long' in match1.group(5)

    test_line2 = 'tests/pre-commit-testing/violations/ruff_errors.py:18:10: F821 Undefined name `undefined_variable`'
    match2 = re.search(pattern['regex'], test_line2)
    assert match2 is not None, f"Pattern didn't match: {test_line2}"
    assert match2.group(4) == 'F821'


def test_codespell_typo_pattern(builtin_pattern):
    """Test codespell spelling error pattern."""
    pattern = builtin_pattern('codespell_typo')

    # This fixture sits under tests/fixtures/pre-commit-violations/, which pre-commit excludes,
    # so the typos it quotes never fail the codespell hook.
    captured = (Path(__file__).parents[1] / 'fixtures/pre-commit-violations/codespell_output.txt').read_text().splitlines()
    assert len(captured) == 2

    for line in captured:
        path, number, finding = line.split(':', 2)
        typo, suggestions = finding.strip().split(' ==> ')
        match = re.search(pattern['regex'], line)
        assert match is not None, f"Pattern didn't match: {line}"
        assert match.group(1, 2, 3, 4) == (path, number, typo, suggestions)

    assert captured[1].endswith('==> feature, future'), 'a multi-suggestion line must stay covered'


def test_file_validation_patterns(builtin_pattern):
    """Test file format validation patterns (YAML, TOML, JSON)."""
    # Test YAML pattern
    yaml_pattern = builtin_pattern('check_yaml_error')
    yaml_line = '  in "tests/pre-commit-testing/violations/bad.yaml", line 7, column 10'
    match = re.search(yaml_pattern['regex'], yaml_line)
    assert match is not None
    assert match.group(2) == '7'

    # Test TOML pattern
    toml_pattern = builtin_pattern('check_toml_error')
    toml_line = "tests/pre-commit-testing/violations/bad.toml: Expected '=' after a key in a key/value pair (at line 3, column 9)"
    match = re.search(toml_pattern['regex'], toml_line)
    assert match is not None
    assert match.group(3) == '3'

    # Test JSON pattern
    json_pattern = builtin_pattern('check_json_error')
    json_line = 'tests/pre-commit-testing/violations/bad.json: Failed to json decode (Expecting value: line 4 column 14 (char 53))'
    match = re.search(json_pattern['regex'], json_line)
    assert match is not None
    assert match.group(1) == 'tests/pre-commit-testing/violations/bad.json'


def test_bandit_patterns(builtin_pattern):
    """Test bandit security scanning patterns."""
    # Test issue header pattern
    issue_pattern = builtin_pattern('bandit_issue_header')
    issue_line = '>> Issue: [B307:blacklist] Use of possibly insecure function - consider using safer ast.literal_eval.'
    match = re.search(issue_pattern['regex'], issue_line)
    assert match is not None
    assert match.group(1) == 'B307'
    assert 'insecure function' in match.group(2)

    # Test high severity pattern
    high_pattern = builtin_pattern('bandit_severity_high')
    high_line = '   Severity: High   Confidence: High'
    match = re.search(high_pattern['regex'], high_line)
    assert match is not None

    # Test medium severity pattern
    medium_pattern = builtin_pattern('bandit_severity_medium')
    medium_line = '   Severity: Medium   Confidence: High'
    match = re.search(medium_pattern['regex'], medium_line)
    assert match is not None

    # Test location pattern
    location_pattern = builtin_pattern('bandit_location')
    location_line = '   Location: ./.venv/lib/python3.13/site-packages/_pytest/_code/code.py:170:15'
    match = re.search(location_pattern['regex'], location_line)
    assert match is not None
    assert match.group(1) == './.venv/lib/python3.13/site-packages/_pytest/_code/code.py'
    assert match.group(2) == '170'
    assert match.group(3) == '15'


def test_markdownlint_error_pattern(builtin_pattern):
    """Test markdownlint rule violation pattern."""
    pattern = builtin_pattern('markdownlint_error')

    # Real markdownlint output with context
    test_line1 = (
        'docs/hook-final-test.md:1 MD041/first-line-heading/first-line-h1 '
        'First line in a file should be a top-level heading [Context: "Final test"]'
    )
    match1 = re.search(pattern['regex'], test_line1)
    assert match1 is not None, f"Pattern didn't match: {test_line1}"
    assert match1.group(1) == 'docs/hook-final-test.md'
    assert match1.group(2) == '1'
    assert match1.group(3) == 'MD041'
    assert match1.group(4) == 'first-line-heading/first-line-h1'
    assert 'First line in a file' in match1.group(5)
    assert match1.group(6) == 'Final test'

    # Real markdownlint output without context
    test_line2 = 'README.md:42 MD033/no-inline-html Inline HTML [Element: br]'
    match2 = re.search(pattern['regex'], test_line2)
    assert match2 is not None, f"Pattern didn't match: {test_line2}"
    assert match2.group(1) == 'README.md'
    assert match2.group(2) == '42'
    assert match2.group(3) == 'MD033'
    assert match2.group(4) == 'no-inline-html'
    assert 'Inline HTML' in match2.group(5)
