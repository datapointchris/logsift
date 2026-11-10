"""How every command finds one saved file: the most recently written of a run name, or one picked with fzf.

These own the message and exit code of a miss, an empty cache and a cancelled pick, so every
group that reaches a saved file answers each one the same way.
"""

import sys
from pathlib import Path
from typing import Annotated
from typing import NoReturn

import typer
from rich.console import Console

from logsift.cache.manager import CacheManager
from logsift.cache.manager import SavedKind
from logsift.utils.fzf import is_fzf_available
from logsift.utils.fzf import select_log_file

stderr_console = Console(stderr=True)

# Printed under every empty-cache message: monitor is the one command that writes logs and analyses.
CAPTURE_HINT = '[dim]Run `logsift monitor -- <command>` to capture a run and analyze it[/dim]'

# What a kind's files are called in a message.
NOUNS = {
    SavedKind.RAW: 'logs',
    SavedKind.JSON: 'JSON analyses',
    SavedKind.TOON: 'toon analyses',
    SavedKind.MD: 'Markdown analyses',
}

NameArgument = Annotated[
    str | None,
    typer.Argument(help='Take the newest whose run name contains this, such as "pytest". Else the newest of all', show_default=False),
]
TailOption = Annotated[bool, typer.Option('--tail', help='Follow the file as it grows instead of paging it')]
IntervalOption = Annotated[int, typer.Option('-i', '--interval', help='Seconds between checks when tailing')]


def exit_empty(kind: SavedKind) -> NoReturn:
    """Say no file of kind is saved yet, and how to save one, then exit 1."""
    stderr_console.print(f'[red]Error: no {NOUNS[kind]} saved yet[/red]')
    stderr_console.print(CAPTURE_HINT)
    raise typer.Exit(1)


def latest_file(kind: SavedKind, name: str | None) -> Path:
    """The most recently written file of kind, or the most recent whose run name contains name. A miss exits 1."""
    found = CacheManager().latest(kind, name)
    if found is not None:
        return found
    if not name:
        exit_empty(kind)
    stderr_console.print(f'[red]Error: no saved {NOUNS[kind]} have a run name containing "{name}"[/red]')
    stderr_console.print(f'[dim]Run `logsift {kind} list` to see the saved names[/dim]')
    raise typer.Exit(1)


def require_picker(instead: str) -> None:
    """Exit unless a person at a terminal can pick, naming the command that needs no picker.

    A picker waiting on a closed stdin would hang its caller, so without a terminal this exits 2
    at once. Without fzf it exits 1 and says to install it.

    Args:
        instead: The command that names the file outright, such as "`logsift logs latest <name>`"
    """
    if not sys.stdin.isatty():
        stderr_console.print(f'[red]Error: choose needs a terminal to pick on. Without one, run {instead}[/red]')
        raise typer.Exit(2)
    if not is_fzf_available():
        stderr_console.print('[red]Error: choose needs fzf, which is not on PATH[/red]')
        stderr_console.print(f'Install fzf (https://github.com/junegunn/fzf#installation), or run {instead}')
        raise typer.Exit(1)


def choose_file(kind: SavedKind, prompt: str, instead: str) -> Path:
    """A file of kind picked with fzf. An empty cache exits 1, and a cancelled pick exits 0.

    Args:
        kind: Which saved files to offer
        prompt: The line fzf shows above the files
        instead: The command that names the file outright, for a caller with no terminal or no fzf
    """
    require_picker(instead)
    files = CacheManager().listing(kind)
    if not files:
        exit_empty(kind)
    chosen = select_log_file(files, prompt)
    if not chosen:
        stderr_console.print('[dim]No file chosen[/dim]')
        raise typer.Exit(0)
    return Path(chosen)
