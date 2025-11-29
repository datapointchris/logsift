"""Watch subcommand implementation.

Monitors a log file in real-time and provides live analysis.
"""

import sys
import time
from pathlib import Path

from rich.console import Console

from logsift.core.analyzer import Analyzer
from logsift.monitor.watcher import LogWatcher
from logsift.output.markdown_formatter import format_markdown

console = Console()


def watch_log(log_file: str, interval: int = 1) -> None:
    """Watch and analyze a log file in real-time.

    Args:
        log_file: Path to the log file to watch
        interval: Update interval in seconds
    """
    file_path = Path(log_file).expanduser().resolve()

    if not file_path.exists():
        console.print(f'[red]Error: Log file not found: {file_path}[/red]')
        sys.exit(1)

    console.print(f'[blue]Watching:[/blue] {file_path}')
    console.print(f'[dim]Update interval: {interval}s (Press Ctrl+C to stop)[/dim]\n')

    # Initialize components
    analyzer = Analyzer()

    # Track accumulated log lines
    log_lines: list[str] = []

    def process_new_line(line: str) -> None:
        """Process each new log line."""
        log_lines.append(line)

        # Analyze the accumulated log
        log_content = '\n'.join(log_lines)
        result = analyzer.analyze(log_content)

        # Display live update
        console.clear()
        console.print(f'[blue]Watching:[/blue] {file_path}')
        errors = result['stats']['total_errors']
        warnings = result['stats']['total_warnings']
        console.print(f'[dim]Lines: {len(log_lines)} | Errors: {errors} | Warnings: {warnings}[/dim]\n')

        if errors > 0 or warnings > 0:
            markdown = format_markdown(result)
            console.print(markdown)
        else:
            console.print('[green]✓[/green] No errors or warnings detected yet')

    # Start watching
    watcher = LogWatcher(file_path, interval)

    try:
        watcher.watch(process_new_line)
    except KeyboardInterrupt:
        console.print('\n[yellow]Stopped watching log file[/yellow]')
        watcher.stop()
        sys.exit(0)


def tail_log(log_file: str, interval: int = 1) -> None:
    """Tail a log file in real-time (like tail -f).

    Just shows raw log lines as they appear, without analysis.

    Args:
        log_file: Path to the log file to tail
        interval: Update interval in seconds
    """
    file_path = Path(log_file).expanduser().resolve()

    if not file_path.exists():
        console.print(f'[red]Error: Log file not found: {file_path}[/red]')
        sys.exit(1)

    console.print(f'[blue]Tailing:[/blue] {file_path}')
    console.print('[dim]Press Ctrl+C to stop[/dim]\n')

    # Open file and seek to end
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
        console.print('\n[yellow]Stopped tailing log file[/yellow]')
        sys.exit(0)
