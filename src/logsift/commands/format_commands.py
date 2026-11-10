"""The `raw`, `json`, `toon` and `md` groups: one kind of saved file each, shown exactly as stored."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from logsift.cache.manager import CacheManager
from logsift.cache.manager import SavedKind
from logsift.commands.choose import require_picker
from logsift.commands.listing import LimitOption
from logsift.commands.listing import ListFormat
from logsift.commands.listing import ListFormatOption
from logsift.commands.listing import print_listing
from logsift.utils.display import display_file_with_bat
from logsift.utils.display import tail_file
from logsift.utils.fzf import select_log_file

console = Console()
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


def create_format_commands(kind: SavedKind) -> typer.Typer:
    """The `list`, `latest` and `choose` commands over one kind of saved file."""
    examples = '\n'.join(
        f'  logsift {kind} {invocation}'
        for invocation in ('list -n 10', 'list --format json', 'latest', 'latest pytest', 'latest build --tail', 'choose')
    )
    app = typer.Typer(
        name=kind,
        help=FORMAT_HELP[kind],
        epilog=f'\b\nExamples:\n{examples}',
        no_args_is_help=True,
        pretty_exceptions_enable=False,
    )

    def show(file_path: Path, tail: bool, interval: int) -> None:
        if tail:
            tail_file(file_path, interval)
        else:
            display_file_with_bat(file_path, language=BAT_LANGUAGES[kind])

    @app.command('list')
    def format_list(output_format: ListFormatOption = ListFormat.TABLE, limit: LimitOption = None) -> None:
        """List the files, newest first, with their size and modification time."""
        print_listing(kind, output_format, limit, f'{kind.upper()} Files', f'No {kind} files found')

    @app.command('latest')
    def format_latest(
        name: Annotated[
            str | None,
            typer.Argument(help='Show the newest file whose run name contains this, such as "pytest". Else the newest of all'),
        ] = None,
        tail: Annotated[
            bool,
            typer.Option(
                '--tail',
                help='Tail the file in real-time instead of displaying it',
            ),
        ] = False,
        interval: Annotated[
            int,
            typer.Option(
                '-i',
                '--interval',
                help='Update interval in seconds when tailing',
            ),
        ] = 1,
    ) -> None:
        """Show the most recent file, optionally tailing it."""
        file_path = CacheManager().latest(kind, name)
        if not file_path:
            matching = f' matching "{name}"' if name else ''
            stderr_console.print(f'[red]Error: No {kind} files found{matching}[/red]')
            raise typer.Exit(1)

        stderr_console.print(f'[cyan]Latest {kind}: {file_path}[/cyan]\n')
        show(file_path, tail, interval)

    @app.command('choose')
    def format_choose(
        tail: Annotated[
            bool,
            typer.Option(
                '--tail',
                help='Tail the selected file in real-time',
            ),
        ] = False,
        interval: Annotated[
            int,
            typer.Option(
                '-i',
                '--interval',
                help='Update interval in seconds when tailing',
            ),
        ] = 1,
    ) -> None:
        """Pick a file with fzf, then show or tail it. Needs a terminal and fzf."""
        require_picker(f'`logsift {kind} latest <name>`')

        files = CacheManager().listing(kind)
        if not files:
            stderr_console.print(f'[yellow]No {kind} files found[/yellow]')
            return

        selected_path = select_log_file(files, f'Select {kind} file')
        if not selected_path:
            stderr_console.print('[dim]No file selected[/dim]')
            return

        stderr_console.print(f'[cyan]Selected: {selected_path}[/cyan]\n')
        show(Path(selected_path), tail, interval)

    return app
