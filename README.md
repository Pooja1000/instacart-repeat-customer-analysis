# Among 206,209 repeat Instacart customers, produce share (1st order) in the first 3 orders is the strongest early signal associated with becoming a heavy user (OR 1.14, 95% CI [1.12–1.15]).

## Business Question

Which early shopping behaviours (first 3 orders) are associated with becoming a
heavy, regular grocery customer, and which nudges would be worth A/B testing to
increase repeat ordering?

## Data Source

**Instacart Online Grocery Shopping Dataset** (Kaggle, "Instacart Market Basket
Analysis"): 3,421,083 orders from 206,209 users, 49,688
products across 134 aisles and 21
departments.

> ⚠️ Read the dataset's licence/terms on Kaggle before publishing anything
> derived from it.

## Method

- Features from orders 1–3 only; outcomes from orders 4+ only (strict temporal
  split to prevent leakage).
- "Heavy user" = top 25% by total orders (≥ 20 orders).
- Bootstrap 95% CIs (10,000 iterations) for group comparisons.
- Logistic regression with standardised features, two versions (with/without
  gap features), 0.568 cross-validated AUC.
- Sensitivity checks at top-20% and top-30% thresholds.
- Lifecycle segments defined from orders 1–3 only.

## Key Chart

![Odds ratios for heavy-user status](results/figures/odds_ratios_no_gap.png)

## How to Run

```bash
pip install -r requirements.txt
make run          # runs: tests → Phase 0 → SQL pipeline → analysis → docs
```

Alternatively, step by step:
```bash
python src/generate_phase0_results.py   # data reality check → results.json
python src/run_pipeline.py              # SQL pipeline → parquet
python src/analysis.py                  # analysis → charts + results.json
python src/generate_docs.py             # memo, README, CV bullet from results.json
```

## Limitations

1. **Survivorship bias** (stated first): Only users with ≥ 4 orders are in the
   data. Customers who never returned are not represented.
2. No calendar dates — only order sequence and relative gaps.
3. No prices or revenue — basket size is item count, not dollar value.
4. No user demographics (age, location, device, acquisition channel).
5. **Descriptive only** — all associations are observational, not causal.
6. `days_since_prior_order` capped at 30 — long gaps are right-censored.
7. Single retailer, single time period.

## Project Structure

```
├── config.yaml              # All tuneable parameters
├── data/raw/                 # Raw CSVs (gitignored)
├── data/processed/           # Parquet exports (gitignored)
├── sql/                      # DuckDB SQL pipeline (staging → features → outcomes)
├── src/
│   ├── generate_phase0_results.py
│   ├── run_pipeline.py
│   ├── analysis.py
│   └── generate_docs.py
├── tests/                    # pytest: leakage, integrity, outcome definitions
├── results/
│   ├── results.json          # All computed numbers
│   └── figures/              # All charts
├── docs/
│   ├── analysis_plan.md
│   ├── memo.md
│   ├── nudges.md
│   ├── metrics_tree.md
│   ├── cv_bullet.md
│   └── INTERVIEW_NOTES.md
├── notebooks/analysis.ipynb
├── Makefile
└── requirements.txt
```
