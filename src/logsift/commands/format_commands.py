"""Template-based format command generation.

Creates standardized command groups for each log format (raw, json, toon, md).
"""

import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from typer.core import TyperGroup

console = Console()


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
    # Import ColoredTyperGroup to ensure consistent formatting
    import click

    from logsift.cli_formatter import format_help_with_colors

    class ColoredTyperGroup(TyperGroup):
        """Custom TyperGroup that uses our uv-style colored formatter."""

        def format_help(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
            """Override help formatting to use our custom colored formatter."""
            help_text = format_help_with_colors(ctx)
            click.echo(help_text, color=True)

    app = typer.Typer(
        name=format_name,
        help=f'View {format_name} format files',
        rich_markup_mode=None,
        pretty_exceptions_enable=False,
        cls=ColoredTyperGroup,
        invoke_without_command=True,
    )

    @app.callback()
    def format_callback(ctx: typer.Context) -> None:
        """Manage format files."""
        # Show help if no subcommand provided
        if ctx.invoked_subcommand is None:
            help_text = format_help_with_colors(ctx)
            click.echo(help_text, color=True)
            raise typer.Exit()

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

        Examples:
            logsift <format> list
            logsift <format> list --format json
            logsift <format> list --format plain
        """
        from logsift.cache.manager import CacheManager

        cache = CacheManager()

        # Get files for this format
        files = cache.list_all_in_format(format_name)

        if not files:
            console.print(f'[yellow]No {format_name} files found[/yellow]')
            return

        if output_format == 'json':
            import json

            print(json.dumps(files, indent=2))
        elif output_format == 'plain':
            for file in files:
                print(f'{file["path"]}\t{file["size_bytes"]}\t{file["modified_iso"]}')
        else:
            # Table format (default)
            from rich.table import Table

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
                help='Update interval in seconds when tailing (default: 1)',
            ),
        ] = 1,
    ) -> None:
        """Show the most recent file, optionally tailing it.

        Finds the latest file by name and displays its contents.  Use --tail to watch it in real-time.

        Examples:
            logsift <format> latest
            logsift <format> latest pytest
            logsift <format> latest build --tail
            logsift <format> latest pytest --tail --interval 5
        """
        from logsift.cache.manager import CacheManager

        cache = CacheManager()

        # Get the format directory
        format_dir = getattr(cache, cache_attr)

        # Get latest file
        if name:
            # Find latest file matching name
            matching_files = [f for f in format_dir.glob(f'*{extension}') if name in f.stem]

            if not matching_files:
                console.print(f'[red]Error: No {format_name} files found matching "{name}"[/red]')
                raise typer.Exit(1)

            # Sort by modification time
            file_path = max(matching_files, key=lambda f: f.stat().st_mtime)
        else:
            # Get absolute latest
            all_files = list(format_dir.glob(f'*{extension}'))

            if not all_files:
                console.print(f'[red]Error: No {format_name} files found[/red]')
                raise typer.Exit(1)

            file_path = max(all_files, key=lambda f: f.stat().st_mtime)

        console.print(f'[cyan]Latest {format_name}: {file_path}[/cyan]\n')

        # Either tail or display
        if tail:
            _tail_file(file_path, interval)
        else:
            _display_file(file_path, language)

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
                help='Update interval in seconds when tailing (default: 1)',
            ),
        ] = 1,
    ) -> None:  # nosec B608
        """Browse and select files interactively using fzf.

        Opens an interactive fuzzy-finder interface to search and select from files.
        Displays the selected file or tails it in real-time.

        Requires fzf to be installed (install with: brew install fzf).

        Examples:
            logsift <format> browse
            logsift <format> browse --tail
        """
        from logsift.cache.manager import CacheManager
        from logsift.utils.fzf import is_fzf_available
        from logsift.utils.fzf import select_log_file

        if not is_fzf_available():
            console.print('[red]Error: fzf is not installed or not in PATH[/red]')
            console.print('[dim]Install fzf: https://github.com/junegunn/fzf#installation[/dim]')
            raise typer.Exit(1)

        cache = CacheManager()
        files = cache.list_all_in_format(format_name)

        if not files:
            console.print(f'[yellow]No {format_name} files found[/yellow]')
            return

        selected_path = select_log_file(files, f'Select {format_name} file')

        if not selected_path:
            console.print('[dim]No file selected[/dim]')
            return

        console.print(f'[cyan]Selected: {selected_path}[/cyan]\n')

        file_path = Path(selected_path)

        if tail:
            _tail_file(file_path, interval)
        else:
            _display_file(file_path, language)

    return app


def _display_file(file_path: Path, language: str) -> None:
    """Display a file with bat for syntax highlighting.

    Args:
        file_path: Path to file to display
        language: Language for syntax highlighting
    """
    from logsift.utils.display import display_file_with_bat

    display_file_with_bat(file_path, language=language)


def _tail_file(file_path: Path, interval: int = 1) -> None:
    """Tail a file in real-time.

    Args:
        file_path: Path to file to tail
        interval: Update interval in seconds
    """
    import time

    if not file_path.exists():
        console.print(f'[red]Error: File not found: {file_path}[/red]')
        sys.exit(1)

    console.print(f'[blue]Tailing:[/blue] {file_path}')
    console.print('[dim]Press Ctrl+C to stop[/dim]\n')

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
        console.print('\n[yellow]Stopped tailing file[/yellow]')
        sys.exit(0)
