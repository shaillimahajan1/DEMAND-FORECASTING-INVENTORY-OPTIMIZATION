-- ==============================================================================
-- 07_safety_stock_rop.sql
-- Inventory Layer: Safety Stock & Reorder Point Calculations
-- Note: Assumptions (lead_time_days, z_score) are loaded from scenario parameters.
-- ==============================================================================

CREATE OR REPLACE TABLE fct_inventory_policy_metrics AS
WITH demand_stats AS (
    SELECT
        store_id,
        sku_id,
        AVG(quantity) AS daily_demand_mean,
        STDDEV(quantity) AS daily_demand_std,
        AVG(unit_cost) AS unit_cost
    FROM stg_sales
    WHERE sale_date >= (SELECT MAX(sale_date) - INTERVAL '90 DAYS' FROM stg_sales)
    GROUP BY store_id, sku_id
)
SELECT
    d.store_id,
    d.sku_id,
    ROUND(d.daily_demand_mean, 2) AS avg_daily_demand,
    ROUND(d.daily_demand_std, 2) AS std_daily_demand,
    ROUND(d.unit_cost, 2) AS unit_cost,
    
    -- Assumptions layer (Scenario Baseline: Lead Time = 7 days, std = 1.5, Z = 1.645 for 95% SL)
    7.0 AS lead_time_days,
    1.5 AS lead_time_std_days,
    1.6449 AS z_score_95,
    
    -- Safety Stock formula with combined demand and lead time uncertainty:
    -- SS = Z * sqrt( L * sigma_D^2 + D^2 * sigma_L^2 )
    ROUND(
        1.6449 * SQRT(
            7.0 * POW(d.daily_demand_std, 2) + 
            POW(d.daily_demand_mean, 2) * POW(1.5, 2)
        ), 
        0
    ) AS safety_stock_units,
    
    -- Lead Time Demand = D * L
    ROUND(d.daily_demand_mean * 7.0, 0) AS lead_time_demand_units,
    
    -- Reorder Point (ROP) = Lead Time Demand + Safety Stock
    ROUND(
        (d.daily_demand_mean * 7.0) + 
        (1.6449 * SQRT(7.0 * POW(d.daily_demand_std, 2) + POW(d.daily_demand_mean, 2) * POW(1.5, 2))),
        0
    ) AS reorder_point_units
FROM demand_stats d;
