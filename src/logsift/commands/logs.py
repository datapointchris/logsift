"""Logs subcommand implementation.

Lists and manages cached log files.
"""

import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

from logsift.cache.manager import CacheManager
from logsift.cache.rotation import clean_old_logs
from logsift.utils.fzf import browse_log_with_preview
from logsift.utils.fzf import is_fzf_available
from logsift.utils.fzf import select_log_file

console = Console()


def list_logs(output_format: str = 'table') -> None:
    """List cached log files.

    Args:
        output_format: Output format (table, json, plain)
    """
    cache = CacheManager()
    logs = cache.list_all_logs()

    if not logs:
        console.print('[yellow]No cached logs found[/yellow]')
        return

    if output_format == 'json':
        import json

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
    """Clean old log files from cache.

    Args:
        days: Number of days to retain (delete older files)
        dry_run: If True, show what would be deleted without deleting
    """
    cache = CacheManager()

    if not cache.cache_dir.exists():
        console.print('[yellow]No cache directory found[/yellow]')
        return

    if dry_run:
        # Show what would be deleted
        from datetime import UTC
        from datetime import datetime
        from datetime import timedelta

        cutoff_time = datetime.now(tz=UTC) - timedelta(days=days)
        cutoff_timestamp = cutoff_time.timestamp()

        to_delete = []
        for log_file in cache.cache_dir.rglob('*.log'):
            if log_file.is_file():
                mtime = log_file.stat().st_mtime
                if mtime < cutoff_timestamp:
                    to_delete.append(log_file)

        if not to_delete:
            console.print(f'[green]No log files older than {days} days[/green]')
            return

        console.print(f'[yellow]Would delete {len(to_delete)} log file(s) older than {days} days:[/yellow]')
        for log_file in to_delete[:10]:  # Show first 10
            console.print(f'  - {log_file}')
        if len(to_delete) > 10:
            console.print(f'  ... and {len(to_delete) - 10} more')

        console.print('\n[dim]Run without --dry-run to actually delete[/dim]')
    else:
        # Actually delete
        deleted_count = clean_old_logs(cache.cache_dir, retention_days=days)

        if deleted_count == 0:
            console.print(f'[green]No log files older than {days} days[/green]')
        else:
            console.print(f'[green]Deleted {deleted_count} log file(s) older than {days} days[/green]')


def browse_logs(action: str = 'select') -> None:
    """Browse cached log files interactively using fzf.

    Args:
        action: Action to perform - 'select' (choose and analyze) or 'view' (preview only)
    """
    # Check if fzf is available
    if not is_fzf_available():
        console.print('[red]Error: fzf is not installed or not in PATH[/red]')
        console.print('[dim]Install fzf: https://github.com/junegunn/fzf#installation[/dim]')
        sys.exit(1)

    # Get log files
    cache = CacheManager()
    logs = cache.list_all_logs()

    if not logs:
        console.print('[yellow]No cached logs found[/yellow]')
        return

    # Select log file with fzf
    if action == 'select':
        selected_path = select_log_file(logs, 'Select log file to analyze')

        if not selected_path:
            console.print('[dim]No file selected[/dim]')
            return

        # Analyze the selected log
        console.print(f'[cyan]Analyzing: {selected_path}[/cyan]')

        from logsift.commands.analyze import analyze_log

        analyze_log(selected_path, output_format='markdown')

    elif action == 'view':
        selected_path = select_log_file(logs, 'Select log file to view')

        if not selected_path:
            console.print('[dim]No file selected[/dim]')
            return

        # Browse the selected log
        log_path = Path(selected_path)
        if browse_log_with_preview(log_path):
            console.print(f'[dim]Browsed: {log_path}[/dim]')
        else:
            console.print('[red]Error browsing log file[/red]')
