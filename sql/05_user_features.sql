-- =============================================================
-- 05_user_features.sql
-- Final user-level table joining features and outcomes.
-- Heavy-user and fast-cadence flags are computed here.
-- =============================================================

-- Compute the heavy-user threshold (p75 of total orders)
CREATE OR REPLACE TABLE tmp_thresholds AS
SELECT
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY total_orders) AS heavy_threshold_p75,
    PERCENTILE_CONT(0.70) WITHIN GROUP (ORDER BY total_orders) AS heavy_threshold_p70,
    PERCENTILE_CONT(0.80) WITHIN GROUP (ORDER BY total_orders) AS heavy_threshold_p80
FROM tmp_outcomes;

-- Compute lifecycle segment splits (medians of first_order_size and mean_early_gap)
CREATE OR REPLACE TABLE tmp_segment_splits AS
SELECT
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY bf.first_order_size) AS basket_median,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY of2.mean_early_gap)  AS gap_median
FROM tmp_basket_features bf
JOIN tmp_order_features of2 ON bf.user_id = of2.user_id;

-- Final user_features table
CREATE OR REPLACE TABLE user_features AS
SELECT
    -- User ID
    bf.user_id,

    -- ── FEATURES (orders 1-3 only) ──────────────────────────
    bf.first_order_size,
    bf.avg_basket_size_1_3,
    bf.reorder_rate_2_3,
    of2.days_to_second_order,
    of2.days_to_third_order,
    of2.mean_early_gap,
    of2.busiest_days_share_1_3,
    of2.morning_share_1_3,
    of2.evening_share_1_3,
    bf.pct_produce_order1,
    bf.pct_dairy_order1,
    bf.pct_snacks_order1,
    bf.n_departments_order1,
    bf.n_aisles_order1,

    -- ── OUTCOMES (orders 4+ only) ───────────────────────────
    oc.total_orders,
    oc.median_gap_orders_4plus,

    -- Heavy user flags (primary + sensitivity)
    CASE WHEN oc.total_orders >= t.heavy_threshold_p75 THEN 1 ELSE 0 END
        AS is_heavy_p75,
    CASE WHEN oc.total_orders >= t.heavy_threshold_p70 THEN 1 ELSE 0 END
        AS is_heavy_p70,
    CASE WHEN oc.total_orders >= t.heavy_threshold_p80 THEN 1 ELSE 0 END
        AS is_heavy_p80,

    -- Fast cadence flag (secondary outcome)
    CASE WHEN oc.median_gap_orders_4plus <= 7 THEN 1 ELSE 0 END
        AS is_fast_cadence,

    -- ── LIFECYCLE SEGMENTS (orders 1-3 data only) ───────────
    CASE
        WHEN bf.first_order_size <  s.basket_median AND of2.mean_early_gap >  s.gap_median
            THEN 'small-and-slow'
        WHEN bf.first_order_size <  s.basket_median AND of2.mean_early_gap <= s.gap_median
            THEN 'small-and-fast'
        WHEN bf.first_order_size >= s.basket_median AND of2.mean_early_gap >  s.gap_median
            THEN 'big-and-slow'
        WHEN bf.first_order_size >= s.basket_median AND of2.mean_early_gap <= s.gap_median
            THEN 'big-and-fast'
    END AS lifecycle_segment,

    -- Store thresholds for reference
    t.heavy_threshold_p75,
    t.heavy_threshold_p70,
    t.heavy_threshold_p80,
    s.basket_median  AS segment_basket_median,
    s.gap_median     AS segment_gap_median

FROM tmp_basket_features bf
JOIN tmp_order_features of2 ON bf.user_id = of2.user_id
JOIN tmp_outcomes oc         ON bf.user_id = oc.user_id
CROSS JOIN tmp_thresholds t
CROSS JOIN tmp_segment_splits s;
