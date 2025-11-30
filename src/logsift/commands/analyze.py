"""Analyze subcommand implementation.

Analyzes an existing log file and outputs results.
"""

import sys
from pathlib import Path

from rich.console import Console

from logsift.core.analyzer import Analyzer
from logsift.monitor.watcher import LogWatcher
from logsift.output.json_formatter import format_json
from logsift.output.markdown_formatter import format_markdown
from logsift.output.toon_formatter import format_toon
from logsift.utils.tty import detect_output_format

console = Console()


def analyze_log(log_file: str, output_format: str = 'auto', save: bool = True) -> None:
    """Analyze an existing log file.

    Args:
        log_file: Path to the log file to analyze
        output_format: Desired output format (auto, json, markdown, plain)
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

    # Auto-save analysis result in all formats
    if save:
        import json
        from contextlib import suppress

        from logsift.cache.manager import CacheManager

        cache = CacheManager()

        # Get stem from log file name (without extension)
        stem = log_path.stem

        # Create paths for all analysis formats
        json_path = cache.json_dir / f'{stem}.json'
        toon_path = cache.toon_dir / f'{stem}.toon'
        md_path = cache.md_dir / f'{stem}.md'

        # Silently fail if we can't save - don't interrupt the analysis
        # Save JSON (full analysis with metadata)
        with suppress(OSError), json_path.open('w', encoding='utf-8') as f:
            json.dump(analysis_result, f, indent=2)

        # Save TOON (compact for LLMs)
        with suppress(OSError), toon_path.open('w', encoding='utf-8') as f:
            f.write(format_toon(analysis_result))

        # Save Markdown (curated for humans)
        with suppress(OSError), md_path.open('w', encoding='utf-8') as f:
            f.write(format_markdown(analysis_result))

    # Determine output format
    if output_format == 'auto':
        output_format = detect_output_format()

    # Format and output results
    if output_format == 'json':
        output = format_json(analysis_result)
        print(output)
    elif output_format == 'toon':
        output = format_toon(analysis_result)
        print(output)
    elif output_format == 'markdown':
        output = format_markdown(analysis_result)
        print(output)
    else:
        # Plain format fallback - just use markdown
        output = format_markdown(analysis_result)
        print(output)


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
        console.print(f'[red]Error: Log file not found: {file_path}[/red]')
        sys.exit(1)

    console.print(f'[blue]Stream analyzing:[/blue] {file_path}')
    console.print(f'[dim]Update interval: {interval}s (Press Ctrl+C to stop)[/dim]\n')

    # Initialize analyzer
    analyzer = Analyzer()

    # Read and analyze existing content first
    try:
        with file_path.open('r', encoding='utf-8') as f:
            existing_content = f.read()
    except OSError as e:
        console.print(f'[red]Error reading file: {e}[/red]')
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
        console.print('\n[yellow]Stopped stream analysis[/yellow]')
        watcher.stop()
        sys.exit(0)
