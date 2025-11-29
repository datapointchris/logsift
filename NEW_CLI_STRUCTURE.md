# New CLI Structure - Implementation Plan

## Complete Command Listing

```bash
# Monitor
logsift monitor [OPTIONS] -- COMMAND

# Analyze (perform analysis)
logsift analyze <file>
logsift analyze <file> --stream
logsift analyze latest
logsift analyze latest --stream
logsift analyze browse
logsift analyze browse --stream

# Logs (raw log files)
logsift logs list
logsift logs browse
logsift logs browse --tail
logsift logs latest [name]
logsift logs latest --tail
logsift logs clean

# Analyzed (saved analysis results)
logsift analyzed list
logsift analyzed browse
logsift analyzed latest [name]
logsift analyzed clean

# Patterns
logsift patterns list
logsift patterns show <name>
logsift patterns validate <file>

# Help
logsift help [command]
```

## Key Changes to Implement

### 1. Remove `watch` Command

- Delete `logsift watch` entirely
- Replaced by `logsift analyze --stream`

### 2. Add `--stream` Flag to Analyze

- `analyze --stream <file>` - Continuously analyze as file grows
- `analyze latest --stream` - Stream analyze latest log
- `analyze browse --stream` - Browse with fzf, then stream analyze
- Starts from beginning of file, then watches for new lines

### 3. Change `-i` to `browse` Subcommand

- Current: `logsift analyze -i`
- New: `logsift analyze browse`
- Consistency with `logsift logs browse`

### 4. Add `--tail` to `logs browse`

- `logsift logs browse --tail` - Select with fzf, then tail it
- Useful for tailing non-latest logs

### 5. Create `analyzed` Subcommand

- New namespace for saved analysis results
- Mirrors `logs` structure for consistency

### 6. Update Directory Structure

```
~/.cache/logsift/
  logs/
    2025-11-29T22:00:00-myapp.log
    2025-11-29T22:00:00-build.log
  analyzed/
    2025-11-29T22:00:00-myapp.json
    2025-11-29T22:00:00-build.json
```

**Migration:** Move existing logs from `~/.cache/logsift/*.log` to `~/.cache/logsift/logs/*.log`

### 7. Auto-Save Analyses

- When running `analyze`, automatically save result to `analyzed/`
- Same filename as log but with `.json` extension
- Enables `analyzed` subcommand to work

## Implementation Tasks

### Phase 1: Directory Structure

- [ ] Update `CacheManager` to use subdirectories
- [ ] Add migration logic to move existing logs to `logs/`
- [ ] Update all file paths in code
- [ ] Update tests for new structure

### Phase 2: Analyze Changes

- [ ] Add `--stream` flag to analyze command
- [ ] Implement streaming analysis (read file + tail new lines)
- [ ] Change `-i/--interactive` to `browse` subcommand
- [ ] Add `analyze browse --stream` combination
- [ ] Add `analyze latest --stream` combination
- [ ] Auto-save analysis results to `analyzed/`

### Phase 3: Logs Changes

- [ ] Add `--tail` flag to `logs browse` command
- [ ] Update to work with `logs/` subdirectory

### Phase 4: Analyzed Subcommand

- [ ] Create `analyzed` subcommand structure
- [ ] Implement `analyzed list`
- [ ] Implement `analyzed browse`
- [ ] Implement `analyzed latest [name]`
- [ ] Implement `analyzed clean`

### Phase 5: Remove Watch

- [ ] Delete `watch` command from CLI
- [ ] Delete `src/logsift/commands/watch.py` (keep tail_log function)
- [ ] Update documentation
- [ ] Update tests

### Phase 6: Testing

- [ ] Update all existing tests
- [ ] Add tests for new functionality
- [ ] Verify migration works
- [ ] Test all command combinations

## Implementation Notes

### Substring Matching

- Already implemented (commit 67f5328)
- Pattern: `*{name}*.log` for flexible matching

### Streaming Implementation

```python
def analyze_stream(file_path: Path, interval: int = 1):
    """Analyze entire file, then continue analyzing as it grows."""
    # 1. Read and analyze existing content
    with open(file_path) as f:
        existing = f.read()
        result = analyzer.analyze(existing)
        print_analysis(result)

        # 2. Tail for new lines
        f.seek(0, 2)  # Go to end
        while True:
            line = f.readline()
            if line:
                # Re-analyze with new line added
                existing += line
                result = analyzer.analyze(existing)
                print_analysis(result)
            else:
                time.sleep(interval)
```

### Auto-Save Implementation

```python
def analyze_log(log_file: str, output_format: str = 'auto', save: bool = True):
    """Analyze a log file and optionally save results."""
    result = analyzer.analyze(log_content)

    if save:
        # Save to analyzed/ directory
        analyzed_path = get_analyzed_path(log_file)
        with open(analyzed_path, 'w') as f:
            json.dump(result, f, indent=2)

    # Display to user
    print_analysis(result, output_format)
```

## Breaking Changes

1. **Directory Structure** - Logs move to subdirectory
2. **`watch` command removed** - Use `analyze --stream` instead
3. **`-i` flag removed** - Use `browse` subcommand instead

## Migration Guide for Users

```bash
# Old: logsift watch /var/log/app.log
# New: logsift analyze --stream /var/log/app.log

# Old: logsift analyze -i
# New: logsift analyze browse

# Old: ~/.cache/logsift/2025-11-29T22:00:00-app.log
# New: ~/.cache/logsift/logs/2025-11-29T22:00:00-app.log
```

## Current Status

✅ Completed (already committed):

- Shell function support
- Clean UI (markdown headers)
- Test isolation
- Better log naming (slashes → dashes)
- Separate tail/watch functionality
- Substring matching

🚧 To Implement:

- Everything listed in this document
