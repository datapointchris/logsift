"""Find the file:line references in a log message.

These are the shapes every tool prints a source location in, so no tool's TOML owns them.
"""

import re

# Tried in this order, and a later shape never claims text an earlier one matched.
REFERENCE_SHAPES = (
    # A Windows path: C:\Users\dev\project\src\main.py:100
    re.compile(r'([A-Za-z]:[\\/][\w\\/.-]+\.\w+):(\d+)(?::\d+)?'),
    # A Python traceback: File "/app/main.py", line 42, in handler
    re.compile(r'File\s+"([^"]+)",\s+line\s+(\d+)', re.IGNORECASE),
    # path:line or path:line:column, as most compilers and linters print it: ./src/app.py:42:7
    re.compile(r'([\w/.-]+\.\w+):(\d+)(?::\d+)?'),
)


class FileReferenceDetector:
    """Detect file:line references from log entries."""

    def detect_references(self, text: str) -> list[tuple[str, int]]:
        """Each (path, line) referenced in text, in the order of REFERENCE_SHAPES."""
        references: list[tuple[str, int]] = []
        claimed: list[tuple[int, int]] = []
        for shape in REFERENCE_SHAPES:
            for found in shape.finditer(text):
                start, end = found.span()
                if any(start < claimed_end and end > claimed_start for claimed_start, claimed_end in claimed):
                    continue
                references.append((found.group(1), int(found.group(2))))
                claimed.append((start, end))
        return references
