# Architecture

Why logsift is built this way, and what happens to a log between input and output. Read these
before changing the parser, the detector, or the output schema.

## Documentation

- [Design Principles](design-principles.md) — Fail-fast and LLM-first reasoning, the trade-offs behind TOML patterns and subprocess monitoring, and the explicit non-goals
- [Data Flow](data-flow.md) — The parse, detect, analyze, format pipeline stage by stage, with the data structures passed between stages and the complexity of each
