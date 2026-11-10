"""What only the `logs` group does with a raw log: analyze, search or tail the one chosen, and clean."""

from rich.console import Console

from logsift.cache.manager import SavedKind
from logsift.commands.analyze import analyze_log
from logsift.commands.clean import clean_saved_files
from logsift.commands.find_saved_file import choose_file
from logsift.utils.display import tail_file
from logsift.utils.fzf import search_log_lines

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
    prompts = {'select': 'Choose a log to analyze', 'view': 'Choose a log to search', 'tail': 'Choose a log to tail'}
    chosen = choose_file(SavedKind.RAW, prompts[action], '`logsift logs latest <name>`, or `logsift analyze <path>`')

    if action == 'select':
        stderr_console.print(f'[cyan]Analyzing: {chosen}[/cyan]')
        analyze_log(str(chosen), output_format='markdown')
    elif action == 'view':
        if search_log_lines(chosen):
            stderr_console.print(f'[dim]Searched: {chosen}[/dim]')
        else:
            stderr_console.print('[red]Error searching the log[/red]')
    else:
        tail_file(chosen, interval=interval)
