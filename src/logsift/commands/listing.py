"""What every `list` command prints: the saved files of one kind, newest first."""

import enum
import json
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from logsift.cache.manager import CacheManager
from logsift.cache.manager import SavedKind
from logsift.commands.find_saved_file import CAPTURE_HINT
from logsift.commands.find_saved_file import NOUNS
from logsift.utils.display import human_size

console = Console()
stderr_console = Console(stderr=True)


class ListFormat(enum.StrEnum):
    TABLE = 'table'
    JSON = 'json'
    PLAIN = 'plain'


ListFormatOption = Annotated[
    ListFormat,
    typer.Option('--format', help='table for a person, json for a program, plain for one tab-separated path, size and time per file'),
]
LimitOption = Annotated[int | None, typer.Option('--limit', '-n', min=0, help='Print only the newest N files')]


def print_listing(kind: SavedKind, output_format: ListFormat, limit: int | None) -> None:
    """Print the saved files of kind, newest first, at most limit of them.

    An empty cache prints `[]` as json and nothing as plain, so a program reads it like any other
    listing. The table says so on stderr instead.
    """
    rows = CacheManager().listing(kind)
    shown = rows[:limit]

    if output_format is ListFormat.JSON:
        print(json.dumps(shown, indent=2))
        return
    if output_format is ListFormat.PLAIN:
        for row in shown:
            print(f'{row["path"]}\t{row["size_bytes"]}\t{row["modified_iso"]}')
        return

    if not rows:
        stderr_console.print(f'[yellow]No {NOUNS[kind]} saved yet[/yellow]')
        stderr_console.print(CAPTURE_HINT)
        return

    table = Table(title=f'Saved {NOUNS[kind]}')
    table.add_column('Name', style='white')
    table.add_column('Size', justify='right', style='green')
    table.add_column('Modified (UTC)', style='yellow')
    for row in shown:
        modified = str(row['modified_iso'])[:16].replace('T', ' ')
        table.add_row(str(row['name']), human_size(int(row['size_bytes'])), modified)
    console.print(table)
    console.print(f'\n[dim]{len(shown)} of {len(rows)} file(s)[/dim]')
