# Executive Memo: What Turns a Grocery Customer into a Regular?

## Problem

Which early shopping behaviours (first 3 orders) are associated with becoming
a heavy, regular Instacart customer, and what nudges should we test to increase
repeat ordering?

## Data and Its Limits

We analysed **3,421,083 orders** from **206,209 users** in the Instacart
public dataset. Every user has at least 4 orders — customers who tried the
service and never returned are **not** represented (survivorship bias). There
are no prices, revenue, user demographics, or calendar dates. All findings are
**associations among already-retained customers**, not causal effects.

## Method

Features were computed from each user's first 3 orders only. Outcomes (total
orders, cadence) were measured from order 4 onward, preventing data leakage.
"Heavy user" = top 25% by total orders (≥ 20 orders, n = 53,931).
We compared heavy vs non-heavy users on 11 early features using bootstrap CIs
and Cohen's d, then fit a logistic regression (standardised features, without
early-gap features) to identify which signals matter together. Cross-validated
AUC: 0.568. Sensitivity checks at top-20% and top-30% thresholds
confirmed stability.

## Findings

The logistic regression (without gap features) identifies these as the
strongest associations with heavy-user status:

| Feature | Odds ratio | 95% CI |
|---------|-----------|--------|
| produce share (1st order) | 1.14 | [1.12, 1.15] |
| dairy share (1st order) | 1.13 | [1.12, 1.14] |
| morning-order share | 1.12 | [1.11, 1.13] |

58.3% of heavy users also have fast cadence
(median gap ≤ 7 days), and 58.1% of fast-cadence
users are also heavy. The two outcomes are correlated but not identical.

**Lifecycle segments** (defined from orders 1–3 only):
- **big-and-fast**: 59,334 users (28.8%), 42.8% heavy
- **small-and-fast**: 44,411 users (21.5%), 38.4% heavy
- **big-and-slow**: 55,132 users (26.7%), 12.2% heavy
- **small-and-slow**: 47,332 users (23.0%), 10.1% heavy

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
