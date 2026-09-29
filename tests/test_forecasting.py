"""
Unit tests for forecasting models, evaluation metrics, and data leakage prevention.
"""

import numpy as np
import pandas as pd
import pytest
from src.forecasting.baselines import NaiveForecaster, SeasonalNaiveForecaster, MovingAverageForecaster
from src.forecasting.evaluation import (
    calculate_mae,
    calculate_rmse,
    calculate_wape,
    calculate_bias,
    calculate_normalized_bias,
)
from src.forecasting.ml import LightGBMForecaster


def test_forecast_metrics_known_values():
    """Verify metrics match exact hand-calculated ground truth values."""
    actuals = np.array([10.0, 20.0])
    forecasts = np.array([12.0, 18.0])

    mae = calculate_mae(actuals, forecasts)
    rmse = calculate_rmse(actuals, forecasts)
    wape = calculate_wape(actuals, forecasts)
    bias = calculate_bias(actuals, forecasts)
    norm_bias = calculate_normalized_bias(actuals, forecasts)

    # MAE = (|10-12| + |20-18|) / 2 = 4 / 2 = 2.0
    assert pytest.approx(mae, rel=1e-3) == 2.0
    # RMSE = sqrt(((10-12)^2 + (20-18)^2) / 2) = sqrt((4 + 4) / 2) = 2.0
    assert pytest.approx(rmse, rel=1e-3) == 2.0
    # WAPE = (2 + 2) / (10 + 20) * 100 = 4 / 30 * 100 = 13.333%
    assert pytest.approx(wape, rel=1e-3) == 13.333
    # Bias = (12-10) + (18-20) = 2 - 2 = 0.0
    assert pytest.approx(bias, rel=1e-3) == 0.0
    assert pytest.approx(norm_bias, rel=1e-3) == 0.0


def test_forecast_metrics_non_negativity():
    """Verify that magnitude error metrics are always strictly non-negative."""
    rng = np.random.default_rng(42)
    act = rng.integers(0, 100, size=50).astype(float)
    fc = rng.integers(0, 100, size=50).astype(float)

    assert calculate_mae(act, fc) >= 0.0
    assert calculate_rmse(act, fc) >= 0.0
    assert calculate_wape(act, fc) >= 0.0


def test_naive_forecaster():
    """Verify Naive forecaster projects the last observed value."""
    dates = pd.date_range("2024-01-01", "2024-01-10", freq="D")
    df = pd.DataFrame({
        "date": dates,
        "store_id": "FC-1",
        "sku_id": "SKU-1",
        "quantity": [5, 6, 7, 8, 9, 10, 11, 12, 13, 25],  # Last is 25
    })
    model = NaiveForecaster()
    model.fit(df, target_col="quantity", date_col="date", entity_cols=["store_id", "sku_id"])
    preds = model.predict(horizon_days=5)

    assert len(preds) == 5
    assert (preds["forecast"] == 25.0).all()
    assert (preds["horizon_step"].values == [1, 2, 3, 4, 5]).all()


def test_seasonal_naive_forecaster():
    """Verify Seasonal Naive forecaster repeats the exact 7-day seasonal cycle."""
    dates = pd.date_range("2024-01-01", "2024-01-14", freq="D")
    weekly_pattern = [10, 12, 14, 16, 20, 30, 25]  # Mon to Sun
    df = pd.DataFrame({
        "date": dates,
        "store_id": "FC-1",
        "sku_id": "SKU-1",
        "quantity": weekly_pattern * 2,
    })
    model = SeasonalNaiveForecaster(seasonal_period=7)
    model.fit(df, target_col="quantity", date_col="date", entity_cols=["store_id", "sku_id"])
    preds = model.predict(horizon_days=7)

    assert len(preds) == 7
    assert preds["forecast"].tolist() == weekly_pattern


def test_future_leakage_prevention():
    """
    Critical Test: Ensure feature engineering strictly uses historical observations.
    Modifying the target at date T must NOT change features computed at date T.
    """
    dates = pd.date_range("2024-01-01", periods=40, freq="D")
    df_base = pd.DataFrame({
        "date": dates,
        "store_id": "FC-1",
        "sku_id": "SKU-1",
        "category": "Electronics",
        "quantity": np.ones(40) * 10,
        "unit_price": 20.0,
        "promotion_flag": 0,
    })

    # Create modified dataset where day 39 quantity is changed dramatically from 10 to 9999
    df_mod = df_base.copy()
    df_mod.loc[38, "quantity"] = 9999

    forecaster = LightGBMForecaster()
    feat_base = forecaster.build_features(df_base, target_col="quantity", is_training=False)
    feat_mod = forecaster.build_features(df_mod, target_col="quantity", is_training=False)

    # Feature at index 38 (date 2024-02-08) MUST NOT be affected by quantity on index 38
    # Because lag_1 looks at index 37, and rolling_mean_7d looks at index 31..37
    assert feat_base.loc[38, "lag_1"] == feat_mod.loc[38, "lag_1"]
    assert feat_base.loc[38, "rolling_mean_7d"] == feat_mod.loc[38, "rolling_mean_7d"]
