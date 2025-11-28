"""Tests for pattern loader."""

import tempfile
from pathlib import Path

from logsift.patterns.loader import PatternLoader


def test_pattern_loader_initialization():
    """Test PatternLoader initialization."""
    loader = PatternLoader()
    assert loader.patterns == {}


def test_load_builtin_patterns():
    """Test loading built-in patterns."""
    loader = PatternLoader()
    patterns = loader.load_builtin_patterns()

    # Should have loaded at least the common patterns
    assert 'common' in patterns
    assert isinstance(patterns['common'], list)
    assert len(patterns['common']) > 0

    # Verify pattern structure
    first_pattern = patterns['common'][0]
    assert 'name' in first_pattern
    assert 'regex' in first_pattern
    assert 'severity' in first_pattern
    assert 'description' in first_pattern
    assert 'tags' in first_pattern


def test_load_builtin_patterns_stores_in_instance():
    """Test that builtin patterns are stored in instance."""
    loader = PatternLoader()
    loader.load_builtin_patterns()

    # Should be stored in instance
    assert 'common' in loader.patterns


def test_load_custom_patterns_from_directory():
    """Test loading custom patterns from a directory."""
    # Create temporary directory with pattern file
    with tempfile.TemporaryDirectory() as tmpdir:
        pattern_dir = Path(tmpdir)

        # Create a custom pattern file
        custom_pattern = """
[[patterns]]
name = "custom_error"
regex = "CUSTOM_ERROR: (.+)"
severity = "error"
description = "Custom error pattern"
tags = ["custom"]
"""
        pattern_file = pattern_dir / 'custom.toml'
        pattern_file.write_text(custom_pattern)

        # Load custom patterns
        loader = PatternLoader()
        patterns = loader.load_custom_patterns(pattern_dir)

        assert 'custom' in patterns
        assert len(patterns['custom']) == 1
        assert patterns['custom'][0]['name'] == 'custom_error'


def test_load_custom_patterns_stores_in_instance():
    """Test that custom patterns are stored in instance."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pattern_dir = Path(tmpdir)

        custom_pattern = """
[[patterns]]
name = "test_pattern"
regex = "TEST: (.+)"
severity = "warning"
description = "Test pattern"
tags = ["test"]
"""
        pattern_file = pattern_dir / 'test.toml'
        pattern_file.write_text(custom_pattern)

        loader = PatternLoader()
        loader.load_custom_patterns(pattern_dir)

        assert 'test' in loader.patterns


def test_load_custom_patterns_nonexistent_directory():
    """Test loading custom patterns from nonexistent directory."""
    loader = PatternLoader()
    patterns = loader.load_custom_patterns(Path('/nonexistent/path'))

    # Should return empty dict, not raise
    assert patterns == {}


def test_load_custom_patterns_skips_invalid_files():
    """Test that invalid pattern files are skipped."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pattern_dir = Path(tmpdir)

        # Create invalid pattern file
        invalid_pattern = """
[[patterns]]
name = "invalid"
# Missing required fields
"""
        pattern_file = pattern_dir / 'invalid.toml'
        pattern_file.write_text(invalid_pattern)

        loader = PatternLoader()
        patterns = loader.load_custom_patterns(pattern_dir)

        # Should skip invalid file and return empty
        assert patterns == {}


def test_load_pattern_file():
    """Test loading a single pattern file."""
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.toml', delete=False) as f:
        f.write("""
[[patterns]]
name = "test_error"
regex = "ERROR: (.+)"
severity = "error"
description = "Test error"
tags = ["test"]
""")
        pattern_path = Path(f.name)

    try:
        loader = PatternLoader()
        data = loader.load_pattern_file(pattern_path)

        assert 'patterns' in data
        assert len(data['patterns']) == 1
        assert data['patterns'][0]['name'] == 'test_error'
    finally:
        pattern_path.unlink()


def test_load_pattern_file_invalid_toml():
    """Test loading pattern file with invalid TOML."""
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.toml', delete=False) as f:
        f.write('[invalid toml content')
        pattern_path = Path(f.name)

    try:
        loader = PatternLoader()
        try:
            loader.load_pattern_file(pattern_path)
            raise AssertionError('Should have raised ValueError')
        except ValueError as e:
            assert 'Invalid TOML' in str(e)
    finally:
        pattern_path.unlink()


def test_get_all_patterns():
    """Test getting all loaded patterns."""
    loader = PatternLoader()
    loader.load_builtin_patterns()

    all_patterns = loader.get_all_patterns()

    # Should have common patterns
    assert 'common' in all_patterns
    assert isinstance(all_patterns, dict)

    # Should return a copy (modifying shouldn't affect original)
    all_patterns['test'] = []
    assert 'test' not in loader.patterns


def test_get_patterns_by_category():
    """Test getting patterns by specific category."""
    loader = PatternLoader()
    loader.load_builtin_patterns()

    common_patterns = loader.get_patterns_by_category('common')

    assert isinstance(common_patterns, list)
    assert len(common_patterns) > 0


def test_get_patterns_by_category_nonexistent():
    """Test getting patterns for nonexistent category."""
    loader = PatternLoader()

    patterns = loader.get_patterns_by_category('nonexistent')

    # Should return empty list
    assert patterns == []


def test_custom_patterns_merge_with_builtin():
    """Test that custom patterns merge with builtin patterns."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pattern_dir = Path(tmpdir)

        custom_pattern = """
[[patterns]]
name = "custom_pattern"
regex = "CUSTOM: (.+)"
severity = "info"
description = "Custom pattern"
tags = ["custom"]
"""
        pattern_file = pattern_dir / 'mycustom.toml'
        pattern_file.write_text(custom_pattern)

        loader = PatternLoader()
        loader.load_builtin_patterns()
        loader.load_custom_patterns(pattern_dir)

        # Should have both builtin and custom
        assert 'common' in loader.patterns
        assert 'mycustom' in loader.patterns


def test_load_pattern_file_with_suggestion():
    """Test loading pattern with optional suggestion field."""
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.toml', delete=False) as f:
        f.write("""
[[patterns]]
name = "test_error"
regex = "ERROR: (.+)"
severity = "error"
description = "Test error"
tags = ["test"]
suggestion = "Try fixing the error"
""")
        pattern_path = Path(f.name)

    try:
        loader = PatternLoader()
        data = loader.load_pattern_file(pattern_path)

        assert data['patterns'][0]['suggestion'] == 'Try fixing the error'
    finally:
        pattern_path.unlink()
