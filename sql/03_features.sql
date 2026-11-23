-- =============================================================
-- 03_features.sql
-- Compute per-user features using ONLY orders 1-3.
-- Each feature is documented with its source window.
-- =============================================================

-- ── 3a. Order-level features (timing, basket size) ───────────
-- Aggregate order-level attributes for orders 1-3
CREATE OR REPLACE TABLE tmp_order_features AS
SELECT
    o.user_id,

    -- First order size (from order_products_prior joined on order 1)
    -- We'll compute basket sizes below

    -- Days to second and third order
    MAX(CASE WHEN o.order_number = 2 THEN o.days_since_prior_order END)
        AS days_to_second_order,
    MAX(CASE WHEN o.order_number = 3 THEN o.days_since_prior_order END)
        AS days_to_third_order,

    -- Mean early gap (for lifecycle segments)
    AVG(CASE WHEN o.order_number IN (2, 3) THEN o.days_since_prior_order END)
        AS mean_early_gap,

    -- Share of orders 1-3 on busiest days (order_dow IN (0, 1))
    AVG(CASE WHEN o.order_dow IN (0, 1) THEN 1.0 ELSE 0.0 END)
        AS busiest_days_share_1_3,

    -- Share of orders 1-3 in morning hours (6-11)
    AVG(CASE WHEN o.order_hour_of_day BETWEEN 6 AND 11 THEN 1.0 ELSE 0.0 END)
        AS morning_share_1_3,

    -- Share of orders 1-3 in evening hours (17-22)
    AVG(CASE WHEN o.order_hour_of_day BETWEEN 17 AND 22 THEN 1.0 ELSE 0.0 END)
        AS evening_share_1_3

FROM stg_orders o
WHERE o.order_number <= 3          -- FEATURE WINDOW ONLY
  AND o.eval_set = 'prior'         -- orders 1-3 are always prior
GROUP BY o.user_id;


-- ── 3b. Basket-level features (items, reorders, departments) ─
-- Join order_products_prior to orders 1-3 to get item-level data
CREATE OR REPLACE TABLE tmp_basket_features AS
WITH order1_products AS (
    -- First order basket details
    SELECT
        o.user_id,
        op.product_id,
        p.department,
        op.reordered
    FROM stg_orders o
    JOIN stg_order_products_prior op ON o.order_id = op.order_id
    JOIN stg_products p              ON op.product_id = p.product_id
    WHERE o.order_number = 1
      AND o.eval_set = 'prior'
),
order1_agg AS (
    SELECT
        user_id,
        COUNT(*)                                              AS first_order_size,
        COUNT(DISTINCT department)                            AS n_departments_order1,
        -- Department shares in first order
        AVG(CASE WHEN department = 'produce'    THEN 1.0 ELSE 0.0 END) AS pct_produce_order1,
        AVG(CASE WHEN department = 'dairy eggs' THEN 1.0 ELSE 0.0 END) AS pct_dairy_order1,
        AVG(CASE WHEN department = 'snacks'     THEN 1.0 ELSE 0.0 END) AS pct_snacks_order1
    FROM order1_products
    GROUP BY user_id
),
-- Aisle count for first order (separate because we need aisle_id)
order1_aisles AS (
    SELECT
        o.user_id,
        COUNT(DISTINCT p.aisle_id) AS n_aisles_order1
    FROM stg_orders o
    JOIN stg_order_products_prior op ON o.order_id = op.order_id
    JOIN stg_products p              ON op.product_id = p.product_id
    WHERE o.order_number = 1
      AND o.eval_set = 'prior'
    GROUP BY o.user_id
),
-- Average basket size across orders 1-3
basket_sizes AS (
    SELECT
        o.user_id,
        AVG(basket.n_items) AS avg_basket_size_1_3
    FROM stg_orders o
    JOIN (
        SELECT order_id, COUNT(*) AS n_items
        FROM stg_order_products_prior
        GROUP BY order_id
    ) basket ON o.order_id = basket.order_id
    WHERE o.order_number <= 3
      AND o.eval_set = 'prior'
    GROUP BY o.user_id
),
-- Reorder rate in orders 2-3 (share of items that are reorders)
reorder_rate AS (
    SELECT
        o.user_id,
        AVG(op.reordered * 1.0) AS reorder_rate_2_3
    FROM stg_orders o
    JOIN stg_order_products_prior op ON o.order_id = op.order_id
    WHERE o.order_number IN (2, 3)
      AND o.eval_set = 'prior'
    GROUP BY o.user_id
)
SELECT
    o1.user_id,
    o1.first_order_size,
    o1.n_departments_order1,
    o1.pct_produce_order1,
    o1.pct_dairy_order1,
    o1.pct_snacks_order1,
    oa.n_aisles_order1,
    bs.avg_basket_size_1_3,
    rr.reorder_rate_2_3
FROM order1_agg o1
LEFT JOIN order1_aisles oa ON o1.user_id = oa.user_id
LEFT JOIN basket_sizes bs  ON o1.user_id = bs.user_id
LEFT JOIN reorder_rate rr  ON o1.user_id = rr.user_id;
