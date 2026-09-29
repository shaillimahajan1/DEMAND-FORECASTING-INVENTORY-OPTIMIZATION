-- ==============================================================================
-- 04_abc_xyz_classification.sql
-- Analytics Layer: ABC Revenue & XYZ Volatility 9-Box Portfolio Segmentation
-- ==============================================================================

CREATE OR REPLACE TABLE dim_abc_xyz_segmentation AS
WITH sku_totals AS (
    SELECT
        sku_id,
        MIN(sku_name) AS sku_name,
        MIN(category) AS category,
        MIN(sub_category) AS sub_category,
        AVG(unit_price) AS avg_unit_price,
        AVG(unit_cost) AS unit_cost,
        SUM(quantity) AS total_units_sold,
        SUM(revenue) AS total_revenue,
        SUM(gross_margin) AS total_gross_margin,
        AVG(quantity) AS mean_daily_demand,
        STDDEV(quantity) AS std_daily_demand,
        CASE 
            WHEN AVG(quantity) > 0 THEN STDDEV(quantity) / AVG(quantity)
            ELSE 0.0 
        END AS coefficient_of_variation
    FROM stg_sales
    GROUP BY sku_id
),
abc_ranked AS (
    SELECT
        *,
        SUM(total_revenue) OVER () AS global_revenue,
        SUM(total_revenue) OVER (ORDER BY total_revenue DESC) AS cumulative_revenue,
        SUM(total_revenue) OVER (ORDER BY total_revenue DESC) / SUM(total_revenue) OVER () AS cumulative_revenue_pct
    FROM sku_totals
),
classified AS (
    SELECT
        sku_id,
        sku_name,
        category,
        sub_category,
        ROUND(avg_unit_price, 2) AS avg_unit_price,
        ROUND(unit_cost, 2) AS unit_cost,
        total_units_sold,
        ROUND(total_revenue, 2) AS total_revenue,
        ROUND(total_gross_margin, 2) AS total_gross_margin,
        ROUND(mean_daily_demand, 2) AS mean_daily_demand,
        ROUND(std_daily_demand, 2) AS std_daily_demand,
        ROUND(coefficient_of_variation, 3) AS cv,
        ROUND(cumulative_revenue_pct * 100, 2) AS cumulative_revenue_pct,
        -- ABC Classification based on revenue share
        CASE
            WHEN cumulative_revenue_pct <= 0.70 THEN 'A'
            WHEN cumulative_revenue_pct <= 0.90 THEN 'B'
            ELSE 'C'
        END AS abc_class,
        -- XYZ Classification based on Demand Predictability (CV)
        CASE
            WHEN coefficient_of_variation < 0.50 THEN 'X'
            WHEN coefficient_of_variation < 1.00 THEN 'Y'
            ELSE 'Z'
        END AS xyz_class
    FROM abc_ranked
)
SELECT
    *,
    CONCAT(abc_class, xyz_class) AS abc_xyz_segment,
    CASE CONCAT(abc_class, xyz_class)
        WHEN 'AX' THEN 'High Value, Highly Predictable (Automate Replenishment)'
        WHEN 'AY' THEN 'High Value, Moderate Volatility (Buffer with Safety Stock)'
        WHEN 'AZ' THEN 'High Value, Erratic / Volatile (Active S&OP / Close Monitoring)'
        WHEN 'BX' THEN 'Medium Value, Steady Demand (Standard Periodic Review)'
        WHEN 'BY' THEN 'Medium Value, Moderate Volatility (Standard Safety Stock)'
        WHEN 'BZ' THEN 'Medium Value, Erratic (Exception Based Review)'
        WHEN 'CX' THEN 'Low Value, Predictable (Bulk Replenishment / Low Touch)'
        WHEN 'CY' THEN 'Low Value, Moderate Volatility (Low Stock Priority)'
        WHEN 'CZ' THEN 'Low Value, Erratic / Intermittent (Make-to-Order or Minimal Buffer)'
    END AS operational_strategy
FROM classified
ORDER BY total_revenue DESC;
