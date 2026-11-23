# Nudge Proposals: A/B Experiment Designs to Increase Repeat Ordering

> **Status:** Test designs only. These are prospective experiment designs grounded
> in observed descriptive associations. They do not claim any causal impact
> prior to empirical testing.

---

## Strategic Context

Our empirical analysis revealed three key structural realities among repeat customers:
1. **Cadence is the primary differentiator**: Early inter-order gap is the single
   strongest signal separating heavy from non-heavy customers ($d \approx -0.72$ to $-0.76$;
   odds ratios $\approx 0.51$–$0.55$).
2. **Basket composition effects are small**: Early department mix and basket breadth
   have small individual associations ($|d| < 0.20$; odds ratios $\approx 1.03$–$1.14$).
3. **The second order is the critical juncture**: The sharpest hazard of drop-off
   occurs between order 1 and order 2, whereas reorder rate accelerates rapidly
   from order 2 onward ($28.2\%$ at order 2 to $40.3\%$ at order 3).

Consequently, all proposed interventions **target the second order for slow starters**
and address pacing and replenishment friction, rather than artificially prompting
first-basket expansion.

---

## Nudge 1: Replenishment-Timed Reorder Reminder for "Big-and-Slow" Customers

### Background & Grounding
Users in the `big-and-slow` segment ($26.7\%$ of customers, $n = 55,132$) place
above-average first baskets ($\ge 8$ items) but exhibit slow early cadence
($> 14.5$ days between orders). Only $12.2\%$ become heavy users, compared to
$42.8\%$ of `big-and-fast` customers. Because these users already demonstrated high
basket willingness, their slow return is more likely due to consumption cycles or
absence of timely triggers rather than lack of category interest.

### Hypothesis
**Hypothesis (to be tested):** Delivering a personalized replenishment notification
anchored to the perishable staples in a customer's large first order (timed to
typical household depletion at days 10–12) will pull forward the timing of order 2
and increase 60-day repeat order conversion without cannibalizing order size.

### Experiment Design

| Design Element | Specification |
|---|---|
| **Target Segment** | `big-and-slow` users (first basket $\ge 8$ items, no second order placed by day 10). |
| **Trigger** | Day 11 following delivery of order 1 if no second order has been initiated. |
| **Treatment** | Push notification / email: *"Running low on [Product 1] and [Product 2]? Tap to add your staples back to your cart."* Deep-links directly to a pre-filled cart. |
| **Control** | Standard marketing communications (business-as-usual; no personalized replenishment prompt). |
| **Unit of Randomisation** | User (randomised $1:1$ upon delivery of order 1). |
| **Primary Metric** | Conversion to order 2 within 30 days of order 1 delivery ($\%$). |
| **Secondary Metric** | Days between order 1 and order 2 (survival analysis / time-to-event). |
| **Guardrail Metrics** | (1) Average basket size of order 2 (items per order; must not shrink by $>5\%$); (2) Unsubscribe / notification disable rate (must remain $<2\%$). |
| **Assumed Baseline** | Baseline 30-day second-order conversion in this segment: $\approx 55\%$. Assumed standard deviation of gap: $\approx 8$ days. |
| **Minimum Detectable Effect (MDE)** | $+3.0$ percentage points in 30-day conversion (from $55\%$ to $58\%$), or $1.5$-day reduction in median gap. |
| **Sample Size (Rough)** | $\approx 8,500$ users per variant ($\alpha = 0.05$ two-sided, power $80\%$). At current volume, enrolment window $\approx 3$ weeks. |
| **Duration** | 3 weeks enrolment $+$ 30-day follow-up window. |
| **Stop Criteria** | Terminate early if notification opt-out / unsubscribe rate exceeds $3.0\%$ or if order 2 basket size decreases by $>10\%$. |

---

## Nudge 2: Second-Order Re-engagement Incentive for "Small-and-Slow" Starters

### Background & Grounding
Customers in the `small-and-slow` segment ($23.0\%$ of users, $n = 47,332$) start with
below-median initial baskets ($<8$ items) and extended inter-order gaps ($>14.5$ days).
Only $10.1\%$ become heavy users, averaging just $10.2$ total orders. These users have
the lowest retention on the platform and face high attrition risk immediately after order 1.

### Hypothesis
**Hypothesis (to be tested):** Offering a targeted, time-limited delivery incentive
for the second order before typical drop-off (at day 10) will lower the perceived
friction of a second trial, lifting second-order conversion and preventing early churn.

### Experiment Design

| Design Element | Specification |
|---|---|
| **Target Segment** | `small-and-slow` users (first basket $< 8$ items, no second order placed by day 10). |
| **Trigger** | Day 10 post-order 1 delivery if no active cart or order exists. |
| **Treatment** | In-app message and email: *"$0 Delivery on your next order — expires in 5 days."* |
| **Control** | Standard transactional communications without special second-order delivery subsidy. |
| **Unit of Randomisation** | User (randomised $1:1$ upon order 1 completion). |
| **Primary Metric** | Conversion to order 2 within 21 days of trigger ($\%$). |
| **Secondary Metric** | Total orders placed within 90 days. |
| **Guardrail Metrics** | (1) Net contribution margin per acquired user (repeat gross profit minus subsidy cost); (2) Basket size of order 2 (must not drop below 5 items). |
| **Assumed Baseline** | Baseline second-order conversion at day 10 without incentive: $\approx 40\%$. |
| **Minimum Detectable Effect (MDE)** | $+4.0$ percentage points in conversion (from $40\%$ to $44\%$). |
| **Sample Size (Rough)** | $\approx 5,000$ users per variant ($\alpha = 0.05$ two-sided, power $80\%$). Enrolment window $\approx 2$ weeks. |
| **Duration** | 2 weeks enrolment $+$ 30-day post-trigger observation. |
| **Stop Criteria** | Stop if net contribution margin per user is negative after accounting for subsequent repeat ordering (futility/cost guardrail). |

---

## Nudge 3: "Reorder Your Favorites in 1 Click" Quick-Cart Drawer for Order 2

### Background & Grounding
Empirical reorder rates accelerate from $0\%$ at order 1 to $28.2\%$ at order 2 and
$40.3\%$ at order 3 among persisting customers. Returning customers frequently spend
excessive session time searching for items they previously purchased. Reducing this
search friction on visit 2 can compress the decision cycle.

### Hypothesis
**Hypothesis (to be tested):** Surfacing an instant "Order 1 Favorites" quick-cart
drawer upon session start for returning second-order shoppers will reduce cart-building
time, increase visit-to-checkout conversion, and shorten the gap between orders 1 and 2.

### Experiment Design

| Design Element | Specification |
|---|---|
| **Target Segment** | All returning users initiating a session after order 1 (prior to placing order 2), with emphasis on slow starters. |
| **Trigger** | User opens app or website after completing order 1. |
| **Treatment** | Prominent sticky bottom sheet / homepage drawer displaying all items from order 1 with a single *"Add All Recent Items"* button and individual one-tap plus buttons. |
| **Control** | Standard homepage interface (generic search bar and category tiles). |
| **Unit of Randomisation** | User account. |
| **Primary Metric** | Session-to-checkout conversion rate on visit 2 ($\%$). |
| **Secondary Metric** | Median time-to-checkout in minutes during visit 2 session. |
| **Guardrail Metrics** | (1) Total department diversity in order 2 (shelf must not narrow exploration to only repeat items); (2) Total basket item count. |
| **Assumed Baseline** | Baseline session conversion on visit 2: $\approx 32\%$. Median session time: 14 minutes. |
| **Minimum Detectable Effect (MDE)** | $+2.5$ percentage points in visit-2 conversion (from $32\%$ to $34.5\%$) and $\ge 2$-minute reduction in session duration. |
| **Sample Size (Rough)** | $\approx 12,000$ users per arm ($\alpha = 0.05$, power $80\%$). |
| **Duration** | 4 weeks of concurrent live traffic. |
| **Stop Criteria** | Stop if department diversity in order 2 drops by $>15\%$ compared to control. |

---

## Methodological Guardrails for All Proposed Tests

- **Designs, Not Claims**: All expected lifts are minimum detectable effects (MDEs) used for power sizing, not claimed results.
- **Unit of Randomisation**: Randomisation is strictly at the **user level** to avoid intra-user contamination across multi-device sessions.
- **Fixed Horizon Analysis**: All conversion metrics specify predefined evaluation windows (e.g. 30 days) to prevent continuous monitoring bias.
- **Economic Guardrail**: Every test must evaluate customer lifetime contribution margin net of incentive and messaging costs.
