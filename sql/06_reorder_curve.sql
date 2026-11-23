-- =============================================================
-- 06_reorder_curve.sql
-- Reorder rate by order number (1-10) for users with >= 10 orders.
-- Constant cohort: only users who reached order 10.
-- =============================================================

CREATE OR REPLACE TABLE reorder_curve AS
WITH cohort AS (
    -- Users with at least 10 PRIOR orders (constant cohort).
    -- We count only prior orders so the cohort is constant across
    -- all order positions 1-10 (every cohort member has product data
    -- for all 10 positions).
    SELECT user_id
    FROM stg_orders
    WHERE eval_set = 'prior'
    GROUP BY user_id
    HAVING COUNT(*) >= 10
)
SELECT
    o.order_number,
    COUNT(*)                     AS n_items,
    SUM(op.reordered)            AS n_reordered,
    AVG(op.reordered * 1.0)      AS reorder_rate,
    COUNT(DISTINCT o.user_id)    AS n_users
FROM stg_orders o
JOIN cohort c                    ON o.user_id = c.user_id
JOIN stg_order_products_prior op ON o.order_id = op.order_id
WHERE o.order_number BETWEEN 1 AND 10
  AND o.eval_set = 'prior'
GROUP BY o.order_number
ORDER BY o.order_number;
