"""Tests for pattern library files."""

import tomllib
from pathlib import Path


def test_docker_patterns_valid():
    """Test that docker.toml is valid TOML and has correct structure."""
    pattern_file = Path('src/logsift/patterns/defaults/docker.toml')
    assert pattern_file.exists()

    with pattern_file.open('rb') as f:
        data = tomllib.load(f)

    assert 'patterns' in data
    patterns = data['patterns']
    assert len(patterns) > 0

    # Check first few patterns have required fields
    for pattern in patterns[:3]:
        assert 'name' in pattern
        assert 'regex' in pattern
        assert 'severity' in pattern
        assert 'description' in pattern
        assert 'tags' in pattern
        assert pattern['severity'] in ('error', 'warning', 'info')


def test_npm_patterns_valid():
    """Test that npm.toml is valid TOML and has correct structure."""
    pattern_file = Path('src/logsift/patterns/defaults/npm.toml')
    assert pattern_file.exists()

    with pattern_file.open('rb') as f:
        data = tomllib.load(f)

    assert 'patterns' in data
    patterns = data['patterns']
    assert len(patterns) > 0

    # Verify common NPM error patterns exist
    pattern_names = [p['name'] for p in patterns]
    assert 'npm_package_not_found' in pattern_names
    assert 'npm_permission_denied' in pattern_names


def test_cargo_patterns_valid():
    """Test that cargo.toml is valid TOML and has correct structure."""
    pattern_file = Path('src/logsift/patterns/defaults/cargo.toml')
    assert pattern_file.exists()

    with pattern_file.open('rb') as f:
        data = tomllib.load(f)

    assert 'patterns' in data
    patterns = data['patterns']
    assert len(patterns) > 0

    # Verify common Rust/Cargo error patterns exist
    pattern_names = [p['name'] for p in patterns]
    assert 'cargo_compilation_error' in pattern_names
    assert 'cargo_missing_crate' in pattern_names


def test_make_patterns_valid():
    """Test that make.toml is valid TOML and has correct structure."""
    pattern_file = Path('src/logsift/patterns/defaults/make.toml')
    assert pattern_file.exists()

    with pattern_file.open('rb') as f:
        data = tomllib.load(f)

    assert 'patterns' in data
    patterns = data['patterns']
    assert len(patterns) > 0

    # Verify common Make error patterns exist
    pattern_names = [p['name'] for p in patterns]
    assert 'make_no_rule_to_make_target' in pattern_names
    assert 'make_missing_separator' in pattern_names


def test_pytest_patterns_valid():
    """Test that pytest.toml is valid TOML and has correct structure."""
    pattern_file = Path('src/logsift/patterns/defaults/pytest.toml')
    assert pattern_file.exists()

    with pattern_file.open('rb') as f:
        data = tomllib.load(f)

    assert 'patterns' in data
    patterns = data['patterns']
    assert len(patterns) > 0

    # Verify common pytest error patterns exist
    pattern_names = [p['name'] for p in patterns]
    assert 'pytest_test_failed' in pattern_names
    assert 'pytest_assertion_error' in pattern_names


def test_all_pattern_files_exist():
    """Test that all expected pattern files exist."""
    pattern_dir = Path('src/logsift/patterns/defaults')
    assert pattern_dir.exists()

    expected_files = [
        'common.toml',
        'brew.toml',
        'apt.toml',
        'docker.toml',
        'npm.toml',
        'cargo.toml',
        'make.toml',
        'pytest.toml',
        'http.toml',
        'shell.toml',
    ]

    for filename in expected_files:
        pattern_file = pattern_dir / filename
        assert pattern_file.exists(), f'Missing pattern file: {filename}'


def test_pattern_uniqueness():
    """Test that pattern names are unique within each file."""
    pattern_dir = Path('src/logsift/patterns/defaults')

    for pattern_file in pattern_dir.glob('*.toml'):
        with pattern_file.open('rb') as f:
            data = tomllib.load(f)

        if 'patterns' not in data:
            continue

        pattern_names = [p['name'] for p in data['patterns']]
        unique_names = set(pattern_names)

        assert len(pattern_names) == len(unique_names), f'Duplicate pattern names in {pattern_file.name}'


def test_pattern_tags_are_lists():
    """Test that all pattern tags are lists."""
    pattern_dir = Path('src/logsift/patterns/defaults')

    for pattern_file in pattern_dir.glob('*.toml'):
        with pattern_file.open('rb') as f:
            data = tomllib.load(f)

        if 'patterns' not in data:
            continue

        for pattern in data['patterns']:
            assert isinstance(pattern['tags'], list), f'Tags must be list in {pattern["name"]}'
            assert len(pattern['tags']) > 0, f'Tags cannot be empty in {pattern["name"]}'


def test_pattern_severity_valid():
    """Test that all patterns have valid severity levels."""
    pattern_dir = Path('src/logsift/patterns/defaults')
    valid_severities = {'error', 'warning', 'info'}

    for pattern_file in pattern_dir.glob('*.toml'):
        with pattern_file.open('rb') as f:
            data = tomllib.load(f)

        if 'patterns' not in data:
            continue

        for pattern in data['patterns']:
            severity = pattern['severity']
            assert severity in valid_severities, f"Invalid severity '{severity}' in {pattern['name']}"


def test_docker_image_not_found_pattern():
    """Test specific Docker pattern regex."""
    import re

    pattern_file = Path('src/logsift/patterns/defaults/docker.toml')
    with pattern_file.open('rb') as f:
        data = tomllib.load(f)

    # Find the pattern
    pattern = next((p for p in data['patterns'] if p['name'] == 'docker_image_not_found'), None)
    assert pattern is not None

    # Test the regex
    test_line = 'Error response from daemon: pull access denied for myimage, repository does not exist'
    match = re.search(pattern['regex'], test_line)
    assert match is not None


def test_npm_package_not_found_pattern():
    """Test specific NPM pattern regex."""
    import re

    pattern_file = Path('src/logsift/patterns/defaults/npm.toml')
    with pattern_file.open('rb') as f:
        data = tomllib.load(f)

    # Find the pattern
    pattern = next((p for p in data['patterns'] if p['name'] == 'npm_package_not_found'), None)
    assert pattern is not None

    # Test the regex
    test_line = "npm ERR! 404  '@mycompany/nonexistent-package' is not in the npm registry"
    match = re.search(pattern['regex'], test_line)
    assert match is not None


def test_cargo_compilation_error_pattern():
    """Test specific Cargo pattern regex."""
    import re

    pattern_file = Path('src/logsift/patterns/defaults/cargo.toml')
    with pattern_file.open('rb') as f:
        data = tomllib.load(f)

    # Find the pattern
    pattern = next((p for p in data['patterns'] if p['name'] == 'cargo_compilation_error'), None)
    assert pattern is not None

    # Test the regex
    test_line = 'error[E0425]: cannot find value `foo` in this scope'
    match = re.search(pattern['regex'], test_line)
    assert match is not None


def test_make_no_rule_pattern():
    """Test specific Make pattern regex."""
    import re

    pattern_file = Path('src/logsift/patterns/defaults/make.toml')
    with pattern_file.open('rb') as f:
        data = tomllib.load(f)

    # Find the pattern
    pattern = next((p for p in data['patterns'] if p['name'] == 'make_no_rule_to_make_target'), None)
    assert pattern is not None

    # Test the regex
    test_line = "make: *** No rule to make target `build'"
    match = re.search(pattern['regex'], test_line)
    assert match is not None


def test_pytest_test_failed_pattern():
    """Test specific pytest pattern regex."""
    import re

    pattern_file = Path('src/logsift/patterns/defaults/pytest.toml')
    with pattern_file.open('rb') as f:
        data = tomllib.load(f)

    # Find the pattern
    pattern = next((p for p in data['patterns'] if p['name'] == 'pytest_test_failed'), None)
    assert pattern is not None

    # Test the regex
    test_line = 'FAILED tests/test_example.py::test_function - AssertionError: assert False'
    match = re.search(pattern['regex'], test_line)
    assert match is not None


def test_http_patterns_valid():
    """Test that http.toml is valid TOML and has correct structure."""
    pattern_file = Path('src/logsift/patterns/defaults/http.toml')
    assert pattern_file.exists()

    with pattern_file.open('rb') as f:
        data = tomllib.load(f)

    assert 'patterns' in data
    patterns = data['patterns']
    assert len(patterns) > 0

    # Verify common HTTP error patterns exist
    pattern_names = [p['name'] for p in patterns]
    assert 'http_404_not_found' in pattern_names
    assert 'http_500_internal_server_error' in pattern_names
    assert 'connection_refused' in pattern_names


def test_http_404_pattern():
    """Test HTTP 404 pattern regex."""
    import re

    pattern_file = Path('src/logsift/patterns/defaults/http.toml')
    with pattern_file.open('rb') as f:
        data = tomllib.load(f)

    # Find the pattern
    pattern = next((p for p in data['patterns'] if p['name'] == 'http_404_not_found'), None)
    assert pattern is not None

    # Test the regex with various formats
    test_lines = [
        'HTTP 404 Not Found',
        'Error: 404',
        'could not GET url: HTTP status client error (404 Not Found)',
    ]
    for test_line in test_lines:
        match = re.search(pattern['regex'], test_line, re.IGNORECASE)
        assert match is not None, f'Pattern should match: {test_line}'


def test_http_500_pattern():
    """Test HTTP 500 pattern regex."""
    import re

    pattern_file = Path('src/logsift/patterns/defaults/http.toml')
    with pattern_file.open('rb') as f:
        data = tomllib.load(f)

    # Find the pattern
    pattern = next((p for p in data['patterns'] if p['name'] == 'http_500_internal_server_error'), None)
    assert pattern is not None

    # Test the regex
    test_lines = [
        'HTTP 500 Internal Server Error',
        'Error: 500',
        'Server returned 500',
    ]
    for test_line in test_lines:
        match = re.search(pattern['regex'], test_line, re.IGNORECASE)
        assert match is not None, f'Pattern should match: {test_line}'


def test_connection_refused_pattern():
    """Test connection refused pattern regex."""
    import re

    pattern_file = Path('src/logsift/patterns/defaults/http.toml')
    with pattern_file.open('rb') as f:
        data = tomllib.load(f)

    # Find the pattern
    pattern = next((p for p in data['patterns'] if p['name'] == 'connection_refused'), None)
    assert pattern is not None

    # Test the regex
    test_lines = [
        'connection refused',
        'could not connect to server',
        'Connection refused',
    ]
    for test_line in test_lines:
        match = re.search(pattern['regex'], test_line, re.IGNORECASE)
        assert match is not None, f'Pattern should match: {test_line}'


def test_test_failed_marker_pattern():
    """Test cross mark test failure pattern regex."""
    import re

    pattern_file = Path('src/logsift/patterns/defaults/common.toml')
    with pattern_file.open('rb') as f:
        data = tomllib.load(f)

    # Find the pattern
    pattern = next((p for p in data['patterns'] if p['name'] == 'test_failed_cross_mark'), None)
    assert pattern is not None

    # Test the regex with ANSI-stripped lines
    test_lines = [
        '✗ notes help FAILED: notes --help',
        '✗ ZDOTDIR set FAILED: test -n "$ZDOTDIR"',
    ]
    for test_line in test_lines:
        match = re.search(pattern['regex'], test_line)
        assert match is not None, f'Pattern should match: {test_line}'


def test_test_summary_failures_pattern():
    """Test test summary with failures pattern regex."""
    import re

    pattern_file = Path('src/logsift/patterns/defaults/common.toml')
    with pattern_file.open('rb') as f:
        data = tomllib.load(f)

    # Find the pattern
    pattern = next((p for p in data['patterns'] if p['name'] == 'test_suite_failures'), None)
    assert pattern is not None

    # Test the regex
    test_lines = [
        'FAILURES: 28 passed, 2 failed',
        'failures: 10 passed, 5 failed',
    ]
    for test_line in test_lines:
        match = re.search(pattern['regex'], test_line, re.IGNORECASE)
        assert match is not None, f'Pattern should match: {test_line}'


def test_shell_patterns_valid():
    """Test that shell.toml is valid TOML and has correct structure."""
    pattern_file = Path('src/logsift/patterns/defaults/shell.toml')
    assert pattern_file.exists()

    with pattern_file.open('rb') as f:
        data = tomllib.load(f)

    assert 'patterns' in data
    patterns = data['patterns']
    assert len(patterns) > 0

    # Verify shell-specific patterns exist (not test patterns - those moved to common.toml)
    pattern_names = [p['name'] for p in patterns]
    assert 'bash_command_not_found' in pattern_names
    assert 'shell_no_such_file' in pattern_names
    assert 'segmentation_fault' in pattern_names


def test_shell_command_not_found_pattern():
    """Test shell command not found pattern regex."""
    import re

    pattern_file = Path('src/logsift/patterns/defaults/shell.toml')
    with pattern_file.open('rb') as f:
        data = tomllib.load(f)

    # Find the pattern
    pattern = next((p for p in data['patterns'] if p['name'] == 'bash_command_not_found'), None)
    assert pattern is not None

    # Test the regex
    test_line = 'bash: foo: command not found'
    match = re.search(pattern['regex'], test_line)
    assert match is not None


def test_common_patterns_include_tests():
    """Test that common.toml includes universal test patterns."""
    pattern_file = Path('src/logsift/patterns/defaults/common.toml')
    with pattern_file.open('rb') as f:
        data = tomllib.load(f)

    pattern_names = [p['name'] for p in data['patterns']]
    assert 'test_failed_cross_mark' in pattern_names
    assert 'test_suite_failures' in pattern_names
