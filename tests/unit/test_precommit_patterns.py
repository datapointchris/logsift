"""Tests for pre-commit hook patterns.

This test file verifies that patterns in pre-commit.toml correctly match
real pre-commit hook output. Each test uses actual violation files and
captured hook output to ensure patterns work in practice.
"""

import re
import tomllib
from pathlib import Path


def test_precommit_pattern_file_exists():
    """Test that pre-commit.toml pattern file exists."""
    pattern_file = Path('src/logsift/patterns/defaults/pre-commit.toml')
    assert pattern_file.exists(), 'Missing pre-commit.toml pattern file'


def test_precommit_pattern_file_structure():
    """Test that pre-commit.toml has correct TOML structure."""
    pattern_file = Path('src/logsift/patterns/defaults/pre-commit.toml')
    with pattern_file.open('rb') as f:
        data = tomllib.load(f)

    # File might be empty initially (skeleton), but should be valid TOML
    # Once patterns are added, verify structure
    if 'patterns' in data:
        patterns = data['patterns']
        assert isinstance(patterns, list), 'patterns must be a list'

        if len(patterns) > 0:
            # Check first pattern has required fields
            first_pattern = patterns[0]
            required_fields = ['name', 'regex', 'severity', 'description', 'tags']
            for field in required_fields:
                assert field in first_pattern, f'Pattern missing required field: {field}'


# Individual hook pattern tests will be added below as patterns are created
# Format: test_<hook_name>_pattern()


def test_shellcheck_file_location_pattern():
    """Test shellcheck file location header pattern."""
    pattern_file = Path('src/logsift/patterns/defaults/pre-commit.toml')
    with pattern_file.open('rb') as f:
        data = tomllib.load(f)

    pattern = next((p for p in data['patterns'] if p['name'] == 'shellcheck_file_location'), None)
    assert pattern is not None, 'shellcheck_file_location pattern not found'

    # Real shellcheck output line
    test_line = 'In tests/pre-commit-testing/violations/shellcheck_unquoted.sh line 5:'
    match = re.search(pattern['regex'], test_line)
    assert match is not None, f"Pattern didn't match: {test_line}"
    assert match.group(1) == 'tests/pre-commit-testing/violations/shellcheck_unquoted.sh'
    assert match.group(2) == '5'


def test_shellcheck_info_pattern():
    """Test shellcheck info/style pattern."""
    pattern_file = Path('src/logsift/patterns/defaults/pre-commit.toml')
    with pattern_file.open('rb') as f:
        data = tomllib.load(f)

    pattern = next((p for p in data['patterns'] if p['name'] == 'shellcheck_info'), None)
    assert pattern is not None, 'shellcheck_info pattern not found'

    # Real shellcheck output (info severity)
    test_line = '    ^---^ SC2086 (info): Double quote to prevent globbing and word splitting.'
    match = re.search(pattern['regex'], test_line)
    assert match is not None, f"Pattern didn't match: {test_line}"
    assert match.group(1) == '2086'
    assert 'Double quote' in match.group(2)


def test_shellcheck_warning_pattern():
    """Test shellcheck warning pattern."""
    pattern_file = Path('src/logsift/patterns/defaults/pre-commit.toml')
    with pattern_file.open('rb') as f:
        data = tomllib.load(f)

    pattern = next((p for p in data['patterns'] if p['name'] == 'shellcheck_warning'), None)
    assert pattern is not None, 'shellcheck_warning pattern not found'

    # Real shellcheck output (warning severity)
    test_line1 = '^--------^ SC2034 (warning): UNUSED_VAR appears unused. Verify use (or export if used externally).'
    match1 = re.search(pattern['regex'], test_line1)
    assert match1 is not None, f"Pattern didn't match: {test_line1}"
    assert match1.group(1) == '2034'

    test_line2 = '^----------------^ SC2154 (warning): undefined_command is referenced but not assigned.'
    match2 = re.search(pattern['regex'], test_line2)
    assert match2 is not None, f"Pattern didn't match: {test_line2}"
    assert match2.group(1) == '2154'


def test_refurb_suggestion_pattern():
    """Test refurb suggestion pattern."""
    pattern_file = Path('src/logsift/patterns/defaults/pre-commit.toml')
    with pattern_file.open('rb') as f:
        data = tomllib.load(f)

    pattern = next((p for p in data['patterns'] if p['name'] == 'refurb_suggestion'), None)
    assert pattern is not None, 'refurb_suggestion pattern not found'

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
    assert match1.group(4) == '101'
    assert 'Replace' in match1.group(5)

    test_line2 = (
        'tests/pre-commit-testing/violations/refurb_pathlib.py:10:1 [FURB103]: '
        'Replace `with open(x, ...) as f: f.write(y)` with `Path(x).write_text(y)`'
    )
    match2 = re.search(pattern['regex'], test_line2)
    assert match2 is not None, f"Pattern didn't match: {test_line2}"
    assert match2.group(4) == '103'


def test_mypy_error_pattern():
    """Test mypy error pattern (first line of multi-line error)."""
    pattern_file = Path('src/logsift/patterns/defaults/pre-commit.toml')
    with pattern_file.open('rb') as f:
        data = tomllib.load(f)

    pattern = next((p for p in data['patterns'] if p['name'] == 'mypy_error_no_code'), None)
    assert pattern is not None, 'mypy_error_no_code pattern not found'

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


def test_ruff_error_pattern():
    """Test ruff linting error pattern."""
    pattern_file = Path('src/logsift/patterns/defaults/pre-commit.toml')
    with pattern_file.open('rb') as f:
        data = tomllib.load(f)

    pattern = next((p for p in data['patterns'] if p['name'] == 'ruff_error'), None)
    assert pattern is not None, 'ruff_error pattern not found'

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
