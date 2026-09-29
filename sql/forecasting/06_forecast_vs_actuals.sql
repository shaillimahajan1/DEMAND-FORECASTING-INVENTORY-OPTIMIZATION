-- ==============================================================================
-- 06_forecast_vs_actuals.sql
-- Forecasting Layer: Model Evaluation Aggregates (MAE, RMSE, WAPE, Bias)
-- ==============================================================================

CREATE OR REPLACE VIEW v_forecast_evaluation_summary AS
SELECT
    model_name,
    COUNT(*) AS total_forecast_points,
    ROUND(AVG(ABS(actual - forecast)), 3) AS mae,
    ROUND(SQRT(AVG(POW(actual - forecast, 2))), 3) AS rmse,
    ROUND(SUM(ABS(actual - forecast)) / NULLIF(SUM(actual), 0) * 100, 2) AS wape_pct,
    ROUND(SUM(forecast - actual), 2) AS total_bias_units,
    ROUND(AVG(forecast - actual), 3) AS mean_bias_per_day,
    ROUND((SUM(forecast - actual) / NULLIF(SUM(actual), 0)) * 100, 2) AS normalized_bias_pct
FROM fct_backtest_predictions
GROUP BY model_name
ORDER BY wape_pct ASC;
