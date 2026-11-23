# Executive Memo: What Turns a Grocery Customer into a Regular?

## Bottom Line

- **Early pacing separates future heavy users far more than basket composition**: A model using early basket and timing features achieves a cross-validated AUC of 0.57 (~0.57), while adding early inter-order gaps raises AUC to 0.76 (~0.76).
- **Circularity caveat**: Part of the gap link is built into how "heavy" is defined. Cumulative order count is mechanically linked to order cadence, assuming comparable observation windows.
- **Recommended next step**: It is unknown whether customer pace can be influenced. The highest-leverage next step is to run A/B test designs targeting second-order timing to test whether pacing can be accelerated.

---

## Problem

Which early shopping behaviours (orders 1–3) are associated with becoming a heavy, regular Instacart customer later, and which interventions would be worth testing to increase repeat ordering?

---

## Data and Its Limits

We analysed **3,421,083 orders** from **206,209 users** in the Instacart public dataset.
- **Survivorship bias (critical)**: Every customer in this dataset has at least 4 orders. Customers who tried the service once or twice and left are completely absent. All findings describe observational associations among already-retained customers, not the full acquisition funnel.
- **Total orders capped at 100**: Order sequence is truncated at 100 orders, right-censoring the extreme power-user tail.
- **Median gap capped at 30 days**: `days_since_prior_order` is truncated at 30 days (evidenced by a 19.2x spike at 30 vs 29 days), compressing long churn gaps.
- **No prices, revenue, user demographics, or calendar dates**: Basket size is item count, not currency value.
- **Descriptive only**: We report observational associations; we never claim any behavior causes retention.

---

## Method (3–5 lines)

Features were computed exclusively from each customer's first 3 orders; outcomes (total orders, cadence) were measured from order 4 onward to prevent leakage. "Heavy user" was defined as the top quartile by total orders (>= 20 orders, n = 53,931). We compared early features using bootstrap CIs and Cohen's d, then fit standardized logistic regressions. To eliminate collinearity, `first_order_size` and `n_aisles_order1` were dropped, ensuring all Variance Inflation Factors are strictly < 2.5 (true maximum VIF across both models = 2.28) with zero sign flips.

---

## Findings: Lead Model (Early Basket & Timing Features)

Leading with the no-gap model, early basket composition and timing features achieve a cross-validated AUC of **0.568** (~0.57).

**Plain-English takeaway**: Basket-composition and breadth effects are **negligible to small**. Every basket feature has a Cohen's d < 0.20 (negligible to small by standard conventions), and odds ratios are modest (1.03–1.14). While statistically detectable due to the large sample size (N = 206,209), early basket mix alone offers limited ability to discriminate future heavy users.

| Feature | Odds Ratio (std) | 95% CI | Univariate Cohen's d | Effect Magnitude |
|---|---|---|---|---|
| produce share (1st order) | 1.14 | [1.13, 1.16] | +0.090 | negligible to small |
| dairy share (1st order) | 1.13 | [1.12, 1.14] | +0.089 | negligible to small |
| morning-order share (6am–11am) | 1.12 | [1.11, 1.13] | +0.121 | negligible to small |
| average basket size (orders 1–3) | 1.10 | [1.08, 1.11] | +0.122 | negligible to small |
| snacks share (1st order) | 1.07 | [1.06, 1.09] | +0.025 | negligible to small |

---

## Why Early Gaps Are Partly Circular

When early inter-order gaps (`days_to_second_order` and `days_to_third_order`) are added to the model, cross-validated AUC jumps from **0.568** to **0.756**, with early gap odds ratios of **0.55** [95% CI 0.54–0.56] and **0.51** [95% CI 0.50–0.52]. In univariate comparisons, gap effects are medium (|d| about 0.72–0.76; d = -0.724 for order 2 gap, d = -0.760 for order 3 gap).

However, this association is **likely partly mechanical, assuming comparable observation windows**:
- "Heavy user" status is defined by accumulated total orders across the dataset window.
- A customer who orders every 5 days will mechanically accumulate 20+ orders much faster than a customer who orders every 25 days.
- It is **unknown whether pace can be influenced** by product features or marketing interventions. Pacing reflects a customer's underlying household grocery rhythm. We present early pace as a separate finding about cadence velocity, rather than an actionable basket feature.

---

## Cadence & Heavy-User Overlap (Sensitivity Check)

At our primary 7-day cadence threshold, **58.3%** of heavy users qualify as fast-cadence, and **58.1%** of fast-cadence users qualify as heavy.

To test robustness, we evaluated cutoffs across 6, 7, and 8 days:
- **Share of fast users who are heavy is stable (56–59%)**: 59.1% at 6 days, 58.1% at 7 days, and 56.1% at 8 days.
- **Share of heavy users who are fast varies widely (37% to 70%)**: 37.1% at 6 days, 58.3% at 7 days, and 69.6% at 8 days.
- **41–44% of fast users are not heavy**: (40.9% at 6d, 41.9% at 7d, 43.9% at 8d). Fast pacing and cumulative order volume are strongly linked, yet distinct.

---

## Lifecycle Segments (Defined at Order 3 Decision Point)

Segments are defined at order 3 using two specific metrics:
- **Basket size**: First-order item count (split at median = 8 items).
- **Early gap**: Mean inter-order gap across orders 1->2 and 2->3 (split at median = 14.5 days).

**Note on circularity**: Because early gap restates early pace, these segments are partly circular with total orders.

**Key takeaway**:
- **Pace segments differ by about 28–32 percentage points in heavy rate**:
  - `big-and-fast` (42.8%) vs `big-and-slow` (12.2%) = 30.6 point difference.
  - `small-and-fast` (38.4%) vs `small-and-slow` (10.1%) = 28.3 point difference.
- **Basket-size segments differ by only about 2–4 percentage points**:
  - `big-and-fast` (42.8%) vs `small-and-fast` (38.4%) = 4.4 point difference.
  - `big-and-slow` (12.2%) vs `small-and-slow` (10.1%) = 2.1 point difference.

| Segment | Users | % of Base | Heavy Rate | Fast Cadence Rate | Avg Total Orders |
|---|---|---|---|---|---|
| **big-and-fast** | 59,334 | 28.8% | 42.8% | 41.0% | 23.2 |
| **small-and-fast** | 44,411 | 21.5% | 38.4% | 41.5% | 21.6 |
| **big-and-slow** | 55,132 | 26.7% | 12.2% | 10.5% | 10.9 |
| **small-and-slow** | 47,332 | 23.0% | 10.1% | 11.7% | 10.2 |

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
