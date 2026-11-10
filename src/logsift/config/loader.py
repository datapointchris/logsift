"""The user's config.toml: read whole or refused, then handed to Click as its default_map.

Click resolves an option from its flag, then its environment variable, then the default_map,
then the option's own default. Loading the file into the default_map is the whole file layer, so
the precedence and the source `logsift config` reports both come from Click and cannot drift.
"""

import tomllib
from collections.abc import Iterator
from pathlib import Path
from typing import Any
from typing import NamedTuple

from logsift.output.analysis_format import AnalysisFormat


class FileKey(NamedTuple):
    toml_type: type
    # Each option the key sets, as its command path then the option's parameter name.
    sets: tuple[tuple[str, ...], ...]
    # The values the options accept, where they accept a fixed set.
    allowed: tuple[str, ...] = ()


# Every key config.toml may carry.
FILE_KEYS = {
    'print_analysis_as': FileKey(str, (('monitor', 'format'), ('analyze', 'format')), tuple(AnalysisFormat)),
    'monitor.report_progress_every_seconds': FileKey(int, (('monitor', 'update_interval'),)),
    'logs.clean.delete_older_than_days': FileKey(int, (('logs', 'clean', 'days'),)),
    'analyzed.clean.delete_older_than_days': FileKey(int, (('analyzed', 'clean', 'days'),)),
}


class ConfigError(Exception):
    """A config.toml that exists and cannot be honored."""


def leaf_keys(table: dict[str, Any], prefix: str = '') -> Iterator[tuple[str, Any]]:
    """Yield each value in a parsed TOML document under its dotted key."""
    for key, value in table.items():
        if isinstance(value, dict):
            yield from leaf_keys(value, f'{prefix}{key}.')
        else:
            yield f'{prefix}{key}', value


def load_user_config(path: Path) -> dict[str, Any]:
    """Return config.toml's values by dotted key, or nothing when the file is absent.

    A present file is honored whole or refused. A key left under an old name would otherwise
    leave its setting on the default in silence, which reads exactly like a file that never set it.
    """
    if not path.exists():
        return {}
    try:
        parsed = tomllib.loads(path.read_text())
    except (tomllib.TOMLDecodeError, OSError) as exc:
        raise ConfigError(f'{path}: {exc}') from exc
    values = dict(leaf_keys(parsed))
    unknown = sorted(set(values) - set(FILE_KEYS))
    if unknown:
        raise ConfigError(f'{path}: unknown key(s) {", ".join(unknown)}; known: {", ".join(FILE_KEYS)}')
    for key, value in values.items():
        expected = FILE_KEYS[key].toml_type
        # TOML's true and false are ints to Python, and neither is a count of anything.
        if not isinstance(value, expected) or (expected is int and isinstance(value, bool)):
            raise ConfigError(f'{path}: {key} must be a TOML {expected.__name__}, not {value!r}')
        allowed = FILE_KEYS[key].allowed
        if allowed and value not in allowed:
            raise ConfigError(f'{path}: {key} must be one of {", ".join(allowed)}, not {value!r}')
    return values


def default_map(values: dict[str, Any]) -> dict[str, Any]:
    """Nest config.toml's values by command, the shape Click's default_map reads."""
    nested: dict[str, Any] = {}
    for key, value in values.items():
        for *command_path, parameter in FILE_KEYS[key].sets:
            scope = nested
            for command in command_path:
                scope = scope.setdefault(command, {})
            scope[parameter] = value
    return nested
