"""Load and merge configuration from TOML files.

Handles loading from ~/.config/logsift/config.toml and merging with defaults.
"""

import copy
import tomllib
from pathlib import Path
from typing import Any

from logsift.config.defaults import DEFAULT_CONFIG


def load_config(config_file: Path | None = None) -> dict[str, Any]:
    """Load configuration from file and merge with defaults.

    Args:
        config_file: Optional path to config file (defaults to ~/.config/logsift/config.toml)

    Returns:
        Merged configuration dictionary
    """
    # Start with a deep copy of defaults
    config = copy.deepcopy(DEFAULT_CONFIG)

    # Determine config file path
    if config_file is None:
        config_file = Path.home() / '.config' / 'logsift' / 'config.toml'

    # If config file doesn't exist, return defaults
    if not config_file.exists():
        return config

    # Load TOML config
    try:
        with config_file.open('rb') as f:
            user_config = tomllib.load(f)
    except (tomllib.TOMLDecodeError, OSError):
        # If there's an error reading/parsing, return defaults
        return config

    # Merge user config into defaults
    _deep_merge(config, user_config)

    return config


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> None:
    """Recursively merge override dict into base dict.

    Args:
        base: Base dictionary (will be modified in-place)
        override: Override dictionary to merge in
    """
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            # Recursively merge nested dicts
            _deep_merge(base[key], value)
        else:
            # Override the value
            base[key] = value
