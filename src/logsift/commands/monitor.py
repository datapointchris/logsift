"""Monitor subcommand implementation.

Monitors a command and analyzes its output.
"""

import sys
import threading
from pathlib import Path

from logsift.cache.manager import CacheManager
from logsift.core.analyzer import Analyzer
from logsift.monitor.process import ProcessMonitor
from logsift.monitor.watcher import LogWatcher
from logsift.output.json_formatter import format_json
from logsift.output.markdown_formatter import format_markdown
from logsift.utils.notifications import notify_command_complete
from logsift.utils.tty import detect_output_format


def monitor_command(
    command: list[str],
    name: str | None = None,
    output_format: str = 'auto',
    save_log: bool = True,
    notify: bool = False,
    external_log: str | None = None,
    append: bool = False,
) -> None:
    """Monitor a command and analyze its output.

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

    # Handle external log watching
    external_lines: list[str] = []
    watcher = None
    watcher_thread = None

    if external_log:
        external_path = Path(external_log).expanduser().resolve()

        if not external_path.exists():
            print(f'Error: External log file not found: {external_path}', file=sys.stderr)
            sys.exit(1)

        # Start watching external log in background
        watcher = LogWatcher(external_path, interval=1)

        def watch_external():
            watcher.watch(external_lines.append)

        watcher_thread = threading.Thread(target=watch_external, daemon=True)
        watcher_thread.start()

    # Run the command
    monitor = ProcessMonitor(command)
    result = monitor.run()

    # Stop external log watcher if running
    if watcher:
        watcher.stop()
        if watcher_thread:
            watcher_thread.join(timeout=1)

    # Merge external log with command output
    if external_lines:
        external_content = '\n'.join(external_lines)
        result['output'] = result['output'] + '\n' + external_content

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

        # Write or append log content
        if append and log_file.exists():
            # Append to existing file
            with log_file.open('a', encoding='utf-8') as f:
                f.write('\n')
                f.write(result['output'])
        else:
            # Write new file
            log_file.write_text(result['output'], encoding='utf-8')

    # Analyze the output
    analyzer = Analyzer()
    analysis_result = analyzer.analyze(result['output'])

    # Add command metadata to analysis result
    analysis_result['summary'] = {
        'status': 'success' if result['success'] else 'failed',
        'exit_code': result['exit_code'],
        'duration_seconds': result['duration_seconds'],
        'command': result['command'],
        'log_file': str(log_file) if log_file else None,
    }

    # Determine output format
    if output_format == 'auto':
        output_format = detect_output_format()

    # Format and output results
    if output_format == 'json':
        output = format_json(analysis_result)
        print(output)
    else:
        # Use markdown for both markdown and plain
        output = format_markdown(analysis_result)
        print(output)

    # Send notification if requested
    if notify:
        notify_command_complete(
            command=result['command'],
            success=result['success'],
            errors=analysis_result['stats']['total_errors'],
            warnings=analysis_result['stats']['total_warnings'],
            duration_seconds=result['duration_seconds'],
        )

    # Exit with command's exit code
    if not result['success']:
        sys.exit(result['exit_code'])
