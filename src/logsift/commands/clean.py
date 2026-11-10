"""What `logs clean` and `analyzed clean` print: the files older than the retention, then their deletion."""

import typer
from rich.console import Console

from logsift.cache.manager import CacheManager
from logsift.cache.manager import SavedKind

console = Console()
stderr_console = Console(stderr=True)


def clean_saved_files(kinds: tuple[SavedKind, ...], days: int, dry_run: bool, noun: str) -> None:
    """Delete the saved files of kinds older than days, or with dry_run name each one instead.

    Args:
        kinds: The kinds of saved file to clean
        days: Keep files modified within this many days
        dry_run: Name what would be deleted and delete nothing
        noun: What one file is called in the report, such as "log file"

    Exits 1 when a file could not be deleted, after naming each one on stderr.
    """
    cache = CacheManager()
    stale = cache.stale(kinds, days)

    if not stale:
        console.print(f'[green]No {noun}s older than {days} days[/green]')
        return

    if dry_run:
        console.print(f'[yellow]Would delete {len(stale)} {noun}(s) older than {days} days:[/yellow]')
        for path in stale:
            # soft_wrap keeps a long path whole on a narrow terminal or a pipe
            console.print(f'  - {path}', soft_wrap=True)
        console.print('\n[dim]Run without --dry-run to actually delete[/dim]')
        return

    failures = cache.delete(stale)
    console.print(f'[green]Deleted {len(stale) - len(failures)} {noun}(s) older than {days} days[/green]')
    for failure in failures:
        stderr_console.print(f'[red]Error: could not delete {failure}[/red]', soft_wrap=True)
    if failures:
        raise typer.Exit(1)
