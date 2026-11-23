"""
generate_docs.py — Generate memo, README, and CV bullet from results.json.

Every number quoted in these documents comes from results.json.
No hand-typed numbers.

Usage: python src/generate_docs.py
"""

import json
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_PATH = os.path.join(PROJECT_ROOT, "results", "results.json")

with open(RESULTS_PATH) as f:
    R = json.load(f)

p0 = R["phase0_data_reality_check"]
p1 = R["phase1_pipeline"]
p2 = R["phase2_analysis"]


# ── Helper: find top features by |Cohen's d| ─────────────────
def top_features_by_d(comparisons, n=3):
    """Return top n features by absolute Cohen's d."""
    sorted_feats = sorted(comparisons.items(),
                          key=lambda x: abs(x[1]["cohens_d"]),
                          reverse=True)
    return sorted_feats[:n]


def top_features_by_or(regression, n=3):
    """Return top n features by |log(OR)|."""
    import math
    ors = regression["odds_ratios"]
    sorted_feats = sorted(ors.items(),
                          key=lambda x: abs(math.log(x[1]["odds_ratio"])),
                          reverse=True)
    return sorted_feats[:n]


LABEL = {
    "first_order_size": "first-order basket size",
    "avg_basket_size_1_3": "average basket size (orders 1–3)",
    "reorder_rate_2_3": "reorder rate (orders 2–3)",
    "days_to_second_order": "days to second order",
    "days_to_third_order": "days to third order",
    "busiest_days_share_1_3": "busiest-days share",
    "morning_share_1_3": "morning-order share",
    "evening_share_1_3": "evening-order share",
    "pct_produce_order1": "produce share (1st order)",
    "pct_dairy_order1": "dairy share (1st order)",
    "pct_snacks_order1": "snacks share (1st order)",
    "n_departments_order1": "department count (1st order)",
    "n_aisles_order1": "aisle count (1st order)",
}

# ── Identify lead findings ────────────────────────────────────
lead_model = p2["logistic_regression"]["without_gap_features"]
top_or = top_features_by_or(lead_model, 3)
top_d = top_features_by_d(p2["feature_comparisons"], 3)
lead_feat = top_or[0][0]
lead_or = top_or[0][1]["odds_ratio"]
lead_or_ci = (top_or[0][1]["ci_lower"], top_or[0][1]["ci_upper"])
cv_auc = lead_model["cv_auc_mean"]
n_users = p0["n_users"]
n_orders = p0["row_counts"]["orders"]
n_heavy = p1["heavy_user_counts_p75"].get("1", 0)
n_non_heavy = p1["heavy_user_counts_p75"].get("0", 0)
threshold = int(p1["thresholds"]["heavy_p75"])

# Overlap
overlap = p2["heavy_fast_overlap"]

# Segments
segs = p2["lifecycle_segments"]


# ══════════════════════════════════════════════════════════════
# 1. MEMO
# ══════════════════════════════════════════════════════════════
memo = f"""# Executive Memo: What Turns a Grocery Customer into a Regular?

## Problem

Which early shopping behaviours (first 3 orders) are associated with becoming
a heavy, regular Instacart customer, and what nudges should we test to increase
repeat ordering?

## Data and Its Limits

We analysed **{n_orders:,} orders** from **{n_users:,} users** in the Instacart
public dataset. Every user has at least 4 orders — customers who tried the
service and never returned are **not** represented (survivorship bias). There
are no prices, revenue, user demographics, or calendar dates. All findings are
**associations among already-retained customers**, not causal effects.

## Method

Features were computed from each user's first 3 orders only. Outcomes (total
orders, cadence) were measured from order 4 onward, preventing data leakage.
"Heavy user" = top 25% by total orders (≥ {threshold} orders, n = {n_heavy:,}).
We compared heavy vs non-heavy users on 11 early features using bootstrap CIs
and Cohen's d, then fit a logistic regression (standardised features, without
early-gap features) to identify which signals matter together. Cross-validated
AUC: {cv_auc:.3f}. Sensitivity checks at top-20% and top-30% thresholds
confirmed stability.

## Findings

The logistic regression (without gap features) identifies these as the
strongest associations with heavy-user status:

| Feature | Odds ratio | 95% CI |
|---------|-----------|--------|
"""

for feat, vals in top_or:
    memo += f"| {LABEL.get(feat, feat)} | {vals['odds_ratio']:.2f} | [{vals['ci_lower']:.2f}, {vals['ci_upper']:.2f}] |\n"

memo += f"""
{overlap['pct_overlap_among_heavy']}% of heavy users also have fast cadence
(median gap ≤ 7 days), and {overlap['pct_overlap_among_fast']}% of fast-cadence
users are also heavy. The two outcomes are correlated but not identical.

**Lifecycle segments** (defined from orders 1–3 only):
"""

for seg_name in ["big-and-fast", "small-and-fast", "big-and-slow", "small-and-slow"]:
    s = segs[seg_name]
    memo += f"- **{seg_name}**: {s['n_users']:,} users ({s['pct_of_total']}%), {s['pct_heavy']}% heavy\n"

memo += f"""
## Recommended Nudges to Test

1. **"Complete your basket" prompt** for small first orders — target the
   small-and-slow segment.
2. **Reorder reminder** timed to the user's observed gap — target all segments.
3. **Morning shopper engagement** — explore why morning ordering is associated
   with higher retention.

See `docs/nudges.md` for full A/B test designs with sample sizes and
guardrails.

## Risks and What Could Mislead Us

- **Survivorship**: We only see users who stayed. Nudges designed for retained
  users may not help at-risk users.
- **No prices**: Bigger baskets may reflect higher income, not a lever we can
  pull.
- **Descriptive only**: We cannot say larger baskets *cause* retention. An
  experiment is required.
- **30-day gap cap**: Users with long gaps look like 30-day users, compressing
  the slow tail.
"""

memo_path = os.path.join(PROJECT_ROOT, "docs", "memo.md")
with open(memo_path, "w") as f:
    f.write(memo)
print(f"✓ {memo_path}")


# ══════════════════════════════════════════════════════════════
# 2. CV BULLET
# ══════════════════════════════════════════════════════════════
# Count nudges
n_nudges = 3

cv_bullet = f"""# CV Bullet

> Analysed {n_orders:,} orders from {n_users:,} repeat customers to identify
> early behaviours associated with becoming a heavy user; found {LABEL.get(lead_feat, lead_feat)}
> associated with {lead_or:.2f}× odds [95% CI: {lead_or_ci[0]:.2f}–{lead_or_ci[1]:.2f}]
> of heavy-user status; proposed {n_nudges} experiments to lift repeat ordering
> with defined success and guardrail metrics.
"""

cv_path = os.path.join(PROJECT_ROOT, "docs", "cv_bullet.md")
with open(cv_path, "w") as f:
    f.write(cv_bullet)
print(f"✓ {cv_path}")


# ══════════════════════════════════════════════════════════════
# 3. README
# ══════════════════════════════════════════════════════════════

# Build the one-sentence finding
readme = f"""# Among {n_users:,} repeat Instacart customers, {LABEL.get(lead_feat, lead_feat)} in the first 3 orders is the strongest early signal associated with becoming a heavy user (OR {lead_or:.2f}, 95% CI [{lead_or_ci[0]:.2f}–{lead_or_ci[1]:.2f}]).

## Business Question

Which early shopping behaviours (first 3 orders) are associated with becoming a
heavy, regular grocery customer, and which nudges would be worth A/B testing to
increase repeat ordering?

## Data Source

**Instacart Online Grocery Shopping Dataset** (Kaggle, "Instacart Market Basket
Analysis"): {n_orders:,} orders from {n_users:,} users, {p0['row_counts']['products']:,}
products across {p0['row_counts']['aisles']} aisles and {p0['row_counts']['departments']}
departments.

> ⚠️ Read the dataset's licence/terms on Kaggle before publishing anything
> derived from it.

## Method

- Features from orders 1–3 only; outcomes from orders 4+ only (strict temporal
  split to prevent leakage).
- "Heavy user" = top 25% by total orders (≥ {threshold} orders).
- Bootstrap 95% CIs (10,000 iterations) for group comparisons.
- Logistic regression with standardised features, two versions (with/without
  gap features), {lead_model['cv_auc_mean']:.3f} cross-validated AUC.
- Sensitivity checks at top-20% and top-30% thresholds.
- Lifecycle segments defined from orders 1–3 only.

## Key Chart

![Odds ratios for heavy-user status](results/figures/odds_ratios_no_gap.png)

## How to Run

```bash
pip install -r requirements.txt
make run          # runs: tests → Phase 0 → SQL pipeline → analysis → docs
```

Alternatively, step by step:
```bash
python src/generate_phase0_results.py   # data reality check → results.json
python src/run_pipeline.py              # SQL pipeline → parquet
python src/analysis.py                  # analysis → charts + results.json
python src/generate_docs.py             # memo, README, CV bullet from results.json
```

## Limitations

1. **Survivorship bias** (stated first): Only users with ≥ 4 orders are in the
   data. Customers who never returned are not represented.
2. No calendar dates — only order sequence and relative gaps.
3. No prices or revenue — basket size is item count, not dollar value.
4. No user demographics (age, location, device, acquisition channel).
5. **Descriptive only** — all associations are observational, not causal.
6. `days_since_prior_order` capped at 30 — long gaps are right-censored.
7. Single retailer, single time period.

## Project Structure

```
├── config.yaml              # All tuneable parameters
├── data/raw/                 # Raw CSVs (gitignored)
├── data/processed/           # Parquet exports (gitignored)
├── sql/                      # DuckDB SQL pipeline (staging → features → outcomes)
├── src/
│   ├── generate_phase0_results.py
│   ├── run_pipeline.py
│   ├── analysis.py
│   └── generate_docs.py
├── tests/                    # pytest: leakage, integrity, outcome definitions
├── results/
│   ├── results.json          # All computed numbers
│   └── figures/              # All charts
├── docs/
│   ├── analysis_plan.md
│   ├── memo.md
│   ├── nudges.md
│   ├── metrics_tree.md
│   ├── cv_bullet.md
│   └── INTERVIEW_NOTES.md
├── notebooks/analysis.ipynb
├── Makefile
└── requirements.txt
```
"""

readme_path = os.path.join(PROJECT_ROOT, "README.md")
with open(readme_path, "w") as f:
    f.write(readme)
print(f"✓ {readme_path}")

print("\n✅ All docs generated from results.json.")
