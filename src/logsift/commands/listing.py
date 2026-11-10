"""What every `list` command prints: the saved files of one kind, newest first."""

import json
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from logsift.cache.manager import CacheManager
from logsift.cache.manager import SavedKind
from logsift.commands.find_saved_file import CAPTURE_HINT
from logsift.commands.find_saved_file import KIND_TEXT
from logsift.utils.display import human_size

console = Console()
stderr_console = Console(stderr=True)


JsonOption = Annotated[bool, typer.Option('--json', help='Print the files as a JSON array, for a program')]
PlainOption = Annotated[bool, typer.Option('--plain', help='Print one tab-separated path, size and time per file')]
LimitOption = Annotated[int | None, typer.Option('--limit', '-n', min=0, help='Print only the newest N files')]


def print_listing(kind: SavedKind, as_json: bool, plain: bool, limit: int | None) -> None:
    """Print the saved files of kind, newest first, at most limit of them.

    An empty cache prints `[]` as json and nothing as plain, so a program reads it like any other
    listing. The table says so on stderr instead.
    """
    if as_json and plain:
        stderr_console.print('[red]Error: --json and --plain cannot be given together[/red]')
        raise typer.Exit(2)

    rows = CacheManager().listing(kind)
    shown = rows[:limit]

    if as_json:
        print(json.dumps(shown, indent=2))
        return
    if plain:
        for row in shown:
            print(f'{row["path"]}\t{row["size_bytes"]}\t{row["modified_iso"]}')
        return

    if not rows:
        stderr_console.print(f'[yellow]No {KIND_TEXT[kind].noun} saved yet[/yellow]')
        stderr_console.print(CAPTURE_HINT)
        return

    table = Table(title=f'Saved {KIND_TEXT[kind].noun}')
    table.add_column('Name', style='white')
    table.add_column('Size', justify='right', style='green')
    table.add_column('Modified (UTC)', style='yellow')
    for row in shown:
        modified = str(row['modified_iso'])[:16].replace('T', ' ')
        table.add_row(str(row['name']), human_size(int(row['size_bytes'])), modified)
    console.print(table)
    console.print(f'\n[dim]{len(shown)} of {len(rows)} file(s)[/dim]')
