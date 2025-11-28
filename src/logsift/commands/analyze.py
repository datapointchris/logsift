"""Analyze subcommand implementation.

Analyzes an existing log file and outputs results.
"""

import sys
from pathlib import Path

from logsift.core.analyzer import Analyzer
from logsift.output.json_formatter import format_json
from logsift.output.markdown_formatter import format_markdown
from logsift.utils.tty import detect_output_format


def analyze_log(log_file: str, output_format: str = 'auto') -> None:
    """Analyze an existing log file.

    Args:
        log_file: Path to the log file to analyze
        output_format: Desired output format (auto, json, markdown, plain)
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

    # Determine output format
    if output_format == 'auto':
        output_format = detect_output_format()

    # Format and output results
    if output_format == 'json':
        output = format_json(analysis_result)
        print(output)
    elif output_format == 'markdown':
        output = format_markdown(analysis_result)
        print(output)
    else:
        # Plain format fallback - just use markdown
        output = format_markdown(analysis_result)
        print(output)
