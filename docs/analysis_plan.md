# Analysis Plan: What Turns a Grocery Customer into a Regular?

> **Status:** Draft — awaiting approval before any outcome-vs-behaviour analysis.

---

## 1. Business Question

Among repeat grocery customers, which early behaviours (first 3 orders) are
associated with becoming a heavy, regular customer later, and which 2–3 nudges
would be worth A/B testing to increase repeat ordering?

---

## 2. Data Source

**Instacart Online Grocery Shopping Dataset** (Kaggle, "Instacart Market Basket
Analysis"). Six CSV files in `data/raw/`.

> [!IMPORTANT]
> Read the dataset's licence/terms on Kaggle before publishing anything derived
> from it. Raw data is gitignored and must never be committed.

### 2.1 Data Reality Check (computed, not hand-typed)

| Metric | Value |
|---|---|
| Total orders | 3,421,083 |
| Total users | 206,209 |
| Total products | 49,688 |
| Aisles | 134 |
| Departments | 21 |
| Min orders per user | 4 |
| Max orders per user | 100 |
| Mean orders per user | 16.6 |
| Median orders per user | 10 |

### 2.2 Column Verification

All expected columns confirmed:

- **orders.csv:** `order_id, user_id, eval_set, order_number, order_dow,
  order_hour_of_day, days_since_prior_order`
- **order_products__prior.csv / order_products__train.csv:**
  `order_id, product_id, add_to_cart_order, reordered`
- **products.csv:** `product_id, product_name, aisle_id, department_id`
- **aisles.csv:** `aisle_id, aisle`
- **departments.csv:** `department_id, department`

No duplicate `order_id`s. No duplicate `(order_id, product_id)` pairs.

### 2.3 eval_set Structure

Each user has:
- **Multiple "prior" orders** (all orders except the last): full product data
  available in `order_products__prior.csv`.
- **One "train" or "test" order** (the user's last order):
  - train (131,209 users): product data available in
    `order_products__train.csv`.
  - test (75,000 users): **no product data** (Kaggle holdout).

**Decision:** We use **prior** orders for all features and outcomes because they
form the full sequence. The train order can be included in the outcome count
(total orders) for train-set users, adding one extra order to their count.
Test-set users' last order has no product data, so we still count it toward
total orders but cannot use it for basket-level features. Since our features
come only from orders 1–3 (all prior), this is clean.

### 2.4 days_since_prior_order

- **Null for first orders** (confirmed: 206,209 nulls = 206,209 first orders).
- **Apparently capped at 30 days**: 369,323 orders show exactly 30 days, vs
  19,191 at 29 days (a 19.2× spike). Any gap longer than 30 days is recorded
  as 30.
- **Impact:** Cadence metrics (median gap) are **right-censored** at 30 days.
  Users who truly waited 45 or 60 days look like 30-day users. This
  compresses the slow end of the gap distribution and biases median gap
  downward for infrequent users. We document this as a limitation and note
  that "fast cadence" thresholds below 30 are unaffected.

### 2.5 No Calendar Dates

Time is represented only as an order sequence (`order_number`) with relative
gaps (`days_since_prior_order`). There are no absolute dates. We cannot control
for seasonality, promotions, or calendar effects.

### 2.6 Survivorship Bias (Critical Limitation)

**Every user in this dataset has at least 4 orders.** Customers who tried
Instacart once and never returned are **not** represented. This means:

- We **cannot** study what makes a first-time buyer come back.
- "Reaching order N" for small N (N ≤ 4) cannot be used as a retention
  outcome because every user already reached it.
- All findings describe **differences among already-retained customers**, not
  the full funnel from acquisition to retention.
- Associations we find may not generalise to the dropped-off population.

This is stated upfront in every output document.

---

## 3. Observation Window & Leakage Prevention

```
Orders 1  2  3 │ 4  5  6  7  ...  N
───────────────┼──────────────────────
  FEATURES     │  OUTCOMES
(input only)   │ (measured here)
```

- **Features** are computed from orders 1–3 only (the "observation window").
- **Outcomes** are computed from orders 4 onward only.
- This strict temporal split prevents data leakage: we never use future
  behaviour to predict future behaviour.
- A leakage test will verify no feature incorporates data from order 4+.

---

## 4. Outcome Definitions

### 4.1 Primary: Heavy User (binary)

A user is "heavy" if their **total number of orders ≥ the 75th percentile**
of the distribution.

- From the reality check: p75 = 20 orders.
- So "heavy" ≈ users with 20+ orders (top 25%).
- Threshold is set in `config.yaml` as a percentile so it adapts if the data
  changes.

**Justification:** The top quartile represents a natural break in a
right-skewed distribution. These are the users who ordered ≥ 20 times — well
above the median of 10. This is a meaningful "regular customer" bar.

### 4.2 Secondary: Fast Cadence (binary)

A user has "fast cadence" if their **median days_since_prior_order over orders
4+** is ≤ 7 days (weekly or faster).

- Threshold set in `config.yaml`.
- Affected by the 30-day cap (see §2.4), but the 7-day threshold is well
  below the cap so it is unaffected.

### 4.3 Sensitivity Checks

We re-run the main analysis with alternative heavy-user thresholds:
- **Top 30%** (p70 = 17 orders)
- **Top 20%** (p80 = 24 orders)

If the same features rank similarly across thresholds, findings are robust.

---

## 5. Feature List (from Orders 1–3 Only)

| # | Feature | Source | Description |
|---|---------|--------|-------------|
| 1 | `first_order_size` | order 1 basket | Number of items in the first order |
| 2 | `avg_basket_size_1_3` | orders 1–3 | Mean items per order across first 3 orders |
| 3 | `reorder_rate_2_3` | orders 2–3 | Share of items in orders 2–3 that are reorders |
| 4 | `days_to_second_order` | orders 1→2 gap | days_since_prior_order for order 2 |
| 5 | `days_to_third_order` | orders 2→3 gap | days_since_prior_order for order 3 |
| 6 | `weekend_share_1_3` | orders 1–3 | Share of orders 1–3 placed on a weekend day |
| 7 | `morning_share_1_3` | orders 1–3 | Share of orders 1–3 placed in morning hours |
| 8 | `evening_share_1_3` | orders 1–3 | Share of orders 1–3 placed in evening hours |
| 9 | `pct_produce_order1` | order 1 basket | % of first-order items from Produce dept |
| 10 | `pct_dairy_order1` | order 1 basket | % of first-order items from Dairy Eggs dept |
| 11 | `pct_snacks_order1` | order 1 basket | % of first-order items from Snacks dept |
| 12 | `n_departments_order1` | order 1 basket | Number of distinct departments in first order |
| 13 | `n_aisles_order1` | order 1 basket | Number of distinct aisles in first order |

**Notes:**
- Features 4 and 5 are affected by the 30-day cap. We document this but keep
  them because the cap affects both heavy and non-heavy users.
- Features 6–8 use day-of-week values 0–6 from `order_dow`. We assume 0 = Saturday,
  1 = Sunday based on known Instacart shopping patterns, but this is unconfirmed
  and documented as an assumption.

---

## 6. Methods

### 6.1 Descriptive Comparison

For each feature, compare the distribution between heavy and non-heavy users:
- Means or proportions with **bootstrap 95% confidence intervals** (10,000
  iterations, fixed seed).
- Cohen's d effect sizes for continuous features.
- Visualised as a forest-style chart showing differences with CIs.

### 6.2 Logistic Regression

An interpretable logistic regression with:
- **Standardised features** (z-scored) so coefficients are comparable.
- **Odds ratios with 95% CIs** from the model.
- **Multicollinearity check** via Variance Inflation Factors (VIF); if any
  VIF > 5, we document and consider dropping or combining features.
- **Discrimination:** AUC on the same data (not for prediction — just to
  gauge how much early behaviour explains).
- **Calibration:** Hosmer-Lemeshow or calibration plot.

This is presented as "which signals matter when considered together," **not**
as a prediction product.

### 6.3 Reorder-Rate Evolution

Population-level reorder rate (share of items that are reorders) across orders
1–10. This shows how reordering behaviour changes with order sequence, but we
label clearly that it is a cross-sectional pattern across users, not a
within-user causal trajectory (because later orders over-represent heavier
users due to survivorship).

### 6.4 Sensitivity Checks

Re-run the logistic regression with the alternative heavy-user thresholds
(top 20%, top 30%) and report whether the top features and their direction
remain stable.

---

## 7. Lifecycle Segments

For nudge targeting, we segment users by engagement level:

| Segment | Rule |
|---------|------|
| **New** | Total orders ≤ 5 |
| **Regular** | Total orders ≥ 6 AND median gap ≤ 14 days |
| **Slowing** | Total orders ≥ 6 AND median gap > 14 days |

Thresholds are set in `config.yaml`. We report segment sizes and key trait
differences.

---

## 8. Metrics Tree

```
North Star: Repeat orders per user
├── Input: Reorder rate (share of reordered items)
├── Input: Basket size (items per order)
├── Input: Days between orders (cadence)
├── Guardrail: Basket size not shrinking
│   (nudges should not drive tiny top-up orders)
└── Guardrail: Order frequency quality
    (frequency not inflated by split baskets)
```

A full diagram is in `docs/metrics_tree.md`.

---

## 9. Limitations (stated upfront in all outputs)

1. **Survivorship bias:** Only users with 4+ orders are in the data. We
   cannot study what makes a first-time buyer return. All findings are among
   already-retained customers.
2. **No calendar dates:** Only order sequence and relative gaps. No
   seasonality or promotion controls.
3. **No prices or revenue:** Basket size is item count, not dollar value. We
   cannot assess revenue impact.
4. **No user demographics:** No age, location, device, or acquisition
   channel.
5. **Descriptive only:** All associations are observational. We cannot say
   that any behaviour *causes* higher retention.
6. **days_since_prior_order capped at 30:** Long gaps are censored, biasing
   cadence metrics downward for infrequent users.
7. **Single retailer, single period:** Findings may not generalise to other
   grocers or time periods.
8. **Weekend day labels unconfirmed:** We assume 0 = Saturday, 1 = Sunday but
   this is not documented by Instacart.

---

## 10. Deliverables Checklist

- [ ] SQL feature pipeline (`sql/`)
- [ ] Data tests (leakage, duplicates, counts)
- [ ] User-level parquet export
- [ ] Outcome distribution charts
- [ ] Heavy vs non-heavy comparison with CIs
- [ ] Logistic regression with odds ratios
- [ ] Sensitivity checks
- [ ] Lifecycle segments
- [ ] Reorder-rate evolution chart
- [ ] Nudge proposals (`docs/nudges.md`)
- [ ] Metrics tree (`docs/metrics_tree.md`)
- [ ] Executive memo (`docs/memo.md`)
- [ ] README with finding
- [ ] Analysis notebook
- [ ] Interview notes
- [ ] CV bullet

---

## 11. Tool Choices

| Tool | Purpose |
|------|---------|
| **DuckDB** | In-process SQL engine for aggregating the 32M-row order_products file without loading it into pandas. No Docker needed. |
| **pandas** | User-level analysis (~206K rows) after SQL aggregation |
| **statsmodels** | Logistic regression, VIF |
| **scipy** | Bootstrap CIs |
| **matplotlib** | Charts |
| **pytest** | Data and leakage tests |

> **Note on PostgreSQL vs DuckDB:** The task spec mentions PostgreSQL via
> Docker. DuckDB achieves the same SQL-first aggregation pattern without
> Docker overhead and is simpler to reproduce (`pip install duckdb`). If
> PostgreSQL is preferred, say so and I will add `docker-compose.yml`. The SQL
> will be nearly identical either way.
