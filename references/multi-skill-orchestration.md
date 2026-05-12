# Multi-Skill Orchestration Pattern

## Overview

This document describes the pattern used by `scripts/analyze_stock.py` to aggregate data from multiple independent moomoo skills into a unified stock analysis report.

## Why This Pattern Exists

The moomoo ecosystem has specialized skills for different data domains:
- `moomooapi` — quotes, K-lines, portfolio
- `moomoo-capital-anomaly` — capital flow signals
- `moomoo-derivatives-anomaly` — options anomaly detection
- `moomoo-news-search` — news sentiment

Rather than requiring the user to run each skill manually, `analyze_stock.py` calls them programmatically via `subprocess.run()`, collects their outputs, and synthesizes a single structured report.

## Architecture

```
analyze_stock.py (orchestrator)
├── get_snapshot()          → moomoo OpenAPI (OpenQuoteContext)
├── get_kline_summary()     → moomoo OpenAPI (request_history_kline)
├── get_capital_anomaly()   → subprocess → moomoo-capital-anomaly
├── get_derivatives_anomaly() → subprocess → moomoo-derivatives-anomaly
├── get_option_chain()      → moomoo OpenAPI (get_option_chain)
├── get_news()              → HTTP → moomoo news API
└── format_report()         → synthesizes all into markdown
```

## Key Implementation Details

### 1. Subprocess Invocation

```python
result = subprocess.run(
    ['python3', 'scripts/handle_capital_anomaly.py', symbol, '--json'],
    cwd='/root/.hermes/skills/moomoo-capital-anomaly',
    capture_output=True, text=True, timeout=30
)
```

- Always use `--json` flag for machine-parseable output
- Set `cwd` to the target skill's directory
- Use `timeout=30` to avoid hanging on network calls

### 2. Direct API vs Subprocess

Use **direct API** when:
- The data is available through `OpenQuoteContext`
- You need structured DataFrame output
- Latency matters

Use **subprocess** when:
- The logic is complex and already implemented in another skill
- The skill does post-processing (anomaly detection, sentiment scoring)
- You want to reuse the skill's output formatting

### 3. Error Handling

Each collector wraps its call in try/except and returns `None` on failure. The formatter skips `None` sections gracefully — the report is still useful even if one data source fails.

### 4. PYTHONPATH Requirement

All moomoo scripts require:
```bash
export PYTHONPATH=/usr/local/lib/python3.12/dist-packages:$PYTHONPATH
```

The orchestrator script injects this via `sys.path.insert(0, ...)` at runtime.

## Extending the Orchestrator

To add a new analysis dimension:

1. Write a collector function:
```python
def get_new_metric(symbol):
    try:
        result = subprocess.run(
            ['python3', 'scripts/metric.py', symbol, '--json'],
            cwd='/root/.hermes/skills/some-skill',
            capture_output=True, text=True, timeout=30
        )
        return result.stdout if result.returncode == 0 else None
    except:
        return None
```

2. Add it to the main flow:
```python
new_metric = get_new_metric(symbol)
```

3. Update `format_report()` to include the new section.

## Pitfalls

| Pitfall | Solution |
|---------|----------|
| Skill not installed | Check `~/.hermes/skills/` before calling; gracefully skip |
| NumPy 2.x crash | Use `pip install --upgrade pandas --break-system-packages` |
| OpenD not running | Check port 11111 first; return early with clear error |
| Chinese output from sub-skills | Parse structurally (JSON) not by string matching |
| Timeout on news API | Use short timeout (10s) and fallback to empty |

## Related

- `scripts/analyze_stock.py` — the orchestrator implementation
- `SKILL.md` — usage examples and CLI reference
