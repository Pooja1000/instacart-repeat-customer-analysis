-- =============================================================
-- 02_orders_sequenced.sql
-- View that tags each order with its sequence position and
-- identifies which window it belongs to (feature vs outcome).
-- =============================================================

CREATE OR REPLACE VIEW v_orders_sequenced AS
SELECT
    o.*,
    -- Feature window: orders 1-3; Outcome window: orders 4+
    CASE
        WHEN o.order_number <= 3 THEN 'feature'
        ELSE 'outcome'
    END AS analysis_window
FROM stg_orders o;
