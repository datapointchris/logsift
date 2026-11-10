"""fzf: picking a saved file, and searching a log's lines."""

import shutil
from pathlib import Path

from logsift import process_runner
from logsift.utils.display import human_size


def is_fzf_available() -> bool:
    """Check if fzf is installed and available in PATH.

    Returns:
        True if fzf is available, False otherwise
    """
    return shutil.which('fzf') is not None


def select_log_file(log_files: list[dict[str, str | int]], prompt: str = 'Select log file') -> str | None:
    """Use fzf to interactively select a log file.

    Args:
        log_files: List of log file metadata dictionaries (from CacheManager.listing)
        prompt: Prompt text to show in fzf

    Returns:
        Path to selected log file, or None if cancelled

    Example:
        logs = CacheManager().listing(SavedKind.RAW)
        selected = select_log_file(logs, "Choose log to analyze")
    """
    if not is_fzf_available():
        return None

    if not log_files:
        return None

    entries = []
    for log in log_files:
        modified = str(log['modified_iso']).split('T')[0]
        display = f'{log["name"]} ({human_size(int(log["size_bytes"]))}) - {modified}'
        path = str(log['path'])

        # Store as "display|path" so we can extract the path later
        entries.append(f'{display}|{path}')

    input_text = '\n'.join(entries)

    try:
        # 100% width, 100% height, with 80% preview and 20% for list (showing ~10 logs)
        result = process_runner.run(
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
            input_text=input_text,
            capture=True,
        )

        if result.returncode == 0 and result.stdout.strip():
            selected = result.stdout.strip()
            if '|' in selected:
                return selected.split('|', 1)[1]
            return None

        return None

    except OSError:
        return None


def search_log_lines(log_path: Path) -> bool:
    """Open a log file in fzf for interactive browsing with preview.

    Args:
        log_path: Path to the log to search

    Returns:
        True if browsing was successful, False otherwise

    Example:
        log_path = Path("/path/to/log.log")
        search_log_lines(log_path)
    """
    if not is_fzf_available():
        return False

    if not log_path.exists():
        return False

    try:
        with log_path.open('r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()

        numbered_lines = [f'{i + 1:6d} | {line.rstrip()}' for i, line in enumerate(lines)]
        input_text = '\n'.join(numbered_lines)

        # Run fzf with preview showing context around selected line
        process_runner.run(
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
            input_text=input_text,
        )

        return True

    except OSError:
        return False
