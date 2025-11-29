"""FZF integration for interactive log browsing.

Provides utilities for using fzf to select log files and browse logs interactively.
"""

import shutil
import subprocess  # nosec B404
from pathlib import Path


def is_fzf_available() -> bool:
    """Check if fzf is installed and available in PATH.

    Returns:
        True if fzf is available, False otherwise
    """
    return shutil.which('fzf') is not None


def select_log_file(log_files: list[dict[str, str | int]], prompt: str = 'Select log file') -> str | None:
    """Use fzf to interactively select a log file.

    Args:
        log_files: List of log file metadata dictionaries (from CacheManager.list_all_logs)
        prompt: Prompt text to show in fzf

    Returns:
        Path to selected log file, or None if cancelled

    Example:
        cache = CacheManager()
        logs = cache.list_all_logs()
        selected = select_log_file(logs, "Choose log to analyze")
    """
    if not is_fzf_available():
        return None

    if not log_files:
        return None

    # Format log entries for fzf display
    # Format: "name (size) - date"
    entries = []
    for log in log_files:
        name = str(log['name'])
        size_bytes = int(log['size_bytes'])
        modified = str(log['modified_iso']).split('T')[0]

        # Format size
        if size_bytes < 1024:
            size_str = f'{size_bytes}B'
        elif size_bytes < 1024 * 1024:
            size_str = f'{size_bytes / 1024:.1f}KB'
        else:
            size_str = f'{size_bytes / (1024 * 1024):.1f}MB'

        # Create display line with path as suffix
        display = f'{name} ({size_str}) - {modified}'
        path = str(log['path'])

        # Store as "display|path" so we can extract the path later
        entries.append(f'{display}|{path}')

    # Join entries with newlines for fzf input
    input_text = '\n'.join(entries)

    try:
        # Run fzf with enhanced options
        # 100% width, 100% height, with 80% preview and 20% for list (showing ~10 logs)
        result = subprocess.run(  # nosec B603 B607
            [
                'fzf',
                '--prompt',
                f'{prompt}> ',
                '--height',
                '100%',  # Full screen
                '--layout',
                'reverse',
                '--border',
                '--preview',
                'head -100 {2}',  # Preview first 100 lines, {2} is the path after |
                '--preview-window',
                'down:80%:wrap',  # 80% height for preview, 20% for list (~10 logs)
                '--delimiter',
                '|',
                '--with-nth',
                '1',  # Only show first field (before |) in main window
                '--reverse',  # Newest (first in list) at top
            ],
            input=input_text,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0 and result.stdout.strip():
            # Extract path from "display|path" format
            selected = result.stdout.strip()
            if '|' in selected:
                return selected.split('|', 1)[1]
            return None

        return None

    except (subprocess.SubprocessError, FileNotFoundError):
        return None


def browse_log_with_preview(log_path: Path) -> bool:
    """Open a log file in fzf for interactive browsing with preview.

    Args:
        log_path: Path to log file to browse

    Returns:
        True if browsing was successful, False otherwise

    Example:
        log_path = Path("/path/to/log.log")
        browse_log_with_preview(log_path)
    """
    if not is_fzf_available():
        return False

    if not log_path.exists():
        return False

    try:
        # Read log file lines
        with log_path.open('r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()

        # Add line numbers
        numbered_lines = [f'{i + 1:6d} | {line.rstrip()}' for i, line in enumerate(lines)]
        input_text = '\n'.join(numbered_lines)

        # Run fzf with preview showing context around selected line
        subprocess.run(  # nosec B603 B607
            [
                'fzf',
                '--prompt',
                f'{log_path.name}> ',
                '--height',
                '100%',
                '--layout',
                'reverse',
                '--border',
                '--preview',
                f'grep -C 5 {{1}} {log_path}',  # Show 5 lines of context
                '--preview-window',
                'down:50%:wrap',
                '--bind',
                'ctrl-/:toggle-preview',
                '--header',
                'CTRL-/: toggle preview | ESC: exit',
                '--no-sort',  # Keep original order
            ],
            input=input_text,
            text=True,
            check=False,
        )

        return True

    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        return False


def search_in_logs(log_files: list[dict[str, str | int]], search_term: str | None = None) -> str | None:
    """Search through multiple log files and select matching lines.

    Args:
        log_files: List of log file metadata dictionaries
        search_term: Optional initial search term

    Returns:
        Selected line's file path, or None if cancelled

    Example:
        cache = CacheManager()
        logs = cache.list_all_logs()
        selected = search_in_logs(logs, "error")
    """
    if not is_fzf_available():
        return None

    if not log_files:
        return None

    # Build list of lines from all logs with file context
    all_lines = []
    for log in log_files:
        log_path = Path(str(log['path']))
        if not log_path.exists():
            continue

        try:
            with log_path.open('r', encoding='utf-8', errors='replace') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.rstrip()
                    if line:  # Skip empty lines
                        # Format: "filename:line_num | content"
                        all_lines.append(f'{log_path.name}:{line_num} | {line}')
        except OSError:
            continue

    if not all_lines:
        return None

    input_text = '\n'.join(all_lines)

    try:
        # Run fzf with search capability
        fzf_args = [
            'fzf',
            '--prompt',
            'Search logs> ',
            '--height',
            '100%',
            '--layout',
            'reverse',
            '--border',
            '--preview',
            'echo {}',  # Show full line in preview
            '--preview-window',
            'down:3:wrap',
            '--delimiter',
            '|',
            '--with-nth',
            '2',  # Show only content in main window
        ]

        if search_term:
            fzf_args.extend(['--query', search_term])

        result = subprocess.run(  # nosec B603 B607
            fzf_args,
            input=input_text,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0 and result.stdout.strip():
            selected = result.stdout.strip()
            # Extract filename from "filename:line_num | content"
            if '|' in selected:
                file_info = selected.split('|', 1)[0].strip()
                filename = file_info.split(':')[0]
                return filename

        return None

    except (subprocess.SubprocessError, FileNotFoundError):
        return None
