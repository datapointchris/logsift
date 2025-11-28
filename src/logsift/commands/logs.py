"""Logs subcommand implementation.

Lists and manages cached log files.
"""

from rich.console import Console
from rich.table import Table

from logsift.cache.manager import CacheManager
from logsift.cache.rotation import clean_old_logs

console = Console()


def list_logs(context: str | None = None, output_format: str = 'table') -> None:
    """List cached log files.

    Args:
        context: Optional context filter for log files
        output_format: Output format (table, json, plain)
    """
    cache = CacheManager()
    logs = cache.list_all_logs(context=context)

    if not logs:
        if context:
            console.print(f'[yellow]No logs found for context: {context}[/yellow]')
        else:
            console.print('[yellow]No cached logs found[/yellow]')
        return

    if output_format == 'json':
        import json

        print(json.dumps(logs, indent=2))
    elif output_format == 'plain':
        for log in logs:
            print(f'{log["path"]}\t{log["context"]}\t{log["size_bytes"]}\t{log["modified_iso"]}')
    else:
        # Table format (default)
        table = Table(title='Cached Log Files')
        table.add_column('Context', style='cyan')
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
            if len(name) > 40:
                name = name[:37] + '...'

            # Format timestamp
            modified = str(log['modified_iso']).split('T')[0]  # Just the date

            table.add_row(str(log['context']), name, size_str, modified)

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
