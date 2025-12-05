"""Test file with ruff violations."""

import json  # noqa: F401 - unused import

# F841: Local variable assigned but never used
unused_var = "never used"

# E501: Line too long (will be over 88 chars which is ruff's default)
very_long_variable_name_that_exceeds_the_line_length_limit = "This is a very long line that definitely exceeds the standard line length limit"

# E402: Module level import not at top of file
def some_function():
    """Do something."""
    pass


# F821: Undefined name
result = undefined_variable

# F401: Imported but unused (already have json above)
