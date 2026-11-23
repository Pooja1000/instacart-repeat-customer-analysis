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
   odds ratios 1.03–1.14).
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

The table below shows key percentiles of `days_to_second_order` in the dataset, along with the volume of customers in this data who had not yet placed their second order by each trigger day.

| Percentile / Trigger Day | Days to Second Order | Customers in Data Placing Order 2 After Day X | % of Cohort Placing Order 2 After Day X | Empirical Role & Trigger Grounding |
|---|---|---|---|---|
| 10th percentile | 3.0 days | 184,874 | 89.7% | Rapid initial reorder |
| 25th percentile (trigger day 7) | 7.0 days | 139,036 | 67.4% | Typical fast-cadence threshold |
| **45th percentile (trigger day 11)** | **11.0 days** | **110,240** | **53.5%** | **Nudge 1 Trigger** (pantry staple replenishment window) |
| **50th percentile (median, trigger day 13)** | **13.0 days** | **98,936** | **48.0%** | **Nudge 2 Trigger** (median return cadence milestone) |
| 55th percentile (trigger day 14) | 14.0 days | 91,256 | 44.3% | Two-week post-purchase mark |
| 60th percentile (trigger day 16) | 16.0 days | 82,904 | 40.2% | Extended return window |
| 75th percentile (trigger day 28) | 28.0 days | 49,825 | 24.2% | Delayed return tail |
| Right-censored cap (day 30) | 30.0 days | 0 | 0.0% | Maximum recorded value |

> **Selection Effect Note (Descriptive)**: This distribution is descriptive and reflects only customers who placed at least 4 orders in the dataset. Customers who placed fewer than 4 orders are not in this data. In a live production environment, true one-time dropouts will shift these distributions and lower baseline conversion rates.

---

## Nudge 1: Replenishment-Timed Reorder Reminder for Large First Baskets (Hypothesis)

### Background & Grounding
Customers whose first order contains >= 8 items (the population median) have demonstrated
willingness to shop across multiple grocery categories. In the historical data, 110,240 customers
(53.5%) placed their second order after day 11 (the 45th percentile of `days_to_second_order`).
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
