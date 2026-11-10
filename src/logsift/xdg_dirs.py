"""logsift's config and cache directories, resolved by the XDG Base Directory specification.

Hand-edited settings and custom patterns are config, read from `$XDG_CONFIG_HOME/logsift`.
Captured logs and saved analyses cost only a re-run to rebuild, so they are cache, written to
`$XDG_CACHE_HOME/logsift`. Each variable falls back to its standard home-relative path when it is
unset, empty or relative, as the specification requires.
"""

import os
from pathlib import Path
from typing import NamedTuple

APP_NAME = 'logsift'

# Each base directory logsift resolves: the variable that moves it, and its home-relative fallback.
BASE_DIRS = {
    'config': ('XDG_CONFIG_HOME', '.config'),
    'cache': ('XDG_CACHE_HOME', '.cache'),
}


class ResolvedDir(NamedTuple):
    path: Path
    # The layer that answered: `$XDG_CONFIG_HOME`, `$XDG_CACHE_HOME` or `default`.
    source: str


def resolve_dir(kind: str) -> ResolvedDir:
    """Return logsift's directory of this kind, and which layer set it."""
    variable, fallback = BASE_DIRS[kind]
    value = os.environ.get(variable, '')
    if value and Path(value).is_absolute():
        return ResolvedDir(Path(value) / APP_NAME, f'${variable}')
    return ResolvedDir(Path.home() / fallback / APP_NAME, 'default')


def config_dir() -> Path:
    """Return logsift's config directory: `$XDG_CONFIG_HOME/logsift`, else `~/.config/logsift`."""
    return resolve_dir('config').path


def cache_dir() -> Path:
    """Return logsift's cache directory: `$XDG_CACHE_HOME/logsift`, else `~/.cache/logsift`."""
    return resolve_dir('cache').path


def config_file() -> Path:
    """Return the user's config file, which may not exist."""
    return config_dir() / 'config.toml'


def custom_patterns_dir() -> Path:
    """Return the directory whose `*.toml` pattern files run before the built-in ones."""
    return config_dir() / 'patterns'
