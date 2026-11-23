# Executive Memo: What Turns a Grocery Customer into a Regular?

## Problem

Which early shopping behaviours (orders 1–3) are associated with becoming
a heavy, regular Instacart customer later, and which interventions should we
test to increase repeat ordering?

## Data and Its Limits

We analysed **3,421,083 orders** from **206,209 users** in the Instacart
public dataset. Every user in this dataset has at least 4 orders — customers
who tried the service once or twice and left are **not** represented
(survivorship bias). Furthermore:
- **Total orders are capped at 100**: The distribution is truncated at 100 orders.
- **Median gap is capped at 30 days**: `days_since_prior_order` is right-censored
  at 30 (19.2× spike at 30 vs 29 days).
- **No prices, revenue, user demographics, or calendar dates**.
- All findings describe **observational associations among already-retained
  customers**, not causal drivers.

## Method (3–5 lines)

Features were computed exclusively from each user's first 3 orders; outcomes
(total orders, cadence) were measured from order 4 onward to prevent leakage.
"Heavy user" was defined as the top quartile by total orders (≥ 20 orders,
$n = 53,931$). We compared early features using bootstrap CIs and Cohen's $d$,
then fit standardized logistic regressions. To eliminate collinearity, `first_order_size`
and `n_aisles_order1` were dropped, ensuring all Variance Inflation Factors are
strictly $< 2.5$ (max VIF = 2.27) with zero sign flips.

## Findings: Lead Model (Early Basket & Timing Features)

Leading with the no-gap model, early basket and timing signals achieve a
cross-validated AUC of **0.568** ($\approx 0.57$).

**Plain-English takeaway**: Basket-composition effects are **small**. Every basket
feature has a Cohen's $d < 0.20$ (negligible/small by conventional standards), and
odds ratios are modest ($1.03$–$1.14$). While statistically detectable due to large
sample size ($N = 206,209$), early basket mix alone offers limited ability to
discriminate future heavy users.

| Feature | Odds ratio (std) | 95% CI | Univariate Cohen's d |
|---|---|---|---|
| produce share (1st order) | 1.14 | [1.13, 1.16] | +0.090 (negligible) |
| dairy share (1st order) | 1.13 | [1.12, 1.14] | +0.089 (negligible) |
| morning-order share | 1.12 | [1.11, 1.13] | +0.121 (negligible) |
| average basket size (orders 1–3) | 1.10 | [1.08, 1.11] | +0.122 (negligible) |
| snacks share (1st order) | 1.07 | [1.06, 1.09] | +0.025 (negligible) |

## Why Early Gaps Are Partly Circular

When early inter-order gaps (`days_to_second_order` and `days_to_third_order`)
are added to the model, cross-validated AUC jumps from **0.568** to **0.756**,
with early gap odds ratios of **0.55** [95% CI 0.54–0.55] and **0.51** [95% CI 0.50–0.52].

However, this association is **partly circular**:
- "Heavy user" status is defined by accumulated total orders across the dataset window.
- A customer who orders every 5 days will mechanically accumulate 20+ orders much faster
  over any fixed time horizon than a customer who orders every 25 days.
- Early gap timing is not an independent causal lever; it is an early observation of the
  very cadence that defines the outcome. We present early pace as a separate diagnostic
  finding about habit velocity, rather than an actionable basket feature.

## Cadence & Heavy-User Overlap (Sensitivity Check)

At our primary 7-day cadence threshold, **58.3%** of heavy
users qualify as fast-cadence, and **58.1%** of fast-cadence
users qualify as heavy.

To ensure this relationship is not an artifact of the 7-day cutoff, we performed a
sensitivity check across 6, 7, and 8-day thresholds:
- **Threshold 6 days**: 33,839 fast users; 37.1% of heavy are fast; 59.1% of fast are heavy.
- **Threshold 7 days**: 54,086 fast users; 58.3% of heavy are fast; 58.1% of fast are heavy.
- **Threshold 8 days**: 66,840 fast users; 69.6% of heavy are fast; 56.1% of fast are heavy.

The conclusion is invariant: fast cadence and heavy order volume are closely linked,
yet distinct (~40% of fast-cadence shoppers are not top-quartile volume buyers).

## Lifecycle Segments (at Order 3 Decision Point)

Segmenting users at order 3 by basket size (median = 8) and early gap (median = 14.5d):
- **big-and-fast**: 59,334 users (28.8%), 42.8% heavy, avg 23.2 orders.
- **small-and-fast**: 44,411 users (21.5%), 38.4% heavy, avg 21.6 orders.
- **big-and-slow**: 55,132 users (26.7%), 12.2% heavy, avg 10.9 orders.
- **small-and-slow**: 47,332 users (23.0%), 10.1% heavy, avg 10.2 orders.

## Recommended Nudges to Test (Targeting Second Order)

Because the second order is the critical retention hurdle, we propose 3 A/B test designs
targeting second-order conversion and cadence (see `docs/nudges.md`):

1. **Replenishment-timed reminder for "big-and-slow" customers (Hypothesis)**:
   Target customers who built large first baskets but have not returned by day 10–12
   with a reminder anchored to perishable replenishment cycles.
2. **Second-order re-engagement incentive for "small-and-slow" starters**:
   Target high-churn-risk slow starters with a time-limited delivery subsidy at day 10.
3. **"Reorder in 1-Click" quick-cart drawer for returning order-2 shoppers**:
   Streamline cart building on visit 2 to capitalize on the natural jump in reorder
   propensity (from 0% to 28.2%).

## Risks and What Could Mislead Us

- **Survivorship**: Nudges derived from already-retained users may fail for true one-time dropouts.
- **Total orders capped at 100 & gaps capped at 30**: Censors both volume and churn extremes.
- **No prices / margins**: Cannot observe whether larger baskets reflect higher customer profitability.
- **Descriptive, not causal**: An experiment is required before implementing any production changes.
