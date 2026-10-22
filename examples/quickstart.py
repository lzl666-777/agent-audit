"""Quickstart: catch a plausible-but-wrong agent answer.

Run:
    python examples/quickstart.py
"""

from agent_audit import Auditor, Check

# What the agent (LLM) claims in its final answer.
agent_claims = {
    "return_rate": 0.348,          # 34.8% return rate
    "revenue": 542060,             # claimed revenue
    "price": 7.99,                 # unit price
    "qty": 23000,                  # units sold
    "market_price_as_of": "2025-01-01",  # when the market price was fetched
}

auditor = Auditor(checks=[
    # SOP red line: return rate must not exceed 8%.
    Check.threshold("return_rate", max=0.08),
    # Revenue must equal price * qty (7.99 * 23000 = 183770, not 542060).
    Check.consistency("revenue", formula="price * qty"),
    # Market data older than 180 days is suspicious.
    Check.freshness("market_price_as_of", max_age_days=180),
])

report = auditor.check(agent_claims)

print(report.to_markdown())
print()
print("passed:", report.passed)
print("errors:", len(report.errors), "| warnings:", len(report.warnings))
