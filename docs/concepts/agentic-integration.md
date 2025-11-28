# Agentic Integration

How to use logsift with Claude Code and other AI agents for fully automated diagnose-fix-retry workflows.

## Overview

logsift was designed from the ground up to enable AI agents to autonomously fix errors. The JSON output schema provides structured, predictable information that agents can parse and act on without human intervention.

## Why logsift for Agents?

Traditional tools dump thousands of lines of logs that:

- **Burn context windows** - 2000+ lines consume precious tokens
- **Require parsing** - No structured format for machine consumption
- **Miss patterns** - Agents must identify error types manually
- **Lack suggestions** - No actionable fix hints

logsift solves all of these by:

- **Compressing logs** - 2000 lines → 20-50 actionable lines
- **Structured JSON** - Predictable schema optimized for parsing
- **Pattern matching** - Automatic error type detection
- **Fix suggestions** - Actionable hints with confidence levels

## The Agentic Loop

The core pattern for autonomous error fixing:

```
1. RUN    → logsift monitor --format=json -- <command>
2. PARSE  → Extract errors and suggestions from JSON
3. FIX    → Apply suggested fixes automatically
4. VERIFY → logsift monitor --format=json -- <command>
5. REPEAT → Until success or escalate
```

This loop can run completely autonomously without human intervention.

## JSON Output Schema

logsift's JSON output is a stable contract designed for LLM consumption:

```json
{
  "summary": {
    "status": "failed|success",
    "exit_code": 1,
    "duration_seconds": 2.45,
    "command": "npm run build",
    "timestamp": "2024-01-15T10:30:00Z",
    "log_file": "/path/to/log.log"
  },
  "errors": [
    {
      "id": 1,
      "severity": "error",
      "line_in_log": 45,
      "message": "Module not found: Error: Can't resolve './missing.js'",
      "file": "src/index.js",
      "file_line": 12,
      "context_before": ["import React from 'react';"],
      "context_after": [""],
      "suggestion": {
        "action": "create_missing_file",
        "description": "Create the missing file or fix the import path",
        "confidence": "high",
        "automated_fix": "touch src/missing.js"
      },
      "pattern_matched": "webpack_module_not_found",
      "tags": ["webpack", "import", "fixable"]
    }
  ],
  "actionable_items": [
    {
      "priority": 1,
      "file": "src/index.js",
      "line": 12,
      "action": "fix_import",
      "description": "Create ./missing.js or fix import path",
      "automated": true
    }
  ],
  "stats": {
    "total_errors": 1,
    "total_warnings": 0,
    "fixable_errors": 1,
    "log_size_bytes": 45678,
    "log_lines": 234
  }
}
```

## Key Fields for Agents

### `summary`

Quick decision point - did command succeed?

```python
result = json.loads(logsift_output)
if result['summary']['status'] == 'success':
    return  # All done
else:
    # Process errors
    process_errors(result['errors'])
```

### `errors`

List of all errors with:

- `message` - What went wrong
- `file` + `file_line` - Where to fix (if applicable)
- `context_before` + `context_after` - Surrounding code
- `suggestion` - How to fix
- `pattern_matched` - Error type for routing

### `actionable_items`

Prioritized list of fixes sorted by importance:

```python
for item in result['actionable_items']:
    if item['automated']:
        apply_fix(item)
```

## Claude Code Integration

Claude Code can use logsift natively to enable fully autonomous workflows.

### Basic Pattern

```python
import subprocess
import json

def run_with_logsift(command: list[str]) -> dict:
    """Run command through logsift and parse JSON output."""
    result = subprocess.run(
        ['logsift', 'monitor', '--format=json', '--'] + command,
        capture_output=True,
        text=True
    )
    return json.loads(result.stdout)

# Use it
analysis = run_with_logsift(['npm', 'run', 'build'])
if analysis['summary']['status'] == 'failed':
    for error in analysis['errors']:
        print(f"Error: {error['message']}")
        if error.get('suggestion'):
            print(f"Fix: {error['suggestion']['description']}")
```

### Autonomous Fix Loop

```python
def autonomous_fix_loop(command: list[str], max_attempts: int = 3) -> bool:
    """Autonomously fix errors until success or max attempts."""

    for attempt in range(max_attempts):
        # Run command through logsift
        analysis = run_with_logsift(command)

        # Success - we're done
        if analysis['summary']['status'] == 'success':
            return True

        # Extract fixable errors
        fixable = [e for e in analysis['errors']
                  if e.get('suggestion', {}).get('automated_fix')]

        if not fixable:
            # No automated fixes available - escalate to human
            escalate_to_human(analysis)
            return False

        # Apply fixes
        for error in fixable:
            fix_command = error['suggestion']['automated_fix']
            subprocess.run(fix_command, shell=True)

        # Retry in next iteration

    # Max attempts reached - escalate
    escalate_to_human(analysis)
    return False

# Use it
success = autonomous_fix_loop(['npm', 'run', 'build'])
```

### Pattern-Based Routing

Route errors to specialized handlers based on pattern:

```python
def handle_error(error: dict) -> None:
    """Route error to appropriate handler based on pattern."""

    pattern = error.get('pattern_matched')

    handlers = {
        'python_import_error': fix_python_import,
        'npm_module_not_found': fix_npm_dependency,
        'webpack_module_not_found': fix_webpack_import,
        'typescript_type_error': fix_typescript_type,
        'pytest_test_failed': fix_pytest_assertion,
    }

    handler = handlers.get(pattern)
    if handler:
        handler(error)
    else:
        # Generic handler
        apply_generic_fix(error)

# Process all errors
analysis = run_with_logsift(['pytest', 'tests/'])
for error in analysis['errors']:
    handle_error(error)
```

## Advanced Workflows

### Incremental Fix Strategy

Fix one error at a time and verify:

```python
def incremental_fix(command: list[str]) -> bool:
    """Fix errors one at a time, verifying after each fix."""

    while True:
        analysis = run_with_logsift(command)

        if analysis['summary']['status'] == 'success':
            return True

        # Get highest priority fixable error
        fixable = [e for e in analysis['errors']
                  if e.get('suggestion', {}).get('automated_fix')]

        if not fixable:
            return False

        # Fix only the first error
        error = fixable[0]
        fix = error['suggestion']['automated_fix']
        subprocess.run(fix, shell=True)

        # Verify fix worked (loop will re-run command)
```

### Confidence-Based Decisions

Use suggestion confidence to decide automation level:

```python
def smart_fix(error: dict) -> bool:
    """Apply fix based on confidence level."""

    suggestion = error.get('suggestion', {})
    confidence = suggestion.get('confidence', 'low')

    if confidence == 'high':
        # Fully automated
        fix = suggestion.get('automated_fix')
        if fix:
            subprocess.run(fix, shell=True)
            return True

    elif confidence == 'medium':
        # Apply with verification
        fix = suggestion.get('automated_fix')
        if fix:
            subprocess.run(fix, shell=True)
            # Re-run to verify
            retest_result = run_with_logsift(command)
            if retest_result['summary']['status'] == 'failed':
                # Fix didn't work - revert
                revert_changes()
                return False
            return True

    else:  # low confidence
        # Escalate to human
        request_human_review(error)
        return False
```

### Multi-Stage Workflows

Chain multiple operations with verification:

```python
def multi_stage_workflow():
    """Run multi-stage build with verification at each step."""

    stages = [
        (['npm', 'install'], 'install dependencies'),
        (['npm', 'run', 'lint'], 'lint code'),
        (['npm', 'run', 'test'], 'run tests'),
        (['npm', 'run', 'build'], 'build production'),
    ]

    for command, description in stages:
        print(f"Running: {description}")

        analysis = run_with_logsift(command)

        if analysis['summary']['status'] == 'failed':
            # Try to fix this stage
            if not autonomous_fix_loop(command):
                print(f"Failed at stage: {description}")
                return False

        print(f"✓ {description} succeeded")

    return True
```

## Best Practices

### 1. Always Use JSON Format

```python
# ✓ GOOD - Structured, parseable
logsift monitor --format=json -- command

# ✗ BAD - Markdown is for humans
logsift monitor --format=markdown -- command
```

### 2. Check Status First

```python
# ✓ GOOD - Quick decision
if analysis['summary']['status'] == 'success':
    return

# ✗ BAD - Unnecessary error processing
for error in analysis['errors']:
    # ... process even if succeeded
```

### 3. Use Pattern Matching

```python
# ✓ GOOD - Pattern-based routing
if error['pattern_matched'] == 'python_import_error':
    fix_import(error)

# ✗ BAD - String matching fragile
if 'ImportError' in error['message']:
    fix_import(error)
```

### 4. Respect Confidence Levels

```python
# ✓ GOOD - Confidence-based automation
if suggestion['confidence'] == 'high':
    apply_fix_automatically()
else:
    request_human_review()

# ✗ BAD - Blind automation
apply_fix(suggestion['automated_fix'])
```

### 5. Limit Retry Attempts

```python
# ✓ GOOD - Bounded retries
for attempt in range(MAX_ATTEMPTS):
    if try_fix():
        break
else:
    escalate()

# ✗ BAD - Infinite loop
while not success:
    try_fix()
```

### 6. Save Logs for Debugging

```python
# ✓ GOOD - Logs saved to cache
logsift monitor -n build-$(date +%s) -- npm run build

# Logs available at ~/.cache/logsift/monitor/
```

### 7. Extract File References

```python
# ✓ GOOD - Use structured file:line
if error.get('file'):
    edit_file(error['file'], error['file_line'])

# ✗ BAD - Parse from message
match = re.search(r'(\S+):(\d+)', error['message'])
```

## Common Patterns

### Pattern: Missing Dependency

```python
def fix_missing_dependency(error: dict) -> None:
    """Fix missing dependency errors."""

    if error['pattern_matched'] in ['python_import_error', 'npm_module_not_found']:
        suggestion = error['suggestion']
        if suggestion.get('automated_fix'):
            # e.g., "pip install requests" or "npm install lodash"
            subprocess.run(suggestion['automated_fix'], shell=True)
```

### Pattern: Syntax Error

```python
def fix_syntax_error(error: dict) -> None:
    """Fix syntax errors using file reference."""

    if not error.get('file'):
        return

    # Read file
    with open(error['file']) as f:
        lines = f.readlines()

    # Get context
    line_idx = error['file_line'] - 1
    context = error['context_before'] + [lines[line_idx]] + error['context_after']

    # Use LLM to fix syntax
    fixed_line = llm_fix_syntax(context, error['message'])

    # Apply fix
    lines[line_idx] = fixed_line
    with open(error['file'], 'w') as f:
        f.writelines(lines)
```

### Pattern: Test Failure

```python
def fix_test_failure(error: dict) -> None:
    """Fix failed test assertions."""

    if error['pattern_matched'] == 'pytest_test_failed':
        # Extract test name and failure reason
        test_file = error['file']
        test_line = error['file_line']
        failure_msg = error['message']

        # Analyze test context
        context = error['context_before'] + error['context_after']

        # Generate fix
        fix = llm_analyze_test_failure(test_file, test_line, failure_msg, context)

        # Apply fix
        apply_code_change(test_file, test_line, fix)
```

## Integration with MCP Server (Phase 3)

In Phase 3, logsift will provide a Model Context Protocol (MCP) server for native Claude Code integration:

```python
# Future: Claude Code can call logsift as a native tool

# Instead of subprocess:
result = subprocess.run(['logsift', 'monitor', ...])

# Use MCP tool directly:
result = await logsift_monitor(command=['npm', 'run', 'build'])
```

This enables:

- Native tool calling without subprocess overhead
- Streaming analysis results
- Bidirectional communication
- Better error handling

See MCP Integration documentation (Phase 3 - coming soon).

## Troubleshooting

### Agent Not Parsing JSON

Ensure `--format=json` is specified:

```python
# ✓ Correct
subprocess.run(['logsift', 'monitor', '--format=json', '--', 'command'])

# ✗ Wrong - might get Markdown
subprocess.run(['logsift', 'monitor', '--', 'command'])
```

### Missing Suggestions

Not all errors have automated fix suggestions. Check before accessing:

```python
# ✓ Safe
suggestion = error.get('suggestion')
if suggestion and suggestion.get('automated_fix'):
    apply_fix(suggestion['automated_fix'])

# ✗ Unsafe
fix = error['suggestion']['automated_fix']  # May KeyError
```

### Pattern Not Matched

Unknown error types return `pattern_matched: null`. Create custom patterns:

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

## Example: Complete Autonomous Agent

```python
import subprocess
import json
from typing import Optional

class AutonomousFixAgent:
    """Autonomous error-fixing agent using logsift."""

    def __init__(self, max_attempts: int = 3):
        self.max_attempts = max_attempts

    def run_command(self, command: list[str]) -> dict:
        """Run command through logsift and parse JSON."""
        result = subprocess.run(
            ['logsift', 'monitor', '--format=json', '--'] + command,
            capture_output=True,
            text=True
        )
        return json.loads(result.stdout)

    def fix_error(self, error: dict) -> bool:
        """Attempt to fix a single error."""
        suggestion = error.get('suggestion', {})

        # Check confidence
        if suggestion.get('confidence') != 'high':
            return False

        # Get automated fix
        fix = suggestion.get('automated_fix')
        if not fix:
            return False

        # Apply fix
        result = subprocess.run(fix, shell=True, capture_output=True)
        return result.returncode == 0

    def autonomous_build(self, command: list[str]) -> bool:
        """Autonomously build project, fixing errors as needed."""

        for attempt in range(self.max_attempts):
            print(f"Attempt {attempt + 1}/{self.max_attempts}")

            # Run through logsift
            analysis = self.run_command(command)

            # Success
            if analysis['summary']['status'] == 'success':
                print("✓ Build succeeded")
                return True

            # Try to fix errors
            fixed_any = False
            for error in analysis['errors']:
                if self.fix_error(error):
                    print(f"✓ Fixed: {error['message'][:50]}...")
                    fixed_any = True

            if not fixed_any:
                print("✗ No fixable errors found")
                return False

        print("✗ Max attempts reached")
        return False

# Use it
agent = AutonomousFixAgent(max_attempts=5)
success = agent.autonomous_build(['npm', 'run', 'build'])
```

## See Also

- [JSON Schema](../api/json-schema.md) - Complete JSON output specification
- [Pattern Format](../api/pattern-format.md) - Create custom patterns
- [Structured Logging](../guides/structured-logging.md) - Write log-friendly scripts
- [CLI Reference](../cli-reference.md) - Complete command documentation
