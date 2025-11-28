"""Tests for configuration loader."""

import tempfile
from pathlib import Path

from logsift.config.defaults import DEFAULT_CONFIG
from logsift.config.loader import load_config


def test_load_config_with_no_file():
    """Test loading config when no file exists returns defaults."""
    config = load_config(Path('/nonexistent/config.toml'))

    assert config is not None
    assert 'general' in config
    assert 'output' in config
    assert config['output']['context_lines'] == 2


def test_load_config_with_none_uses_default_path():
    """Test loading config with None checks default location."""
    # Should not raise even if default location doesn't exist
    config = load_config(None)

    assert config is not None
    assert 'general' in config


def test_load_config_returns_copy_of_defaults():
    """Test that load_config returns a copy, not the original DEFAULT_CONFIG."""
    config1 = load_config(Path('/nonexistent/config.toml'))
    config2 = load_config(Path('/nonexistent/config.toml'))

    # Modify one
    config1['output']['context_lines'] = 999

    # Should not affect the other or the defaults
    assert config2['output']['context_lines'] == 2
    assert DEFAULT_CONFIG['output']['context_lines'] == 2


def test_load_config_with_partial_override():
    """Test loading config that partially overrides defaults."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
        f.write('[output]\n')
        f.write('context_lines = 5\n')
        f.write('use_colors = false\n')
        config_path = Path(f.name)

    try:
        config = load_config(config_path)

        # Overridden values
        assert config['output']['context_lines'] == 5
        assert config['output']['use_colors'] is False

        # Default values that weren't overridden
        assert config['output']['use_emoji'] is True
        assert config['summary']['max_errors'] == 10
    finally:
        config_path.unlink()


def test_load_config_with_complete_section():
    """Test loading config that completely overrides a section."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
        f.write('[summary]\n')
        f.write('max_errors = 20\n')
        f.write('max_warnings = 10\n')
        f.write('show_line_numbers = false\n')
        f.write('show_context = false\n')
        f.write('show_suggestions = false\n')
        f.write('deduplicate_errors = false\n')
        config_path = Path(f.name)

    try:
        config = load_config(config_path)

        # All summary values overridden
        assert config['summary']['max_errors'] == 20
        assert config['summary']['max_warnings'] == 10
        assert config['summary']['show_line_numbers'] is False

        # Other sections still have defaults
        assert config['output']['context_lines'] == 2
    finally:
        config_path.unlink()


def test_load_config_with_new_section():
    """Test loading config that adds a new section not in defaults."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
        f.write('[custom_section]\n')
        f.write('custom_key = "custom_value"\n')
        config_path = Path(f.name)

    try:
        config = load_config(config_path)

        # New section should be added
        assert 'custom_section' in config
        assert config['custom_section']['custom_key'] == 'custom_value'

        # Defaults still present
        assert 'output' in config
    finally:
        config_path.unlink()


def test_load_config_with_nested_values():
    """Test loading config with various data types."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
        f.write('[output]\n')
        f.write('context_lines = 10\n')
        f.write('use_colors = true\n')
        f.write('default_format = "json"\n')
        config_path = Path(f.name)

    try:
        config = load_config(config_path)

        assert config['output']['context_lines'] == 10
        assert config['output']['use_colors'] is True
        assert config['output']['default_format'] == 'json'
    finally:
        config_path.unlink()


def test_load_config_with_paths():
    """Test loading config with path values."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
        f.write('[general]\n')
        f.write('cache_dir = "/tmp/custom_cache"\n')
        config_path = Path(f.name)

    try:
        config = load_config(config_path)

        # Path should be loaded as string or Path
        cache_dir = config['general']['cache_dir']
        assert '/tmp/custom_cache' in str(cache_dir)
    finally:
        config_path.unlink()


def test_load_config_preserves_all_defaults():
    """Test that all default sections and keys are preserved."""
    config = load_config(Path('/nonexistent/config.toml'))

    # Check all default sections exist
    expected_sections = ['general', 'output', 'summary', 'patterns', 'notifications', 'cleanup', 'monitor', 'watch']

    for section in expected_sections:
        assert section in config, f'Section {section} missing from loaded config'


def test_load_config_handles_invalid_toml():
    """Test loading config handles invalid TOML gracefully."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
        f.write('this is not valid TOML [[[\n')
        config_path = Path(f.name)

    try:
        # Should fall back to defaults rather than crashing
        config = load_config(config_path)

        # Should still have defaults
        assert 'output' in config
        assert config['output']['context_lines'] == 2
    finally:
        config_path.unlink()


def test_load_config_with_empty_file():
    """Test loading config from an empty file returns defaults."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
        # Write nothing
        config_path = Path(f.name)

    try:
        config = load_config(config_path)

        # Should have all defaults
        assert config['output']['context_lines'] == 2
        assert config['summary']['max_errors'] == 10
    finally:
        config_path.unlink()


def test_load_config_multiple_sections():
    """Test loading config that overrides multiple sections."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
        f.write('[output]\n')
        f.write('context_lines = 5\n')
        f.write('\n')
        f.write('[summary]\n')
        f.write('max_errors = 15\n')
        f.write('\n')
        f.write('[monitor]\n')
        f.write('show_progress = false\n')
        config_path = Path(f.name)

    try:
        config = load_config(config_path)

        # All overridden values
        assert config['output']['context_lines'] == 5
        assert config['summary']['max_errors'] == 15
        assert config['monitor']['show_progress'] is False

        # Other defaults preserved
        assert config['output']['use_emoji'] is True
        assert config['summary']['max_warnings'] == 5
    finally:
        config_path.unlink()
