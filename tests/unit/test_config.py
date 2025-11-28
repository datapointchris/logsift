"""Unit tests for configuration system."""

from logsift.config.defaults import DEFAULT_CONFIG


def test_default_config_structure():
    """Test that default config has expected structure."""
    assert 'general' in DEFAULT_CONFIG
    assert 'output' in DEFAULT_CONFIG
    assert 'patterns' in DEFAULT_CONFIG
    assert 'monitor' in DEFAULT_CONFIG


def test_default_config_general_settings():
    """Test general configuration defaults."""
    assert DEFAULT_CONFIG['general']['default_interval'] == 60


def test_default_config_output_settings():
    """Test output configuration defaults."""
    assert DEFAULT_CONFIG['output']['default_format'] == 'auto'
    assert DEFAULT_CONFIG['output']['use_colors'] is True
    assert DEFAULT_CONFIG['output']['context_lines'] == 2
