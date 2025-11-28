# Custom Patterns

Create custom TOML pattern libraries for domain-specific error detection.

## Quick Start

Create a custom pattern file:

```bash
mkdir -p ~/.config/logsift/patterns
cat > ~/.config/logsift/patterns/myapp.toml << 'EOF'
[[patterns]]
name = "myapp_database_error"
regex = "DATABASE ERROR: (.+)"
severity = "error"
description = "Database connection or query error"
tags = ["database", "myapp"]
suggestion = "Check database connection string and credentials"
EOF
```

Patterns are automatically loaded on next logsift run.

## Pattern Format

```toml
[[patterns]]
name = "unique_pattern_name"
regex = "Error pattern with (capture groups)"
severity = "error"  # error, warning, or info
description = "Human-readable description"
tags = ["tag1", "tag2"]
suggestion = "How to fix this error"  # Optional
automated_fix = "command to run"      # Optional
confidence = "high"                    # Optional: high, medium, low
```

### Required Fields

- `name` - Unique identifier (no duplicates)
- `regex` - Python regex pattern
- `severity` - `error`, `warning`, or `info`
- `description` - What this error means
- `tags` - Array of categorization tags

### Optional Fields

- `suggestion` - Fix hint for users/agents
- `automated_fix` - Shell command to fix
- `confidence` - `high`, `medium`, `low`

## Examples

### API Error Pattern

```toml
[[patterns]]
name = "api_rate_limit"
regex = "HTTP 429: Too Many Requests"
severity = "warning"
description = "API rate limit exceeded"
tags = ["api", "rate-limit", "http"]
suggestion = "Implement exponential backoff retry logic"
confidence = "high"
```

### Configuration Error

```toml
[[patterns]]
name = "missing_config_file"
regex = "FileNotFoundError: \\[Errno 2\\] No such file or directory: '(.+\\.yaml)'"
severity = "error"
description = "Configuration file not found"
tags = ["config", "file", "fixable"]
suggestion = "Create the missing configuration file"
automated_fix = "touch $1"  # $1 = captured filename
confidence = "medium"
```

### Custom Application Error

```toml
[[patterns]]
name = "myapp_authentication_failed"
regex = "AUTH_ERROR: Invalid credentials for user (.+)"
severity = "error"
description = "User authentication failed"
tags = ["auth", "security", "myapp"]
suggestion = "Verify username and password, check user exists in database"
```

## Regex Tips

### Capture Groups

```toml
# Capture module name
regex = "ModuleNotFoundError: No module named ['\"](.+)['\"]"
# Group 1 = module name

# Multiple captures
regex = "ERROR at (.+):(\\d+) - (.+)"
# Group 1 = file, Group 2 = line, Group 3 = message
```

### Escaping

```toml
# Escape special regex characters
regex = "Error: Cannot find module \\((.+)\\)"
# \\( = literal parenthesis

# Quotes
regex = "['\"](.+)['\"]"
# Matches both single and double quotes
```

### Common Patterns

```toml
# File paths
regex = "Error in ([a-zA-Z0-9_/.-]+\\.py)"

# Line numbers
regex = "line (\\d+)"

# URLs
regex = "Failed to fetch (https?://[^\\s]+)"

# Timestamps
regex = "\\[(\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2})\\]"
```

## Testing Patterns

Validate your pattern file:

```bash
# Test against sample log
logsift analyze test.log
```

Check:

- [ ] Pattern matches expected errors
- [ ] Regex is not too greedy
- [ ] Suggestions are helpful
- [ ] No duplicate pattern names

## Pattern Priority

Patterns are tried in order. First match wins.

```toml
# More specific pattern first
[[patterns]]
name = "python_import_error_specific"
regex = "ImportError: cannot import name '(.+)' from '(.+)'"
severity = "error"
description = "Specific import failed"
tags = ["python", "import"]

# More general pattern second
[[patterns]]
name = "python_import_error_general"
regex = "ImportError: (.+)"
severity = "error"
description = "General import error"
tags = ["python", "import"]
```

## Organizing Pattern Files

```
~/.config/logsift/patterns/
├── python.toml      # Python-specific patterns
├── docker.toml      # Docker/container patterns
├── ci.toml          # CI/CD patterns
└── myapp.toml       # Application-specific
```

Each file can contain multiple `[[patterns]]` sections.

## Contributing Patterns

Share useful patterns with the community:

1. Create pattern file in `src/logsift/patterns/defaults/`
2. Add comprehensive examples
3. Test thoroughly
4. Submit pull request

See [Development Setup](../development/setup.md).

## See Also

- [Pattern Format API](../api/pattern-format.md) - Complete spec
- [Pattern Matching Concepts](../concepts/pattern-matching.md) - How it works
