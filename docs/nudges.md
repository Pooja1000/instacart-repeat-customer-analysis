# Nudge Proposals: A/B Experiment Designs to Increase Repeat Ordering

> **Status:** Prospective test designs only. All proposed interventions are hypotheses
> grounded in observed descriptive associations. They do not claim any causal impact
> prior to empirical testing.

---

## Strategic Context

Our empirical analysis revealed three key findings:
1. **Pacing separates heavy from non-heavy customers**: Early return cadence shows a
   medium association with long-term volume (|d| about 0.72–0.76; odds ratios 0.51–0.55),
   whereas early basket composition effects are negligible to small (|d| < 0.20;
   odds ratios 0.96–1.14).
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

## Empirical Distribution of Days to Second Order (N = 206,209)

The table below shows key percentiles of `days_to_second_order` in the dataset, along with the volume of customers in this data who placed their second order after each trigger day.

| Percentile / Trigger Day | Days to Second Order | Customers in Data Placing Order 2 After Day X | % of Cohort Placing Order 2 After Day X | Empirical Role & Trigger Grounding |
|---|---|---|---|---|
| 10th percentile (trigger day 3) | 3.0 days | 184,874 | 89.7% | Rapid initial reorder |
| 25th percentile (trigger day 7) | 7.0 days | 139,036 | 67.4% | Typical fast-cadence threshold |
| **45th percentile (trigger day 11)** | **11.0 days** | **110,240** | **53.5%** | **Nudge 1 trigger (hypothesised replenishment window; not shown by this data)** |
| **50th percentile (median, trigger day 13)** | **13.0 days** | **98,936** | **48.0%** | **Nudge 2 Trigger** (median return cadence milestone) |
| 55th percentile (trigger day 14) | 14.0 days | 91,256 | 44.3% | Two-week post-purchase mark |
| 60th percentile (trigger day 16) | 16.0 days | 82,246 | 39.9% | Extended return window |
| 75th percentile (trigger day 28) | 28.0 days | 49,825 | 24.2% | Delayed return tail |

> **Selection Effect Note (Descriptive)**: This distribution is descriptive and reflects only customers who placed at least 4 orders in the dataset. Customers who placed fewer than 4 orders are not in this data. In a live production environment, true one-time dropouts will shift these distributions and lower baseline conversion rates.
>
> **Right-Censoring Note**: `days_since_prior_order` is capped at 30 days in this dataset, meaning any customer with an actual gap longer than 30 days is recorded as 30; all such customers fall inside the day-28 count.
>
> **Volume & Budget Note**: The day-11 trigger (53.5% of cohort) and day-13 trigger (48.0% of cohort) reach about half of all retained customers in this data. Because eligible volume is substantial, financial incentive costs (e.g. $0 delivery in Nudge 2) must scale with targeting volume and be gated strictly by the unit-economic guardrail.

---

## Nudge 1: Replenishment-Timed Reorder Reminder for Large First Baskets (Hypothesis)

### Background & Grounding
In the historical data, **60,176 customers (29.2% of users)** had a first order containing >= 8 items (the population median) AND placed their second order after day 11 (the 45th percentile of `days_to_second_order`). A replenishment notification timed to expected depletion of perishable staples from a large first order may encourage timely habit formation.

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
| **Unit of Randomisation** | Customer account (randomised 1:1 at day 11 among eligible customers who have not placed order 2). |
| **Primary Metric** | Conversion to order 2 within 21 days of trigger (%). |
| **Secondary Metric** | Days between order 1 and order 2 (survival analysis / time-to-event). |
| **Guardrail Metrics** | (1) Relative change in basket size of order 2 vs control; (2) Notification opt-out rate (must remain < 2%). |
| **Baseline & Sample Sizing Note** | **The data cannot provide a baseline return rate, so sample size must be estimated from production data.** See Sample Size Planning table below. |
| **Duration** | 3 weeks enrolment + 21-day post-trigger observation window. |
| **Stop Criteria** | Terminate early if notification opt-out rate exceeds 2.0% or second-order basket size drops by > 10% vs control. |

---

## Nudge 2: Second-Order Re-engagement Incentive for Slow Starters (Hypothesis)

### Background & Grounding
In the historical data, the empirical median time to second order is 13.0 days (p50).
Customers who have not placed a second order by day 13 (98,936 customers in this data, or 48.0%)
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
| **Guardrail Metrics** | (1) **Incentive cost per incremental order**: (promo cost in treatment − promo cost in control) / incremental orders; (2) Relative change in basket size vs control. |
| **Pricing Caveat** | The dataset contains no product prices, delivery fees, or margins. Incentive cost per incremental order must be evaluated using production financial unit economics. |
| **Baseline & Sample Sizing Note** | **The data cannot provide a baseline return rate, so sample size must be estimated from production data.** See Sample Size Planning table below. |
| **Duration** | 2 weeks enrolment + 30-day post-trigger observation. |
| **Stop Criteria** | Stop if incentive cost per incremental order exceeds allowable customer acquisition cost (CAC) threshold. |

---

## Nudge 3: "Reorder in 1 Click" Quick-Cart Drawer on Visit 2 (Hypothesis)

### Background & Grounding
**Link to Findings:** Weak link to historical data. The dataset has only day-of-week, hour-of-day and days-since-prior-order; no timestamps, browsing, clickstream or session data.

However, when customers return to the app or website after placing their first order, they face search and browsing friction to locate previously purchased items. Streamlining the cart-building process on visit 2 can reduce cognitive load and shorten the path to checkout.

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
| **Guardrail Metrics** | (1) Department diversity in order 2 (relative change vs control; quick-cart drawer should not trap users in a narrow set of products); (2) Relative change in basket item count vs control. |
| **Baseline & Sample Sizing Note** | **The data cannot provide a baseline return rate, so sample size must be estimated from production data.** See Sample Size Planning table below. |
| **Duration** | 4 weeks concurrent traffic. |
| **Stop Criteria** | Stop if department diversity in order 2 drops by > 15% compared to control. |

---

## Sample Size Planning (Placeholder; Replace Baselines with Production Data)

Because this historical dataset suffers from survivorship bias (all customers placed >= 4 orders), **the data cannot provide baseline return rates**. True baseline conversion rates and minimum detectable effects (MDE) must be estimated from live production data.

The table below provides required sample sizes (per-arm and total) for a two-sided two-proportion test at alpha = 0.05 and 80% statistical power across hypothetical baseline conversion rates (20%, 30%, 40%, 50%) and minimum detectable effects (+2%, +3%, +4% percentage points). Do not treat any baseline below as realistic or established for production.

**Formula**: Sample sizes are computed using the standard two-proportion formula with pooled variance under the null (no continuity correction): $n = (z_{\alpha/2} \sqrt{2 \bar p (1-\bar p)} + z_\beta \sqrt{p_1(1-p_1)+p_2(1-p_2)})^2 / (p_2-p_1)^2$, where $\bar p = (p_1+p_2)/2$, implemented via `scipy.stats.norm.ppf`.

| Baseline Conversion Rate | MDE (+ percentage points) | Sample Size Per Arm (n) | Total Sample Size (2n) |
|---|---|---|---|
| 20% | +2% pts (to 22%) | 6,510 | 13,020 |
| 20% | +3% pts (to 23%) | 2,943 | 5,886 |
| 20% | +4% pts (to 24%) | 1,683 | 3,366 |
| 30% | +2% pts (to 32%) | 8,394 | 16,788 |
| 30% | +3% pts (to 33%) | 3,763 | 7,526 |
| 30% | +4% pts (to 34%) | 2,134 | 4,268 |
| 40% | +2% pts (to 42%) | 9,493 | 18,986 |
| 40% | +3% pts (to 43%) | 4,234 | 8,468 |
| 40% | +4% pts (to 44%) | 2,389 | 4,778 |
| 50% | +2% pts (to 52%) | 9,806 | 19,612 |
| 50% | +3% pts (to 53%) | 4,356 | 8,712 |
| 50% | +4% pts (to 54%) | 2,448 | 4,896 |

> **Note**: This table is a planning placeholder. Production teams should substitute actual baseline conversion rates from live tracking to determine experiment duration and traffic allocation.

---

## Test Interaction Note

Nudges 1 and 2 can target the same customers (day-11 trigger vs day-13 trigger for users with first order >= 8 items). To avoid contamination, either run them as **separate, sequential tests** or make the audiences **mutually exclusive** (e.g., randomly assign eligible customers to one nudge only).

---

## Summary of Methodological Guardrails

- **Hypotheses, Not Results**: All proposed lifts are minimum detectable effects for test sizing, not proven outcomes.
- **Pre-Intervention Targeting**: No nudge uses order-3 lifecycle definitions; all targeting rules rely strictly on data available at trigger time.
- **Holdout Controls**: Untreated holdout controls are mandatory to isolate true incremental returns from survivorship-driven organic returns.
- **Economic Evaluation**: Financial guardrails (incentive cost per incremental order: (promo cost in treatment − promo cost in control) / incremental orders) must be evaluated with production cost data, as the dataset contains no pricing.
