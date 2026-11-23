"""
run_pipeline.py
Executes the full SQL pipeline in DuckDB (in-process) and exports
the user_features table to parquet. Also exports the reorder_curve.

Usage: python src/run_pipeline.py
"""
import duckdb
import json
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SQL_DIR = os.path.join(PROJECT_ROOT, "sql")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")

os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)


def run_sql_file(con, path):
    """Execute a SQL file, splitting on semicolons.

    Strips single-line comments (-- ...) before splitting so that
    comments containing semicolons don't break the parser.
    """
    with open(path, "r") as f:
        lines = f.readlines()
    # Remove full-line comments; keep inline SQL
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("--"):
            continue
        # Remove trailing inline comments
        if "--" in line:
            line = line[:line.index("--")]
        cleaned.append(line)
    sql = "".join(cleaned)
    for stmt in sql.split(";"):
        stmt = stmt.strip()
        if stmt:
            con.execute(stmt)


def main():
    # Use in-memory DuckDB; set working directory so relative paths in SQL work
    os.chdir(PROJECT_ROOT)
    con = duckdb.connect()

    # Run SQL scripts in order
    sql_files = sorted(f for f in os.listdir(SQL_DIR) if f.endswith(".sql"))
    for sql_file in sql_files:
        path = os.path.join(SQL_DIR, sql_file)
        print(f"  Running {sql_file}...")
        run_sql_file(con, path)
        print(f"    ✓ {sql_file} done")

    # ── Verification queries ──────────────────────────────────
    n_users = con.execute("SELECT count(*) FROM user_features").fetchone()[0]
    print(f"\n  user_features rows: {n_users:,}")

    # Sample check
    sample = con.execute("""
        SELECT user_id, first_order_size, total_orders, is_heavy_p75,
               lifecycle_segment, heavy_threshold_p75,
               segment_basket_median, segment_gap_median
        FROM user_features LIMIT 5
    """).fetchall()
    print("  Sample rows:")
    for row in sample:
        print(f"    {row}")

    # Threshold info
    thresholds = con.execute("""
        SELECT
            heavy_threshold_p75, heavy_threshold_p70, heavy_threshold_p80,
            segment_basket_median, segment_gap_median
        FROM user_features LIMIT 1
    """).fetchone()
    print(f"\n  Heavy threshold p75: {thresholds[0]}")
    print(f"  Heavy threshold p70: {thresholds[1]}")
    print(f"  Heavy threshold p80: {thresholds[2]}")
    print(f"  Segment basket median: {thresholds[3]}")
    print(f"  Segment gap median: {thresholds[4]}")

    # Outcome counts
    heavy_counts = con.execute("""
        SELECT is_heavy_p75, count(*) FROM user_features GROUP BY is_heavy_p75
    """).fetchall()
    print(f"\n  Heavy user distribution (p75):")
    for row in heavy_counts:
        print(f"    is_heavy={row[0]}: {row[1]:,}")

    cadence_counts = con.execute("""
        SELECT is_fast_cadence, count(*) FROM user_features GROUP BY is_fast_cadence
    """).fetchall()
    print(f"  Fast cadence distribution:")
    for row in cadence_counts:
        print(f"    is_fast_cadence={row[0]}: {row[1]:,}")

    # Overlap between heavy and fast cadence
    overlap = con.execute("""
        SELECT
            SUM(CASE WHEN is_heavy_p75 = 1 AND is_fast_cadence = 1 THEN 1 ELSE 0 END) AS both,
            SUM(CASE WHEN is_heavy_p75 = 1 AND is_fast_cadence = 0 THEN 1 ELSE 0 END) AS heavy_only,
            SUM(CASE WHEN is_heavy_p75 = 0 AND is_fast_cadence = 1 THEN 1 ELSE 0 END) AS fast_only,
            SUM(CASE WHEN is_heavy_p75 = 0 AND is_fast_cadence = 0 THEN 1 ELSE 0 END) AS neither,
            COUNT(*) AS total
        FROM user_features
    """).fetchone()
    print(f"\n  Heavy × Fast-cadence overlap:")
    print(f"    Both:        {overlap[0]:,}")
    print(f"    Heavy only:  {overlap[1]:,}")
    print(f"    Fast only:   {overlap[2]:,}")
    print(f"    Neither:     {overlap[3]:,}")

    # Lifecycle segment sizes
    segments = con.execute("""
        SELECT lifecycle_segment, count(*) AS n,
               round(avg(total_orders), 1) AS avg_orders,
               round(avg(median_gap_orders_4plus), 1) AS avg_gap,
               round(avg(is_heavy_p75) * 100, 1) AS pct_heavy
        FROM user_features
        GROUP BY lifecycle_segment
        ORDER BY lifecycle_segment
    """).fetchall()
    print(f"\n  Lifecycle segments (later outcomes):")
    for row in segments:
        print(f"    {row[0]}: n={row[1]:,}, avg_orders={row[2]}, avg_gap={row[3]}, pct_heavy={row[4]}%")

    # Reorder curve
    reorder = con.execute("SELECT * FROM reorder_curve ORDER BY order_number").fetchall()
    print(f"\n  Reorder curve (constant cohort, users with 10+ orders):")
    for row in reorder:
        print(f"    order {row[0]}: reorder_rate={row[3]:.3f}, n_users={row[4]:,}")

    # ── Export to parquet ─────────────────────────────────────
    parquet_path = os.path.join(PROCESSED_DIR, "user_features.parquet")
    con.execute(f"COPY user_features TO '{parquet_path}' (FORMAT PARQUET)")
    print(f"\n  ✓ Exported user_features to {parquet_path}")

    reorder_parquet = os.path.join(PROCESSED_DIR, "reorder_curve.parquet")
    con.execute(f"COPY reorder_curve TO '{reorder_parquet}' (FORMAT PARQUET)")
    print(f"  ✓ Exported reorder_curve to {reorder_parquet}")

    # ── Update results.json with Phase 1 numbers ─────────────
    results_path = os.path.join(RESULTS_DIR, "results.json")
    if os.path.exists(results_path):
        with open(results_path) as f:
            results = json.load(f)
    else:
        results = {}

    null_check = con.execute("""
        SELECT
            count(*) FILTER (WHERE first_order_size IS NULL) AS null_fos,
            count(*) FILTER (WHERE avg_basket_size_1_3 IS NULL) AS null_abs,
            count(*) FILTER (WHERE reorder_rate_2_3 IS NULL) AS null_rr,
            count(*) FILTER (WHERE days_to_second_order IS NULL) AS null_d2,
            count(*) FILTER (WHERE days_to_third_order IS NULL) AS null_d3,
            count(*) FILTER (WHERE lifecycle_segment IS NULL) AS null_seg
        FROM user_features
    """).fetchone()

    results["phase1_pipeline"] = {
        "n_users_in_features": n_users,
        "thresholds": {
            "heavy_p75": float(thresholds[0]),
            "heavy_p70": float(thresholds[1]),
            "heavy_p80": float(thresholds[2]),
            "segment_basket_median": float(thresholds[3]),
            "segment_gap_median": float(thresholds[4]),
        },
        "heavy_user_counts_p75": {
            str(row[0]): row[1] for row in heavy_counts
        },
        "fast_cadence_counts": {
            str(row[0]): row[1] for row in cadence_counts
        },
        "heavy_fast_overlap": {
            "both": int(overlap[0]),
            "heavy_only": int(overlap[1]),
            "fast_only": int(overlap[2]),
            "neither": int(overlap[3]),
            "total": int(overlap[4]),
        },
        "lifecycle_segments": {
            row[0]: {
                "n_users": row[1],
                "avg_total_orders": float(row[2]),
                "avg_median_gap": float(row[3]),
                "pct_heavy": float(row[4]),
            } for row in segments
        },
        "reorder_curve": {
            str(row[0]): {
                "reorder_rate": round(float(row[3]), 4),
                "n_users": int(row[4]),
            } for row in reorder
        },
        "null_counts": {
            "first_order_size": int(null_check[0]),
            "avg_basket_size_1_3": int(null_check[1]),
            "reorder_rate_2_3": int(null_check[2]),
            "days_to_second_order": int(null_check[3]),
            "days_to_third_order": int(null_check[4]),
            "lifecycle_segment": int(null_check[5]),
        },
    }

    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"  ✓ Updated {results_path}")

    print("\n✅ Pipeline complete.")
    con.close()


if __name__ == "__main__":
    main()
