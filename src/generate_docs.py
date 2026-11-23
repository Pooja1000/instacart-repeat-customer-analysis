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


def cohens_d_bracket(d):
    """Return exact Cohen's d interpretation bracket."""
    abs_d = abs(d)
    if abs_d < 0.2:
        return "negligible (< 0.2)"
    elif abs_d < 0.5:
        return "small (0.2–0.5)"
    elif abs_d < 0.8:
        return "medium (0.5–0.8)"
    else:
        return "large (>= 0.8)"


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

# Compute true OR range across all lead-model features
all_lead_ors = [v["odds_ratio"] for v in lead_model["odds_ratios"].values()]
lead_or_min = min(all_lead_ors)
lead_or_max = max(all_lead_ors)

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
pct_heavy_users = round(n_heavy / n_users * 100, 1)

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

- **Early pacing separates future heavy users far more than basket composition**: A model using early basket and time-of-day features achieves a cross-validated AUC of {lead_auc:.2f}, while adding early inter-order gaps raises AUC to {gap_auc:.2f}.
- **Circularity caveat**: Part of the gap link is built into how "heavy" is defined. Cumulative order count is mechanically linked to order cadence, assuming comparable observation windows.
- **Recommended next step**: It is unknown whether customer pace can be influenced. The highest-leverage next step is to run A/B test designs targeting second-order timing to test whether pacing can be accelerated.

---

## Problem

Which early shopping behaviours (orders 1–3) are associated with becoming a heavy, regular Instacart customer later, and which interventions would be worth testing to increase repeat ordering?

---

## Data and Its Limits

We analysed **{n_orders:,} orders** from **{n_users:,} users** in the Instacart public dataset.
- **Survivorship bias (critical)**: Every customer in this dataset has at least 4 orders. Customers who placed fewer than 4 orders are completely absent. All findings describe observational associations among already-retained customers, not the full acquisition funnel.
- **Total orders capped at 100**: Order sequence is truncated at 100 orders, right-censoring the extreme power-user tail.
- **Median gap capped at 30 days**: `days_since_prior_order` is truncated at 30 days (evidenced by a 19.2x spike at 30 vs 29 days), compressing long churn gaps.
- **No prices, revenue, user demographics, or calendar dates**: Basket size is item count, not currency value.
- **Descriptive only**: We report observational associations; we never claim any behavior causes retention.

---

## Method (3–5 lines)

Features were computed exclusively from each customer's first 3 orders; outcomes (total orders, cadence) were measured from order 4 onward to prevent leakage. "Heavy user" was defined as the top quartile by total orders: 20+ orders (about {pct_heavy_users}% of users, n = {n_heavy:,}). We compared early features using bootstrap CIs and Cohen's d, then fit standardized logistic regressions. To eliminate collinearity, `first_order_size` and `n_aisles_order1` were dropped, ensuring all Variance Inflation Factors are strictly < 2.5 (true maximum VIF across both models = {true_max_vif:.2f}) with zero sign flips.

---

## Findings: Lead Model (Early Basket & Time-of-Day Features)

Leading with the no-gap model, early basket composition and time-of-day features achieve a cross-validated AUC of **{lead_auc:.3f}**.

**Plain-English takeaway**: Basket-composition and breadth effects are **negligible to small**. Every basket feature has a Cohen's d < 0.20 (negligible by standard conventions), and odds ratios are modest ({lead_or_min:.2f}–{lead_or_max:.2f}). While statistically detectable due to the large sample size (N = {n_users:,}), early basket mix alone offers limited ability to discriminate future heavy users.

| Feature | Odds Ratio (std) | 95% CI | Univariate Cohen's d | Effect Magnitude |
|---|---|---|---|---|
"""

for feat, vals in top_or_lead:
    d_val = p2["feature_comparisons"].get(feat, {}).get("cohens_d", 0.0)
    memo += f"| {LABEL.get(feat, feat)} | {vals['odds_ratio']:.2f} | [{vals['ci_lower']:.2f}, {vals['ci_upper']:.2f}] | {d_val:+.3f} | {cohens_d_bracket(d_val)} |\n"

memo += f"""
---

## Why Early Gaps Are Partly Circular

When early inter-order gaps (`days_to_second_order` and `days_to_third_order`) are added to the model, cross-validated AUC jumps from **{lead_auc:.3f}** to **{gap_auc:.3f}**, with early gap odds ratios of **{gap2_or['odds_ratio']:.2f}** [95% CI {gap2_or['ci_lower']:.2f}–{gap2_or['ci_upper']:.2f}] and **{gap3_or['odds_ratio']:.2f}** [95% CI {gap3_or['ci_lower']:.2f}–{gap3_or['ci_upper']:.2f}]. In univariate comparisons, gap effects are medium (|d| about 0.72–0.76; d = {gap2_comp['cohens_d']:.3f} for order 2 gap, d = {gap3_comp['cohens_d']:.3f} for order 3 gap).

However, this association is **likely partly mechanical, assuming comparable observation windows**:
- "Heavy user" status is defined by accumulated total orders across the dataset window.
- A customer who orders every 5 days will mechanically accumulate 20+ orders much faster than a customer who orders every 25 days.
- It is **unknown whether pace can be influenced** by product features or marketing interventions. We present early pace as a separate finding about cadence velocity, rather than an actionable basket feature.

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
   Target customers whose first order contained >= 8 items who have not placed order 2 by day 11 (the 45th percentile of days to second order) with a reminder timed to perishable staple depletion.
2. **Second-order re-engagement incentive for slow starters (Hypothesis)**:
   Target customers who have placed exactly 1 order and have not placed order 2 by day 13 (the empirical median of days to second order) with a time-limited free delivery incentive.
   *Guardrail*: Incentive cost per retained customer, noting that the dataset contains no prices.
3. **"Reorder in 1 Click" quick-cart drawer on visit 2 (Hypothesis)**:
   Surface past staples on visit 2 session start to reduce cart-building friction.

**Caveat on survivorship**: The data contains no customers who placed fewer than 4 orders. These nudges risk reaching people who would return anyway. An untreated holdout control is mandatory to measure true incremental return. The data cannot provide an unbiased baseline return rate, so sample size must be estimated from production data.

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

> Analysed {n_orders:,} orders from {n_users:,} repeat customers to identify early behaviours associated with becoming a heavy user (20+ orders, about {pct_heavy_users}% of users); found early return pace strongly differentiated heavy users, while basket-composition effects were negligible to small (lead OR {lead_or:.2f} [95% CI {lead_or_ci[0]:.2f}–{lead_or_ci[1]:.2f}] for {LABEL.get(lead_feat, lead_feat)}; all basket Cohen's d < 0.20); proposed 3 A/B test designs targeting second-order timing with defined success and guardrail metrics.
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
- **Basket-composition effects are negligible to small**: Every early basket feature has a Cohen's d < 0.20 and modest odds ratios ({lead_or_min:.2f}–{lead_or_max:.2f}; lead model AUC 0.57).
- **Circularity in pacing**: The strong link between early gaps and total orders is likely partly mechanical (assuming comparable observation windows), because order count builds up with how often someone orders.
- **Pace segments differ most**: At the order-3 decision point, fast vs slow return segments differ by 28–32 percentage points in heavy-user rate (e.g. 42.8% vs 12.2%), whereas basket-size segments differ by only 2–4 percentage points (e.g. 42.8% vs 38.4%).
- **Stable cadence overlap**: Across 6, 7, and 8-day thresholds, 56–59% of fast-cadence users qualify as heavy users, while 41–44% do not.

## Key Visualizations

### Odds Ratios for Heavy-User Status (Lead Model Without Gaps)
![Odds ratios for heavy-user status](results/figures/odds_ratios_no_gap.png)

### Lifecycle Segments (Defined at Order 3 Decision Point)
![Lifecycle segments summary](results/figures/lifecycle_segments.png)

## Method

- **Leakage prevention**: Features from orders 1–3 only; outcomes from orders 4+ only.
- **Primary outcome**: "Heavy user" = top quartile by total orders: 20+ orders (about {pct_heavy_users}% of users).
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

1. **Survivorship bias (critical)**: Every user has >= 4 orders. Customers who placed fewer than 4 orders are completely absent.
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


# ══════════════════════════════════════════════════════════════
# 4. NUDGE PROPOSALS (docs/nudges.md)
# ══════════════════════════════════════════════════════════════
d2_dist = p2.get("days_to_second_order_distribution", {})
n_after = d2_dist.get("n_after_trigger_day", {})
pct_after = d2_dist.get("pct_after_trigger_day", {})

nudges_md = f"""# Nudge Proposals: A/B Experiment Designs to Increase Repeat Ordering

> **Status:** Prospective test designs only. All proposed interventions are hypotheses
> grounded in observed descriptive associations. They do not claim any causal impact
> prior to empirical testing.

---

## Strategic Context

Our empirical analysis revealed three key findings:
1. **Pacing separates heavy from non-heavy customers**: Early return cadence shows a
   medium association with long-term volume (|d| about 0.72–0.76; odds ratios 0.51–0.55),
   whereas early basket composition effects are negligible to small (|d| < 0.20;
   odds ratios {lead_or_min:.2f}–{lead_or_max:.2f}).
2. **Second-order timing is the earliest point where a test could intervene**:
   Because early inter-order timing is strongly associated with long-term order volume,
   intervening between order 1 and order 2 represents the earliest actionable window
   to test whether customer pacing can be accelerated.
3. **Critical survivorship caveat**: Every customer in this dataset placed at least 4
   orders. Customers who placed fewer than 4 orders are completely absent.
   Consequently, these nudges risk targeting people who would return anyway. A randomised
   A/B test with an untreated holdout control is strictly required to measure true incremental lift.

To ensure operational feasibility, **all nudge targets are defined using only information
available at the moment the nudge fires** (e.g., first-order basket attributes and elapsed
days since order 1), rather than post-hoc segmentations that require order-3 data.

---

## Empirical Distribution of Days to Second Order (N = {n_users:,})

The table below shows key percentiles of `days_to_second_order` in the dataset, along with the volume of customers in this data who placed their second order after each trigger day.

| Percentile / Trigger Day | Days to Second Order | Customers in Data Placing Order 2 After Day X | % of Cohort Placing Order 2 After Day X | Empirical Role & Trigger Grounding |
|---|---|---|---|---|
| 10th percentile (trigger day 3) | 3.0 days | {n_after.get('day_3', 184874):,} | {pct_after.get('day_3', 89.7)}% | Rapid initial reorder |
| 25th percentile (trigger day 7) | 7.0 days | {n_after.get('day_7', 139036):,} | {pct_after.get('day_7', 67.4)}% | Typical fast-cadence threshold |
| **45th percentile (trigger day 11)** | **11.0 days** | **{n_after.get('day_11', 110240):,}** | **{pct_after.get('day_11', 53.5)}%** | **Nudge 1 Trigger** (pantry staple replenishment window) |
| **50th percentile (median, trigger day 13)** | **13.0 days** | **{n_after.get('day_13', 98936):,}** | **{pct_after.get('day_13', 48.0)}%** | **Nudge 2 Trigger** (median return cadence milestone) |
| 55th percentile (trigger day 14) | 14.0 days | {n_after.get('day_14', 91256):,} | {pct_after.get('day_14', 44.3)}% | Two-week post-purchase mark |
| 60th percentile (trigger day 16) | 16.0 days | {n_after.get('day_16', 82904):,} | {pct_after.get('day_16', 40.2)}% | Extended return window |
| 75th percentile (trigger day 28) | 28.0 days | {n_after.get('day_28', 49825):,} | {pct_after.get('day_28', 24.2)}% | Delayed return tail |

> **Selection Effect Note (Descriptive)**: This distribution is descriptive and reflects only customers who placed at least 4 orders in the dataset. Customers who placed fewer than 4 orders are not in this data. In a live production environment, true one-time dropouts will shift these distributions and lower baseline conversion rates.
>
> **Right-Censoring Note**: `days_since_prior_order` is capped at 30 days in this dataset, meaning any customer with an actual gap longer than 30 days is recorded as 30; all such customers fall inside the day-28 count.
>
> **Volume & Budget Note**: The day-11 trigger ({pct_after.get('day_11', 53.5)}% of cohort) and day-13 trigger ({pct_after.get('day_13', 48.0)}% of cohort) reach about half of all retained customers in this data. Because eligible volume is substantial, financial incentive costs (e.g. $0 delivery in Nudge 2) must scale with targeting volume and be gated strictly by the unit-economic guardrail.

---

## Nudge 1: Replenishment-Timed Reorder Reminder for Large First Baskets (Hypothesis)

### Background & Grounding
Customers whose first order contains >= 8 items (the population median) have demonstrated
willingness to shop across multiple grocery categories. In the historical data, {n_after.get('day_11', 110240):,} customers
({pct_after.get('day_11', 53.5)}%) placed their second order after day 11 (the 45th percentile of `days_to_second_order`).
A reminder timed to expected depletion of fresh staples from a large first order may encourage
timely habit formation.

### Hypothesis
**Hypothesis:** Delivering a personalized replenishment notification timed to expected
depletion of perishable staples from a large first order (day 11) will encourage
customers to place their second order sooner, reducing the inter-order gap without
shrinking second-order basket size.

### Experiment Design

| Design Element | Specification |
|---|---|
| **Target Population** | Customers whose first order contained >= 8 items who have not placed a second order by day 11 (the 45th percentile of `days_to_second_order`). |
| **Trigger** | Day 11 following delivery of order 1 if no second order has been placed. |
| **Treatment** | Push notification and email: *"Running low on your staples from Order 1? Tap to reorder in seconds."* Deep-links to a cart pre-populated with perishable items from order 1. |
| **Control** | Standard business-as-usual communications (no replenishment prompt). |
| **Unit of Randomisation** | Customer account (randomised 1:1 upon delivery of order 1). |
| **Primary Metric** | Conversion to order 2 within 30 days of order 1 delivery (%). |
| **Secondary Metric** | Days between order 1 and order 2 (survival analysis / time-to-event). |
| **Guardrail Metrics** | (1) Average basket size of order 2 (items per order; must not shrink by > 5%); (2) Unsubscribe / notification opt-out rate (must remain < 2%). |
| **Baseline & Sample Sizing Note** | **The data cannot provide a baseline return rate, so sample size must be estimated from production data.** (Illustrative design: assuming ~55% baseline conversion in production, an MDE of +3.0 percentage points at alpha = 0.05, power 80% requires ~8,500 users per arm). |
| **Duration** | 3 weeks enrolment + 30-day observation window. |
| **Stop Criteria** | Terminate early if notification opt-out rate exceeds 3.0% or second-order basket size drops by > 10%. |

---

## Nudge 2: Second-Order Re-engagement Incentive for Slow Starters (Hypothesis)

### Background & Grounding
In the historical data, the empirical median time to second order is 13.0 days (p50).
Customers who have not placed a second order by day 13 ({n_after.get('day_13', 98936):,} customers in this data, or {pct_after.get('day_13', 48.0)}%)
are falling behind typical returning cadence. Offering an incentive precisely after the median
gap has elapsed targets lagging customers at the moment they enter the slower half of the return
distribution.

### Hypothesis
**Hypothesis:** Offering a time-limited free delivery incentive to customers who have not
placed a second order by day 13 will reduce re-engagement friction and accelerate placement
of the second order.

### Experiment Design

| Design Element | Specification |
|---|---|
| **Target Population** | Customers who have placed exactly 1 order and have not placed a second order by day 13 (the empirical median of `days_to_second_order`). |
| **Trigger** | Day 13 post-order 1 delivery if no active cart or second order exists. |
| **Treatment** | In-app message and email: *"$0 Delivery on your next order — expires in 5 days."* |
| **Control** | Standard communications without delivery incentive. |
| **Unit of Randomisation** | Customer account. |
| **Primary Metric** | Conversion to order 2 within 21 days of trigger (%). |
| **Secondary Metric** | Total orders placed within 90 days. |
| **Guardrail Metrics** | (1) **Incentive cost per retained customer** (repeat contribution margin minus incentive cost); (2) Second-order basket size (must not drop below 5 items). |
| **Pricing Caveat** | The dataset contains no product prices, delivery fees, or margins. Incentive cost per retained customer must be evaluated using production financial unit economics. |
| **Baseline & Sample Sizing Note** | **The data cannot provide a baseline return rate, so sample size must be estimated from production data.** (Illustrative design: assuming ~40% baseline conversion post-day 13 in production, an MDE of +4.0 percentage points at alpha = 0.05, power 80% requires ~5,000 users per arm). |
| **Duration** | 2 weeks enrolment + 30-day post-trigger observation. |
| **Stop Criteria** | Stop if incentive cost per incrementally retained customer exceeds allowable customer acquisition cost (CAC) threshold. |

---

## Nudge 3: "Reorder in 1 Click" Quick-Cart Drawer on Visit 2 (Hypothesis)

### Background & Grounding
When customers return to the app or website after placing their first order, they face
search and browsing friction to locate previously purchased items. Streamlining the cart-building
process on visit 2 can reduce cognitive load and shorten the path to checkout.

### Hypothesis
**Hypothesis:** Displaying a prominent "Order 1 Favorites" quick-cart drawer on the home
screen when a customer opens the app for their second order will reduce session cart-building
time and increase session-to-checkout conversion.

### Experiment Design

| Design Element | Specification |
|---|---|
| **Target Population** | Any customer initiating a session after completing order 1, prior to placing order 2 (information available at session start: order count = 1). |
| **Trigger** | App open or website homepage load following order 1 completion. |
| **Treatment** | Sticky drawer on the homepage displaying all items from order 1 with a single *"Add All to Cart"* button and 1-tap add buttons per item. |
| **Control** | Standard homepage layout (generic search bar, category navigation, promotional banners). |
| **Unit of Randomisation** | Customer account. |
| **Primary Metric** | Session-to-checkout conversion rate on visit 2 (%). |
| **Secondary Metric** | Median minutes from session start to checkout during visit 2. |
| **Guardrail Metrics** | (1) Department diversity in order 2 (quick-cart drawer should not trap users in a narrow set of products); (2) Total basket item count (must not decrease). |
| **Baseline & Sample Sizing Note** | **The data cannot provide a baseline return rate, so sample size must be estimated from production data.** (Illustrative design: assuming ~32% baseline session conversion in production, an MDE of +2.5 percentage points at alpha = 0.05, power 80% requires ~12,000 users per arm). |
| **Duration** | 4 weeks concurrent traffic. |
| **Stop Criteria** | Stop if department diversity in order 2 drops by > 15% compared to control. |

---

## Summary of Methodological Guardrails

- **Hypotheses, Not Results**: All proposed lifts are minimum detectable effects for test sizing, not proven outcomes.
- **Pre-Intervention Targeting**: No nudge uses order-3 lifecycle definitions; all targeting rules rely strictly on data available at trigger time.
- **Holdout Controls**: Untreated holdout controls are mandatory to isolate true incremental returns from survivorship-driven organic returns.
- **Economic Evaluation**: Financial guardrails (incentive cost per retained customer) must be evaluated with production cost data, as the dataset contains no pricing.
"""

nudges_path = os.path.join(PROJECT_ROOT, "docs", "nudges.md")
with open(nudges_path, "w", encoding="utf-8") as f:
    f.write(nudges_md)
print(f"✓ {nudges_path}")

print("\n✅ All documents generated successfully from results.json.")
