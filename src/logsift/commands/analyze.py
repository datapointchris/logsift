"""Analyze subcommand implementation.

Analyzes an existing log file and outputs results.
"""

import sys
from pathlib import Path

import typer
from rich.console import Console

from logsift.cache.manager import CacheManager
from logsift.cache.manager import SavedKind
from logsift.core.analyzer import Analyzer
from logsift.monitor.watcher import LogWatcher
from logsift.output.analysis_format import AnalysisFormat
from logsift.output.analysis_format import render_analysis
from logsift.output.markdown_formatter import format_markdown
from logsift.utils.fzf import is_fzf_available
from logsift.utils.fzf import select_log_file

console = Console()
stderr_console = Console(stderr=True)

# Printed under every empty-cache message: monitor is the one command that writes logs and analyses.
CAPTURE_HINT = '[dim]Run `logsift monitor -- <command>` to capture a run and analyze it[/dim]'


def analyze_log(log_file: str, output_format: str = AnalysisFormat.AUTO, save: bool = True) -> None:
    """Analyze an existing log file.

    Args:
        log_file: Path to the log file to analyze
        output_format: An AnalysisFormat value
        save: Whether to auto-save the analysis result (default: True)
    """
    # Check if file exists
    log_path = Path(log_file)
    if not log_path.exists():
        print(f'Error: Log file not found: {log_file}', file=sys.stderr)
        sys.exit(1)

    # Read log content
    try:
        log_content = log_path.read_text()
    except OSError as e:
        print(f'Error reading log file: {e}', file=sys.stderr)
        sys.exit(1)

    # Run analysis
    analyzer = Analyzer()
    analysis_result = analyzer.analyze(log_content)

    if save:
        report_unsaved(CacheManager().save_analysis(analysis_result, log_path.stem))

    print(render_analysis(analysis_result, output_format))


def log_file_for(argument: str, stream: bool) -> str:
    """The log file analyze's argument names: a path, `latest` for the newest raw log, or `browse` to pick one."""
    if argument == 'latest':
        latest_log = CacheManager().latest(SavedKind.RAW)
        if not latest_log:
            stderr_console.print('[red]Error: No cached logs found[/red]')
            stderr_console.print(CAPTURE_HINT)
            raise typer.Exit(1)
        log_file = str(latest_log)
    elif argument == 'browse':
        if not is_fzf_available():
            stderr_console.print('[red]Error: fzf is not available[/red]')
            stderr_console.print('[dim]Install fzf to use browse mode[/dim]')
            raise typer.Exit(1)
        logs = CacheManager().listing(SavedKind.RAW)
        if not logs:
            stderr_console.print('[yellow]No cached logs found[/yellow]')
            stderr_console.print(CAPTURE_HINT)
            raise typer.Exit(1)
        selected = select_log_file(logs, 'Select log file to analyze')
        if not selected:
            stderr_console.print('[dim]No file selected[/dim]')
            raise typer.Exit(0)
        log_file = selected
    else:
        return argument

    action = 'Stream analyzing' if stream else 'Analyzing'
    stderr_console.print(f'[cyan]{action}: {log_file}[/cyan]\n')
    return log_file


def report_unsaved(failures: list[str]) -> None:
    """Name on stderr each analysis file a run could not save, so a later `latest` finding none is explained."""
    for failure in failures:
        stderr_console.print(f'[yellow]Warning: analysis not saved to {failure}[/yellow]', soft_wrap=True)


def stream_analyze_log(log_file: str, interval: int = 1) -> None:
    """Stream analyze a log file (analyze entire file, then continue as it grows).

    Starts by analyzing the entire existing content of the file, then continues
    to monitor for new lines and re-analyze as the file grows.

    Args:
        log_file: Path to the log file to analyze
        interval: Update interval in seconds for checking new lines
    """
    file_path = Path(log_file).expanduser().resolve()

    if not file_path.exists():
        stderr_console.print(f'[red]Error: Log file not found: {file_path}[/red]')
        sys.exit(1)

    stderr_console.print(f'[blue]Stream analyzing:[/blue] {file_path}')
    stderr_console.print(f'[dim]Update interval: {interval}s (Press Ctrl+C to stop)[/dim]\n')

    # Initialize analyzer
    analyzer = Analyzer()

    # Read and analyze existing content first
    try:
        with file_path.open('r', encoding='utf-8') as f:
            existing_content = f.read()
    except OSError as e:
        stderr_console.print(f'[red]Error reading file: {e}[/red]')
        sys.exit(1)

    # Initial analysis of existing content
    if existing_content:
        result = analyzer.analyze(existing_content)
        console.clear()
        console.print(f'[blue]Stream analyzing:[/blue] {file_path}')
        lines_count = len(existing_content.splitlines())
        errors = result['stats']['total_errors']
        warnings = result['stats']['total_warnings']
        console.print(f'[dim]Lines: {lines_count} | Errors: {errors} | Warnings: {warnings}[/dim]\n')

        if errors > 0 or warnings > 0:
            markdown = format_markdown(result)
            console.print(markdown)
        else:
            console.print('[green]✓[/green] No errors or warnings detected yet')

    # Track accumulated content
    accumulated_content = existing_content

    def process_new_line(line: str) -> None:
        """Process each new log line."""
        nonlocal accumulated_content
        accumulated_content += line + '\n'

        # Re-analyze with new content
        result = analyzer.analyze(accumulated_content)

        # Display live update
        console.clear()
        console.print(f'[blue]Stream analyzing:[/blue] {file_path}')
        lines_count = len(accumulated_content.splitlines())
        errors = result['stats']['total_errors']
        warnings = result['stats']['total_warnings']
        console.print(f'[dim]Lines: {lines_count} | Errors: {errors} | Warnings: {warnings}[/dim]\n')

        if errors > 0 or warnings > 0:
            markdown = format_markdown(result)
            console.print(markdown)
        else:
            console.print('[green]✓[/green] No errors or warnings detected')

    # Start watching for new lines
    watcher = LogWatcher(file_path, interval)

    try:
        watcher.watch(process_new_line)
    except KeyboardInterrupt:
        stderr_console.print('\n[yellow]Stopped stream analysis[/yellow]')
        watcher.stop()
        sys.exit(0)
