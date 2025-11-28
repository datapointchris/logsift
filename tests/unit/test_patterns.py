"""Unit tests for the pattern system."""

from pathlib import Path

import pytest

from logsift.patterns.loader import PatternLoader


def test_pattern_loader_initialization():
    """Test that pattern loader can be initialized."""
    loader = PatternLoader()
    assert loader is not None
    assert loader.patterns == {}


# Built-in Pattern Loading Tests


def test_load_builtin_patterns():
    """Test loading built-in pattern files."""
    loader = PatternLoader()
    patterns = loader.load_builtin_patterns()
    assert isinstance(patterns, dict)
    assert len(patterns) > 0
    # Should have patterns from common, brew, apt
    assert 'common' in patterns
    assert 'brew' in patterns
    assert 'apt' in patterns


def test_builtin_patterns_have_required_fields():
    """Test that built-in patterns have all required fields."""
    loader = PatternLoader()
    patterns = loader.load_builtin_patterns()
    for _category, pattern_list in patterns.items():
        assert isinstance(pattern_list, list)
        for pattern in pattern_list:
            assert 'name' in pattern
            assert 'regex' in pattern
            assert 'severity' in pattern
            assert 'description' in pattern
            assert 'tags' in pattern
            assert isinstance(pattern['tags'], list)


def test_builtin_patterns_optional_suggestion():
    """Test that suggestion field is optional in patterns."""
    loader = PatternLoader()
    patterns = loader.load_builtin_patterns()
    # Some patterns should have suggestions, some may not
    found_with_suggestion = False
    for _category, pattern_list in patterns.items():
        for pattern in pattern_list:
            if 'suggestion' in pattern:
                found_with_suggestion = True
                assert isinstance(pattern['suggestion'], str)

    assert found_with_suggestion  # At least one pattern should have a suggestion


# Individual Pattern File Loading Tests


def test_load_single_pattern_file(tmp_path: Path):
    """Test loading a single pattern file."""
    pattern_file = tmp_path / 'test.toml'
    pattern_file.write_text("""\
[[patterns]]
name = "test_error"
regex = "ERROR: (.+)"
severity = "error"
description = "Test error pattern"
tags = ["test", "error"]
""")

    loader = PatternLoader()
    patterns = loader.load_pattern_file(pattern_file)
    assert 'patterns' in patterns
    assert len(patterns['patterns']) == 1
    assert patterns['patterns'][0]['name'] == 'test_error'
    assert patterns['patterns'][0]['severity'] == 'error'


def test_load_pattern_file_with_suggestion(tmp_path: Path):
    """Test loading pattern file with suggestion field."""
    pattern_file = tmp_path / 'test.toml'
    pattern_file.write_text("""\
[[patterns]]
name = "test_error"
regex = "ERROR: (.+)"
severity = "error"
description = "Test error pattern"
tags = ["test"]
suggestion = "Fix the error"
""")

    loader = PatternLoader()
    patterns = loader.load_pattern_file(pattern_file)
    assert patterns['patterns'][0]['suggestion'] == 'Fix the error'


def test_load_pattern_file_multiple_patterns(tmp_path: Path):
    """Test loading pattern file with multiple patterns."""
    pattern_file = tmp_path / 'test.toml'
    pattern_file.write_text("""\
[[patterns]]
name = "error_1"
regex = "ERROR: (.+)"
severity = "error"
description = "First error"
tags = ["test"]

[[patterns]]
name = "warning_1"
regex = "WARNING: (.+)"
severity = "warning"
description = "First warning"
tags = ["test"]
""")

    loader = PatternLoader()
    patterns = loader.load_pattern_file(pattern_file)
    assert len(patterns['patterns']) == 2
    assert patterns['patterns'][0]['name'] == 'error_1'
    assert patterns['patterns'][1]['name'] == 'warning_1'


# Custom Pattern Directory Loading Tests


def test_load_custom_patterns_from_directory(tmp_path: Path):
    """Test loading custom patterns from a directory."""
    patterns_dir = tmp_path / 'patterns'
    patterns_dir.mkdir()

    # Create two pattern files
    (patterns_dir / 'custom1.toml').write_text("""\
[[patterns]]
name = "custom_error"
regex = "CUSTOM ERROR: (.+)"
severity = "error"
description = "Custom error"
tags = ["custom"]
""")

    (patterns_dir / 'custom2.toml').write_text("""\
[[patterns]]
name = "custom_warning"
regex = "CUSTOM WARNING: (.+)"
severity = "warning"
description = "Custom warning"
tags = ["custom"]
""")

    loader = PatternLoader()
    patterns = loader.load_custom_patterns(patterns_dir)
    assert isinstance(patterns, dict)
    assert 'custom1' in patterns
    assert 'custom2' in patterns
    assert len(patterns['custom1']) == 1
    assert len(patterns['custom2']) == 1


def test_load_custom_patterns_empty_directory(tmp_path: Path):
    """Test loading from empty custom patterns directory."""
    patterns_dir = tmp_path / 'empty_patterns'
    patterns_dir.mkdir()

    loader = PatternLoader()
    patterns = loader.load_custom_patterns(patterns_dir)
    assert isinstance(patterns, dict)
    assert len(patterns) == 0


def test_load_custom_patterns_nonexistent_directory(tmp_path: Path):
    """Test loading from non-existent directory returns empty dict."""
    patterns_dir = tmp_path / 'nonexistent'

    loader = PatternLoader()
    patterns = loader.load_custom_patterns(patterns_dir)
    assert isinstance(patterns, dict)
    assert len(patterns) == 0


# Error Handling Tests


def test_load_invalid_toml_file(tmp_path: Path):
    """Test that invalid TOML files are handled gracefully."""
    pattern_file = tmp_path / 'invalid.toml'
    pattern_file.write_text('this is not valid TOML [[')

    loader = PatternLoader()
    with pytest.raises((ValueError, Exception)):
        loader.load_pattern_file(pattern_file)


def test_load_pattern_file_missing_required_fields(tmp_path: Path):
    """Test that patterns missing required fields raise an error."""
    pattern_file = tmp_path / 'incomplete.toml'
    pattern_file.write_text("""\
[[patterns]]
name = "incomplete_pattern"
regex = "ERROR: (.+)"
# Missing severity, description, tags
""")

    loader = PatternLoader()
    with pytest.raises((KeyError, ValueError)):
        loader.load_pattern_file(pattern_file)


def test_load_pattern_file_empty_patterns_list(tmp_path: Path):
    """Test loading pattern file with no patterns."""
    pattern_file = tmp_path / 'empty.toml'
    pattern_file.write_text('# No patterns defined\n')

    loader = PatternLoader()
    patterns = loader.load_pattern_file(pattern_file)
    # Should return empty patterns list or empty dict
    assert patterns.get('patterns', []) == []


# Pattern Access and Retrieval Tests


def test_get_all_patterns_combines_builtin_and_custom(tmp_path: Path):
    """Test that get_all_patterns combines built-in and custom patterns."""
    patterns_dir = tmp_path / 'patterns'
    patterns_dir.mkdir()

    (patterns_dir / 'custom.toml').write_text("""\
[[patterns]]
name = "custom_error"
regex = "CUSTOM: (.+)"
severity = "error"
description = "Custom error"
tags = ["custom"]
""")

    loader = PatternLoader()
    loader.load_builtin_patterns()
    loader.load_custom_patterns(patterns_dir)

    all_patterns = loader.get_all_patterns()
    assert isinstance(all_patterns, dict)
    # Should have built-in categories
    assert 'common' in all_patterns
    assert 'brew' in all_patterns
    # Should have custom category
    assert 'custom' in all_patterns


def test_get_patterns_by_category():
    """Test retrieving patterns by category."""
    loader = PatternLoader()
    loader.load_builtin_patterns()

    brew_patterns = loader.get_patterns_by_category('brew')
    assert isinstance(brew_patterns, list)
    assert len(brew_patterns) > 0
    # All patterns should have brew tag
    for pattern in brew_patterns:
        assert 'brew' in pattern['tags']


def test_get_patterns_by_nonexistent_category():
    """Test retrieving patterns from non-existent category returns empty list."""
    loader = PatternLoader()
    loader.load_builtin_patterns()

    patterns = loader.get_patterns_by_category('nonexistent')
    assert patterns == []
