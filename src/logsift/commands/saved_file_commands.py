"""The `list`, `latest` and `choose` commands over one kind of saved file, and the groups built from them.

`logs` and `analyzed` add these to their own groups, then add what only they do. The `raw`, `json`,
`toon` and `md` groups are these three alone, showing each file exactly as stored.
"""

from pathlib import Path

import typer
from rich.console import Console

from logsift.cache.manager import SavedKind
from logsift.commands.find_saved_file import NOUNS
from logsift.commands.find_saved_file import IntervalOption
from logsift.commands.find_saved_file import NameArgument
from logsift.commands.find_saved_file import TailOption
from logsift.commands.find_saved_file import choose_file
from logsift.commands.find_saved_file import latest_file
from logsift.commands.listing import JsonOption
from logsift.commands.listing import LimitOption
from logsift.commands.listing import PlainOption
from logsift.commands.listing import print_listing
from logsift.utils.display import display_file_with_bat
from logsift.utils.display import tail_file

stderr_console = Console(stderr=True)

# What each namespace holds, so its row on the root screen says how it differs from `logs` and `analyzed`.
FORMAT_HELP = {
    SavedKind.RAW: 'Show raw logs, exactly what each run printed, as stored',
    SavedKind.JSON: 'Show saved analyses as the JSON `--format json` prints, as stored',
    SavedKind.TOON: 'Show saved analyses as the toon a piped run prints, as stored',
    SavedKind.MD: 'Show saved analyses as the Markdown a terminal run prints, as stored',
}

# The language bat highlights each kind as. toon is close enough to YAML to read.
BAT_LANGUAGES = {SavedKind.RAW: 'txt', SavedKind.JSON: 'json', SavedKind.TOON: 'yaml', SavedKind.MD: 'markdown'}


def examples(group: str, *invocations: str) -> str:
    """A command's Examples epilog, one `logsift <group> <invocation>` line each."""
    return '\b\nExamples:\n' + '\n'.join(f'  logsift {group} {invocation}' for invocation in invocations)


def show_saved_file(kind: SavedKind, path: Path, tail: bool, interval: int) -> None:
    """Page a saved file as stored, or follow it as it grows."""
    if tail:
        tail_file(path, interval)
    else:
        display_file_with_bat(path, language=BAT_LANGUAGES[kind])


def add_list_command(app: typer.Typer, kind: SavedKind, group: str) -> None:
    """Add `list` to a group, over the files of kind."""

    @app.command(
        'list',
        help=f"List the saved {NOUNS[kind]}, newest first, with each one's size and modification time.",
        epilog=examples(group, 'list -n 10', 'list --json', 'list --plain'),
    )
    def list_files(as_json: JsonOption = False, plain: PlainOption = False, limit: LimitOption = None) -> None:
        print_listing(kind, as_json, plain, limit)


def add_latest_command(app: typer.Typer, kind: SavedKind, group: str) -> None:
    """Add `latest` to a group: page the most recently written file of kind as stored, or follow it."""

    @app.command(
        'latest',
        help=f'Page the most recently written of the saved {NOUNS[kind]} as stored, or follow it with --tail.',
        epilog=examples(group, 'latest', 'latest pytest', 'latest build --tail'),
    )
    def latest(name: NameArgument = None, tail: TailOption = False, interval: IntervalOption = 1) -> None:
        path = latest_file(kind, name)
        stderr_console.print(f'[cyan]Latest: {path}[/cyan]\n')
        show_saved_file(kind, path, tail, interval)


def add_choose_command(app: typer.Typer, kind: SavedKind, group: str) -> None:
    """Add `choose` to a group: pick a file of kind with fzf, then page it as stored or follow it."""

    @app.command(
        'choose',
        help=f'Pick one of the saved {NOUNS[kind]} with fzf, then page it as stored or follow it with --tail. Needs a terminal and fzf.',
        epilog=examples(group, 'choose', 'choose --tail'),
    )
    def choose(tail: TailOption = False, interval: IntervalOption = 1) -> None:
        path = choose_file(kind, f'Choose one of the saved {NOUNS[kind]}', f'`logsift {group} latest <name>`')
        stderr_console.print(f'[cyan]Chosen: {path}[/cyan]\n')
        show_saved_file(kind, path, tail, interval)


def create_kind_group(kind: SavedKind) -> typer.Typer:
    """The group named for kind: its `list`, `latest` and `choose`, and nothing else."""
    app = typer.Typer(name=kind, help=FORMAT_HELP[kind], no_args_is_help=True, pretty_exceptions_enable=False)
    add_list_command(app, kind, kind)
    add_latest_command(app, kind, kind)
    add_choose_command(app, kind, kind)
    return app
