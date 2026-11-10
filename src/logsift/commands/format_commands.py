"""Template-based format command generation.

Creates standardized command groups for each log format (raw, json, toon, md).
"""

import json
import sys
import time
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from logsift.cache.manager import CacheManager
from logsift.utils.display import display_file_with_bat
from logsift.utils.fzf import is_fzf_available
from logsift.utils.fzf import select_log_file

console = Console()
stderr_console = Console(stderr=True)

# What each namespace holds, so its row on the root screen says how it differs from `logs` and `analyzed`.
FORMAT_HELP = {
    'raw': 'Show raw logs, exactly what each run printed, as stored',
    'json': 'Show saved analyses as the JSON `--format json` prints, as stored',
    'toon': 'Show saved analyses as the toon a piped run prints, as stored',
    'md': 'Show saved analyses as the Markdown a terminal run prints, as stored',
}


def create_format_commands(
    format_name: str,
    extension: str,
    cache_attr: str,
    language: str,
) -> typer.Typer:
    """Create a standard set of commands for a log format.

    Args:
        format_name: Format name for command group (e.g., "raw", "md", "json", "toon")
        extension: File extension (e.g., ".log", ".md", ".json", ".toon")
        cache_attr: CacheManager attribute for directory (e.g., "raw_dir", "md_dir")
        language: Language for bat syntax highlighting (e.g., "txt", "markdown", "json", "toon")

    Returns:
        Typer app with browse, latest, and list commands

    Generated commands:
        - logsift {format} browse [--tail]
        - logsift {format} latest [name] [--tail]
        - logsift {format} list
    """
    examples = '\n'.join(
        f'  logsift {format_name} {invocation}'
        for invocation in ('list', 'list --format json', 'latest', 'latest pytest', 'latest build --tail', 'browse')
    )
    app = typer.Typer(
        name=format_name,
        help=FORMAT_HELP[format_name],
        epilog=f'\b\nExamples:\n{examples}',
        no_args_is_help=True,
        pretty_exceptions_enable=False,
    )

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
        """List all files with metadata.

        Shows all files in the cache directory with their size and modification time.
        """
        cache = CacheManager()

        # Get files for this format
        files = cache.list_all_in_format(format_name)

        if not files:
            stderr_console.print(f'[yellow]No {format_name} files found[/yellow]')
            return

        if output_format == 'json':
            print(json.dumps(files, indent=2))
        elif output_format == 'plain':
            for file in files:
                print(f'{file["path"]}\t{file["size_bytes"]}\t{file["modified_iso"]}')
        else:
            # Table format (default)
            table = Table(title=f'{format_name.upper()} Files')
            table.add_column('Name', style='white')
            table.add_column('Size', justify='right', style='green')
            table.add_column('Modified', style='yellow')

            for file in files:
                # Format size in human-readable format
                size_bytes = int(file['size_bytes'])
                if size_bytes < 1024:
                    size_str = f'{size_bytes} B'
                elif size_bytes < 1024 * 1024:
                    size_str = f'{size_bytes / 1024:.1f} KB'
                else:
                    size_str = f'{size_bytes / (1024 * 1024):.1f} MB'

                # Truncate name if too long
                name = str(file['name'])
                if len(name) > 60:
                    name = name[:57] + '...'

                # Format timestamp
                modified = str(file['modified_iso']).split('T')[0]  # Just the date

                table.add_row(name, size_str, modified)

            console.print(table)
            console.print(f'\n[dim]Total: {len(files)} file(s)[/dim]')

    @app.command('latest')
    def format_latest(
        name: Annotated[
            str | None,
            typer.Argument(help='Name to filter by (e.g., "pytest", "build"). If omitted, shows absolute latest file'),
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
        """Show the most recent file, optionally tailing it.

        Finds the latest file by name and displays its contents.  Use --tail to watch it in real-time.
        """
        cache = CacheManager()

        # Get the format directory
        format_dir = getattr(cache, cache_attr)

        # Get latest file
        if name:
            # Find latest file matching name
            matching_files = [f for f in format_dir.glob(f'*{extension}') if name in f.stem]

            if not matching_files:
                stderr_console.print(f'[red]Error: No {format_name} files found matching "{name}"[/red]')
                raise typer.Exit(1)

            # Sort by modification time
            file_path = max(matching_files, key=lambda f: f.stat().st_mtime)
        else:
            # Get absolute latest
            all_files = list(format_dir.glob(f'*{extension}'))

            if not all_files:
                stderr_console.print(f'[red]Error: No {format_name} files found[/red]')
                raise typer.Exit(1)

            file_path = max(all_files, key=lambda f: f.stat().st_mtime)

        stderr_console.print(f'[cyan]Latest {format_name}: {file_path}[/cyan]\n')

        # Either tail or display
        if tail:
            tail_file(file_path, interval)
        else:
            display_file(file_path, language)

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
    ) -> None:  # nosec B608
        """Browse and select files interactively using fzf.

        Opens an interactive fuzzy-finder interface to search and select from files.
        Displays the selected file or tails it in real-time.

        Requires fzf to be installed (see https://github.com/junegunn/fzf#installation).
        """
        if not is_fzf_available():
            stderr_console.print('[red]Error: fzf is not installed or not in PATH[/red]')
            stderr_console.print('[dim]Install fzf: https://github.com/junegunn/fzf#installation[/dim]')
            raise typer.Exit(1)

        cache = CacheManager()
        files = cache.list_all_in_format(format_name)

        if not files:
            stderr_console.print(f'[yellow]No {format_name} files found[/yellow]')
            return

        selected_path = select_log_file(files, f'Select {format_name} file')

        if not selected_path:
            stderr_console.print('[dim]No file selected[/dim]')
            return

        stderr_console.print(f'[cyan]Selected: {selected_path}[/cyan]\n')

        file_path = Path(selected_path)

        if tail:
            tail_file(file_path, interval)
        else:
            display_file(file_path, language)

    return app


def display_file(file_path: Path, language: str) -> None:
    """Display a file with bat for syntax highlighting.

    Args:
        file_path: Path to file to display
        language: Language for syntax highlighting
    """
    display_file_with_bat(file_path, language=language)


def tail_file(file_path: Path, interval: int = 1) -> None:
    """Tail a file in real-time.

    Args:
        file_path: Path to file to tail
        interval: Update interval in seconds
    """
    if not file_path.exists():
        stderr_console.print(f'[red]Error: File not found: {file_path}[/red]')
        sys.exit(1)

    stderr_console.print(f'[blue]Tailing:[/blue] {file_path}')
    stderr_console.print('[dim]Press Ctrl+C to stop[/dim]\n')

    try:
        with file_path.open('r', encoding='utf-8') as f:
            # Go to end of file
            f.seek(0, 2)

            while True:
                line = f.readline()

                if line:
                    # New line available - print it
                    print(line, end='')
                else:
                    # No new data - wait before checking again
                    time.sleep(interval)

    except KeyboardInterrupt:
        stderr_console.print('\n[yellow]Stopped tailing file[/yellow]')
        sys.exit(0)
