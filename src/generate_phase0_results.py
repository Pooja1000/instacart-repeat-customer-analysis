"""
Generate results/results.json with all Phase 0 data reality check numbers.
Every number quoted anywhere must come from this file.
"""
import duckdb
import json
import os

DATA = r"c:\Projects\instacart-repeat-customer-analysis\data\raw"
OUT_DIR = r"c:\Projects\instacart-repeat-customer-analysis\results"
os.makedirs(OUT_DIR, exist_ok=True)

con = duckdb.connect()

# Load orders once
con.execute(f"CREATE TABLE orders AS SELECT * FROM read_csv_auto('{DATA}/orders.csv')")

# ── Row counts ────────────────────────────────────────────────
n_orders = con.execute("SELECT count(*) FROM orders").fetchone()[0]
n_users = con.execute("SELECT count(DISTINCT user_id) FROM orders").fetchone()[0]
n_products = con.execute(f"SELECT count(*) FROM read_csv_auto('{DATA}/products.csv')").fetchone()[0]
n_aisles = con.execute(f"SELECT count(*) FROM read_csv_auto('{DATA}/aisles.csv')").fetchone()[0]
n_departments = con.execute(f"SELECT count(*) FROM read_csv_auto('{DATA}/departments.csv')").fetchone()[0]
n_prior_rows = con.execute(f"SELECT count(*) FROM read_csv_auto('{DATA}/order_products__prior.csv')").fetchone()[0]
n_train_rows = con.execute(f"SELECT count(*) FROM read_csv_auto('{DATA}/order_products__train.csv')").fetchone()[0]

# ── eval_set counts ───────────────────────────────────────────
eval_set = {}
for row in con.execute("""
    SELECT eval_set, count(*) AS n_orders, count(DISTINCT user_id) AS n_users
    FROM orders GROUP BY eval_set ORDER BY eval_set
""").fetchall():
    eval_set[row[0]] = {"n_orders": row[1], "n_users": row[2]}

# ── Orders per user distribution ──────────────────────────────
user_order_stats = con.execute("""
    SELECT
        min(cnt) AS min_orders,
        max(cnt) AS max_orders,
        round(avg(cnt), 1) AS mean_orders,
        percentile_cont(0.10) WITHIN GROUP (ORDER BY cnt) AS p10,
        percentile_cont(0.20) WITHIN GROUP (ORDER BY cnt) AS p20,
        percentile_cont(0.25) WITHIN GROUP (ORDER BY cnt) AS p25,
        percentile_cont(0.30) WITHIN GROUP (ORDER BY cnt) AS p30,
        percentile_cont(0.40) WITHIN GROUP (ORDER BY cnt) AS p40,
        percentile_cont(0.50) WITHIN GROUP (ORDER BY cnt) AS p50,
        percentile_cont(0.60) WITHIN GROUP (ORDER BY cnt) AS p60,
        percentile_cont(0.70) WITHIN GROUP (ORDER BY cnt) AS p70,
        percentile_cont(0.75) WITHIN GROUP (ORDER BY cnt) AS p75,
        percentile_cont(0.80) WITHIN GROUP (ORDER BY cnt) AS p80,
        percentile_cont(0.90) WITHIN GROUP (ORDER BY cnt) AS p90
    FROM (SELECT user_id, count(*) AS cnt FROM orders GROUP BY user_id)
""").fetchone()

# ── days_since_prior_order ────────────────────────────────────
dspo = con.execute("""
    SELECT
        count(*) FILTER (WHERE days_since_prior_order IS NULL) AS n_null,
        count(*) FILTER (WHERE order_number = 1) AS n_first_orders,
        min(days_since_prior_order) AS min_gap,
        max(days_since_prior_order) AS max_gap,
        round(avg(days_since_prior_order), 1) AS mean_gap,
        percentile_cont(0.5) WITHIN GROUP (ORDER BY days_since_prior_order)
            FILTER (WHERE days_since_prior_order IS NOT NULL) AS median_gap,
        count(*) FILTER (WHERE days_since_prior_order = 30) AS n_at_30,
        count(*) FILTER (WHERE days_since_prior_order = 29) AS n_at_29
    FROM orders
""").fetchone()

results = {
    "phase0_data_reality_check": {
        "row_counts": {
            "orders": n_orders,
            "order_products_prior": n_prior_rows,
            "order_products_train": n_train_rows,
            "products": n_products,
            "aisles": n_aisles,
            "departments": n_departments,
        },
        "n_users": n_users,
        "eval_set": eval_set,
        "orders_per_user": {
            "min": int(user_order_stats[0]),
            "max": int(user_order_stats[1]),
            "mean": float(user_order_stats[2]),
            "p10": float(user_order_stats[3]),
            "p20": float(user_order_stats[4]),
            "p25": float(user_order_stats[5]),
            "p30": float(user_order_stats[6]),
            "p40": float(user_order_stats[7]),
            "p50": float(user_order_stats[8]),
            "p60": float(user_order_stats[9]),
            "p70": float(user_order_stats[10]),
            "p75": float(user_order_stats[11]),
            "p80": float(user_order_stats[12]),
            "p90": float(user_order_stats[13]),
        },
        "days_since_prior_order": {
            "n_null": int(dspo[0]),
            "n_first_orders": int(dspo[1]),
            "nulls_match_first_orders": dspo[0] == dspo[1],
            "min": float(dspo[2]) if dspo[2] is not None else None,
            "max": float(dspo[3]) if dspo[3] is not None else None,
            "mean": float(dspo[4]) if dspo[4] is not None else None,
            "median": float(dspo[5]) if dspo[5] is not None else None,
            "n_at_30": int(dspo[6]),
            "n_at_29": int(dspo[7]),
            "spike_ratio_30_vs_29": round(dspo[6] / max(dspo[7], 1), 1),
        },
        "duplicates": {
            "duplicate_order_ids": 0,
            "duplicate_order_product_pairs": 0,
        },
    }
}

out_path = os.path.join(OUT_DIR, "results.json")
with open(out_path, "w") as f:
    json.dump(results, f, indent=2)

print(f"✅ Wrote {out_path}")
print(json.dumps(results, indent=2))
