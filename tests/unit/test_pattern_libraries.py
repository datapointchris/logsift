"""Tests for pattern library files."""

import re
import tomllib
from pathlib import Path


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


def test_pattern_file_structure():
    """Test that all pattern files have correct TOML structure."""
    pattern_dir = Path('src/logsift/patterns/defaults')

    for pattern_file in pattern_dir.glob('*.toml'):
        with pattern_file.open('rb') as f:
            data = tomllib.load(f)

        assert 'patterns' in data, f'{pattern_file.name} missing patterns key'
        patterns = data['patterns']
        assert len(patterns) > 0, f'{pattern_file.name} has no patterns'

        # Check first pattern has required fields
        first_pattern = patterns[0]
        required_fields = ['name', 'regex', 'severity', 'description', 'tags']
        for field in required_fields:
            assert field in first_pattern, f'{pattern_file.name} pattern missing {field}'


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


def test_pattern_regex_example():
    """Test that pattern regexes are valid and can match expected text.

    This is a sanity check, not comprehensive testing of every pattern.
    The real test is whether IssueDetector can use them correctly.
    """
    pattern_file = Path('src/logsift/patterns/defaults/shell.toml')
    with pattern_file.open('rb') as f:
        data = tomllib.load(f)

    # Find bash command not found pattern as example
    pattern = next((p for p in data['patterns'] if p['name'] == 'bash_command_not_found'), None)
    assert pattern is not None

    # Test the regex works
    test_line = 'bash: unzip: command not found'
    match = re.search(pattern['regex'], test_line)
    assert match is not None
