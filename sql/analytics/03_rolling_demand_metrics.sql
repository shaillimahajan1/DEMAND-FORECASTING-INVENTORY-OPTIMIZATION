-- ==============================================================================
-- 03_rolling_demand_metrics.sql
-- Analytics Layer: Rolling Window Demand Statistics (7-day, 14-day, 28-day)
-- ==============================================================================

CREATE OR REPLACE TABLE agg_rolling_demand AS
SELECT
    sale_date,
    store_id,
    sku_id,
    demand_qty,
    -- 7-Day Rolling Window
    AVG(demand_qty) OVER (
        PARTITION BY store_id, sku_id 
        ORDER BY sale_date 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS rolling_mean_7d,
    STDDEV(demand_qty) OVER (
        PARTITION BY store_id, sku_id 
        ORDER BY sale_date 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS rolling_std_7d,

    -- 14-Day Rolling Window
    AVG(demand_qty) OVER (
        PARTITION BY store_id, sku_id 
        ORDER BY sale_date 
        ROWS BETWEEN 13 PRECEDING AND CURRENT ROW
    ) AS rolling_mean_14d,
    STDDEV(demand_qty) OVER (
        PARTITION BY store_id, sku_id 
        ORDER BY sale_date 
        ROWS BETWEEN 13 PRECEDING AND CURRENT ROW
    ) AS rolling_std_14d,

    -- 28-Day Rolling Window
    AVG(demand_qty) OVER (
        PARTITION BY store_id, sku_id 
        ORDER BY sale_date 
        ROWS BETWEEN 27 PRECEDING AND CURRENT ROW
    ) AS rolling_mean_28d,
    STDDEV(demand_qty) OVER (
        PARTITION BY store_id, sku_id 
        ORDER BY sale_date 
        ROWS BETWEEN 27 PRECEDING AND CURRENT ROW
    ) AS rolling_std_28d
FROM fct_daily_demand;
