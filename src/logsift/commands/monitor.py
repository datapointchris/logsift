"""Monitor subcommand implementation.

Monitors a command and analyzes its output.
"""

import datetime as dt
import sys
import time
from pathlib import Path
from typing import TextIO

from rich.console import Console

from logsift import process_runner
from logsift.cache.manager import CacheManager
from logsift.cache.manager import SavedKind
from logsift.commands.analyze import report_unsaved
from logsift.core.analyzer import Analyzer
from logsift.output.analysis_format import AnalysisFormat
from logsift.output.analysis_format import render_analysis
from logsift.utils.notifications import notify_command_complete

stderr_console = Console(stderr=True)


def generate_log_name(command: list[str]) -> str:
    """Generate an informative log name from a command.

    Includes all non-flag arguments up to 3 parts for descriptive names.
    Examples:
        ['uv', 'run', 'mkdocs', 'build'] → 'uv-run-mkdocs-build'
        ['bash', 'script.sh'] → 'bash-script'
        ['pytest', '-v', 'tests'] → 'pytest-tests'
        ['make', 'test'] → 'make-test'

    Args:
        command: Command list to generate name from

    Returns:
        Descriptive name for the log file
    """
    if not command:
        return 'unknown'

    parts: list[str] = []

    first_cmd = Path(command[0]).name
    parts.append(first_cmd)

    for arg in command[1:]:
        if len(parts) >= 4:  # First cmd + 3 args = 4 total
            break
        if not arg.startswith('-'):
            clean_arg = Path(arg).name
            for ext in ('.sh', '.py', '.js', '.rb', '.pl', '.php'):
                clean_arg = clean_arg.removesuffix(ext)
            parts.append(clean_arg)

    name = '-'.join(parts)

    # Limit length to keep filenames reasonable
    if len(name) > 50:
        name = name[:50]

    return name


def stop_logging(handle: TextIO | None, path: Path | None, fault: OSError | None = None) -> None:
    """Close the run's log. A write that failed, or a close that does, is a warning: the run and its analysis go on."""
    if fault is not None:
        stderr_console.print(
            f'[yellow]Warning: stopped writing {path}: {fault.strerror or fault}. The analysis still covers every line.[/yellow]',
            soft_wrap=True,
        )
    if handle is None:
        return
    try:
        handle.close()
    except OSError as close_fault:
        if fault is None:
            reason = close_fault.strerror or close_fault
            stderr_console.print(f'[yellow]Warning: the end of {path} was not written: {reason}[/yellow]', soft_wrap=True)


def monitor_command(
    command: list[str],
    name: str | None = None,
    output_format: str = AnalysisFormat.AUTO,
    stream: bool = False,
    update_interval: int = 60,
    quiet: bool = False,
    save_log: bool = True,
    notify: bool = False,
    append: bool = False,
) -> None:
    """Monitor a command and analyze its output with live progress updates.

    Args:
        command: Command to monitor as list of strings
        name: Optional name for the monitoring session
        output_format: An AnalysisFormat value
        stream: Whether to stream all output in real-time (default: False, show periodic updates)
        update_interval: Seconds between progress updates when not streaming (default: 60)
        quiet: Print only the analysis, with nothing on stderr
        save_log: Whether to save the log to cache
        notify: Whether to send desktop notification on completion
        append: Whether to append to existing log instead of creating new
    """
    if name is None:
        name = generate_log_name(command)

    log_file = None
    log_paths = None
    if save_log:
        cache = CacheManager()

        if append:
            log_file = cache.latest_run(name)

        if not log_file or not append:
            log_paths = cache.create_paths(name)
            log_file = log_paths[SavedKind.RAW]

    # Progress goes to stderr so it never mixes into the analysis on stdout
    show_progress = not quiet

    if show_progress:
        stderr_console.print('\n[bold cyan]## Starting Monitored Process[/bold cyan]')
        stderr_console.print(f'[bold]Command:[/bold] {" ".join(command)}')
        stderr_console.print(f'[bold]Name:[/bold] {name}')
        if log_file:
            stderr_console.print(f'[bold]Log:[/bold] {log_file}')
        start_time_str = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        stderr_console.print(f'[bold]Started:[/bold] {start_time_str}\n')

    start_time = time.time()
    output_lines: list[str] = []

    # Bound before the try: both handlers touch them, and an exception can
    # reach a handler before the assignments inside the try have run
    log_handle = None
    process = None

    try:
        if log_file:
            try:
                appending = append and log_file.exists()
                log_handle = log_file.open('a' if appending else 'w', encoding='utf-8', buffering=1)
                if appending:
                    log_handle.write('\n')
            except OSError as fault:
                stop_logging(log_handle, log_file, fault)
                log_handle = None

        process = process_runner.stream(command)

        if show_progress:
            stderr_console.print(f'[dim]Process started with PID: {process.pid}[/dim]')
            if stream:
                stderr_console.print('[dim]Streaming output...[/dim]\n')
            else:
                stderr_console.print(f'[dim]Showing updates every {update_interval}s (use --stream for real-time output)...[/dim]\n')

        last_update_time = time.time()
        update_count = 0

        for line in process.lines():
            if log_handle:
                try:
                    log_handle.write(line)
                except OSError as fault:
                    stop_logging(log_handle, log_file, fault)
                    log_handle = None
            output_lines.append(line.rstrip('\n'))

            if show_progress:
                if stream:
                    stderr_console.print(line, end='', markup=False, highlight=False)
                else:
                    current_time = time.time()
                    if current_time - last_update_time >= update_interval:
                        elapsed = current_time - start_time
                        update_count += 1
                        stderr_console.print(
                            f'[dim]Update #{update_count}: {len(output_lines)} lines captured, {elapsed:.0f}s elapsed[/dim]'
                        )
                        last_update_time = current_time

        exit_code = process.wait()

        stop_logging(log_handle, log_file)
        log_handle = None

    except KeyboardInterrupt:
        stderr_console.print('\n\n[yellow]Interrupted by user[/yellow]')
        if process:
            process.terminate()
        stop_logging(log_handle, log_file)
        sys.exit(130)

    except Exception as e:
        stderr_console.print(f'\n\n[red]Error monitoring command: {e}[/red]')
        # A monitor that exits must not leave the command running unobserved.
        if process:
            process.terminate()
        stop_logging(log_handle, log_file)
        sys.exit(1)

    duration = time.time() - start_time

    if show_progress:
        stderr_console.print('\n[bold green]## Process Completed[/bold green]')
        end_time_str = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        stderr_console.print(f'[bold]Completed:[/bold] {end_time_str}')
        stderr_console.print(f'[bold]Duration:[/bold] {duration:.1f}s ({int(duration // 60)}m {int(duration % 60)}s)')
        stderr_console.print(f'[bold]Exit code:[/bold] {exit_code}\n')

    if show_progress:
        stderr_console.print('[dim]Generating analysis summary...[/dim]\n')
    output_text = '\n'.join(output_lines)
    analyzer = Analyzer()
    analysis_result = analyzer.analyze(output_text)

    analysis_result['summary'] = {
        'status': 'success' if exit_code == 0 else 'failed',
        'exit_code': exit_code,
        'duration_seconds': duration,
        'command': ' '.join(command),
        'log_file': str(log_file) if log_file else None,
    }

    # An appended run reuses an earlier log, whose analysis files belong to that earlier run.
    if log_paths:
        report_unsaved(cache.save_analysis(analysis_result, log_paths[SavedKind.RAW].stem))

    if show_progress:
        stderr_console.print('[bold cyan]## Analysis Summary[/bold cyan]')
        stderr_console.print('[dim]' + '─' * 60 + '[/dim]')

    print(render_analysis(analysis_result, output_format))

    if log_file and show_progress:
        stderr_console.print(f'\n[bold]Full log:[/bold] {log_file}')

    if notify:
        posted = notify_command_complete(
            command=' '.join(command),
            success=exit_code == 0,
            errors=analysis_result['stats']['total_errors'],
            warnings=analysis_result['stats']['total_warnings'],
            duration_seconds=duration,
        )
        if not posted:
            stderr_console.print('[yellow]Desktop notification not sent: it needs notify-send on Linux or osascript on macOS[/yellow]')

    if exit_code != 0:
        sys.exit(exit_code)
