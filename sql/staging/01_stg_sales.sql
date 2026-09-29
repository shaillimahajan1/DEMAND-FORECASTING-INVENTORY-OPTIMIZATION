-- ==============================================================================
-- 01_stg_sales.sql
-- Staging Layer: Ingestion and Type Normalization
-- ==============================================================================

CREATE OR REPLACE VIEW stg_sales AS
SELECT
    CAST(date AS DATE) AS sale_date,
    CAST(store_id AS VARCHAR) AS store_id,
    CAST(store_name AS VARCHAR) AS store_name,
    CAST(sku_id AS VARCHAR) AS sku_id,
    CAST(sku_name AS VARCHAR) AS sku_name,
    CAST(category AS VARCHAR) AS category,
    CAST(sub_category AS VARCHAR) AS sub_category,
    CAST(quantity AS INTEGER) AS quantity,
    CAST(unit_price AS DECIMAL(10, 2)) AS unit_price,
    CAST(unit_cost AS DECIMAL(10, 2)) AS unit_cost,
    CAST(revenue AS DECIMAL(12, 2)) AS revenue,
    CAST(gross_margin AS DECIMAL(12, 2)) AS gross_margin,
    CAST(promotion_flag AS INTEGER) AS promotion_flag
FROM demand_daily;
