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
   orders. Customers who tried Instacart once and never returned are completely absent.
   Consequently, these nudges risk targeting people who would return anyway. A randomised
   A/B test with an untreated holdout control is strictly required to measure true incremental lift.

To ensure operational feasibility, **all nudge targets are defined using only information
available at the moment the nudge fires** (e.g., first-order basket attributes and elapsed
days since order 1), rather than post-hoc segmentations that require order-3 data.

---

## Nudge 1: Replenishment-Timed Reorder Reminder for Large First Baskets (Hypothesis)

### Background & Grounding
Customers whose first order contains >= 8 items (the population median) have demonstrated
broad willingness to shop across categories. However, customers who wait longer than the
median gap (14.5 days) to place their second order have substantially lower heavy-user rates
(12.2% vs 42.8% for fast returners). Slow pacing may stem from natural pantry consumption
cycles or the absence of a well-timed reminder.

### Hypothesis
**Hypothesis:** Delivering a personalized replenishment notification timed to expected
depletion of perishable staples from a large first order (days 10–12) will encourage
customers to place their second order sooner, reducing the inter-order gap without
shrinking second-order basket size.

### Experiment Design

| Design Element | Specification |
|---|---|
| **Target Population** | Customers whose first order contained >= 8 items (available from order 1) who have not placed a second order by day 11. |
| **Trigger** | Day 11 following delivery of order 1 if no second order has been initiated. |
| **Treatment** | Push notification and email: *"Running low on your staples from Order 1? Tap to reorder in seconds."* Deep-links to a cart pre-populated with perishable items from order 1. |
| **Control** | Standard business-as-usual communications (no replenishment prompt). |
| **Unit of Randomisation** | Customer account (randomised 1:1 upon delivery of order 1). |
| **Primary Metric** | Conversion to order 2 within 30 days of order 1 delivery (%). |
| **Secondary Metric** | Days between order 1 and order 2 (survival analysis / time-to-event). |
| **Guardrail Metrics** | (1) Average basket size of order 2 (items per order; must not shrink by > 5%); (2) Unsubscribe / notification opt-out rate (must remain < 2%). |
| **Caveats** | (1) May reach customers who would return anyway (survivorship bias in historical baseline); (2) Dataset contains no prices, so basket value must be proxied by item count. |
| **Assumed Baseline** | Baseline 30-day second-order conversion among slow returners: ~55%. |
| **Minimum Detectable Effect (MDE)** | +3.0 percentage points in 30-day conversion (from 55% to 58%), or 1.5-day reduction in median gap. |
| **Sample Size (Rough)** | ~8,500 users per arm (alpha = 0.05 two-sided, power 80%). Enrolment window: ~3 weeks. |
| **Duration** | 3 weeks enrolment + 30-day observation window. |
| **Stop Criteria** | Terminate early if notification opt-out rate exceeds 3.0% or second-order basket size drops by > 10%. |

---

## Nudge 2: Second-Order Re-engagement Incentive for Slow Starters (Hypothesis)

### Background & Grounding
Customers whose second order has not arrived within the population median gap (14.5 days)
show much lower transition rates into regular shopping habits (heavy-user rate is ~10–12%
for slow returners vs ~38–43% for fast returners). Intervening after the median gap has
elapsed targets customers who are lagging behind typical return cadence.

### Hypothesis
**Hypothesis:** Offering a time-limited free delivery incentive to customers whose second
order has not arrived by day 15 will reduce trial friction and accelerate placement of the
second order.

### Experiment Design

| Design Element | Specification |
|---|---|
| **Target Population** | Any customer who has placed exactly 1 order and has not placed a second order by day 15 (information available at trigger time: 1 completed order, elapsed days > 14.5). |
| **Trigger** | Day 15 post-order 1 delivery if no active cart or order exists. |
| **Treatment** | In-app message and email: *"$0 Delivery on your next order — expires in 5 days."* |
| **Control** | Standard communications without delivery incentive. |
| **Unit of Randomisation** | Customer account. |
| **Primary Metric** | Conversion to order 2 within 21 days of trigger (%). |
| **Secondary Metric** | Total orders placed within 90 days. |
| **Guardrail Metrics** | (1) **Incentive cost per retained customer** (repeat contribution margin minus incentive cost); (2) Second-order basket size (must not drop below 5 items). |
| **Caveats** | (1) **No price or margin data**: The dataset contains no product prices, delivery fees, or margins. Incentive cost per retained customer must be evaluated using production financial unit economics. (2) **Subsidizing organic returns**: Because the dataset excludes one-time buyers who never returned, a portion of targeted customers would return organically; the holdout control is essential to evaluate net incremental lift. |
| **Assumed Baseline** | Baseline second-order conversion past day 15 without incentive: ~40%. |
| **Minimum Detectable Effect (MDE)** | +4.0 percentage points in conversion (from 40% to 44%). |
| **Sample Size (Rough)** | ~5,000 users per arm (alpha = 0.05 two-sided, power 80%). |
| **Duration** | 2 weeks enrolment + 30-day post-trigger observation. |
| **Stop Criteria** | Stop if incentive cost per incrementally retained customer exceeds allowable customer acquisition cost (CAC) threshold. |

---

## Nudge 3: "Reorder in 1 Click" Quick-Cart Drawer on Visit 2 (Hypothesis)

### Background & Grounding
When customers return to the app or website after placing their first order, they face
search and browsing friction to find items they liked. Streamlining the cart-building
process on visit 2 can reduce cognitive load and shorten the time to checkout.

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
| **Caveats** | May primarily benefit users who already intend to reorder identical items; impact on long-term category exploration must be monitored via the diversity guardrail. |
| **Assumed Baseline** | Baseline session-to-checkout conversion on visit 2: ~32%. Median session duration: 14 minutes. |
| **Minimum Detectable Effect (MDE)** | +2.5 percentage points in conversion (from 32% to 34.5%) and >= 2-minute reduction in session duration. |
| **Sample Size (Rough)** | ~12,000 users per arm (alpha = 0.05, power 80%). |
| **Duration** | 4 weeks concurrent traffic. |
| **Stop Criteria** | Stop if department diversity in order 2 drops by > 15% compared to control. |

---

## Summary of Methodological Guardrails

- **Hypotheses, Not Results**: All proposed lifts are minimum detectable effects for test sizing, not proven outcomes.
- **Pre-Intervention Targeting**: No nudge uses order-3 lifecycle definitions; all targeting rules rely strictly on data available at trigger time.
- **Holdout Controls**: Untreated holdout controls are mandatory to isolate true incremental returns from survivorship-driven organic returns.
- **Economic Evaluation**: Financial guardrails (incentive cost per retained customer) must be evaluated with production cost data, as the dataset contains no pricing.
