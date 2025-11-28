# Pattern Matching

How logsift uses TOML pattern libraries to identify and suggest fixes for errors.

## Overview

logsift's pattern matching system automatically detects error types and provides fix suggestions using TOML-based pattern libraries.

## Pattern Structure

Each pattern is defined in TOML format:

```toml
[[patterns]]
name = "python_import_error"
regex = "ModuleNotFoundError: No module named ['\"](.+)['\"]"
severity = "error"
description = "Python module import failed"
tags = ["python", "import", "dependency"]
suggestion = "Install the missing module using pip install <module>"
```

### Required Fields

- `name` - Unique identifier for the pattern
- `regex` - Regular expression to match error messages
- `severity` - `error`, `warning`, or `info`
- `description` - Human-readable description
- `tags` - List of tags for categorization

### Optional Fields

- `suggestion` - Fix hint for automated workflows
- `automated_fix` - Shell command to fix (if applicable)
- `confidence` - `high`, `medium`, `low` (for suggestions)

## Built-in Patterns

logsift includes patterns for common tools:

### Python (`patterns/defaults/python.toml`)

- Import errors
- Syntax errors
- Type errors
- Module not found
- Attribute errors

### npm/Node.js (`patterns/defaults/npm.toml`)

- Module not found
- Package version conflicts
- Build errors
- Dependency issues

### Rust/Cargo (`patterns/defaults/rust.toml`)

- Compilation errors
- Type mismatches
- Borrow checker errors
- Missing dependencies

### Pytest (`patterns/defaults/pytest.toml`)

- Test failures
- Assertion errors
- Fixture issues

## Pattern Matching Process

```
1. Parse log line by line
2. For each line, try all patterns
3. First match wins (patterns are ordered)
4. Extract matched groups
5. Add suggestion if available
6. Tag with pattern name
```

## Custom Patterns

Create domain-specific patterns in `~/.config/logsift/patterns/`:

```toml
# ~/.config/logsift/patterns/myapp.toml
[[patterns]]
name = "myapp_database_connection_error"
regex = "DatabaseConnectionError: Unable to connect to (.+)"
severity = "error"
description = "Failed to connect to database"
tags = ["database", "connection", "myapp"]
suggestion = "Check database credentials and network connectivity"
```

Patterns are automatically loaded from:

1. Built-in: `src/logsift/patterns/defaults/*.toml`
2. Custom: `~/.config/logsift/patterns/*.toml`

## See Also

- [Pattern Format](../api/pattern-format.md) - TOML specification
- [Custom Patterns](../guides/custom-patterns.md) - Creating patterns
