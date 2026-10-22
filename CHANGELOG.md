# Changelog

## 0.1.1

Hardening found while wiring this library into a production agent (see
`deepagent_project/tools/audit_core.py`). All three were silent failures: the
audit reported the wrong thing rather than reporting nothing.

### Fixed

- **A broken formula no longer fails the claim.** `safe_eval` accepted any
  constant, so `consistency("x", formula='"abc"')` returned the string `"abc"`,
  the comparison crashed, and `Auditor` reported it as `check crashed` — an
  *error* against the data. Only numeric constants are allowed now, so the
  formula is rejected instead of the claim.
- **`**` is bounded** (`_MAX_EXPONENT = 64`). The AST allowlist stops code
  execution but not exhaustion: `2 ** 10 ** 9` ran for ~5 s and allocated
  hundreds of MB inside a check. Formulas may be model-generated, so this was a
  one-prompt worker bomb.
- **A check returning something other than `None | AuditIssue | SKIP`** is
  coerced into an error issue. Previously it was appended as-is and the next
  `report.passed` raised `AttributeError` inside the caller's code.

### Added

- `Check.threshold(..., expect_range=(low, high))`: a value outside the declared
  scale is reported as an error ("the claim is in different units than the
  bound") instead of being compared against a bound from another scale. It is a
  guard, not a converter: `0.348` and `34.8` are both inside `(0, 100)`, so a
  fraction on a percent scale is only caught by comparing against ground truth
  — which is what `consistency`/`custom` with a `source` are for.

## 0.1.0

First release: `threshold` / `consistency` / `freshness` / `custom` checks, an
AST-restricted formula evaluator, `SKIP` semantics, and an optional ground-truth
`source`.
