"""The `logs` group: each run's raw log, as the command printed it."""

from pathlib import Path

import typer
from rich.console import Console

from logsift.cache.manager import CacheManager
from logsift.cache.manager import SavedKind
from logsift.commands.analyze import CAPTURE_HINT
from logsift.commands.analyze import analyze_log
from logsift.commands.choose import require_picker
from logsift.commands.clean import clean_saved_files
from logsift.utils.display import display_file_with_bat
from logsift.utils.display import tail_file
from logsift.utils.fzf import search_log_lines
from logsift.utils.fzf import select_log_file

console = Console()
stderr_console = Console(stderr=True)


def clean_logs(days: int = 90, dry_run: bool = False) -> None:
    """Delete raw logs older than days, or with dry_run name each one instead."""
    clean_saved_files((SavedKind.RAW,), days, dry_run, 'log file')


def choose_log(action: str = 'select', interval: int = 1) -> None:
    """Pick a raw log with fzf, then analyze it, search it ('view'), or tail it.

    Args:
        action: 'select' to analyze the pick, 'view' to search its lines, or 'tail' to follow it
        interval: Seconds between checks when tailing
    """
    require_picker('`logsift logs latest <name>`, or `logsift analyze <path>`')

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
        if search_log_lines(Path(selected_path)):
            stderr_console.print(f'[dim]Searched: {selected_path}[/dim]')
        else:
            stderr_console.print('[red]Error searching the log[/red]')
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
