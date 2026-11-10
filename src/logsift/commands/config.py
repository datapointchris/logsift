"""Config subcommand implementation.

Prints logsift's locations, then every option that resolves through a layer, each as an aligned table.
"""

from collections.abc import Sequence

import click

from logsift.config.resolved_values import resolve_locations
from logsift.config.resolved_values import resolve_options


def print_table(rows: Sequence[Sequence[str]]) -> None:
    widths = [max(len(cell) for cell in column) for column in zip(*rows, strict=True)]
    for row in rows:
        print('  '.join(cell.ljust(width) for cell, width in zip(row, widths, strict=True)).rstrip())


def show_config(root_ctx: click.Context) -> None:
    print_table([('LOCATION', 'PATH', 'FROM'), *(row[:3] for row in resolve_locations())])
    print()
    print_table([('OPTION', 'VALUE', 'FROM', 'FILE KEY'), *resolve_options(root_ctx)])
