"""Monitor subcommand implementation.

Monitors a command and analyzes its output.
"""

import subprocess  # nosec B404
import sys
import time
from datetime import datetime

from rich.console import Console

from logsift.cache.manager import CacheManager
from logsift.core.analyzer import Analyzer
from logsift.output.json_formatter import format_json
from logsift.output.markdown_formatter import format_markdown
from logsift.utils.notifications import notify_command_complete
from logsift.utils.tty import detect_output_format

console = Console()
stderr_console = Console(stderr=True)


def monitor_command(
    command: list[str],
    name: str | None = None,
    output_format: str = 'auto',
    save_log: bool = True,
    notify: bool = False,
    external_log: str | None = None,
    append: bool = False,
) -> None:
    """Monitor a command and analyze its output with live progress updates.

    Args:
        command: Command to monitor as list of strings
        name: Optional name for the monitoring session
        output_format: Desired output format (auto, json, markdown)
        save_log: Whether to save the log to cache
        notify: Whether to send desktop notification on completion
        external_log: Optional path to external log file to tail while monitoring
        append: Whether to append to existing log instead of creating new
    """
    # Use command name if no name provided
    if name is None:
        name = command[0] if command else 'unknown'

    # Determine log file path
    log_file = None
    if save_log:
        cache = CacheManager()

        if append:
            # Try to get the latest log for this command
            log_file = cache.get_latest_log(name, context='monitor')

        if not log_file or not append:
            # Create new log file
            log_file = cache.create_log_path(name, context='monitor')

    # Determine output format early to decide on interactive output
    final_format = output_format
    if output_format == 'auto':
        final_format = detect_output_format()

    # Always show progress unless explicitly using --format=json
    # This ensures users see streaming output even when stdout is piped
    show_progress = output_format != 'json'

    # Print initial banner (like run-and-summarize.sh) - only in interactive mode
    if show_progress:
        stderr_console.print('\n[bold cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold cyan]')
        stderr_console.print('[bold cyan] Starting monitored process[/bold cyan]')
        stderr_console.print('[bold cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold cyan]\n')
        stderr_console.print(f'[bold]Command:[/bold] {" ".join(command)}')
        stderr_console.print(f'[bold]Name:[/bold] {name}')
        if log_file:
            stderr_console.print(f'[bold]Log:[/bold] {log_file}')
        start_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        stderr_console.print(f'[bold]Started:[/bold] {start_time_str}\n')

    # Run command and stream output
    start_time = time.time()
    output_lines: list[str] = []

    try:
        # Open log file for writing if save_log is enabled
        log_handle = None
        if log_file:
            mode = 'a' if (append and log_file.exists()) else 'w'
            log_handle = log_file.open(mode, encoding='utf-8', buffering=1)
            if append and log_file.exists():
                log_handle.write('\n')

        # Start the command
        process = subprocess.Popen(  # nosec B603
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        if show_progress:
            stderr_console.print(f'[dim]Process started with PID: {process.pid}[/dim]')
            stderr_console.print('[dim]Streaming output...[/dim]\n')

        # Stream output line by line
        if process.stdout:
            for line in process.stdout:
                # Print to console only in interactive mode
                if show_progress:
                    stderr_console.print(line, end='', markup=False, highlight=False)

                # Save to log file
                if log_handle:
                    log_handle.write(line)

                # Keep in memory for analysis
                output_lines.append(line.rstrip('\n'))

        # Wait for process to complete
        exit_code = process.wait()

        # Close log file
        if log_handle:
            log_handle.close()

    except KeyboardInterrupt:
        console.print('\n\n[yellow]Interrupted by user[/yellow]')
        if process:
            process.terminate()
            process.wait()
        if log_handle:
            log_handle.close()
        sys.exit(130)

    except Exception as e:
        console.print(f'\n\n[red]Error monitoring command: {e}[/red]')
        if log_handle:
            log_handle.close()
        sys.exit(1)

    # Calculate duration
    duration = time.time() - start_time

    # Print completion banner - only in interactive mode
    if show_progress:
        stderr_console.print('\n[bold green]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold green]')
        stderr_console.print('[bold green] Process completed[/bold green]')
        stderr_console.print('[bold green]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold green]\n')
        end_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        stderr_console.print(f'[bold]Completed:[/bold] {end_time_str}')
        stderr_console.print(f'[bold]Duration:[/bold] {duration:.1f}s ({int(duration // 60)}m {int(duration % 60)}s)')
        stderr_console.print(f'[bold]Exit code:[/bold] {exit_code}\n')

    # Analyze the output
    if show_progress:
        stderr_console.print('[dim]Generating analysis summary...[/dim]\n')
    output_text = '\n'.join(output_lines)
    analyzer = Analyzer()
    analysis_result = analyzer.analyze(output_text)

    # Add command metadata
    analysis_result['summary'] = {
        'status': 'success' if exit_code == 0 else 'failed',
        'exit_code': exit_code,
        'duration_seconds': duration,
        'command': ' '.join(command),
        'log_file': str(log_file) if log_file else None,
    }

    # Print analysis summary header - only in interactive mode
    if show_progress:
        stderr_console.print('[bold cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold cyan]')
        stderr_console.print('[bold cyan] ANALYSIS SUMMARY[/bold cyan]')
        stderr_console.print('[bold cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold cyan]\n')

    # Format and output results (to stdout, not stderr)
    if final_format == 'json':
        output = format_json(analysis_result)
        print(output)
    else:
        output = format_markdown(analysis_result)
        print(output)

    if log_file and show_progress:
        stderr_console.print(f'\n[dim]Full log: {log_file}[/dim]')

    # Send notification if requested
    if notify:
        notify_command_complete(
            command=' '.join(command),
            success=exit_code == 0,
            errors=analysis_result['stats']['total_errors'],
            warnings=analysis_result['stats']['total_warnings'],
            duration_seconds=duration,
        )

    # Exit with command's exit code
    if exit_code != 0:
        sys.exit(exit_code)
