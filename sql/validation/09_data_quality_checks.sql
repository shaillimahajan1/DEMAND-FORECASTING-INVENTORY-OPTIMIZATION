-- ==============================================================================
-- 09_data_quality_checks.sql
-- Validation Layer: Automated SQL Data Integrity Test Suite
-- ==============================================================================

-- Check 1: Null counts across critical primary keys
SELECT
    COUNT(*) AS total_rows,
    SUM(CASE WHEN sale_date IS NULL THEN 1 ELSE 0 END) AS null_dates,
    SUM(CASE WHEN store_id IS NULL THEN 1 ELSE 0 END) AS null_stores,
    SUM(CASE WHEN sku_id IS NULL THEN 1 ELSE 0 END) AS null_skus,
    SUM(CASE WHEN quantity IS NULL THEN 1 ELSE 0 END) AS null_quantities
FROM stg_sales;

-- Check 2: Grain uniqueness test
SELECT
    sale_date,
    store_id,
    sku_id,
    COUNT(*) AS duplicate_count
FROM stg_sales
GROUP BY sale_date, store_id, sku_id
HAVING COUNT(*) > 1;

-- Check 3: Non-negative demand check
SELECT
    COUNT(*) AS negative_quantity_count
FROM stg_sales
WHERE quantity < 0;
