"""
Forecast Evaluation Metrics Module
Implements MAE, RMSE, WAPE, Bias, and Normalized Bias with numerical safeguards.
"""

from typing import Any
import numpy as np
import pandas as pd
from src.utils.logger import logger


def calculate_mae(actuals: np.ndarray | pd.Series, forecasts: np.ndarray | pd.Series) -> float:
    """Mean Absolute Error: (1 / N) * sum(|Actual - Forecast|)"""
    act = np.asarray(actuals, dtype=float)
    fc = np.asarray(forecasts, dtype=float)
    if len(act) == 0:
        return 0.0
    return float(np.mean(np.abs(act - fc)))


def calculate_rmse(actuals: np.ndarray | pd.Series, forecasts: np.ndarray | pd.Series) -> float:
    """Root Mean Squared Error: sqrt((1 / N) * sum((Actual - Forecast)^2))"""
    act = np.asarray(actuals, dtype=float)
    fc = np.asarray(forecasts, dtype=float)
    if len(act) == 0:
        return 0.0
    return float(np.sqrt(np.mean((act - fc) ** 2)))


def calculate_wape(actuals: np.ndarray | pd.Series, forecasts: np.ndarray | pd.Series) -> float:
    """
    Weighted Absolute Percentage Error (WAPE):
    WAPE = sum(|Actual - Forecast|) / sum(Actual)
    Preferred over MAPE in retail/supply chain because it handles zero-demand days gracefully.
    Returns value as a percentage (e.g. 15.2 for 15.2%).
    """
    act = np.asarray(actuals, dtype=float)
    fc = np.asarray(forecasts, dtype=float)
    sum_actuals = float(np.sum(act))
    if sum_actuals == 0.0:
        return 0.0 if np.sum(fc) == 0.0 else 100.0
    return float((np.sum(np.abs(act - fc)) / sum_actuals) * 100.0)


def calculate_bias(actuals: np.ndarray | pd.Series, forecasts: np.ndarray | pd.Series) -> float:
    """
    Forecast Bias: sum(Forecast - Actual)
    Positive Bias: Systematic overforecasting (leads to excess stock and holding costs).
    Negative Bias: Systematic underforecasting (leads to stockouts and lost revenue).
    """
    act = np.asarray(actuals, dtype=float)
    fc = np.asarray(forecasts, dtype=float)
    return float(np.sum(fc - act))


def calculate_normalized_bias(actuals: np.ndarray | pd.Series, forecasts: np.ndarray | pd.Series) -> float:
    """
    Normalized Forecast Bias (%): sum(Forecast - Actual) / sum(Actual) * 100
    """
    act = np.asarray(actuals, dtype=float)
    fc = np.asarray(forecasts, dtype=float)
    sum_act = float(np.sum(act))
    if sum_act == 0.0:
        return 0.0
    return float((np.sum(fc - act) / sum_act) * 100.0)


def evaluate_forecast_df(df: pd.DataFrame, actual_col: str = "actual", forecast_col: str = "forecast") -> dict[str, float]:
    """Calculate all standard metrics from a predictions DataFrame."""
    act = df[actual_col].values
    fc = df[forecast_col].values

    return {
        "mae": round(calculate_mae(act, fc), 3),
        "rmse": round(calculate_rmse(act, fc), 3),
        "wape_pct": round(calculate_wape(act, fc), 2),
        "total_bias_units": round(calculate_bias(act, fc), 2),
        "normalized_bias_pct": round(calculate_normalized_bias(act, fc), 2),
    }


def summarize_model_performance(backtest_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate backtest performance across models and horizons.
    """
    records = []
    for model_name, grp in backtest_df.groupby("model_name"):
        metrics = evaluate_forecast_df(grp)
        metrics["model_name"] = model_name
        metrics["evaluation_points"] = len(grp)
        records.append(metrics)

    res_df = pd.DataFrame(records)
    cols = ["model_name", "wape_pct", "mae", "rmse", "total_bias_units", "normalized_bias_pct", "evaluation_points"]
    return res_df[cols].sort_values(by="wape_pct").reset_index(drop=True)
