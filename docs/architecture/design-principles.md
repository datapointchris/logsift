# Design Principles

Why logsift works the way it does.

## Core Philosophy

> logsift is **LLM-first**, not human-first. The primary user is AI agents; humans are secondary.

This inverts traditional tool design:

- JSON output is optimized for parsing, not reading
- Schema stability is critical (breaking changes = major version)
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

### 4. Dual Output Modes

- **JSON** for machines (LLMs, scripts, automation)
- **Markdown** for humans (terminals, debugging)

Auto-detected via TTY check.

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

### Why subprocess, not sh Library?

**Chosen:** subprocess.run()
**Rejected:** sh library

Reasoning:

- stdlib - no external dependency
- More predictable behavior
- Better timeout handling
- Simpler for MVP

### Why No Streaming (Phase 1/2)?

**Deferred to Phase 3**

Reasoning:

- MVP needs simple, complete analysis
- Streaming adds complexity
- Most logs are <10MB
- Phase 3 adds for large files

### Why Auto-Format Detection?

**Chosen:** Auto-detect TTY
**Rejected:** Always require --format

Reasoning:

- Best default for 90% of use cases
- Terminal users get beauty
- Scripts get structure
- Can override when needed

## Architecture Decisions

### Modular Pipeline

```
Input → Parser → Extractors → Matchers → Context → Output
```

Each stage is independent and testable.

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

1. **Real-time streaming** (Phase 1/2) - Batch analysis only
2. **Log aggregation** - Use ELK, Splunk, etc.
3. **Metrics/monitoring** - Use Prometheus, Grafana
4. **Log storage** - Cache is temporary, not database
5. **Multi-format output** - JSON + Markdown only

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
