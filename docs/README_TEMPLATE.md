# agent-audit

> Verify what your AI agent claims: consistency, threshold and freshness checks for agent outputs.

<!-- Replace OWNER/REPO after publishing. -->
![tests](https://github.com/OWNER/agent-audit/actions/workflows/ci.yml/badge.svg)
![python](https://img.shields.io/badge/python-3.9%2B-blue)
![license](https://img.shields.io/badge/license-MIT-green)

![audit report](docs/screenshots/01-report.png)

## Why

Guardrails check whether text is safe. `agent-audit` checks whether numbers are
true: it recomputes formulas from the components the agent already reported,
checks business bounds, and flags stale data — deterministically, no second LLM.

## Checks

| Check | What it does |
|---|---|
| `Check.threshold` | numeric bounds / SOP red lines / unit range |
| `Check.consistency` | recompute a formula and compare |
| `Check.freshness` | warn on stale dates |
| `Check.custom` | your own `fn(claims, source)` |

A check returns `None` (pass), `AuditIssue` (fail/warn), or `SKIP` (missing data).
A broken formula is an **audit configuration error**, not a silent skip.

## Quickstart

```bash
pip install -e ".[dev]"
pytest -q
python examples/quickstart.py
```

```python
from agent_audit import Auditor, Check

report = Auditor([
    Check.threshold("return_rate", max=0.08),
    Check.consistency("revenue", formula="price * qty"),
    Check.freshness("market_price_as_of", max_age_days=180),
]).check({...})

print(report.passed)
print(report.to_markdown())
```

## Safety

- formulas use a restricted AST: numbers, names, `+ - * / ** %` only;
- exponent capped;
- check exceptions become errors, not crashes;
- a broken formula fails the audit, not the data.

## Development

```bash
pytest -q
python examples/quickstart.py
```

## License

MIT
