# Design Principles

Why logsift works the way it does.

## Core Philosophy

> logsift is **LLM-first**, not human-first. The primary user is AI agents; humans are secondary.

This inverts traditional tool design:

- Piped output is toon, compact for an LLM to read, and JSON is optimized for parsing
- Schema stability is critical: `schemas/analysis.schema.json` is the contract, and a breaking change raises its `schema_version`
- Fail fast - no defensive coding with inline defaults
- Universal compatibility - works with ANY log format

## Key Principles

### 1. Fail Fast

```python
# ✓ logsift approach
value = config.key  # Raises AttributeError if missing

# ✗ Traditional approach
value = getattr(config, 'key', 'default')  # Hides misconfiguration
```

Configuration validation happens once at startup. Business logic trusts valid configuration and fails loudly if assumptions are violated.

### 2. LLM-Optimized Output

JSON schema is a stable contract:

- Predictable field names
- Explicit types
- No ambiguity in parsing
- Compresses 2000+ lines to 20-50

### 3. Universal Compatibility

Works with ANY log format:

- Plain text
- JSON logs
- Structured logs (key=value)
- Build tool outputs
- System logs

Auto-detection, no configuration needed.

### 4. Three Output Formats

- **toon** for an LLM reading piped output, with the fewest tokens
- **JSON** for programs, with a published schema
- **Markdown** for humans (terminals, debugging)

A TTY check picks Markdown on a terminal and toon otherwise. JSON is always asked for with
`--format json`. Every `monitor` run saves all three.

### 5. Extensible Patterns

TOML-based pattern libraries:

- Built-in patterns for common tools
- Custom patterns in `~/.config/logsift/patterns/`
- Automatic merging
- Validation on load

## Design Trade-offs

### Why TOML for Patterns?

**Chosen:** TOML
**Rejected:** YAML, JSON

Reasoning:

- More readable than JSON
- Less ambiguous than YAML
- Built-in Python support (tomllib)
- Explicit arrays with `[[patterns]]`

### Why subprocess for Process Monitoring?

**Chosen:** `subprocess.Popen`, streaming stdout and stderr together line by line

Reasoning:

- stdlib - no external dependency
- Each line reaches the raw log and the progress display as the command prints it, where
  `subprocess.run()` would hand over the output only once the command exits
- A command that is not an executable, such as a shell alias or function, falls back to
  `$SHELL -i -c`, so it runs as it would at the prompt

No timeout is applied, so a command that hangs keeps `monitor` waiting until it is interrupted.

### Why Read the Whole File?

**Chosen:** Read the whole log, then analyze it
**Rejected:** Incremental parsing

Reasoning:

- Complete analysis is simpler
- Incremental parsing adds complexity
- Most logs are <10MB

### Why Auto-Format Detection?

**Chosen:** Auto-detect TTY
**Rejected:** Always require --format

Reasoning:

- A person at a terminal gets Markdown, and an agent reading a pipe gets toon
- A program asks for JSON, so its parse never depends on whether stdout is a terminal
- Can override when needed

## Architecture Decisions

### Modular Pipeline

```text
Input → LogParser → IssueDetector → Analyzer (file references, context, hooks) → Formatter → Output
```

Each stage is independent and testable. [Data Flow](data-flow.md) walks through each one.

### Stateless Analysis

No database, no persistent state:

- Input: log content
- Output: analysis JSON/Markdown
- Side effect: cache file (optional)

### Pattern-First Matching

Try patterns before generic extraction:

- Specific patterns win
- Generic fallback for unknowns
- First match wins (order matters)

## Non-Goals

What logsift intentionally does NOT do:

1. **Log aggregation** - Use ELK, Splunk, etc.
2. **Metrics/monitoring** - Use Prometheus, Grafana
3. **Log storage** - Cache is temporary, not database
4. **Multi-format output** - JSON, toon and Markdown only

## Success Criteria

logsift succeeds when:

1. Claude Code can autonomously fix errors without human help
2. 2000-line logs compress to 20-50 actionable lines
3. Developers prefer logsift over reading raw logs
4. Pattern library covers 80%+ of common errors
5. Zero-config works for most use cases

## See Also

- [Data Flow](data-flow.md) - How analysis works internally
- [Agentic Integration](../concepts/agentic-integration.md) - LLM usage
