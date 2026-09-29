import sys
from pathlib import Path
from typing import Any

# Ensure workspace root is in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import duckdb
import numpy as np
import pandas as pd
from src.forecasting.baselines import (
    NaiveForecaster,
    SeasonalNaiveForecaster,
    MovingAverageForecaster,
)
from src.forecasting.statistical import HoltWintersForecaster
from src.forecasting.ml import LightGBMForecaster
from src.forecasting.backtesting import RollingOriginBacktester
from src.forecasting.evaluation import (
    evaluate_forecast_df,
    summarize_model_performance,
)
from src.sql.duckdb_engine import DuckDBAnalyticsEngine
from src.utils.logger import logger
from src.utils.helpers import get_project_root, ensure_directory


def run_forecasting_pipeline() -> dict[str, Any]:
    """
    Executes backtesting across candidate models, ranks performance by WAPE,
    trains champion model on full history, generates 28-day out-of-sample forecasts
    with prediction intervals, and persists all evaluation artifacts.
    """
    root = get_project_root()
    parquet_path = root / "data" / "processed" / "demand_daily.parquet"
    if not parquet_path.exists():
        raise FileNotFoundError(f"Processed demand data not found at {parquet_path}")

    logger.info("Loading demand data for forecasting from %s...", parquet_path)
    df = pd.read_parquet(parquet_path)

    # Define candidate models
    candidate_models = [
        NaiveForecaster(name="Naive"),
        SeasonalNaiveForecaster(seasonal_period=7, name="Seasonal_Naive_7d"),
        MovingAverageForecaster(window=7, name="Moving_Average_7d"),
        MovingAverageForecaster(window=28, name="Moving_Average_28d"),
        HoltWintersForecaster(seasonal_periods=7, name="Holt_Winters"),
        LightGBMForecaster(name="LightGBM"),
    ]

    # Execute rolling-origin backtesting (3 origins, 28-day horizon each = 84 days test window)
    backtester = RollingOriginBacktester(
        horizon_days=28,
        n_splits=3,
        step_days=28,
        date_col="date",
        target_col="quantity",
        entity_cols=["store_id", "sku_id"],
    )

    logger.info("Starting candidate model backtesting...")
    backtest_predictions = backtester.run_backtest(df, candidate_models)

    # Save detailed backtest predictions
    out_fc_dir = ensure_directory(root / "outputs" / "forecasts")
    out_metric_dir = ensure_directory(root / "outputs" / "metrics")
    out_report_dir = ensure_directory(root / "outputs" / "reports")

    bt_pred_path = out_fc_dir / "backtest_predictions.csv"
    backtest_predictions.to_csv(bt_pred_path, index=False)
    logger.info("Saved backtest predictions log to %s (%d rows)", bt_pred_path, len(backtest_predictions))

    # Ingest into DuckDB
    duck_engine = DuckDBAnalyticsEngine()
    duck_engine.load_table_from_df("fct_backtest_predictions", backtest_predictions, overwrite=True)
    duck_engine.execute_script("sql/forecasting/06_forecast_vs_actuals.sql")
    logger.info("Loaded fct_backtest_predictions and v_forecast_evaluation_summary in DuckDB.")

    # Compute model comparison summary
    model_comparison = summarize_model_performance(backtest_predictions)
    mc_path = out_metric_dir / "model_comparison.csv"
    model_comparison.to_csv(mc_path, index=False)
    logger.info("Model comparison results:\n%s", model_comparison.to_string())

    # Champion model selection (lowest WAPE)
    champion_name = model_comparison.iloc[0]["model_name"]
    champion_wape = model_comparison.iloc[0]["wape_pct"]
    logger.info("Champion model identified: %s with lowest WAPE = %.2f%%", champion_name, champion_wape)

    # SKU-level forecast quality breakdown
    sku_quality_records = []
    for (m_name, s_id, sku), grp in backtest_predictions.groupby(["model_name", "store_id", "sku_id"]):
        mets = evaluate_forecast_df(grp)
        sku_quality_records.append({
            "model_name": m_name,
            "store_id": s_id,
            "sku_id": sku,
            "mae": mets["mae"],
            "rmse": mets["rmse"],
            "wape_pct": mets["wape_pct"],
            "bias_units": mets["total_bias_units"],
            "normalized_bias_pct": mets["normalized_bias_pct"],
        })

    sku_quality_df = pd.DataFrame(sku_quality_records)
    quality_path = out_report_dir / "forecast_quality.csv"
    sku_quality_df.to_csv(quality_path, index=False)
    logger.info("Saved SKU-level forecast quality metrics to %s", quality_path)

    # Train Champion Model on Full Dataset and Generate 28-day Out-of-Sample Forecast
    logger.info("Fitting champion model (%s) on complete 2-year history...", champion_name)
    if champion_name == "LightGBM":
        final_model = LightGBMForecaster(name="LightGBM")
    elif champion_name == "Holt_Winters":
        final_model = HoltWintersForecaster(seasonal_periods=7, name="Holt_Winters")
    elif champion_name == "Moving_Average_7d":
        final_model = MovingAverageForecaster(window=7, name="Moving_Average_7d")
    else:
        final_model = SeasonalNaiveForecaster(seasonal_period=7, name="Seasonal_Naive_7d")

    final_model.fit(df, target_col="quantity", date_col="date", entity_cols=["store_id", "sku_id"])
    final_forecasts = final_model.predict(horizon_days=28)

    # Estimate uncertainty: Prediction Intervals (using empirical backtest error distribution)
    champ_errors = backtest_predictions[backtest_predictions["model_name"] == champion_name]["error"].values
    sigma_residuals = float(np.std(champ_errors))

    # 95% Prediction Interval: Z = 1.96 * sigma_residual * sqrt(1 + (h-1)*0.03)
    z_val = 1.96
    final_forecasts["uncertainty_std"] = (
        sigma_residuals * np.sqrt(1 + (final_forecasts["horizon_step"] - 1) * 0.03)
    ).round(2)
    final_forecasts["lower_bound"] = np.maximum(
        0.0,
        (final_forecasts["forecast"] - z_val * final_forecasts["uncertainty_std"]).round(2),
    )
    final_forecasts["upper_bound"] = (
        final_forecasts["forecast"] + z_val * final_forecasts["uncertainty_std"]
    ).round(2)

    # Attach product metadata (unique per SKU)
    sku_meta = df[["sku_id", "sku_name", "category", "sub_category", "unit_cost"]].drop_duplicates(subset=["sku_id"]).copy()
    base_prices = df[df["promotion_flag"] == 0].groupby("sku_id")["unit_price"].first()
    sku_meta["unit_price"] = sku_meta["sku_id"].map(base_prices)
    final_forecasts = final_forecasts.merge(sku_meta, on="sku_id", how="left")

    ff_path = out_fc_dir / "final_forecasts.csv"
    final_forecasts.to_csv(ff_path, index=False)
    logger.info("Saved 28-day out-of-sample final forecasts with prediction intervals to %s (%d rows)", ff_path, len(final_forecasts))

    # Serialize models
    model_save_dir = ensure_directory(root / "models" / "saved_models")
    if isinstance(final_model, LightGBMForecaster):
        final_model.save(model_save_dir / "lightgbm_champion.joblib")
    else:
        logger.info("Training and saving LightGBM global model for serving...")
        lgb_model = LightGBMForecaster(name="LightGBM")
        lgb_model.fit(df, target_col="quantity", date_col="date", entity_cols=["store_id", "sku_id"])
        lgb_model.save(model_save_dir / "lightgbm_global_model.joblib")

    duck_engine.close()

    return {
        "status": "SUCCESS",
        "champion_model": champion_name,
        "champion_wape": champion_wape,
        "model_comparison": model_comparison.to_dict(orient="records"),
        "final_forecast_count": len(final_forecasts),
    }


if __name__ == "__main__":
    run_forecasting_pipeline()
