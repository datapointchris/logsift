# Process Monitoring

Advanced techniques for monitoring commands with logsift.

## Basic Monitoring

Monitor any command and analyze its output:

```bash
logsift monitor -- <command> [args...]
```

## Command Naming

Organize logs with custom names:

```bash
# Default: uses command name
logsift monitor -- npm run build
# Saved as: ~/.cache/logsift/monitor/npm-TIMESTAMP.log

# Custom name
logsift monitor -n my-app-build -- npm run build
# Saved as: ~/.cache/logsift/monitor/my-app-build-TIMESTAMP.log
```

## Output Formats

Control output format:

```bash
# Auto-detect (terminal=Markdown, pipe=JSON)
logsift monitor -- make test

# Force JSON (for scripting)
logsift monitor --format=json -- cargo test

# Force Markdown (for reading)
logsift monitor --format=markdown -- pytest tests/
```

## Real-World Examples

### Python Testing

```bash
# Monitor pytest with coverage
logsift monitor -n pytest-run -- uv run pytest --cov=myapp tests/

# Monitor specific test file
logsift monitor -- pytest tests/test_api.py -v
```

### Node.js Builds

```bash
# Monitor npm build
logsift monitor -n frontend-build -- npm run build

# Monitor with environment
NODE_ENV=production logsift monitor -- npm run build
```

### CI/CD Integration

```yaml
# .github/workflows/test.yml
- name: Run tests with logsift
  run: |
    logsift monitor --format=json -n ci-test -- npm test > test-analysis.json

- name: Upload analysis
  uses: actions/upload-artifact@v2
  with:
    name: test-analysis
    path: test-analysis.json
```

### Long-Running Commands

```bash
# Monitor deployment
logsift monitor -n prod-deploy -- bash scripts/deploy.sh

# Monitor database migration
logsift monitor -n db-migration -- python manage.py migrate
```

## Exit Codes

logsift preserves command exit codes:

```bash
logsift monitor -- make test
echo $?  # Returns make's exit code

# Use in conditionals
if logsift monitor -- npm test; then
    echo "Tests passed"
else
    echo "Tests failed"
fi
```

## Combining with Other Tools

### With jq

```bash
# Extract errors
logsift monitor --format=json -- npm run build | jq '.errors'

# Count failures
errors=$(logsift monitor --format=json -- pytest | jq '.stats.total_errors')
```

### With tee

```bash
# Save analysis and display
logsift monitor -- make build | tee build-analysis.txt
```

## Cache Management

Monitored logs are saved to `~/.cache/logsift/monitor/`:

```bash
# List recent logs
ls -lt ~/.cache/logsift/monitor/ | head

# Re-analyze old log
logsift analyze ~/.cache/logsift/monitor/npm-20240115_103000.log
```

Clean old logs:

```python
from logsift.cache.rotation import clean_old_logs
from pathlib import Path

deleted = clean_old_logs(Path.home() / '.cache' / 'logsift', retention_days=30)
```

## Best Practices

1. **Use meaningful names** for better organization
2. **Force JSON in scripts** for consistent parsing
3. **Let auto-format work** in interactive terminals
4. **Monitor multi-stage workflows** separately
5. **Clean cache periodically** to save disk space

## See Also

- [CLI Reference](../cli-reference.md) - Complete command docs
- [Agentic Integration](../concepts/agentic-integration.md) - Automated workflows
