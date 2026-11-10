# 5-Minute Quickstart

Get up and running with logsift in 5 minutes.

## Installation

Install logsift as a global tool using UV:

```bash
# Clone the repository
git clone https://github.com/datapointchris/logsift.git
cd logsift

# Install as editable global tool
uv tool install --editable .
```

Verify installation:

```bash
logsift --version  # Prints the installed version
```

## Your First Analysis

Let's analyze a simple command that produces errors:

```bash
# Monitor a command and analyze its output
logsift monitor -- python -c "import nonexistent_module"
```

The output shows:

- The command's exit code and duration, on stderr
- Each error and warning, with the range of lines around it
- File references, where a message names one
- A fix hint, where the matching pattern has one

## Monitor a Build

Monitor a real build command:

```bash
# Monitor npm build
logsift monitor -- npm run build

# Monitor with custom name for better organization
logsift monitor -n my-app-build -- npm run build

# Get JSON output for scripting
logsift monitor --format=json -- npm run build
```

The raw log is saved under `~/.cache/logsift/raw/`, or `$XDG_CACHE_HOME/logsift/raw/`, and
`logsift analyze --latest` analyzes it again.

## Analyze an Existing Log

Have an existing log file? Analyze it directly:

```bash
# Analyze a log file
logsift analyze /var/log/app.log

# Force JSON output (useful for piping to jq)
logsift analyze build.log --format=json

# Force Markdown output (even when piping)
logsift analyze build.log --format=markdown
```

## Understanding the Output

### Terminal Output (Markdown)

When running in a terminal, `monitor` prints its progress, exit code and duration to stderr, then
the analysis to stdout as Markdown:

```markdown
# Log Analysis Results

**Errors:** 1 | **Warnings:** 0

## Errors

### Error #1 (Line 4)

ModuleNotFoundError: No module named 'nonexistent_module'

**Context:** Lines 2-4
```

An error a pattern has a fix hint for adds a `**Suggestion:**` line, and one naming a file adds
`**Files:**`.

### JSON Output (for LLMs and Scripts)

With `--format=json`, logsift prints the document
[`schemas/analysis.schema.json`](https://github.com/datapointchris/logsift/blob/main/schemas/analysis.schema.json)
describes. [JSON Schema](api/json-schema.md) says how to read it:

```bash
logsift monitor --quiet --format=json -- python -c "import nonexistent_module" \
  | jq -c '{status: .summary.status, errors: [.errors[] | {message, pattern_name}]}'
# {"status":"failed","errors":[{"message":"ModuleNotFoundError: No module named 'nonexistent_module'","pattern_name":"module_not_found"}]}
```

## Auto-Format Detection

logsift automatically detects the best output format:

- **Terminal (TTY)**: Markdown
- **Piped/headless**: compact toon for LLM consumption. Pass `--format json` for JSON.

```bash
# Terminal → Markdown
logsift analyze app.log

# JSON for jq
logsift analyze app.log --format=json | jq '.errors[0].message'

# Force specific format
logsift analyze app.log --format=json
logsift analyze app.log --format=markdown
```

## Real-World Example: Python Tests

Monitor pytest with coverage:

```bash
logsift monitor -n pytest-run -- uv run pytest --cov=myapp tests/
```

If tests fail, logsift extracts:

- Failed test names with `file:line` references
- Assertion errors with context
- Missing dependencies
- Actionable fix suggestions

## Integration with Claude Code

The real power of logsift comes from agentic integration. Enable Claude Code to autonomously fix errors:

```python
# Claude Code workflow
1. Run: logsift monitor --format=json -- npm run build
2. Parse JSON to extract errors and suggestions
3. Apply suggested fixes automatically
4. Retry: logsift monitor --format=json -- npm run build
5. Repeat until success
```

See [Agentic Integration](concepts/agentic-integration.md) for complete workflows.

## Custom Patterns

Create custom patterns for domain-specific errors:

```bash
# Create custom pattern file
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

Every run reads them, before the built-in patterns, so yours wins a line both match.
logsift reads `$XDG_CONFIG_HOME/logsift/patterns/` when `XDG_CONFIG_HOME` is set.

See [Custom Patterns](guides/custom-patterns.md) for detailed guidance.

## Configuration

logsift needs no config file. To make every run print JSON, create
`$XDG_CONFIG_HOME/logsift/config.toml`, else `~/.config/logsift/config.toml`:

```toml
print_analysis_as = "json"
```

`logsift config` prints each value logsift will use and the layer that set it. See
[Config Format](api/config-format.md) for every key.

## Cache Management

Raw logs are saved to `~/.cache/logsift/raw/`, and their analyses beside them under `json/`,
`toon/` and `md/`. Clean old logs:

```bash
# Clean logs older than 30 days
logsift logs clean --days 30
```

## Next Steps

Now that you have logsift running:

1. **[CLI Reference](cli-reference.md)** - Explore all commands and options
2. **[Agentic Integration](concepts/agentic-integration.md)** - Use with Claude Code
3. **[Structured Logging](guides/structured-logging.md)** - Write better logs
4. **[Custom Patterns](guides/custom-patterns.md)** - Create domain patterns

## Getting Help

- Run `logsift --help` for quick reference
- Check [CLI Reference](cli-reference.md) for detailed docs
- Report issues on [GitHub](https://github.com/datapointchris/logsift/issues)
