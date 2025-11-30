"""Display utilities for showing content with bat or fallback."""

import subprocess  # nosec B404
from pathlib import Path


def display_with_bat(content: str, language: str = 'txt', filename: str | None = None) -> None:
    """Display content using bat with syntax highlighting and paging.

    Args:
        content: Text content to display
        language: Language for syntax highlighting (txt, json, markdown, etc.)
        filename: Optional filename to show in bat header

    If bat is not available, falls back to printing to stdout.
    """
    try:
        cmd = ['bat', '--style=auto', '--paging=auto', f'--language={language}']
        if filename:
            cmd.extend(['--file-name', filename])

        subprocess.run(cmd, input=content, text=True, check=False)  # nosec B603
    except FileNotFoundError:
        # bat not installed, fall back to regular print
        print(content)


def display_file_with_bat(file_path: Path, language: str | None = None) -> None:
    """Display a file using bat with syntax highlighting and paging.

    Args:
        file_path: Path to file to display
        language: Optional language override (auto-detected by default)

    If bat is not available, falls back to printing file content.
    """
    try:
        cmd = ['bat', '--style=auto', '--paging=auto', str(file_path)]
        if language:
            cmd.append(f'--language={language}')

        subprocess.run(cmd, check=False)  # nosec B603
    except FileNotFoundError:
        # bat not installed, fall back to regular print
        print(file_path.read_text())
