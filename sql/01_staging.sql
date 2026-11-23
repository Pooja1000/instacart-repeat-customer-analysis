-- =============================================================
-- 01_staging.sql
-- Load raw CSVs into DuckDB staging tables with proper types.
-- =============================================================

-- Orders
CREATE OR REPLACE TABLE stg_orders AS
SELECT
    order_id::INTEGER        AS order_id,
    user_id::INTEGER         AS user_id,
    eval_set::VARCHAR        AS eval_set,
    order_number::INTEGER    AS order_number,
    order_dow::INTEGER       AS order_dow,
    order_hour_of_day::INTEGER AS order_hour_of_day,
    days_since_prior_order::DOUBLE AS days_since_prior_order
FROM read_csv_auto('data/raw/orders.csv');

-- Order products (prior) — the big file, ~32M rows
CREATE OR REPLACE TABLE stg_order_products_prior AS
SELECT
    order_id::INTEGER        AS order_id,
    product_id::INTEGER      AS product_id,
    add_to_cart_order::INTEGER AS add_to_cart_order,
    reordered::INTEGER       AS reordered
FROM read_csv_auto('data/raw/order_products__prior.csv');

-- Order products (train)
CREATE OR REPLACE TABLE stg_order_products_train AS
SELECT
    order_id::INTEGER        AS order_id,
    product_id::INTEGER      AS product_id,
    add_to_cart_order::INTEGER AS add_to_cart_order,
    reordered::INTEGER       AS reordered
FROM read_csv_auto('data/raw/order_products__train.csv');

-- Products with department and aisle info
CREATE OR REPLACE TABLE stg_products AS
SELECT
    p.product_id::INTEGER    AS product_id,
    p.product_name::VARCHAR  AS product_name,
    p.aisle_id::INTEGER      AS aisle_id,
    a.aisle::VARCHAR         AS aisle,
    p.department_id::INTEGER AS department_id,
    d.department::VARCHAR    AS department
FROM read_csv_auto('data/raw/products.csv') p
LEFT JOIN read_csv_auto('data/raw/aisles.csv') a   ON p.aisle_id = a.aisle_id
LEFT JOIN read_csv_auto('data/raw/departments.csv') d ON p.department_id = d.department_id;
