"""Logs subcommand implementation.

Lists and manages cached log files.
"""

import json
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from logsift.cache.manager import CacheManager
from logsift.cache.manager import SavedKind
from logsift.commands.analyze import CAPTURE_HINT
from logsift.commands.analyze import analyze_log
from logsift.commands.clean import clean_saved_files
from logsift.utils.display import display_file_with_bat
from logsift.utils.display import tail_file
from logsift.utils.fzf import browse_log_with_preview
from logsift.utils.fzf import is_fzf_available
from logsift.utils.fzf import select_log_file

console = Console()
stderr_console = Console(stderr=True)


def list_logs(output_format: str = 'table') -> None:
    """List cached log files.

    Args:
        output_format: Output format (table, json, plain)
    """
    logs = CacheManager().listing(SavedKind.RAW)

    if not logs:
        stderr_console.print('[yellow]No cached logs found[/yellow]')
        stderr_console.print(CAPTURE_HINT)
        return

    if output_format == 'json':
        print(json.dumps(logs, indent=2))
    elif output_format == 'plain':
        for log in logs:
            print(f'{log["path"]}\t{log["size_bytes"]}\t{log["modified_iso"]}')
    else:
        # Table format (default)
        table = Table(title='Cached Log Files')
        table.add_column('Name', style='white')
        table.add_column('Size', justify='right', style='green')
        table.add_column('Modified', style='yellow')

        for log in logs:
            # Format size in human-readable format
            size_bytes = int(log['size_bytes'])  # Always int from CacheManager
            if size_bytes < 1024:
                size_str = f'{size_bytes} B'
            elif size_bytes < 1024 * 1024:
                size_str = f'{size_bytes / 1024:.1f} KB'
            else:
                size_str = f'{size_bytes / (1024 * 1024):.1f} MB'

            # Truncate name if too long
            name = str(log['name'])  # Always str from CacheManager
            if len(name) > 60:
                name = name[:57] + '...'

            # Format timestamp
            modified = str(log['modified_iso']).split('T')[0]  # Just the date

            table.add_row(name, size_str, modified)

        console.print(table)
        console.print(f'\n[dim]Total: {len(logs)} log file(s)[/dim]')


def clean_logs(days: int = 90, dry_run: bool = False) -> None:
    """Delete raw logs older than days, or with dry_run name each one instead."""
    clean_saved_files((SavedKind.RAW,), days, dry_run, 'log file')


def browse_logs(action: str = 'select', interval: int = 1) -> None:
    """Pick a raw log with fzf, then analyze it, page it ('view'), or tail it.

    Args:
        action: 'select' to analyze the pick, 'view' to page it, or 'tail' to follow it
        interval: Seconds between checks when tailing
    """
    if not is_fzf_available():
        stderr_console.print('[red]Error: fzf is not installed or not in PATH[/red]')
        stderr_console.print('[dim]Install fzf: https://github.com/junegunn/fzf#installation[/dim]')
        sys.exit(1)

    logs = CacheManager().listing(SavedKind.RAW)
    if not logs:
        stderr_console.print('[yellow]No cached logs found[/yellow]')
        stderr_console.print(CAPTURE_HINT)
        return

    prompts = {'select': 'Select log file to analyze', 'view': 'Select log file to view', 'tail': 'Select log file to tail'}
    selected_path = select_log_file(logs, prompts[action])
    if not selected_path:
        stderr_console.print('[dim]No file selected[/dim]')
        return

    if action == 'select':
        stderr_console.print(f'[cyan]Analyzing: {selected_path}[/cyan]')
        analyze_log(selected_path, output_format='markdown')
    elif action == 'view':
        if browse_log_with_preview(Path(selected_path)):
            stderr_console.print(f'[dim]Browsed: {selected_path}[/dim]')
        else:
            stderr_console.print('[red]Error browsing log file[/red]')
    else:
        tail_file(Path(selected_path), interval=interval)


def show_latest_log(name: str | None, tail: bool, interval: int) -> None:
    """Page the newest raw log, or the newest whose run name contains name, or tail it."""
    log_path = CacheManager().latest(SavedKind.RAW, name)
    if not log_path:
        if name:
            stderr_console.print(f'[red]Error: No logs found for name "{name}"[/red]')
            stderr_console.print('[dim]Run `logsift logs list` to see the cached names[/dim]')
        else:
            stderr_console.print('[red]Error: No cached logs found[/red]')
            stderr_console.print(CAPTURE_HINT)
        raise typer.Exit(1)

    stderr_console.print(f'[cyan]Latest log: {log_path}[/cyan]\n')
    if tail:
        tail_file(log_path, interval=interval)
    else:
        display_file_with_bat(log_path)
