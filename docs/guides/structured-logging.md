# Structured Logging

Best practices for writing log-friendly scripts and applications that work beautifully with logsift.

## Overview

Write scripts and applications that produce clear, parseable logs optimized for both human reading and logsift analysis.

## Core Principles

### 1. Write to stdout/stderr Consistently

```python
# ✓ GOOD - Predictable output
print("Starting build...")  # stdout
print("ERROR: Build failed", file=sys.stderr)  # stderr

# ✗ BAD - Logs to file, logsift can't capture
with open('build.log', 'a') as f:
    f.write("ERROR: Build failed\n")
```

### 2. Use Clear Error Prefixes

```python
# ✓ GOOD - Easy to detect
print("ERROR: Connection timeout")
print("WARNING: Deprecated API used")
print("FATAL: Database connection failed")

# ✗ BAD - Ambiguous
print("Something went wrong")
print("Oops!")
```

### 3. Include File References

```python
# ✓ GOOD - file:line format
print(f"ERROR: Syntax error in {filepath}:{line_number}")
print(f"  File \"{filepath}\", line {line_number}")

# ✗ BAD - No location
print("ERROR: Syntax error")
```

### 4. Provide Context

```python
# ✓ GOOD - Shows surrounding code
print(f"  {prev_line}")
print(f"→ {error_line}  # Error here")
print(f"  {next_line}")

# ✗ BAD - No context
print(f"Error: {error_line}")
```

## Recommended Formats

### Simple Prefix Format

Easiest to implement, works great with logsift:

```
[INFO] Application started
[DEBUG] Loading configuration from config.yaml
[WARNING] Config file not found, using defaults
[ERROR] Failed to connect to database: Connection refused
[FATAL] Application shutting down due to critical error
```

Pattern:

```
[LEVEL] Message with details
```

### File:Line Format

Critical for automated fixes:

```
ERROR: Syntax error in src/app.py:45
  42: def process_data(data):
  43:     try:
  44:         result = transform(data)
→ 45:         return result.value  # Error: 'NoneType' object has no attribute 'value'
  46:     except Exception as e:
  47:         print(f"Error: {e}")
```

Pattern:

```
ERROR: <message> in <file>:<line>
  [context lines with line numbers]
→ [error line]
  [more context]
```

### JSON Lines Format

For structured logging (each line is valid JSON):

```json
{"level":"INFO","message":"Application started","timestamp":"2024-01-15T10:30:00Z"}
{"level":"ERROR","message":"Database connection failed","file":"db.py","line":23,"details":"Connection refused"}
```

logsift automatically detects and parses JSON logs.

## Language-Specific Examples

### Python

```python
import sys
import traceback
from pathlib import Path

def log_error(message: str, exc: Exception | None = None, file: str | None = None, line: int | None = None):
    """Log error in logsift-friendly format."""

    # Basic error
    print(f"ERROR: {message}", file=sys.stderr)

    # File reference if available
    if file and line:
        print(f"  File \"{file}\", line {line}", file=sys.stderr)

    # Exception details
    if exc:
        print(f"  {type(exc).__name__}: {exc}", file=sys.stderr)

    # Stack trace for debugging
    if exc and __debug__:
        traceback.print_exc(file=sys.stderr)

# Usage
try:
    result = risky_operation()
except ValueError as e:
    log_error("Failed to process data", exc=e, file="app.py", line=42)
    sys.exit(1)
```

### Bash

```bash
#!/bin/bash

# Color codes for terminal
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m'  # No Color

log_error() {
    echo -e "${RED}ERROR:${NC} $1" >&2
}

log_warning() {
    echo -e "${YELLOW}WARNING:${NC} $1" >&2
}

log_info() {
    echo "INFO: $1"
}

# Usage
if ! command -v npm &> /dev/null; then
    log_error "npm not found. Install Node.js first."
    exit 1
fi

log_info "Starting build..."
if ! npm run build; then
    log_error "Build failed. Check npm output above."
    exit 1
fi
```

### Node.js/TypeScript

```typescript
// logger.ts
export enum LogLevel {
  INFO = 'INFO',
  WARNING = 'WARNING',
  ERROR = 'ERROR',
}

interface LogContext {
  file?: string;
  line?: number;
  details?: Record<string, any>;
}

export function log(level: LogLevel, message: string, context?: LogContext): void {
  const stream = level === LogLevel.ERROR ? process.stderr : process.stdout;

  // Basic message
  stream.write(`[${level}] ${message}\n`);

  // File reference
  if (context?.file && context?.line) {
    stream.write(`  at ${context.file}:${context.line}\n`);
  }

  // Additional details
  if (context?.details) {
    stream.write(`  ${JSON.stringify(context.details)}\n`);
  }
}

// Usage
try {
  await processData(input);
} catch (error) {
  log(LogLevel.ERROR, 'Failed to process data', {
    file: 'processor.ts',
    line: 42,
    details: { error: error.message }
  });
  process.exit(1);
}
```

## Build Tool Integration

### Make

```makefile
.PHONY: build test clean

# Prefix commands with @echo for clear output
build:
 @echo "[INFO] Starting build..."
 @npm run build || (echo "[ERROR] Build failed" && exit 1)
 @echo "[INFO] Build complete"

test:
 @echo "[INFO] Running tests..."
 @pytest tests/ || (echo "[ERROR] Tests failed" && exit 1)
 @echo "[INFO] All tests passed"

clean:
 @echo "[INFO] Cleaning build artifacts..."
 @rm -rf dist/ build/
 @echo "[INFO] Clean complete"
```

### npm Scripts

```json
{
  "scripts": {
    "prebuild": "echo '[INFO] Preparing build...'",
    "build": "webpack --config webpack.config.js",
    "postbuild": "echo '[INFO] Build complete'",
    "test": "jest --verbose",
    "lint": "eslint src/ || (echo '[ERROR] Linting failed' && exit 1)"
  }
}
```

## Error Message Best Practices

### 1. Be Specific

```python
# ✓ GOOD - Specific and actionable
print("ERROR: Database connection failed: host 'db.example.com' port 5432 - Connection refused")

# ✗ BAD - Vague
print("ERROR: Database error")
```

### 2. Include Values

```python
# ✓ GOOD - Shows actual values
print(f"ERROR: Expected 3 arguments, got {len(args)}")

# ✗ BAD - No context
print("ERROR: Wrong number of arguments")
```

### 3. Suggest Fixes

```python
# ✓ GOOD - Tells user what to do
print("ERROR: Config file not found at /etc/app/config.yaml")
print("  Create config file or set APP_CONFIG environment variable")

# ✗ BAD - No guidance
print("ERROR: Config file not found")
```

### 4. Use Standard Formats

```python
# ✓ GOOD - Standard traceback format
print(f'  File "{filepath}", line {line_number}, in {function_name}')
print(f"    {error_line}")
print(f"{error_type}: {error_message}")

# ✗ BAD - Non-standard format
print(f"{filepath}({line_number}): error {error_message}")
```

## Testing Your Logs

Test that logsift extracts information correctly:

```bash
# Generate test log
./your-script.sh 2>&1 | tee test.log

# Analyze with logsift
logsift analyze test.log

# Check JSON output
logsift analyze test.log --format=json | jq '.errors'
```

Verify:

- [ ] Errors are detected
- [ ] File:line references extracted
- [ ] Error messages are clear
- [ ] Context is captured
- [ ] Suggestions match your intent

## Common Pitfalls

### 1. Silent Failures

```python
# ✗ BAD - Error hidden
try:
    result = operation()
except Exception:
    pass  # Silent failure

# ✓ GOOD - Error logged
try:
    result = operation()
except Exception as e:
    print(f"ERROR: Operation failed: {e}", file=sys.stderr)
    raise
```

### 2. Inconsistent Formatting

```python
# ✗ BAD - Different formats
print("Error: something failed")
print("ERROR - another failure")
print("[ERR] yet another failure")

# ✓ GOOD - Consistent format
print("ERROR: something failed")
print("ERROR: another failure")
print("ERROR: yet another failure")
```

### 3. Missing stderr

```python
# ✗ BAD - Errors to stdout
print("ERROR: Build failed")

# ✓ GOOD - Errors to stderr
print("ERROR: Build failed", file=sys.stderr)
```

### 4. Unclear Context

```bash
# ✗ BAD - No indication what failed
npm run build

# ✓ GOOD - Clear context
echo "[INFO] Building application..."
if ! npm run build; then
    echo "[ERROR] Application build failed" >&2
    exit 1
fi
echo "[INFO] Build successful"
```

## Structured Logging Libraries

### Python: structlog

```python
import structlog

log = structlog.get_logger()

# Structured logging that logsift can parse
log.info("application_started", version="1.0.0")
log.error("database_connection_failed",
          host="db.example.com",
          port=5432,
          error="Connection refused")
```

### Node.js: winston

```typescript
import winston from 'winston';

const logger = winston.createLogger({
  format: winston.format.json(),
  transports: [
    new winston.transports.Console()
  ]
});

logger.info('Application started', { version: '1.0.0' });
logger.error('Database connection failed', {
  host: 'db.example.com',
  port: 5432,
  error: 'Connection refused'
});
```

logsift automatically detects and parses JSON logs from these libraries.

## Real-World Example

Complete example of a log-friendly script:

```python
#!/usr/bin/env python3
"""Build script with logsift-friendly logging."""

import sys
import subprocess
from pathlib import Path

def log_info(message: str):
    print(f"[INFO] {message}")

def log_error(message: str, file: str | None = None, line: int | None = None):
    print(f"[ERROR] {message}", file=sys.stderr)
    if file and line:
        print(f"  at {file}:{line}", file=sys.stderr)

def run_command(command: list[str], description: str) -> bool:
    """Run command with clear logging."""
    log_info(f"{description}...")

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )
        log_info(f"{description} completed successfully")
        return True

    except subprocess.CalledProcessError as e:
        log_error(f"{description} failed with exit code {e.returncode}")
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        return False

def main():
    log_info("Starting build process")

    steps = [
        (["npm", "install"], "Installing dependencies"),
        (["npm", "run", "lint"], "Linting code"),
        (["npm", "run", "test"], "Running tests"),
        (["npm", "run", "build"], "Building application"),
    ]

    for command, description in steps:
        if not run_command(command, description):
            log_error("Build process failed")
            return 1

    log_info("Build process completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

Run with logsift:

```bash
logsift monitor -- ./build.py
```

Output is clear, structured, and fully analyzed by logsift.

## See Also

- [Agentic Integration](../concepts/agentic-integration.md) - Using logs with AI
- [Pattern Matching](../concepts/pattern-matching.md) - How logsift detects errors
- [Custom Patterns](custom-patterns.md) - Match your custom formats
