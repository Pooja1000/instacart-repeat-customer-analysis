# Nudge Proposals: Experiment Designs to Increase Repeat Ordering

> These are **test designs**, not results. We propose experiments based on
> observed associations. No impact is claimed until an experiment is run.

---

## Nudge 1: "Complete Your Basket" Prompt for Small First Orders

### Grounding

Users whose first order contains more items and spans more departments are
associated with higher odds of becoming heavy users (see `results.json`
for exact odds ratios and CIs). This association may reflect that broader
first baskets help users experience enough of the platform to build a habit,
or it may simply reflect that committed users shop more from the start.
An experiment can test whether a prompt to add items changes behaviour.

### Design

| Element | Detail |
|---------|--------|
| **Target segment** | `small-and-slow` and `small-and-fast` (first basket below the median of 8 items) |
| **Hypothesis** | Prompting users with small initial carts to explore complementary staples will increase early basket breadth and engagement, associating with higher repeat order frequency over 90 days. |
| **Trigger** | User has ≤ 5 items in cart and begins checkout on their first order |
| **Treatment** | Show a "Round out your basket?" interstitial with popular items from departments not yet in the cart (produce, dairy, snacks) |
| **Control** | Standard checkout flow |
| **Unit of randomisation** | User (randomised at account creation) |
| **Primary metric** | Number of orders placed in the 90 days following the first order |
| **Guardrail metrics** | (1) First-order completion rate (must not drop — the prompt should not cause cart abandonment); (2) Average basket size in orders 2–5 (prompt should not simply shift items from future orders into the first) |
| **Minimum detectable effect** | +5% relative lift in 90-day order count. With a baseline of ~10 orders per user over the observation period, this is 0.5 additional orders. |
| **Sample size (rough)** | ~20,000 per arm (α = 0.05 two-sided, power = 0.80, estimated from the observed variance in total orders). Adjust with actual conversion data. |
| **Duration** | 4–6 weeks of enrolment + 90-day observation window |
| **Stop criteria** | Stop if first-order completion rate drops > 2 percentage points (guardrail violation). |

---

## Nudge 2: Reorder Reminder Timed to the User's Observed Gap

### Grounding

Users who return for their second order quickly tend to become heavier users
(as shown in the with-gap-features regression model). The median gap between
orders 1 and 2 is about 15 days for non-heavy users vs shorter for heavy users.
A well-timed reminder might pull some users back before the habit window closes.

### Design

| Element | Detail |
|---------|--------|
| **Target segment** | All users after their first order |
| **Hypothesis** | Delivering a personalized reorder reminder at the expected reorder interval will reduce friction for the second order, shortening the inter-order gap and increasing 90-day order retention. |
| **Trigger** | User has not placed a second order N days after their first (N = user's observed gap from similar users, default 7 days) |
| **Treatment** | Push notification or email: "Your [top 3 items from first order] might be running low — reorder with one tap" |
| **Control** | No reminder (or standard marketing cadence) |
| **Unit of randomisation** | User |
| **Primary metric** | Days to second order (survival analysis: time-to-event) |
| **Secondary metric** | Total orders in 90 days |
| **Guardrail metrics** | (1) Unsubscribe / notification-disable rate; (2) Basket size of second order (should not shrink — we don't want tiny "just checking in" orders) |
| **Minimum detectable effect** | 1-day reduction in median gap to second order (from an assumed baseline of ~15 days) |
| **Sample size (rough)** | ~15,000 per arm (depends on variance of gap; use a log-rank test for the survival analysis) |
| **Duration** | 3–4 weeks of enrolment + 30-day observation window |
| **Stop criteria** | Stop if unsubscribe rate exceeds 3% or second-order basket size drops > 10%. |

---

## Nudge 3: "Buy It Again" Shelf Highlighting First-Order Items

### Grounding

Reorder rate rises steeply from order 1 (0%) to order 3 (~40%) among users
who persist (constant-cohort reorder curve). Users who reorder more of their
previous items in orders 2–3 show a small positive association with heavy-user
status. Making it easier to reorder first-order items in subsequent visits may
accelerate habit formation.

### Design

| Element | Detail |
|---------|--------|
| **Target segment** | All users on their 2nd or 3rd visit |
| **Hypothesis** | Reducing search friction for previously purchased items through an upfront "Buy It Again" carousel will increase early reorder rate and accelerate repeat shopping habits. |
| **Trigger** | User opens the app/site for order 2 or 3 |
| **Treatment** | A prominent "Buy it again" carousel at the top of the homepage showing all items from the user's most recent order, with one-tap add-to-cart |
| **Control** | Standard homepage (which may already have recommendation carousels, but not specifically anchored to the user's prior order) |
| **Unit of randomisation** | User |
| **Primary metric** | Reorder rate in orders 2–3 (share of items that are reorders) |
| **Secondary metric** | Total orders in 90 days |
| **Guardrail metrics** | (1) Total basket size (the "buy it again" shelf should supplement, not replace, browsing — basket size should not drop); (2) Product diversity (number of distinct products per order — the shelf should not lock users into a narrow set) |
| **Minimum detectable effect** | +3 percentage points in reorder rate (from a baseline of ~28% at order 2) |
| **Sample size (rough)** | ~10,000 per arm (proportion test, α = 0.05, power = 0.80) |
| **Duration** | 3–4 weeks of enrolment + observation through order 3 |
| **Stop criteria** | Stop if basket size drops > 5% or product diversity drops > 10%. |

---

## Notes for All Nudges

- **Descriptive, not causal**: These designs are grounded in observed
  associations. The experiment is what determines whether the nudge actually
  works.
- **Sample sizes are rough**: They assume normally distributed metrics and
  two-sided tests. Actual power calculations should use the observed variance
  from the specific metric and account for clustering if applicable.
- **Sequential testing**: For production, consider a sequential testing
  framework (e.g., group sequential design or always-valid p-values) to
  enable early stopping for both futility and harm.
- **Interaction effects**: If multiple nudges are run simultaneously, use a
  factorial design or run them on non-overlapping user segments to avoid
  confounding.
