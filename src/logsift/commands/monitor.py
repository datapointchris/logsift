"""Monitor subcommand implementation.

Monitors a command and analyzes its output.
"""

import sys

from logsift.cache.manager import CacheManager
from logsift.core.analyzer import Analyzer
from logsift.monitor.process import ProcessMonitor
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
) -> None:
    """Monitor a command and analyze its output.

    Args:
        command: Command to monitor as list of strings
        name: Optional name for the monitoring session
        output_format: Desired output format (auto, json, markdown)
        save_log: Whether to save the log to cache
        notify: Whether to send desktop notification on completion
    """
    # Use command name if no name provided
    if name is None:
        name = command[0] if command else 'unknown'

    # Run the command
    monitor = ProcessMonitor(command)
    result = monitor.run()

    # Save log to cache if requested
    log_file = None
    if save_log:
        cache = CacheManager()
        log_file = cache.create_log_path(name, context='monitor')
        log_file.write_text(result['output'])

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
