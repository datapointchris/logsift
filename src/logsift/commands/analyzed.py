"""The `analyzed` group: saved analyses, each shown rendered as Markdown."""

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from logsift.cache.manager import ANALYSIS_RENDERERS
from logsift.cache.manager import CacheManager
from logsift.cache.manager import SavedKind
from logsift.commands.analyze import CAPTURE_HINT
from logsift.commands.clean import clean_saved_files
from logsift.output.markdown_formatter import format_markdown
from logsift.utils.display import display_with_bat
from logsift.utils.fzf import is_fzf_available
from logsift.utils.fzf import select_log_file

console = Console()
stderr_console = Console(stderr=True)


def list_analyzed(output_format: str) -> None:
    """List the saved analyses, by their JSON file, newest first."""
    analyses = CacheManager().listing(SavedKind.JSON)

    if not analyses:
        stderr_console.print('[yellow]No saved analyses found[/yellow]')
        stderr_console.print(CAPTURE_HINT)
        return

    if output_format == 'json':
        print(json.dumps(analyses, indent=2))
    elif output_format == 'plain':
        for analysis in analyses:
            print(f'{analysis["name"]}\t{analysis["path"]}\t{analysis["size_bytes"]}\t{analysis["modified_iso"]}')
    else:
        table = Table(title='Saved Analysis Results', show_header=True)
        table.add_column('Name', style='cyan')
        table.add_column('Size', justify='right')
        table.add_column('Modified', style='dim')

        for analysis in analyses:
            size_kb = int(analysis['size_bytes']) / 1024
            size_str = f'{size_kb:.1f} KB' if size_kb < 1024 else f'{size_kb / 1024:.1f} MB'
            table.add_row(str(analysis['name']), size_str, str(analysis['modified_iso']))

        console.print(table)
        console.print(f'\n[dim]Total: {len(analyses)} analysis result(s)[/dim]')


def show_analysis(json_path: Path) -> None:
    """Page a saved analysis rendered as Markdown."""
    try:
        analysis = json.loads(json_path.read_text())
    except (json.JSONDecodeError, OSError) as fault:
        stderr_console.print(f'[red]Error reading analysis: {fault}[/red]')
        raise typer.Exit(1) from None
    display_with_bat(format_markdown(analysis), language='markdown', filename=json_path.name)


def browse_analyzed() -> None:
    """Pick a saved analysis with fzf and page it as Markdown."""
    if not is_fzf_available():
        stderr_console.print('[red]Error: fzf is not installed or not in PATH[/red]')
        stderr_console.print('[dim]Install fzf: https://github.com/junegunn/fzf#installation[/dim]')
        raise typer.Exit(1)

    analyses = CacheManager().listing(SavedKind.JSON)
    if not analyses:
        stderr_console.print('[yellow]No saved analyses found[/yellow]')
        stderr_console.print(CAPTURE_HINT)
        return

    selected_path = select_log_file(analyses, 'Select analysis result to view')
    if not selected_path:
        stderr_console.print('[dim]No file selected[/dim]')
        return

    stderr_console.print(f'[cyan]Analysis: {selected_path}[/cyan]\n')
    show_analysis(Path(selected_path))


def show_latest_analyzed(name: str | None) -> None:
    """Page the newest saved analysis, or the newest whose run name contains name, as Markdown."""
    latest_analysis = CacheManager().latest(SavedKind.JSON, name)
    if not latest_analysis:
        if name:
            stderr_console.print(f'[red]Error: No analyses found matching "{name}"[/red]')
            stderr_console.print('[dim]Run `logsift analyzed list` to see the saved names[/dim]')
        else:
            stderr_console.print('[red]Error: No saved analyses found[/red]')
            stderr_console.print(CAPTURE_HINT)
        raise typer.Exit(1)

    stderr_console.print(f'[cyan]Latest analysis: {latest_analysis}[/cyan]\n')
    show_analysis(latest_analysis)


def clean_analyzed(days: int, dry_run: bool) -> None:
    """Delete the saved analyses older than days, in every format, or with dry_run name each one instead."""
    clean_saved_files(tuple(ANALYSIS_RENDERERS), days, dry_run, 'analysis file')
