# Agentic Integration

How to use logsift with Claude Code and other AI agents for diagnose-fix-retry workflows.

## Overview

A build or test run prints thousands of lines, and an agent reading them all spends its context on
noise. logsift runs the command, finds the error and warning lines with TOML patterns, and hands the
agent those lines with their context, the pattern that recognized each, and the pattern's fix hint.
The agent still decides each fix. logsift tells it where to look and what the line probably means.

## The Agentic Loop

```text
1. RUN    → logsift monitor --minimal --format=json -- <command>
2. READ   → summary.status, then each error's message, pattern_name, suggestion and file_references
3. FIX    → the agent edits the code the errors point at
4. VERIFY → run the same command again
5. REPEAT → until summary.status is success, or a bounded number of attempts
```

`--minimal` keeps the progress banners off stderr. `logsift monitor` exits with the command's own
exit code, so a shell loop can test it directly.

## Choosing a Format

- **Piped with no `--format`, logsift prints toon**, a compact text form meant for an LLM to read.
  It costs fewer tokens than JSON, and suits an agent that reads the output itself. Each issue keeps
  its id, severity, line, message, code and suggestion. It drops `pattern_name`, `tags`,
  `file_references` and the context lines, except the lines a multi-line pattern asked for.
- **`--format=json` is for a program** that parses the output.
  [`schemas/analysis.schema.json`](https://github.com/datapointchris/logsift/blob/main/schemas/analysis.schema.json)
  is its contract, and [JSON Schema](../api/json-schema.md) says how to read it.

## Key Fields for Agents

- `summary.status` and `summary.exit_code`: did the command succeed. Only `monitor` writes `summary`.
- `errors[].message`: the line as logged.
- `errors[].pattern_name`: which pattern recognized it, for routing. Absent when a JSON or key=value
  line was flagged by its own level field.
- `errors[].suggestion`: the pattern's fix hint, a string, present only where the pattern has one.
- `errors[].file_references`: `[path, line]` pairs found in the message.
- `errors[].context_before` and `context_after`: the parsed lines around it, each with
  `line_number` and `message`.
- `hooks.failed`: the pre-commit hooks that failed, when the log is a pre-commit run.

## Claude Code Integration

### Basic Pattern

```python
import json
import subprocess


def run_with_logsift(command: list[str]) -> dict:
    """Run a command through logsift and parse its JSON analysis."""
    result = subprocess.run(['logsift', 'monitor', '--minimal', '--format=json', '--', *command], capture_output=True, text=True)
    return json.loads(result.stdout)


analysis = run_with_logsift(['npm', 'run', 'build'])
if analysis['summary']['status'] == 'failed':
    for error in analysis['errors']:
        print(f'Line {error["line_in_log"]}: {error["message"]}')
        if 'suggestion' in error:
            print(f'  Hint: {error["suggestion"]}')
        for path, line in error.get('file_references', []):
            print(f'  At {path}:{line}')
```

### Bounded Fix Loop

```python
def fix_loop(command: list[str], max_attempts: int = 3) -> bool:
    """Run, fix what the errors point at, and retry until success or max attempts."""
    for _ in range(max_attempts):
        analysis = run_with_logsift(command)
        if analysis['summary']['status'] == 'success':
            return True
        for error in analysis['errors']:
            propose_and_apply_fix(error)  # the agent's own judgment, guided by the fields above
    escalate_to_human(analysis)
    return False
```

### Pattern-Based Routing

```python
def handle_error(error: dict) -> None:
    """Route an error to a handler by the pattern that recognized it."""
    handlers = {
        'module_not_found': fix_python_import,
        'pytest_assertion_error': fix_pytest_assertion,
        'shell_command_not_found': install_missing_command,
    }
    handler = handlers.get(error.get('pattern_name'), apply_generic_fix)
    handler(error)
```

The TOML files under `src/logsift/patterns/defaults/` hold every built-in pattern name.

## Best Practices

### 1. Ask for JSON When a Program Parses It

```bash
# ✓ A program parses this
logsift monitor --minimal --format=json -- make test

# ✓ An agent reads this directly, as toon
logsift monitor --minimal -- make test
```

### 2. Check Status First

```python
if analysis['summary']['status'] == 'success':
    return
```

### 3. Route on `pattern_name`, Not the Message Text

```python
# ✓ Pattern-based routing
if error.get('pattern_name') == 'module_not_found':
    fix_import(error)

# ✗ String matching is fragile
if 'ModuleNotFoundError' in error['message']:
    fix_import(error)
```

### 4. Use `file_references` Rather Than Parsing the Message

```python
for path, line in error.get('file_references', []):
    open_in_editor(path, line)
```

### 5. Limit Retry Attempts

```python
for attempt in range(MAX_ATTEMPTS):
    if try_fix():
        break
else:
    escalate()
```

### 6. Reread a Run Without Running It Again

Every `monitor` run saves the raw log under `$XDG_CACHE_HOME/logsift/raw/` and its analysis under
`json/`, `toon/` and `md/`, with `~/.cache/logsift` as the default:

```bash
logsift analyze --latest --format=json # re-run the patterns over the last capture
logsift analyzed latest                # reread the last saved analysis
```

## Troubleshooting

### Agent Not Parsing JSON

Piped output defaults to toon, so pass `--format=json` to get JSON:

```python
# ✓ JSON
subprocess.run(['logsift', 'monitor', '--format=json', '--', 'command'])

# ✗ toon when piped, Markdown on a terminal
subprocess.run(['logsift', 'monitor', '--', 'command'])
```

### Missing Suggestions

Many patterns carry no `suggestion`, and the key is then absent:

```python
hint = error.get('suggestion')  # ✓ None when there is no hint
hint = error['suggestion']      # ✗ KeyError when there is no hint
```

### Pattern Not Matched

A line no specific pattern knows falls to a catch-all such as `generic_error`. Add a custom pattern
to recognize it, and it is tried before every built-in one:

```toml
# ~/.config/logsift/patterns/custom.toml
[[patterns]]
name = "my_custom_error"
regex = "MY ERROR: (.+)"
severity = "error"
description = "Custom error type"
tags = ["custom"]
suggestion = "Fix this custom error"
```

## See Also

- [JSON Schema](../api/json-schema.md) - How to read the JSON output
- [Pattern Format](../api/pattern-format.md) - Create custom patterns
- [Structured Logging](../guides/structured-logging.md) - Write log-friendly scripts
- [CLI Reference](../cli-reference.md) - Complete command documentation
