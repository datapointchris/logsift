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


def test_codespell_typo_pattern():
    """Test codespell spelling error pattern."""
    pattern_file = Path('src/logsift/patterns/defaults/pre-commit.toml')
    with pattern_file.open('rb') as f:
        data = tomllib.load(f)

    pattern = next((p for p in data['patterns'] if p['name'] == 'codespell_typo'), None)
    assert pattern is not None, 'codespell_typo pattern not found'

    # Real codespell output lines
    test_line1 = 'tests/pre-commit-testing/violations/codespell_typos.txt:3: develoment ==> development'
    match1 = re.search(pattern['regex'], test_line1)
    assert match1 is not None, f"Pattern didn't match: {test_line1}"
    assert match1.group(1) == 'tests/pre-commit-testing/violations/codespell_typos.txt'
    assert match1.group(2) == '3'
    assert match1.group(3) == 'develoment'
    assert match1.group(4) == 'development'

    test_line2 = 'tests/pre-commit-testing/violations/codespell_typos.txt:3: feture ==> feature, future'
    match2 = re.search(pattern['regex'], test_line2)
    assert match2 is not None, f"Pattern didn't match: {test_line2}"
    assert match2.group(3) == 'feture'
    assert 'feature' in match2.group(4)


def test_file_validation_patterns():
    """Test file format validation patterns (YAML, TOML, JSON)."""
    pattern_file = Path('src/logsift/patterns/defaults/pre-commit.toml')
    with pattern_file.open('rb') as f:
        data = tomllib.load(f)

    # Test YAML pattern
    yaml_pattern = next((p for p in data['patterns'] if p['name'] == 'check_yaml_error'), None)
    assert yaml_pattern is not None
    yaml_line = '  in "tests/pre-commit-testing/violations/bad.yaml", line 7, column 10'
    match = re.search(yaml_pattern['regex'], yaml_line)
    assert match is not None
    assert match.group(2) == '7'

    # Test TOML pattern
    toml_pattern = next((p for p in data['patterns'] if p['name'] == 'check_toml_error'), None)
    assert toml_pattern is not None
    toml_line = "tests/pre-commit-testing/violations/bad.toml: Expected '=' after a key in a key/value pair (at line 3, column 9)"
    match = re.search(toml_pattern['regex'], toml_line)
    assert match is not None
    assert match.group(3) == '3'

    # Test JSON pattern
    json_pattern = next((p for p in data['patterns'] if p['name'] == 'check_json_error'), None)
    assert json_pattern is not None
    json_line = 'tests/pre-commit-testing/violations/bad.json: Failed to json decode (Expecting value: line 4 column 14 (char 53))'
    match = re.search(json_pattern['regex'], json_line)
    assert match is not None
    assert match.group(1) == 'tests/pre-commit-testing/violations/bad.json'


def test_bandit_patterns():
    """Test bandit security scanning patterns."""
    pattern_file = Path('src/logsift/patterns/defaults/pre-commit.toml')
    with pattern_file.open('rb') as f:
        data = tomllib.load(f)

    # Test issue header pattern
    issue_pattern = next((p for p in data['patterns'] if p['name'] == 'bandit_issue_header'), None)
    assert issue_pattern is not None
    issue_line = '>> Issue: [B307:blacklist] Use of possibly insecure function - consider using safer ast.literal_eval.'
    match = re.search(issue_pattern['regex'], issue_line)
    assert match is not None
    assert match.group(1) == 'B307'
    assert 'insecure function' in match.group(2)

    # Test high severity pattern
    high_pattern = next((p for p in data['patterns'] if p['name'] == 'bandit_severity_high'), None)
    assert high_pattern is not None
    high_line = '   Severity: High   Confidence: High'
    match = re.search(high_pattern['regex'], high_line)
    assert match is not None

    # Test medium severity pattern
    medium_pattern = next((p for p in data['patterns'] if p['name'] == 'bandit_severity_medium'), None)
    assert medium_pattern is not None
    medium_line = '   Severity: Medium   Confidence: High'
    match = re.search(medium_pattern['regex'], medium_line)
    assert match is not None

    # Test location pattern
    location_pattern = next((p for p in data['patterns'] if p['name'] == 'bandit_location'), None)
    assert location_pattern is not None
    location_line = '   Location: ./.venv/lib/python3.13/site-packages/_pytest/_code/code.py:170:15'
    match = re.search(location_pattern['regex'], location_line)
    assert match is not None
    assert match.group(1) == './.venv/lib/python3.13/site-packages/_pytest/_code/code.py'
    assert match.group(2) == '170'
    assert match.group(3) == '15'
