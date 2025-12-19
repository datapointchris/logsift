# Pattern File Format

TOML specification for logsift pattern libraries.

## File Structure

Pattern files use TOML format with `[[patterns]]` array:

```toml
[[patterns]]
name = "pattern_name_1"
regex = "Error pattern with (capture)"
severity = "error"
description = "What this error means"
tags = ["tag1", "tag2"]
suggestion = "How to fix"

[[patterns]]
name = "pattern_name_2"
regex = "Another pattern"
severity = "warning"
description = "Warning description"
tags = ["tag3"]
```

## Required Fields

### name

Unique pattern identifier (string):

```toml
name = "python_import_error"
```

Rules:

- Must be unique across all loaded pattern files
- Use `snake_case` convention
- Descriptive and specific

### regex

Python regular expression (string):

```toml
regex = "ModuleNotFoundError: No module named ['\"](.+)['\"]"
```

Rules:

- Valid Python regex syntax
- Use capture groups `()` for important values
- Escape special characters: `\(`, `\)`, `\.`, etc.
- Use raw strings in code to avoid double-escaping

### severity

Error severity level (string):

```toml
severity = "error"  # or "warning" or "info"
```

Valid values:

- `"error"` - Critical failures
- `"warning"` - Non-critical issues
- `"info"` - Informational messages

### description

Human-readable description (string):

```toml
description = "Python module import failed - module not installed or not in PYTHONPATH"
```

Rules:

- Clear and concise
- Explains what the error means
- Can include context

### tags

Array of categorization tags (array of strings):

```toml
tags = ["python", "import", "dependency", "fixable"]
```

Common tags:

- Language/tool: `python`, `npm`, `cargo`, `docker`
- Category: `import`, `syntax`, `type`, `network`, `file`
- Priority: `fixable`, `critical`, `breaking`

## Optional Fields

### suggestion

Fix hint for users/agents (string):

```toml
suggestion = "Install the missing module using: pip install <module_name>"
```

Best practices:

- Actionable and specific
- Include commands when possible
- Reference captured groups if applicable

### automated_fix

Shell command to automatically fix (string):

```toml
automated_fix = "pip install $1"  # $1 = first capture group
```

Rules:

- Must be safe to execute
- Use `$1`, `$2`, etc. for capture groups
- Test thoroughly before deploying

### confidence

Confidence level for suggestion (string):

```toml
confidence = "high"  # or "medium" or "low"
```

Valid values:

- `"high"` - Very confident, safe for automation
- `"medium"` - Likely correct, verify first
- `"low"` - Suggestion only, needs human review

### context_lines_after

Number of lines to extract after this pattern (integer):

```toml
context_lines_after = 10
```

Use for multi-line errors where the root cause appears in subsequent lines (e.g., CalledProcessError with stdout/stderr sections). When set, the analyzer extracts this many lines after the match instead of the default context window.

## Complete Example

```toml
[[patterns]]
name = "webpack_module_not_found"
regex = "Module not found: Error: Can't resolve ['\"](.+)['\"]"
severity = "error"
description = "Webpack cannot find the specified module - import path is incorrect or module not installed"
tags = ["webpack", "import", "module", "fixable"]
suggestion = "Check if the module exists or install it with: npm install <module>"
confidence = "high"

[[patterns]]
name = "python_import_error"
regex = "ModuleNotFoundError: No module named ['\"](.+)['\"]"
severity = "error"
description = "Python module not found - module not installed or not in PYTHONPATH"
tags = ["python", "import", "dependency", "fixable"]
suggestion = "Install the missing module using: pip install $1"
automated_fix = "pip install $1"
confidence = "high"

[[patterns]]
name = "npm_deprecated_warning"
regex = "npm WARN deprecated (.+): (.+)"
severity = "warning"
description = "Package is deprecated and should be replaced"
tags = ["npm", "deprecated", "warning"]
suggestion = "Find an alternative package or update to a maintained version"
confidence = "medium"
```

## Validation

Patterns are validated on load. Invalid patterns cause logsift to fail at startup.

Checks:

- [ ] All required fields present
- [ ] `severity` is valid value
- [ ] `regex` is valid Python regex
- [ ] `tags` is non-empty array
- [ ] `name` is unique (no duplicates)
- [ ] `confidence` (if present) is valid value

Test validation:

```bash
logsift analyze test.log
# Will error if patterns are invalid
```

## Pattern Priority

Patterns are matched in order. **First match wins.**

```toml
# More specific patterns first
[[patterns]]
name = "specific_error"
regex = "SpecificError: (.+) in (.+)"
severity = "error"
description = "Specific error type"
tags = ["specific"]

# More general patterns second
[[patterns]]
name = "general_error"
regex = "Error: (.+)"
severity = "error"
description = "General error"
tags = ["general"]
```

## File Organization

### Built-in Patterns

Located in `src/logsift/patterns/defaults/`:

```text
src/logsift/patterns/defaults/
├── common.toml      # Generic errors
├── python.toml      # Python-specific
├── npm.toml         # Node.js/npm
├── rust.toml        # Rust/Cargo
└── pytest.toml      # Pytest
```

### Custom Patterns

Located in `~/.config/logsift/patterns/`:

```text
~/.config/logsift/patterns/
├── myapp.toml       # Application-specific
├── cicd.toml        # CI/CD pipelines
└── docker.toml      # Docker/containers
```

All files are automatically loaded and merged.

## Regex Examples

### Capture Module Name

```toml
regex = "ModuleNotFoundError: No module named ['\"](.+)['\"]"
# Captures: module name between quotes
```

### Capture File and Line

```toml
regex = "File ['\"](.+)['\"], line (\\d+)"
# Captures: file path and line number
```

### Optional Groups

```toml
regex = "ERROR(?:: (.+))?"
# Captures: optional error message after colon
```

### Multiple Quotes

```toml
regex = "['\"](.+)['\"]"
# Matches: both single and double quotes
```

## Testing Patterns

1. Create pattern file
2. Generate test log with known errors
3. Run logsift and verify matches
4. Check JSON output for correctness

```bash
# Test pattern
echo "ERROR: Test error message" > test.log
logsift analyze test.log --format=json | jq '.errors'
```

## Contributing Patterns

To contribute patterns to built-in library:

1. Add pattern to appropriate file in `src/logsift/patterns/defaults/`
2. Test thoroughly with real logs
3. Document with clear description and tags
4. Submit pull request

See [Development Setup](../development/setup.md).

## See Also

- [Pattern Matching](../concepts/pattern-matching.md) - How patterns work
- [Custom Patterns](../guides/custom-patterns.md) - Creating patterns
- [JSON Schema](json-schema.md) - Output format
