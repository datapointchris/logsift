"""The `raw`, `json`, `toon` and `md` groups: one kind of saved file each, shown exactly as stored."""

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from logsift.cache.manager import CacheManager
from logsift.cache.manager import SavedKind
from logsift.utils.display import display_file_with_bat
from logsift.utils.display import tail_file
from logsift.utils.fzf import is_fzf_available
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
    """The `list`, `latest` and `browse` commands over one kind of saved file."""
    examples = '\n'.join(
        f'  logsift {kind} {invocation}'
        for invocation in ('list', 'list --format json', 'latest', 'latest pytest', 'latest build --tail', 'browse')
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
    def format_list(
        output_format: Annotated[
            str,
            typer.Option(
                '--format',
                help='Output format: table (default), json (for scripts), plain (simple list)',
            ),
        ] = 'table',
    ) -> None:
        """List all files with metadata, newest first."""
        files = CacheManager().listing(kind)

        if not files:
            stderr_console.print(f'[yellow]No {kind} files found[/yellow]')
            return

        if output_format == 'json':
            print(json.dumps(files, indent=2))
        elif output_format == 'plain':
            for file in files:
                print(f'{file["path"]}\t{file["size_bytes"]}\t{file["modified_iso"]}')
        else:
            table = Table(title=f'{kind.upper()} Files')
            table.add_column('Name', style='white')
            table.add_column('Size', justify='right', style='green')
            table.add_column('Modified', style='yellow')

            for file in files:
                size_bytes = int(file['size_bytes'])
                if size_bytes < 1024:
                    size_str = f'{size_bytes} B'
                elif size_bytes < 1024 * 1024:
                    size_str = f'{size_bytes / 1024:.1f} KB'
                else:
                    size_str = f'{size_bytes / (1024 * 1024):.1f} MB'

                name = str(file['name'])
                if len(name) > 60:
                    name = name[:57] + '...'

                table.add_row(name, size_str, str(file['modified_iso']).split('T')[0])

            console.print(table)
            console.print(f'\n[dim]Total: {len(files)} file(s)[/dim]')

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

    @app.command('browse')
    def format_browse(
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
        """Pick a file with fzf, then show or tail it.

        Requires fzf to be installed (see https://github.com/junegunn/fzf#installation).
        """
        if not is_fzf_available():
            stderr_console.print('[red]Error: fzf is not installed or not in PATH[/red]')
            stderr_console.print('[dim]Install fzf: https://github.com/junegunn/fzf#installation[/dim]')
            raise typer.Exit(1)

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
