-- =============================================================
-- 04_outcomes.sql
-- Compute per-user outcomes using ONLY orders 4+.
-- =============================================================

CREATE OR REPLACE TABLE tmp_outcomes AS
SELECT
    o.user_id,

    -- Total orders (all eval_sets — includes the train/test last order)
    total.total_orders,

    -- Median days_since_prior_order for orders 4+ (cadence)
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY o.days_since_prior_order)
        AS median_gap_orders_4plus

FROM stg_orders o
JOIN (
    -- Total orders per user (across ALL eval_sets, for the outcome count)
    SELECT user_id, COUNT(*) AS total_orders
    FROM stg_orders
    GROUP BY user_id
) total ON o.user_id = total.user_id
WHERE o.order_number >= 4
  AND o.days_since_prior_order IS NOT NULL   -- shouldn't be null for order 4+
GROUP BY o.user_id, total.total_orders;
