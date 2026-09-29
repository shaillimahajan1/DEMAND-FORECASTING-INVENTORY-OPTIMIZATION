-- ==============================================================================
-- 02_daily_demand.sql
-- Analytics Layer: Daily Aggregated Demand across Stores and Merchandising Categories
-- ==============================================================================

CREATE OR REPLACE TABLE fct_daily_demand AS
SELECT
    sale_date,
    store_id,
    sku_id,
    category,
    sub_category,
    quantity AS demand_qty,
    unit_price,
    unit_cost,
    revenue,
    gross_margin,
    promotion_flag,
    DAYOFWEEK(sale_date) AS day_of_week,
    MONTH(sale_date) AS month_of_year,
    YEAR(sale_date) AS calendar_year,
    CASE 
        WHEN DAYOFWEEK(sale_date) IN (0, 6) THEN 1 
        ELSE 0 
    END AS is_weekend
FROM stg_sales;
