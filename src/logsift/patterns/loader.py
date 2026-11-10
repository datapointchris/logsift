"""Load pattern files from TOML format.

Handles loading both built-in and custom pattern libraries.
"""

import tomllib
from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path
from typing import Any

from logsift.patterns.validator import validate_pattern_file

BUILTIN_PATTERNS = files('logsift.patterns') / 'defaults'


class PatternLoader:
    """Load and manage pattern libraries."""

    def __init__(self) -> None:
        """Initialize the pattern loader."""
        self.patterns: dict[str, Any] = {}

    def load_builtin_patterns(self) -> dict[str, Any]:
        """Load built-in pattern libraries, in the order detection tries them.

        The first pattern to match a line wins. Files are tried by name, and common.toml goes last,
        because its catch-alls such as generic_error would otherwise shadow a tool's specific pattern.

        Returns:
            Dictionary of loaded patterns organized by category
        """
        pattern_files = sorted(
            (entry for entry in BUILTIN_PATTERNS.iterdir() if entry.name.endswith('.toml')),
            key=lambda entry: (entry.name == 'common.toml', entry.name),
        )

        loaded_patterns: dict[str, list[dict[str, Any]]] = {}
        for pattern_file in pattern_files:
            category = pattern_file.name.removesuffix('.toml')
            loaded_patterns[category] = self.load_pattern_file(pattern_file)['patterns']

        # Store in instance
        self.patterns.update(loaded_patterns)

        return loaded_patterns

    def load_custom_patterns(self, pattern_dir: Path) -> dict[str, Any]:
        """Load custom pattern libraries from directory, tried by file name.

        Args:
            pattern_dir: Directory containing custom .toml pattern files

        Returns:
            Dictionary of loaded patterns organized by category

        Raises:
            ValueError: If a file is not valid TOML or holds an invalid pattern, naming the file
        """
        if not pattern_dir.exists() or not pattern_dir.is_dir():
            return {}

        loaded_patterns: dict[str, list[dict[str, Any]]] = {}
        for pattern_file in sorted(pattern_dir.glob('*.toml')):
            try:
                pattern_data = self.load_pattern_file(pattern_file)
            except ValueError as e:
                raise ValueError(f'{pattern_file}: {e}') from e

            loaded_patterns[pattern_file.stem] = pattern_data['patterns']

        # Store in instance
        self.patterns.update(loaded_patterns)

        return loaded_patterns

    def load_pattern_file(self, pattern_file: Traversable) -> dict[str, Any]:
        """Load a single pattern file.

        Args:
            pattern_file: Path to .toml pattern file

        Returns:
            Dictionary of patterns from the file

        Raises:
            ValueError: If the TOML is invalid, holds no patterns list, or a pattern is malformed
        """
        try:
            with pattern_file.open('rb') as f:
                data = tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            raise ValueError(f'Invalid TOML in {pattern_file}: {e}') from e

        validate_pattern_file(data)

        return data

    def get_all_patterns(self) -> dict[str, list[dict[str, Any]]]:
        """Get all loaded patterns.

        Returns:
            Dictionary of all patterns organized by category
        """
        return self.patterns.copy()

    def get_patterns_by_category(self, category: str) -> list[dict[str, Any]]:
        """Get patterns for a specific category.

        Args:
            category: Category name (e.g., 'brew', 'common')

        Returns:
            List of patterns for the category, or empty list if not found
        """
        return self.patterns.get(category, [])
