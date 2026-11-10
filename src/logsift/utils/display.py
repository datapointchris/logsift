"""Display utilities for showing content with bat or fallback."""

import sys
import time
from pathlib import Path
from typing import TextIO

from logsift import process_runner


def _write_plain(text: str, stream: TextIO | None) -> None:
    """Write text and a trailing newline to stream, or sys.stdout at call time."""
    out = stream if stream is not None else sys.stdout
    out.write(text)
    out.write('\n')
    out.flush()


def display_with_bat(content: str, language: str = 'txt', filename: str | None = None, stream: TextIO | None = None) -> None:
    """Display content using bat with syntax highlighting and paging.

    Args:
        content: Text content to display
        language: Language for syntax highlighting (txt, json, markdown, etc.)
        filename: Optional filename to show in bat header
        stream: Stream for the plain fallback; sys.stdout when omitted

    If bat is not available, falls back to writing the content to stream.
    """
    try:
        cmd = ['bat', '--style=auto', '--paging=auto', f'--language={language}']
        if filename:
            cmd.extend(['--file-name', filename])

        process_runner.run(cmd, input_text=content)
    except FileNotFoundError:
        # bat not installed, fall back to plain output
        _write_plain(content, stream)


def display_file_with_bat(file_path: Path, language: str | None = None, stream: TextIO | None = None) -> None:
    """Display a file using bat with syntax highlighting and paging.

    Args:
        file_path: Path to file to display
        language: Optional language override (auto-detected by default)
        stream: Stream for the plain fallback; sys.stdout when omitted

    If bat is not available, falls back to writing the file content to stream.
    """
    try:
        cmd = ['bat', '--style=auto', '--paging=auto', str(file_path)]
        if language:
            cmd.append(f'--language={language}')

        process_runner.run(cmd)
    except FileNotFoundError:
        # bat not installed, fall back to plain output
        _write_plain(file_path.read_text(), stream)


def tail_file(file_path: Path, interval: int = 1) -> None:
    """Print each line appended to file_path until Ctrl+C, checking every interval seconds."""
    if not file_path.exists():
        print(f'Error: File not found: {file_path}', file=sys.stderr)
        sys.exit(1)

    print(f'Tailing: {file_path}\nPress Ctrl+C to stop\n', file=sys.stderr)
    try:
        with file_path.open('r', encoding='utf-8') as f:
            f.seek(0, 2)
            while True:
                line = f.readline()
                if line:
                    print(line, end='', flush=True)
                else:
                    time.sleep(interval)
    except KeyboardInterrupt:
        print('\nStopped tailing', file=sys.stderr)
        sys.exit(0)
