"""Unit tests for the pattern matching system."""

from logsift.patterns.matcher import match_patterns

# Basic Pattern Matching Tests


def test_match_patterns_simple_match():
    """Test matching a simple error pattern."""
    log_entry = {'message': 'Error: Connection failed', 'line_number': 1}
    patterns = {
        'common': [
            {
                'name': 'generic_error',
                'regex': r'(?i)(error|failed):\s*(.+)',
                'severity': 'error',
                'description': 'Generic error pattern',
                'tags': ['generic', 'error'],
            }
        ]
    }
    match = match_patterns(log_entry, patterns)

    assert match is not None
    assert match['pattern_name'] == 'generic_error'
    assert match['severity'] == 'error'
    assert match['description'] == 'Generic error pattern'
    assert match['tags'] == ['generic', 'error']


def test_match_patterns_with_suggestion():
    """Test that suggestions are included when present in pattern."""
    log_entry = {'message': 'Error: tmux is already installed', 'line_number': 1}
    patterns = {
        'brew': [
            {
                'name': 'brew_package_already_installed',
                'regex': r'Error:\s*(.+)\s+is already installed',
                'severity': 'error',
                'description': 'Package is already installed',
                'tags': ['brew', 'package_conflict'],
                'suggestion': "Remove package from install list or use 'brew upgrade' instead",
            }
        ]
    }
    match = match_patterns(log_entry, patterns)

    assert match is not None
    assert match['pattern_name'] == 'brew_package_already_installed'
    assert match['suggestion'] == "Remove package from install list or use 'brew upgrade' instead"


def test_match_patterns_no_match():
    """Test that None is returned when no pattern matches."""
    log_entry = {'message': 'INFO: Everything is fine', 'line_number': 1}
    patterns = {
        'common': [
            {
                'name': 'generic_error',
                'regex': r'(?i)(error|failed):\s*(.+)',
                'severity': 'error',
                'description': 'Generic error',
                'tags': ['error'],
            }
        ]
    }
    match = match_patterns(log_entry, patterns)

    assert match is None


def test_match_patterns_case_insensitive():
    """Test that pattern matching is case insensitive."""
    log_entry = {'message': 'ERROR: Something went wrong', 'line_number': 1}
    patterns = {
        'common': [
            {'name': 'generic_error', 'regex': r'(?i)error:\s*(.+)', 'severity': 'error', 'description': 'Generic error', 'tags': ['error']}
        ]
    }
    match = match_patterns(log_entry, patterns)

    assert match is not None
    assert match['pattern_name'] == 'generic_error'


# Multiple Pattern Tests


def test_match_patterns_first_match_wins():
    """Test that the first matching pattern is returned."""
    log_entry = {'message': 'Error: Connection failed', 'line_number': 1}
    patterns = {
        'common': [
            {
                'name': 'generic_error',
                'regex': r'(?i)error:\s*(.+)',
                'severity': 'error',
                'description': 'Generic error',
                'tags': ['error'],
            },
            {
                'name': 'connection_error',
                'regex': r'(?i)connection failed',
                'severity': 'error',
                'description': 'Connection error',
                'tags': ['network', 'error'],
            },
        ]
    }
    match = match_patterns(log_entry, patterns)

    # Should match the first pattern since it's checked first
    assert match is not None
    assert match['pattern_name'] == 'generic_error'


def test_match_patterns_across_multiple_categories():
    """Test matching patterns from multiple categories."""
    log_entry = {'message': 'Error: No available formula with the name "foobar"', 'line_number': 1}
    patterns = {
        'common': [
            {'name': 'generic_error', 'regex': r'(?i)error:\s*(.+)', 'severity': 'error', 'description': 'Generic error', 'tags': ['error']}
        ],
        'brew': [
            {
                'name': 'brew_formula_not_found',
                'regex': r'Error:\s*No available formula with the name "(.+)"',
                'severity': 'error',
                'description': 'Formula not found',
                'tags': ['brew', 'package_not_found'],
            }
        ],
    }
    match = match_patterns(log_entry, patterns)

    # Should match whichever category is checked first
    assert match is not None
    assert match['pattern_name'] in ('generic_error', 'brew_formula_not_found')


# Edge Cases


def test_match_patterns_empty_message():
    """Test matching against empty message."""
    log_entry = {'message': '', 'line_number': 1}
    patterns = {
        'common': [
            {'name': 'generic_error', 'regex': r'(?i)error:\s*(.+)', 'severity': 'error', 'description': 'Generic error', 'tags': ['error']}
        ]
    }
    match = match_patterns(log_entry, patterns)

    assert match is None


def test_match_patterns_no_patterns():
    """Test matching with empty patterns dict."""
    log_entry = {'message': 'Error: Something failed', 'line_number': 1}
    patterns = {}
    match = match_patterns(log_entry, patterns)

    assert match is None


def test_match_patterns_missing_message_field():
    """Test handling log entry without message field."""
    log_entry = {'level': 'ERROR', 'line_number': 1}
    patterns = {
        'common': [
            {'name': 'generic_error', 'regex': r'(?i)error:\s*(.+)', 'severity': 'error', 'description': 'Generic error', 'tags': ['error']}
        ]
    }
    match = match_patterns(log_entry, patterns)

    assert match is None


# Specific Pattern Tests


def test_match_patterns_permission_denied():
    """Test matching permission denied pattern."""
    log_entry = {'message': 'Permission denied: /etc/config', 'line_number': 1}
    patterns = {
        'common': [
            {
                'name': 'permission_denied',
                'regex': r'(?i)(permission denied|access denied):\s*(.+)',
                'severity': 'error',
                'description': 'Permission/access denied error',
                'tags': ['filesystem', 'permissions', 'error'],
            }
        ]
    }
    match = match_patterns(log_entry, patterns)

    assert match is not None
    assert match['pattern_name'] == 'permission_denied'
    assert 'permissions' in match['tags']


def test_match_patterns_file_not_found():
    """Test matching file not found pattern."""
    log_entry = {'message': 'No such file or directory: /tmp/missing.txt', 'line_number': 1}
    patterns = {
        'common': [
            {
                'name': 'file_not_found',
                'regex': r'(?i)(no such file or directory|file not found):\s*(.+)',
                'severity': 'error',
                'description': 'File not found error',
                'tags': ['filesystem', 'error'],
            }
        ]
    }
    match = match_patterns(log_entry, patterns)

    assert match is not None
    assert match['pattern_name'] == 'file_not_found'
    assert 'filesystem' in match['tags']


def test_match_patterns_warning():
    """Test matching warning patterns."""
    log_entry = {'message': 'Warning: Deprecated API usage', 'line_number': 1}
    patterns = {
        'common': [
            {
                'name': 'generic_warning',
                'regex': r'(?i)(warning|warn):\s*(.+)',
                'severity': 'warning',
                'description': 'Generic warning pattern',
                'tags': ['generic', 'warning'],
            }
        ]
    }
    match = match_patterns(log_entry, patterns)

    assert match is not None
    assert match['pattern_name'] == 'generic_warning'
    assert match['severity'] == 'warning'


# Integration with Real Patterns


def test_match_patterns_with_real_brew_pattern():
    """Test matching with real Homebrew pattern."""
    log_entry = {'message': "Error: Cask 'chrome' is unavailable", 'line_number': 1}
    patterns = {
        'brew': [
            {
                'name': 'brew_cask_not_found',
                'regex': r"Error:\s*Cask '(.+)' is unavailable",
                'severity': 'error',
                'description': 'Cask not found in Homebrew',
                'tags': ['brew', 'cask', 'package_not_found'],
                'suggestion': 'Check cask name or add tap',
            }
        ]
    }
    match = match_patterns(log_entry, patterns)

    assert match is not None
    assert match['pattern_name'] == 'brew_cask_not_found'
    assert match['suggestion'] == 'Check cask name or add tap'
    assert 'cask' in match['tags']


def test_match_patterns_preserves_all_pattern_fields():
    """Test that all pattern fields are preserved in match result."""
    log_entry = {'message': 'Error: Test error', 'line_number': 1}
    patterns = {
        'test': [
            {
                'name': 'test_pattern',
                'regex': r'Error: (.+)',
                'severity': 'error',
                'description': 'Test pattern',
                'tags': ['test', 'error'],
                'suggestion': 'Fix the test',
            }
        ]
    }
    match = match_patterns(log_entry, patterns)

    assert match is not None
    assert match['pattern_name'] == 'test_pattern'
    assert match['severity'] == 'error'
    assert match['description'] == 'Test pattern'
    assert match['tags'] == ['test', 'error']
    assert match['suggestion'] == 'Fix the test'


def test_match_patterns_without_suggestion_field():
    """Test that patterns without suggestions work correctly."""
    log_entry = {'message': 'Error: Test error', 'line_number': 1}
    patterns = {
        'test': [
            {'name': 'test_pattern', 'regex': r'Error: (.+)', 'severity': 'error', 'description': 'Test pattern', 'tags': ['test', 'error']}
        ]
    }
    match = match_patterns(log_entry, patterns)

    assert match is not None
    assert 'suggestion' not in match or match['suggestion'] is None
