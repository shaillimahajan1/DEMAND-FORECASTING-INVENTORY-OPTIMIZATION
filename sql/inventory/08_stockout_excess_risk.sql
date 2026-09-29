-- ==============================================================================
-- 08_stockout_excess_risk.sql
-- Inventory Layer: Stockout and Excess Inventory Risk Profiling
-- ==============================================================================

CREATE OR REPLACE VIEW v_stockout_excess_risk AS
SELECT
    r.store_id,
    r.sku_id,
    r.forecast_demand_28d,
    r.current_inventory_position,
    r.safety_stock,
    r.reorder_point,
    r.days_of_supply,
    -- Stockout Risk Classification
    CASE
        WHEN r.days_of_supply < 3.0 THEN 'Critical'
        WHEN r.days_of_supply < 7.0 THEN 'High'
        WHEN r.days_of_supply < 14.0 THEN 'Medium'
        ELSE 'Low'
    END AS stockout_risk_level,
    -- Excess Inventory Risk Flag
    CASE
        WHEN r.days_of_supply > 45.0 THEN 1
        ELSE 0
    END AS is_excess_inventory,
    -- Replenishment Reorder Trigger Flag
    CASE
        WHEN r.current_inventory_position <= r.reorder_point THEN 1
        ELSE 0
    END AS reorder_triggered_flag
FROM fct_inventory_recommendations r;
