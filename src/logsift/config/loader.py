"""Load and merge configuration from TOML files.

Handles loading from ~/.config/logsift/config.toml and merging with defaults.
"""

from pathlib import Path
from typing import Any


def load_config(config_file: Path | None = None) -> dict[str, Any]:
    """Load configuration from file and merge with defaults.

    Args:
        config_file: Optional path to config file (defaults to ~/.config/logsift/config.toml)

    Returns:
        Merged configuration dictionary
    """
    raise NotImplementedError('Config loading not yet implemented')
