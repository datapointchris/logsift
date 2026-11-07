"""logsift's config and cache directories, resolved by the XDG Base Directory specification.

Hand-edited settings and custom patterns are config, read from `$XDG_CONFIG_HOME/logsift`.
Captured logs and saved analyses cost only a re-run to rebuild, so they are cache, written to
`$XDG_CACHE_HOME/logsift`. Each variable falls back to its standard home-relative path when it is
unset, empty or relative, as the specification requires.
"""

import os
from pathlib import Path

APP_NAME = 'logsift'


def _base_dir(variable: str, fallback: str) -> Path:
    value = os.environ.get(variable, '')
    if value and Path(value).is_absolute():
        return Path(value)
    return Path.home() / fallback


def config_dir() -> Path:
    """Return logsift's config directory: `$XDG_CONFIG_HOME/logsift`, else `~/.config/logsift`."""
    return _base_dir('XDG_CONFIG_HOME', '.config') / APP_NAME


def cache_dir() -> Path:
    """Return logsift's cache directory: `$XDG_CACHE_HOME/logsift`, else `~/.cache/logsift`."""
    return _base_dir('XDG_CACHE_HOME', '.cache') / APP_NAME
