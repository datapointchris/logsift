"""Monitor subcommand implementation.

Monitors a command and analyzes its output.
"""

import os
import shlex
import subprocess  # nosec B404
import sys
import time
from datetime import datetime

from rich.console import Console

from logsift.cache.manager import CacheManager
from logsift.core.analyzer import Analyzer
from logsift.output.json_formatter import format_json
from logsift.output.markdown_formatter import format_markdown
from logsift.output.toon_formatter import format_toon
from logsift.utils.notifications import notify_command_complete
from logsift.utils.tty import detect_output_format

console = Console()
stderr_console = Console(stderr=True)


def _generate_log_name(command: list[str]) -> str:
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

    # Add first command (basename only, no path)
    first_cmd = os.path.basename(command[0])
    parts.append(first_cmd)

    # Add up to 3 more non-flag arguments
    for arg in command[1:]:
        if len(parts) >= 4:  # First cmd + 3 args = 4 total
            break
        if not arg.startswith('-'):
            # Strip common script extensions and path
            clean_arg = os.path.basename(arg)
            for ext in ('.sh', '.py', '.js', '.rb', '.pl', '.php'):
                clean_arg = clean_arg.removesuffix(ext)
            parts.append(clean_arg)

    # Join and sanitize
    name = '-'.join(parts)

    # Limit length to keep filenames reasonable
    if len(name) > 50:
        name = name[:50]

    return name


def monitor_command(
    command: list[str],
    name: str | None = None,
    output_format: str = 'auto',
    stream: bool = False,
    update_interval: int = 60,
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
        stream: Whether to stream all output in real-time (default: False, show periodic updates)
        update_interval: Seconds between progress updates when not streaming (default: 60)
        save_log: Whether to save the log to cache
        notify: Whether to send desktop notification on completion
        external_log: Optional path to external log file to tail while monitoring
        append: Whether to append to existing log instead of creating new
    """
    # Use command name if no name provided
    if name is None:
        name = _generate_log_name(command)

    # Determine log file paths
    log_file = None
    log_paths = None
    if save_log:
        cache = CacheManager()

        if append:
            # Try to get the latest log for this command (context defaults to current working directory)
            log_file = cache.get_latest_log(name)

        if not log_file or not append:
            # Create new log file paths (all 4 formats)
            log_paths = cache.create_paths(name)
            log_file = log_paths['raw']

    # Determine output format early to decide on interactive output
    final_format = output_format
    if output_format == 'auto':
        final_format = detect_output_format()

    # Always show progress unless explicitly using --format=json or --format=toon
    # json and toon formats are for programmatic/LLM consumption, so suppress interactive output
    # This ensures users see streaming output even when stdout is piped, but LLMs get clean output
    show_progress = output_format not in ('json', 'toon')

    # Print initial banner (like run-and-summarize.sh) - only in interactive mode
    if show_progress:
        stderr_console.print('\n[bold cyan]## Starting Monitored Process[/bold cyan]')
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

        # Try to run command directly first (for executables in PATH)
        # If that fails, fall back to interactive shell (for shell functions/aliases)
        use_shell_filtering = False  # Track if we need to filter shell init output
        marker = '___LOGSIFT_COMMAND_START___'

        try:
            # First attempt: direct execution without shell
            process = subprocess.Popen(  # nosec B603
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
        except FileNotFoundError:
            # Command not found - likely a shell function, alias, or builtin
            # Fall back to interactive shell which loads user's configuration
            use_shell_filtering = True
            shell = os.environ.get('SHELL', '/bin/bash')
            command_str = shlex.join(command)

            # Use a marker to separate shell init output from command output
            # We'll filter out everything before the marker
            wrapped_command = f'printf "\\n{marker}\\n" >&2; {command_str}'

            # Use interactive shell to load functions and aliases
            shell_command = [shell, '-i', '-c', wrapped_command]

            process = subprocess.Popen(  # nosec B603
                shell_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

        if show_progress:
            stderr_console.print(f'[dim]Process started with PID: {process.pid}[/dim]')
            if stream:
                stderr_console.print('[dim]Streaming output...[/dim]\n')
            else:
                stderr_console.print(f'[dim]Showing updates every {update_interval}s (use --stream for real-time output)...[/dim]\n')

        # Track time for periodic updates
        last_update_time = time.time()
        update_count = 0

        # Track whether we've seen the marker (for shell init filtering)
        seen_marker = not use_shell_filtering  # If not using shell, act like we've seen it

        # Stream or collect output line by line
        if process.stdout:
            for line in process.stdout:
                # Filter out shell initialization output if using shell fallback
                if use_shell_filtering and not seen_marker:
                    if marker in line:
                        seen_marker = True
                    continue  # Skip all lines until we see the marker

                # Save to log file
                if log_handle:
                    log_handle.write(line)

                # Keep in memory for analysis
                output_lines.append(line.rstrip('\n'))

                # Handle output display based on stream flag
                if show_progress:
                    if stream:
                        # Stream mode: print every line immediately
                        stderr_console.print(line, end='', markup=False, highlight=False)
                    else:
                        # Periodic update mode: show updates at intervals
                        current_time = time.time()
                        if current_time - last_update_time >= update_interval:
                            elapsed = current_time - start_time
                            update_count += 1

                            # Show update with progress info
                            stderr_console.print(
                                f'[dim]Update #{update_count}: {len(output_lines)} lines captured, {elapsed:.0f}s elapsed[/dim]'
                            )

                            last_update_time = current_time

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
        stderr_console.print('\n[bold green]## Process Completed[/bold green]')
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

    # Save all analysis formats if we created new paths
    if log_paths:
        import json
        from contextlib import suppress

        # Save JSON (full analysis with metadata)
        with suppress(OSError), log_paths['json'].open('w', encoding='utf-8') as f:
            json.dump(analysis_result, f, indent=2)

        # Save TOON (compact for LLMs)
        with suppress(OSError, NotImplementedError), log_paths['toon'].open('w', encoding='utf-8') as f:
            f.write(format_toon(analysis_result))

        # Save Markdown (curated for humans)
        with suppress(OSError), log_paths['md'].open('w', encoding='utf-8') as f:
            f.write(format_markdown(analysis_result))

    # Print analysis summary header - only in interactive mode
    if show_progress:
        stderr_console.print('[bold cyan]## Analysis Summary[/bold cyan]')
        stderr_console.print('[dim]' + '─' * 60 + '[/dim]')

    # Format and output results (to stdout, not stderr)
    if final_format == 'json':
        output = format_json(analysis_result)
        print(output)
    elif final_format == 'toon':
        output = format_toon(analysis_result)
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
