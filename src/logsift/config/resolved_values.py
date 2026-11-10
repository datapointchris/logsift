"""What `logsift config` prints: each resolved value beside the layer that set it.

Each option row is read from a Click context built the way the command itself would build it, so
the value and its source are the ones the command would get, not a second walk of the layers.
"""

from typing import NamedTuple

import click
from click.core import ParameterSource

from logsift import xdg_dirs
from logsift.config.loader import FILE_KEYS

# Every option that resolves through a layer, as its command path then its parameter name.
RESOLVED_OPTIONS = (
    ('monitor', 'format'),
    ('monitor', 'update_interval'),
    ('monitor', 'name'),
    ('analyze', 'format'),
    ('logs', 'clean', 'days'),
    ('analyzed', 'clean', 'days'),
)

# What an option left unset does, where that is something other than a value.
UNSET_MEANS: dict[tuple[str, ...], str] = {('monitor', 'name'): 'named after the command'}


class ResolvedValue(NamedTuple):
    setting: str
    value: str
    source: str
    file_key: str


def file_key_for(option: tuple[str, ...]) -> str:
    return next((key for key, file_key in FILE_KEYS.items() if option in file_key.sets), '-')


def resolve_option(root_ctx: click.Context, option: tuple[str, ...]) -> ResolvedValue:
    *command_path, parameter_name = option
    ctx = root_ctx
    for name in command_path:
        group = ctx.command
        command = group.get_command(ctx, name) if isinstance(group, click.Group) else None
        if command is None:
            raise LookupError(f'{group.name} has no subcommand {name}')
        ctx = command.make_context(name, [], parent=ctx)
    param = next(param for param in ctx.command.params if param.name == parameter_name)
    source = ctx.get_parameter_source(parameter_name)
    value = ctx.params[parameter_name]
    labels = {
        ParameterSource.COMMANDLINE: max(param.opts, key=len),
        ParameterSource.ENVIRONMENT: f'${param.envvar}',
        ParameterSource.DEFAULT_MAP: 'config.toml',
        ParameterSource.DEFAULT: 'default',
    }
    return ResolvedValue(
        setting=f'{" ".join(command_path)} {max(param.opts, key=len)}',
        value=UNSET_MEANS.get(option, 'unset') if value is None else str(value),
        # A source added to Click and missing here prints its own name rather than a wrong layer.
        source=labels.get(source, source.name.lower()) if source else 'unknown',
        file_key=file_key_for(option),
    )


def resolve_locations() -> list[ResolvedValue]:
    """The files and directories logsift reads and writes, each moved only by its XDG variable."""
    config_file = xdg_dirs.config_file()
    config = xdg_dirs.resolve_dir('config')
    cache = xdg_dirs.resolve_dir('cache')
    file_state = '' if config_file.exists() else ' (absent)'
    return [
        ResolvedValue('config file', f'{config_file}{file_state}', config.source, '-'),
        ResolvedValue('custom patterns', str(xdg_dirs.custom_patterns_dir()), config.source, '-'),
        ResolvedValue('cache', str(cache.path), cache.source, '-'),
    ]


def resolve_options(root_ctx: click.Context) -> list[ResolvedValue]:
    """Every option that resolves through a layer, given the root context carrying config.toml as its default_map."""
    return [resolve_option(root_ctx, option) for option in RESOLVED_OPTIONS]
