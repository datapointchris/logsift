"""Analyze subcommand implementation.

Analyzes an existing log file and outputs results.
"""

import sys
from pathlib import Path

import typer
from rich.console import Console

from logsift.cache.manager import CacheManager
from logsift.cache.manager import SavedKind
from logsift.commands.find_saved_file import choose_file
from logsift.commands.find_saved_file import latest_file
from logsift.core.analyzer import Analyzer
from logsift.monitor.watcher import LogWatcher
from logsift.output.analysis_format import AnalysisFormat
from logsift.output.analysis_format import render_analysis
from logsift.output.analysis_format import renderings_to_save
from logsift.output.markdown_formatter import format_markdown

console = Console()
stderr_console = Console(stderr=True)


def analyze_log(log_file: str, output_format: str = AnalysisFormat.AUTO, save: bool = True) -> None:
    """Analyze an existing log file.

    Args:
        log_file: Path to the log file to analyze
        output_format: An AnalysisFormat value
        save: Whether to auto-save the analysis result (default: True)
    """
    log_path = Path(log_file)
    if not log_path.exists():
        print(f'Error: Log file not found: {log_file}', file=sys.stderr)
        sys.exit(1)

    try:
        log_content = log_path.read_text()
    except OSError as e:
        print(f'Error reading log file: {e}', file=sys.stderr)
        sys.exit(1)

    analyzer = Analyzer()
    analysis_result = analyzer.analyze(log_content)

    if save:
        report_unsaved(CacheManager().save_analysis(renderings_to_save(analysis_result), log_path.stem))

    print(render_analysis(analysis_result, output_format))


# Paths a caller may have meant as a flag. When no file by that name exists, the usage error names the flag.
FORMER_SENTINELS = {'latest': '--latest', 'browse': '--choose'}


def log_file_for(path: str | None, latest: bool, choose: bool, stream: bool) -> str:
    """The log file analyze reads: the path given, the most recently written raw log with latest, or one picked with choose."""
    if (path is not None) + latest + choose != 1:
        stderr_console.print('[red]Error: give analyze one of a log file, --latest or --choose[/red]')
        raise typer.Exit(2)

    if path is not None:
        if path in FORMER_SENTINELS and not Path(path).exists():
            stderr_console.print(f'[red]Error: Log file not found: {path}[/red]')
            stderr_console.print(f'To analyze a captured log, pass {FORMER_SENTINELS[path]}')
            raise typer.Exit(2)
        return path

    if latest:
        log_file = str(latest_file(SavedKind.RAW, None))
    else:
        log_file = str(choose_file(SavedKind.RAW, 'Choose a log to analyze', '`logsift analyze --latest`, or `logsift analyze <path>`'))

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

    analyzer = Analyzer()

    try:
        with file_path.open('r', encoding='utf-8') as f:
            existing_content = f.read()
    except OSError as e:
        stderr_console.print(f'[red]Error reading file: {e}[/red]')
        sys.exit(1)

    if existing_content:
        result = analyzer.analyze(existing_content)
        console.clear()
        console.print(f'[blue]Stream analyzing:[/blue] {file_path}')
        lines_count = len(existing_content.splitlines())
        errors = result['stats']['total_errors']
        warnings = result['stats']['total_warnings']
        console.print(f'Lines: {lines_count} | Errors: {errors} | Warnings: {warnings}\n')

        if errors > 0 or warnings > 0:
            markdown = format_markdown(result)
            console.print(markdown)
        else:
            console.print('[green]✓[/green] No errors or warnings detected yet')

    accumulated_content = existing_content

    def process_new_line(line: str) -> None:
        """Process each new log line."""
        nonlocal accumulated_content
        accumulated_content += line + '\n'

        result = analyzer.analyze(accumulated_content)

        console.clear()
        console.print(f'[blue]Stream analyzing:[/blue] {file_path}')
        lines_count = len(accumulated_content.splitlines())
        errors = result['stats']['total_errors']
        warnings = result['stats']['total_warnings']
        console.print(f'Lines: {lines_count} | Errors: {errors} | Warnings: {warnings}\n')

        if errors > 0 or warnings > 0:
            markdown = format_markdown(result)
            console.print(markdown)
        else:
            console.print('[green]✓[/green] No errors or warnings detected')

    watcher = LogWatcher(file_path, interval)

    try:
        watcher.watch(process_new_line)
    except KeyboardInterrupt:
        stderr_console.print('\n[yellow]Stopped stream analysis[/yellow]')
        watcher.stop()
        sys.exit(0)
