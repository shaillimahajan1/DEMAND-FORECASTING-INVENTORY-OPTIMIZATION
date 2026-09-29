-- ==============================================================================
-- 05_sku_demand_profiling.sql
-- Analytics Layer: SKU and Location Velocity Ranking
-- ==============================================================================

CREATE OR REPLACE TABLE agg_sku_location_profile AS
SELECT
    store_id,
    sku_id,
    COUNT(sale_date) AS total_calendar_days,
    SUM(CASE WHEN quantity = 0 THEN 1 ELSE 0 END) AS zero_demand_days,
    ROUND(SUM(CASE WHEN quantity = 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(sale_date), 2) AS zero_demand_pct,
    SUM(quantity) AS total_units,
    ROUND(AVG(quantity), 2) AS avg_daily_units,
    ROUND(STDDEV(quantity), 2) AS std_daily_units,
    MAX(quantity) AS max_single_day_units,
    ROUND(SUM(revenue), 2) AS total_revenue,
    ROUND(SUM(gross_margin), 2) AS total_margin,
    DENSE_RANK() OVER (PARTITION BY store_id ORDER BY SUM(revenue) DESC) AS store_revenue_rank
FROM stg_sales
GROUP BY store_id, sku_id;
