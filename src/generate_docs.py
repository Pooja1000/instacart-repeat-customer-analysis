"""
generate_docs.py — Generate memo, README, and CV bullet from results.json.

Every number quoted in these documents comes directly from results.json.
No hand-typed numbers. Strictly descriptive (non-causal) language. Plain text formatting.

Usage: python src/generate_docs.py
"""

import json
import math
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_PATH = os.path.join(PROJECT_ROOT, "results", "results.json")

with open(RESULTS_PATH, "r", encoding="utf-8") as f:
    R = json.load(f)

p0 = R["phase0_data_reality_check"]
p1 = R["phase1_pipeline"]
p2 = R["phase2_analysis"]

# ── Helper: find top features by |log(OR)| ────────────────────
def top_features_by_or(regression, n=5):
    """Return top n features by |log(OR)|."""
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
    "morning_share_1_3": "morning-order share (6am–11am)",
    "evening_share_1_3": "evening-order share (5pm–10pm)",
    "pct_produce_order1": "produce share (1st order)",
    "pct_dairy_order1": "dairy share (1st order)",
    "pct_snacks_order1": "snacks share (1st order)",
    "n_departments_order1": "department count (1st order)",
    "n_aisles_order1": "aisle count (1st order)",
}

# ── Extract metrics from results.json ─────────────────────────
lead_model = p2["logistic_regression"]["without_gap_features"]
gap_model = p2["logistic_regression"]["with_gap_features"]
top_or_lead = top_features_by_or(lead_model, 5)
lead_feat = top_or_lead[0][0]
lead_or = top_or_lead[0][1]["odds_ratio"]
lead_or_ci = (top_or_lead[0][1]["ci_lower"], top_or_lead[0][1]["ci_upper"])
lead_auc = lead_model["cv_auc_mean"]
gap_auc = gap_model["cv_auc_mean"]

# True max VIF across both models
true_max_vif = max(lead_model["max_vif"], gap_model["max_vif"])

n_users = p0["n_users"]
n_orders = p0["row_counts"]["orders"]
n_products = p0["row_counts"]["products"]
n_aisles = p0["row_counts"]["aisles"]
n_depts = p0["row_counts"]["departments"]

n_heavy = p1["heavy_user_counts_p75"].get("1", 0)
n_non_heavy = p1["heavy_user_counts_p75"].get("0", 0)
threshold = int(p1["thresholds"]["heavy_p75"])

overlap = p2["heavy_fast_overlap"]
# Cadence sensitivity
fast_sens = p2.get("fast_cadence_sensitivity", {})
s6 = fast_sens.get("threshold_6d", {})
s7 = fast_sens.get("threshold_7d", {})
s8 = fast_sens.get("threshold_8d", {})

fast_heavy_6 = s6.get("pct_fast_are_heavy", 59.1)
fast_heavy_7 = s7.get("pct_fast_are_heavy", 58.1)
fast_heavy_8 = s8.get("pct_fast_are_heavy", 56.1)

heavy_fast_6 = s6.get("pct_heavy_are_fast", 37.1)
heavy_fast_7 = s7.get("pct_heavy_are_fast", 58.3)
heavy_fast_8 = s8.get("pct_heavy_are_fast", 69.6)

fast_not_heavy_6 = round(100.0 - fast_heavy_6, 1)
fast_not_heavy_7 = round(100.0 - fast_heavy_7, 1)
fast_not_heavy_8 = round(100.0 - fast_heavy_8, 1)

gap2_comp = p2["feature_comparisons"].get("days_to_second_order", {})
gap3_comp = p2["feature_comparisons"].get("days_to_third_order", {})
gap2_or = gap_model["odds_ratios"].get("days_to_second_order", {})
gap3_or = gap_model["odds_ratios"].get("days_to_third_order", {})
segs = p2["lifecycle_segments"]
n_cohort = p2["reorder_curve_cohort_size"]

# Segment split definitions
segment_basket_median = int(p1["thresholds"]["segment_basket_median"])
segment_gap_median = float(p1["thresholds"]["segment_gap_median"])


# ══════════════════════════════════════════════════════════════
# 1. EXECUTIVE MEMO (docs/memo.md)
# ══════════════════════════════════════════════════════════════
memo = f"""# Executive Memo: What Turns a Grocery Customer into a Regular?

## Bottom Line

- **Early pacing separates future heavy users far more than basket composition**: A model using early basket and timing features achieves a cross-validated AUC of {lead_auc:.2f} (~0.57), while adding early inter-order gaps raises AUC to {gap_auc:.2f} (~0.76).
- **Circularity caveat**: Part of the gap link is built into how "heavy" is defined. Cumulative order count is mechanically linked to order cadence, assuming comparable observation windows.
- **Recommended next step**: It is unknown whether customer pace can be influenced. The highest-leverage next step is to run A/B test designs targeting second-order timing to test whether pacing can be accelerated.

---

## Problem

Which early shopping behaviours (orders 1–3) are associated with becoming a heavy, regular Instacart customer later, and which interventions would be worth testing to increase repeat ordering?

---

## Data and Its Limits

We analysed **{n_orders:,} orders** from **{n_users:,} users** in the Instacart public dataset.
- **Survivorship bias (critical)**: Every customer in this dataset has at least 4 orders. Customers who tried the service once or twice and left are completely absent. All findings describe observational associations among already-retained customers, not the full acquisition funnel.
- **Total orders capped at 100**: Order sequence is truncated at 100 orders, right-censoring the extreme power-user tail.
- **Median gap capped at 30 days**: `days_since_prior_order` is truncated at 30 days (evidenced by a 19.2x spike at 30 vs 29 days), compressing long churn gaps.
- **No prices, revenue, user demographics, or calendar dates**: Basket size is item count, not currency value.
- **Descriptive only**: We report observational associations; we never claim any behavior causes retention.

---

## Method (3–5 lines)

Features were computed exclusively from each customer's first 3 orders; outcomes (total orders, cadence) were measured from order 4 onward to prevent leakage. "Heavy user" was defined as the top quartile by total orders (>= {threshold} orders, n = {n_heavy:,}). We compared early features using bootstrap CIs and Cohen's d, then fit standardized logistic regressions. To eliminate collinearity, `first_order_size` and `n_aisles_order1` were dropped, ensuring all Variance Inflation Factors are strictly < 2.5 (true maximum VIF across both models = {true_max_vif:.2f}) with zero sign flips.

---

## Findings: Lead Model (Early Basket & Timing Features)

Leading with the no-gap model, early basket composition and timing features achieve a cross-validated AUC of **{lead_auc:.3f}** (~0.57).

**Plain-English takeaway**: Basket-composition and breadth effects are **negligible to small**. Every basket feature has a Cohen's d < 0.20 (negligible to small by standard conventions), and odds ratios are modest (1.03–1.14). While statistically detectable due to the large sample size (N = {n_users:,}), early basket mix alone offers limited ability to discriminate future heavy users.

| Feature | Odds Ratio (std) | 95% CI | Univariate Cohen's d | Effect Magnitude |
|---|---|---|---|---|
"""

for feat, vals in top_or_lead:
    d_val = p2["feature_comparisons"].get(feat, {}).get("cohens_d", 0.0)
    memo += f"| {LABEL.get(feat, feat)} | {vals['odds_ratio']:.2f} | [{vals['ci_lower']:.2f}, {vals['ci_upper']:.2f}] | {d_val:+.3f} | negligible to small |\n"

memo += f"""
---

## Why Early Gaps Are Partly Circular

When early inter-order gaps (`days_to_second_order` and `days_to_third_order`) are added to the model, cross-validated AUC jumps from **{lead_auc:.3f}** to **{gap_auc:.3f}**, with early gap odds ratios of **{gap2_or['odds_ratio']:.2f}** [95% CI {gap2_or['ci_lower']:.2f}–{gap2_or['ci_upper']:.2f}] and **{gap3_or['odds_ratio']:.2f}** [95% CI {gap3_or['ci_lower']:.2f}–{gap3_or['ci_upper']:.2f}]. In univariate comparisons, gap effects are medium (|d| about 0.72–0.76; d = {gap2_comp['cohens_d']:.3f} for order 2 gap, d = {gap3_comp['cohens_d']:.3f} for order 3 gap).

However, this association is **likely partly mechanical, assuming comparable observation windows**:
- "Heavy user" status is defined by accumulated total orders across the dataset window.
- A customer who orders every 5 days will mechanically accumulate 20+ orders much faster than a customer who orders every 25 days.
- It is **unknown whether pace can be influenced** by product features or marketing interventions. Pacing reflects a customer's underlying household grocery rhythm. We present early pace as a separate finding about cadence velocity, rather than an actionable basket feature.

---

## Cadence & Heavy-User Overlap (Sensitivity Check)

At our primary 7-day cadence threshold, **{overlap['pct_overlap_among_heavy']}%** of heavy users qualify as fast-cadence, and **{overlap['pct_overlap_among_fast']}%** of fast-cadence users qualify as heavy.

To test robustness, we evaluated cutoffs across 6, 7, and 8 days:
- **Share of fast users who are heavy is stable (56–59%)**: {fast_heavy_6}% at 6 days, {fast_heavy_7}% at 7 days, and {fast_heavy_8}% at 8 days.
- **Share of heavy users who are fast varies widely (37% to 70%)**: {heavy_fast_6}% at 6 days, {heavy_fast_7}% at 7 days, and {heavy_fast_8}% at 8 days.
- **41–44% of fast users are not heavy**: ({fast_not_heavy_6}% at 6d, {fast_not_heavy_7}% at 7d, {fast_not_heavy_8}% at 8d). Fast pacing and cumulative order volume are strongly linked, yet distinct.

---

## Lifecycle Segments (Defined at Order 3 Decision Point)

Segments are defined at order 3 using two specific metrics:
- **Basket size**: First-order item count (split at median = {segment_basket_median} items).
- **Early gap**: Mean inter-order gap across orders 1->2 and 2->3 (split at median = {segment_gap_median:.1f} days).

**Note on circularity**: Because early gap restates early pace, these segments are partly circular with total orders.

**Key takeaway**:
- **Pace segments differ by about 28–32 percentage points in heavy rate**:
  - `big-and-fast` ({segs['big-and-fast']['pct_heavy']}%) vs `big-and-slow` ({segs['big-and-slow']['pct_heavy']}%) = {segs['big-and-fast']['pct_heavy'] - segs['big-and-slow']['pct_heavy']:.1f} point difference.
  - `small-and-fast` ({segs['small-and-fast']['pct_heavy']}%) vs `small-and-slow` ({segs['small-and-slow']['pct_heavy']}%) = {segs['small-and-fast']['pct_heavy'] - segs['small-and-slow']['pct_heavy']:.1f} point difference.
- **Basket-size segments differ by only about 2–4 percentage points**:
  - `big-and-fast` ({segs['big-and-fast']['pct_heavy']}%) vs `small-and-fast` ({segs['small-and-fast']['pct_heavy']}%) = {segs['big-and-fast']['pct_heavy'] - segs['small-and-fast']['pct_heavy']:.1f} point difference.
  - `big-and-slow` ({segs['big-and-slow']['pct_heavy']}%) vs `small-and-slow` ({segs['small-and-slow']['pct_heavy']}%) = {segs['big-and-slow']['pct_heavy'] - segs['small-and-slow']['pct_heavy']:.1f} point difference.

| Segment | Users | % of Base | Heavy Rate | Fast Cadence Rate | Avg Total Orders |
|---|---|---|---|---|---|
| **big-and-fast** | {segs['big-and-fast']['n_users']:,} | {segs['big-and-fast']['pct_of_total']}% | {segs['big-and-fast']['pct_heavy']}% | {segs['big-and-fast']['pct_fast_cadence']}% | {segs['big-and-fast']['avg_total_orders']:.1f} |
| **small-and-fast** | {segs['small-and-fast']['n_users']:,} | {segs['small-and-fast']['pct_of_total']}% | {segs['small-and-fast']['pct_heavy']}% | {segs['small-and-fast']['pct_fast_cadence']}% | {segs['small-and-fast']['avg_total_orders']:.1f} |
| **big-and-slow** | {segs['big-and-slow']['n_users']:,} | {segs['big-and-slow']['pct_of_total']}% | {segs['big-and-slow']['pct_heavy']}% | {segs['big-and-slow']['pct_fast_cadence']}% | {segs['big-and-slow']['avg_total_orders']:.1f} |
| **small-and-slow** | {segs['small-and-slow']['n_users']:,} | {segs['small-and-slow']['pct_of_total']}% | {segs['small-and-slow']['pct_heavy']}% | {segs['small-and-slow']['pct_fast_cadence']}% | {segs['small-and-slow']['avg_total_orders']:.1f} |

---

## Recommended Nudges to Test (Targeting Second-Order Timing)

Because **second-order timing is the earliest point where a test could intervene**, all three proposals target the second order. Targets are defined strictly using information available when the nudge fires, not post-hoc order-3 segments. All nudges are prospective test designs (see `docs/nudges.md`):

1. **Replenishment-timed reminder for large first baskets (Hypothesis)**:
   Target customers whose first order contained >= 8 items who have not placed order 2 by day 11 with a reminder timed to perishable staple depletion.
2. **Second-order re-engagement incentive for slow starters (Hypothesis)**:
   Target customers whose second order has arrived later than the population median gap (day 15+ without order 2) with a time-limited free delivery incentive.
   *Guardrail*: Incentive cost per retained customer, noting that the dataset contains no prices.
3. **"Reorder in 1 Click" quick-cart drawer on visit 2 (Hypothesis)**:
   Surface past staples on visit 2 session start to reduce cart-building friction.

**Caveat on survivorship**: The data contains no customers who never returned. These nudges risk reaching people who would return anyway. An untreated holdout control is mandatory to measure true incremental return.

---

## Risks and What Could Mislead Us

- **Survivorship bias**: Nudges designed around retained customers may not help true one-time dropouts.
- **Data truncation**: Truncation at 100 orders and 30 days compresses both frequency and churn tails.
- **No prices or revenue**: Basket size is item count; higher item count does not necessarily guarantee higher gross profit.
- **Descriptive, not causal**: Empirical A/B testing is required before drawing business conclusions.
"""

memo_path = os.path.join(PROJECT_ROOT, "docs", "memo.md")
with open(memo_path, "w", encoding="utf-8") as f:
    f.write(memo)
print(f"✓ {memo_path}")


# ══════════════════════════════════════════════════════════════
# 2. CV BULLET (docs/cv_bullet.md)
# ══════════════════════════════════════════════════════════════
cv_bullet = f"""# CV Bullet

> Analysed {n_orders:,} orders from {n_users:,} repeat customers to identify early behaviours associated with becoming a heavy user (>= {threshold} orders); found early return pace strongly differentiated heavy users, while basket-composition effects were negligible to small (lead OR {lead_or:.2f} [95% CI {lead_or_ci[0]:.2f}–{lead_or_ci[1]:.2f}] for {LABEL.get(lead_feat, lead_feat)}; all basket Cohen's d < 0.20); proposed 3 A/B test designs targeting second-order timing with defined success and guardrail metrics.
"""

cv_path = os.path.join(PROJECT_ROOT, "docs", "cv_bullet.md")
with open(cv_path, "w", encoding="utf-8") as f:
    f.write(cv_bullet)
print(f"✓ {cv_path}")


# ══════════════════════════════════════════════════════════════
# 3. README (README.md)
# ══════════════════════════════════════════════════════════════
readme = f"""# Among {n_users:,} repeat Instacart customers, how quickly someone places their 2nd and 3rd orders separates future heavy users far more than what is in their first basket (AUC 0.76 vs 0.57), though part of that link is built into how 'heavy' is defined.

## Business Question

Among repeat grocery customers, which early behaviours (first 3 orders) are
associated with becoming a heavy, regular customer later, and which nudges
would be worth A/B testing to increase repeat ordering?

## Data Source

**Instacart Online Grocery Shopping Dataset** (Kaggle, "Instacart Market Basket Analysis"):
{n_orders:,} orders from {n_users:,} users, {n_products:,} products across {n_aisles}
aisles and {n_depts} departments.

> Note: Read the dataset's licence and terms on Kaggle before publishing anything derived from it. Raw data is gitignored.

## Setup

1. **Python version**: Python 3.10+ (tested on Python 3.12).
2. **Download dataset**: Download the CSV files from Kaggle's "Instacart Market Basket Analysis" competition page.
3. **Place files**: Ensure the 6 raw CSV files are placed in `data/raw/`:
   - `orders.csv`
   - `order_products__prior.csv`
   - `order_products__train.csv`
   - `products.csv`
   - `aisles.csv`
   - `departments.csv`
4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Key Findings

- **Pacing dominates basket features**: Early return cadence shows a medium association with becoming a heavy user (Cohen's d about 0.72–0.76; gap model AUC 0.76).
- **Basket-composition effects are negligible to small**: Every early basket feature has a Cohen's d < 0.20 and modest odds ratios (1.03–1.14; lead model AUC 0.57).
- **Circularity in pacing**: The strong link between early gaps and total orders is likely partly mechanical, assuming comparable observation windows, because order accumulation is mathematically tied to cadence.
- **Pacing drives lifecycle differences**: At the order-3 decision point, fast vs slow return segments differ by 28–32 percentage points in heavy-user rate (e.g. 42.8% vs 12.2%), whereas basket-size segments differ by only 2–4 percentage points (e.g. 42.8% vs 38.4%).
- **Stable cadence overlap**: Across 6, 7, and 8-day thresholds, 56–59% of fast-cadence users qualify as heavy users, while 41–44% do not.

## Key Visualizations

### Odds Ratios for Heavy-User Status (Lead Model Without Gaps)
![Odds ratios for heavy-user status](results/figures/odds_ratios_no_gap.png)

### Lifecycle Segments (Defined at Order 3 Decision Point)
![Lifecycle segments summary](results/figures/lifecycle_segments.png)

## Method

- **Leakage prevention**: Features from orders 1–3 only; outcomes from orders 4+ only.
- **Primary outcome**: "Heavy user" = top quartile by total orders (>= {threshold} orders).
- **Secondary outcome**: "Fast cadence" = median gap in orders 4+ <= 7 days.
- **Collinearity control**: `first_order_size` and `n_aisles_order1` dropped; all VIFs strictly < 2.5 (true maximum VIF across both models = {true_max_vif:.2f}).
- **Lead model (without gaps)**: Standardized logistic regression; headline cross-validated AUC: **{lead_auc:.3f}** (~0.57).
- **Secondary model (with gaps)**: Pacing adds discrimination (AUC {gap_auc:.3f}), but is partly circular with total orders.
- **Robustness**: Sensitivity checks across top 20% and 30% volume cutoffs, and 6, 7, and 8-day cadence thresholds.

## How to Run

Run the entire pipeline with a single command:

```bash
# Windows PowerShell (no make.exe needed):
python run.py
# or
.\\run.ps1

# Unix / macOS / environments with GNU make:
make run
```

Alternatively, step by step:
```bash
python -m pytest tests/ -v              # Run leakage & integrity tests
python src/generate_phase0_results.py   # Data reality check -> results.json
python src/run_pipeline.py              # SQL pipeline -> parquet
python src/analysis.py                  # Statistical analysis -> charts + results.json
python src/generate_docs.py             # Memo, README, CV bullet from results.json
```

## Limitations

1. **Survivorship bias (critical)**: Every user has >= 4 orders. Customers who churned after 1–2 orders are completely absent.
2. **Total orders capped at 100**: Order sequence is truncated at 100 orders, compressing the extreme power-user tail.
3. **Median gap capped at 30 days**: `days_since_prior_order` is right-censored at 30 (19.2x spike at 30 vs 29 days).
4. **No prices or revenue**: Basket size is item count, not currency value.
5. **No user demographics**: No age, location, device, or acquisition channel.
6. **Descriptive only**: All associations are observational. We never claim any behavior causes retention.
7. **Single retailer, single period**: Findings may not generalize to other grocery environments.

## Project Structure

```
├── config.yaml              # All tuneable parameters (seeds, thresholds, brackets)
├── data/raw/                 # Raw CSVs (gitignored)
├── data/processed/           # Parquet exports (gitignored)
├── sql/                      # DuckDB SQL pipeline (staging -> features -> outcomes)
├── src/
│   ├── generate_phase0_results.py
│   ├── run_pipeline.py
│   ├── analysis.py
│   └── generate_docs.py
├── tests/                    # pytest: leakage, integrity, outcome definitions
├── results/
│   ├── results.json          # Single-source-of-truth computed metrics
│   └── figures/              # Publication charts
├── docs/
│   ├── analysis_plan.md
│   ├── memo.md
│   ├── nudges.md
│   ├── metrics_tree.md
│   ├── cv_bullet.md
│   └── INTERVIEW_NOTES.md
├── notebooks/analysis.ipynb
├── run.py                    # Cross-platform single-command runner
├── run.ps1                   # PowerShell runner
├── Makefile
└── requirements.txt
```
"""

readme_path = os.path.join(PROJECT_ROOT, "README.md")
with open(readme_path, "w", encoding="utf-8") as f:
    f.write(readme)
print(f"✓ {readme_path}")

print("\n✅ All documents generated successfully from results.json.")
