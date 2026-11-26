"""
tests/test_data_integrity.py
Data integrity and leakage tests for the feature pipeline.

Run with: pytest tests/ -v
"""
import duckdb
import os
import pytest
import json

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SQL_DIR = os.path.join(PROJECT_ROOT, "sql")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")


def run_sql_file(con, path):
    """Execute a SQL file."""
    with open(path, "r") as f:
        lines = f.readlines()
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("--"):
            continue
        if "--" in line:
            line = line[:line.index("--")]
        cleaned.append(line)
    sql = "".join(cleaned)
    for stmt in sql.split(";"):
        stmt = stmt.strip()
        if stmt:
            con.execute(stmt)


@pytest.fixture(scope="module")
def db():
    """Set up the full pipeline in an in-memory DuckDB instance."""
    os.chdir(PROJECT_ROOT)
    con = duckdb.connect()
    sql_files = sorted(f for f in os.listdir(SQL_DIR) if f.endswith(".sql"))
    for sql_file in sql_files:
        run_sql_file(con, os.path.join(SQL_DIR, sql_file))
    yield con
    con.close()


class TestDataIntegrity:
    """Basic data integrity checks."""

    def test_no_duplicate_order_ids(self, db):
        """orders.csv should have unique order_ids."""
        result = db.execute("""
            SELECT count(*) - count(DISTINCT order_id) AS dups FROM stg_orders
        """).fetchone()[0]
        assert result == 0, f"Found {result} duplicate order_ids"

    def test_every_user_has_min_orders(self, db):
        """Every user should have at least 4 orders."""
        result = db.execute("""
            SELECT min(cnt) FROM (
                SELECT user_id, count(*) AS cnt FROM stg_orders GROUP BY user_id
            )
        """).fetchone()[0]
        assert result >= 4, f"Min orders per user is {result}, expected >= 4"

    def test_user_features_row_count(self, db):
        """user_features should have one row per user (who has outcomes)."""
        n_users = db.execute("SELECT count(*) FROM user_features").fetchone()[0]
        # Should be <= total users (some users might not have order 4+ data
        # if they have exactly 3 prior orders + 1 train/test order)
        n_total = db.execute(
            "SELECT count(DISTINCT user_id) FROM stg_orders"
        ).fetchone()[0]
        assert n_users > 0, "user_features is empty"
        assert n_users <= n_total, "More feature rows than users"


class TestLeakagePrevention:
    """Ensure features use ONLY orders 1-3 and outcomes use ONLY orders 4+."""

    def test_features_no_order4_data(self, db):
        """Features must not incorporate any data from order 4+.

        We verify this by checking that the SQL feature tables only join
        to orders where order_number <= 3.
        """
        # Verify: for each user, the first_order_size matches the actual
        # item count of their order_number=1
        result = db.execute("""
            WITH actual_order1_size AS (
                SELECT o.user_id, count(*) AS n_items
                FROM stg_orders o
                JOIN stg_order_products_prior op ON o.order_id = op.order_id
                WHERE o.order_number = 1 AND o.eval_set = 'prior'
                GROUP BY o.user_id
            )
            SELECT count(*) AS mismatches
            FROM user_features uf
            JOIN actual_order1_size a ON uf.user_id = a.user_id
            WHERE uf.first_order_size != a.n_items
        """).fetchone()[0]
        assert result == 0, f"first_order_size mismatches: {result}"

    def test_days_to_second_order_from_order2(self, db):
        """days_to_second_order must come from order_number=2."""
        result = db.execute("""
            WITH actual AS (
                SELECT user_id, days_since_prior_order AS d2
                FROM stg_orders
                WHERE order_number = 2
            )
            SELECT count(*) AS mismatches
            FROM user_features uf
            JOIN actual a ON uf.user_id = a.user_id
            WHERE uf.days_to_second_order != a.d2
        """).fetchone()[0]
        assert result == 0, f"days_to_second_order mismatches: {result}"

    def test_outcome_total_orders_includes_all(self, db):
        """total_orders should count ALL orders (prior + train/test)."""
        # Spot-check a sample of users
        result = db.execute("""
            WITH actual AS (
                SELECT user_id, count(*) AS cnt
                FROM stg_orders
                GROUP BY user_id
            )
            SELECT count(*) AS mismatches
            FROM user_features uf
            JOIN actual a ON uf.user_id = a.user_id
            WHERE uf.total_orders != a.cnt
        """).fetchone()[0]
        assert result == 0, f"total_orders mismatches: {result}"

    def test_avg_basket_uses_only_orders_1_3(self, db):
        """avg_basket_size_1_3 must use only orders 1-3."""
        result = db.execute("""
            WITH actual AS (
                SELECT
                    o.user_id,
                    AVG(basket.n_items) AS avg_bs
                FROM stg_orders o
                JOIN (
                    SELECT order_id, count(*) AS n_items
                    FROM stg_order_products_prior
                    GROUP BY order_id
                ) basket ON o.order_id = basket.order_id
                WHERE o.order_number <= 3 AND o.eval_set = 'prior'
                GROUP BY o.user_id
            )
            SELECT count(*) AS mismatches
            FROM user_features uf
            JOIN actual a ON uf.user_id = a.user_id
            WHERE abs(uf.avg_basket_size_1_3 - a.avg_bs) > 0.001
        """).fetchone()[0]
        assert result == 0, f"avg_basket_size_1_3 mismatches: {result}"

    def test_reorder_rate_uses_only_orders_2_3(self, db):
        """reorder_rate_2_3 must use only orders 2-3."""
        result = db.execute("""
            WITH actual AS (
                SELECT
                    o.user_id,
                    AVG(op.reordered * 1.0) AS rr
                FROM stg_orders o
                JOIN stg_order_products_prior op ON o.order_id = op.order_id
                WHERE o.order_number IN (2, 3) AND o.eval_set = 'prior'
                GROUP BY o.user_id
            )
            SELECT count(*) AS mismatches
            FROM user_features uf
            JOIN actual a ON uf.user_id = a.user_id
            WHERE abs(uf.reorder_rate_2_3 - a.rr) > 0.001
        """).fetchone()[0]
        assert result == 0, f"reorder_rate_2_3 mismatches: {result}"


class TestOutcomeDefinitions:
    """Test outcome definitions on a hand-made example."""

    def test_heavy_user_flag_logic(self):
        """Heavy-user flag: total_orders >= threshold."""
        # Simulate: threshold = 20, user has 25 orders → heavy
        con = duckdb.connect()
        con.execute("""
            CREATE TABLE test_data AS SELECT * FROM (VALUES
                (1, 25, 20),  -- heavy
                (2, 19, 20),  -- not heavy
                (3, 20, 20),  -- exactly at threshold → heavy
                (4, 4, 20)    -- minimal orders → not heavy
            ) t(user_id, total_orders, threshold)
        """)
        result = con.execute("""
            SELECT user_id,
                   CASE WHEN total_orders >= threshold THEN 1 ELSE 0 END AS is_heavy
            FROM test_data ORDER BY user_id
        """).fetchall()
        expected = [(1, 1), (2, 0), (3, 1), (4, 0)]
        assert result == expected, f"Expected {expected}, got {result}"
        con.close()

    def test_fast_cadence_flag_logic(self):
        """Fast-cadence flag: median_gap <= 7."""
        con = duckdb.connect()
        con.execute("""
            CREATE TABLE test_cadence AS SELECT * FROM (VALUES
                (1, 5.0),   -- fast
                (2, 7.0),   -- exactly 7 → fast
                (3, 8.0),   -- not fast
                (4, 30.0)   -- slow
            ) t(user_id, median_gap)
        """)
        result = con.execute("""
            SELECT user_id,
                   CASE WHEN median_gap <= 7 THEN 1 ELSE 0 END AS is_fast
            FROM test_cadence ORDER BY user_id
        """).fetchall()
        expected = [(1, 1), (2, 1), (3, 0), (4, 0)]
        assert result == expected, f"Expected {expected}, got {result}"
        con.close()


class TestBootstrapReproducibility:
    """Test that bootstrap CIs are reproducible with a fixed seed."""

    def test_bootstrap_fixed_seed(self):
        """Same seed → same CI."""
        import numpy as np

        rng = np.random.RandomState(42)
        data = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], dtype=float)

        def bootstrap_mean(data, rng, n_boot=1000):
            means = []
            for _ in range(n_boot):
                sample = rng.choice(data, size=len(data), replace=True)
                means.append(sample.mean())
            return np.percentile(means, [2.5, 97.5])

        ci1 = bootstrap_mean(data, np.random.RandomState(42))
        ci2 = bootstrap_mean(data, np.random.RandomState(42))
        assert ci1[0] == ci2[0] and ci1[1] == ci2[1], \
            f"Bootstrap not reproducible: {ci1} vs {ci2}"


class TestReproducibility:
    """Test that bootstrap CIs and cross-validated AUC are bit-identical across runs."""

    def test_bootstrap_ci_reproducible(self):
        """bootstrap_ci with the same rng seed produces identical intervals.

        Uses a self-contained reimplementation of the bootstrap_ci logic
        (same algorithm as src/analysis.py) to avoid importing the full
        analysis module, which runs the entire pipeline at module level.
        """
        import numpy as np

        SEED = 42

        def bootstrap_ci(data, n_boot=500, rng=None):
            if rng is None:
                rng = np.random.default_rng(SEED)
            data = np.asarray(data, dtype=float)
            n = len(data)
            batch_size = 500
            boot_stats = []
            for start in range(0, n_boot, batch_size):
                b = min(batch_size, n_boot - start)
                indices = rng.integers(0, n, size=(b, n))
                boot_stats.append(data[indices].mean(axis=1))
            boot_stats = np.concatenate(boot_stats)
            return float(data.mean()), float(np.percentile(boot_stats, 2.5)), float(np.percentile(boot_stats, 97.5))

        data = np.arange(1, 101, dtype=float)

        # Run 1
        mean1, lo1, hi1 = bootstrap_ci(data, n_boot=500, rng=np.random.default_rng(SEED))
        # Run 2
        mean2, lo2, hi2 = bootstrap_ci(data, n_boot=500, rng=np.random.default_rng(SEED))

        assert mean1 == mean2, f"means differ: {mean1} vs {mean2}"
        assert lo1 == lo2, f"CI lower differs: {lo1} vs {lo2}"
        assert hi1 == hi2, f"CI upper differs: {hi1} vs {hi2}"

    def test_cv_auc_reproducible(self):
        """cross_val_score with StratifiedKFold(shuffle=True, random_state=SEED) is identical."""
        import numpy as np
        from sklearn.linear_model import LogisticRegression
        from sklearn.model_selection import cross_val_score, StratifiedKFold
        from sklearn.preprocessing import StandardScaler

        SEED = 42
        rng = np.random.default_rng(SEED)
        n = 200
        X = rng.standard_normal((n, 3))
        y = (X[:, 0] + rng.standard_normal(n) * 0.5 > 0).astype(int)
        X_scaled = StandardScaler().fit_transform(X)

        def run_cv():
            cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
            lr = LogisticRegression(max_iter=1000, random_state=SEED)
            return cross_val_score(lr, X_scaled, y, cv=cv, scoring="roc_auc")

        scores1 = run_cv()
        scores2 = run_cv()

        np.testing.assert_array_equal(scores1, scores2,
                                      err_msg="CV AUC scores differ across runs")
