"""Load pattern files from TOML format.

Handles loading both built-in and custom pattern libraries.
"""

import tomllib
from pathlib import Path
from typing import Any


class PatternLoader:
    """Load and manage pattern libraries."""

    REQUIRED_FIELDS = {'name', 'regex', 'severity', 'description', 'tags'}

    def __init__(self) -> None:
        """Initialize the pattern loader."""
        self.patterns: dict[str, Any] = {}

    def load_builtin_patterns(self) -> dict[str, Any]:
        """Load built-in pattern libraries.

        Returns:
            Dictionary of loaded patterns organized by category
        """
        # Get the defaults directory relative to this file
        defaults_dir = Path(__file__).parent / 'defaults'

        if not defaults_dir.exists():
            return {}

        # Load all .toml files from defaults directory
        pattern_files = defaults_dir.glob('*.toml')

        loaded_patterns: dict[str, list[dict[str, Any]]] = {}
        for pattern_file in pattern_files:
            category = pattern_file.stem  # filename without .toml
            pattern_data = self.load_pattern_file(pattern_file)

            if 'patterns' in pattern_data and pattern_data['patterns']:
                loaded_patterns[category] = pattern_data['patterns']

        # Store in instance
        self.patterns.update(loaded_patterns)

        return loaded_patterns

    def load_custom_patterns(self, pattern_dir: Path) -> dict[str, Any]:
        """Load custom pattern libraries from directory.

        Args:
            pattern_dir: Directory containing custom .toml pattern files

        Returns:
            Dictionary of loaded patterns organized by category
        """
        if not pattern_dir.exists() or not pattern_dir.is_dir():
            return {}

        pattern_files = pattern_dir.glob('*.toml')

        loaded_patterns: dict[str, list[dict[str, Any]]] = {}
        for pattern_file in pattern_files:
            category = pattern_file.stem  # filename without .toml
            try:
                pattern_data = self.load_pattern_file(pattern_file)

                if 'patterns' in pattern_data and pattern_data['patterns']:
                    loaded_patterns[category] = pattern_data['patterns']
            except (ValueError, KeyError):
                # Skip invalid pattern files in custom directory
                continue

        # Store in instance
        self.patterns.update(loaded_patterns)

        return loaded_patterns

    def load_pattern_file(self, pattern_file: Path) -> dict[str, Any]:
        """Load a single pattern file.

        Args:
            pattern_file: Path to .toml pattern file

        Returns:
            Dictionary of patterns from the file

        Raises:
            ValueError: If TOML is invalid or patterns are malformed
            KeyError: If required fields are missing from patterns
        """
        try:
            with pattern_file.open('rb') as f:
                data = tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            raise ValueError(f'Invalid TOML in {pattern_file}: {e}') from e

        # Validate patterns if present
        if 'patterns' in data:
            for pattern in data['patterns']:
                self._validate_pattern(pattern)

        return data

    def _validate_pattern(self, pattern: dict[str, Any]) -> None:
        """Validate that a pattern has all required fields.

        Args:
            pattern: Pattern dictionary to validate

        Raises:
            KeyError: If required fields are missing
        """
        missing_fields = self.REQUIRED_FIELDS - set(pattern.keys())
        if missing_fields:
            raise KeyError(f'Pattern missing required fields: {missing_fields}')

        # Validate tags is a list
        if not isinstance(pattern['tags'], list):
            raise ValueError(f"Pattern 'tags' must be a list, got {type(pattern['tags'])}")

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
