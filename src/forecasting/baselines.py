"""
Baseline Forecasting Models: Naive, Seasonal Naive, and Moving Average
Essential for benchmark comparison against advanced statistical & ML algorithms.
"""

from datetime import timedelta
import numpy as np
import pandas as pd
from src.forecasting.base import BaseForecaster
from src.utils.logger import logger


class NaiveForecaster(BaseForecaster):
    """
    Naive Forecast Benchmark:
    Forecast(t + h) = Actual(t)
    Carries the most recent observation forward into all forecast horizon periods.
    """

    def __init__(self, name: str = "Naive"):
        super().__init__(name=name)
        self.last_values: dict[tuple, float] = {}
        self.entity_cols = ["store_id", "sku_id"]
        self.last_date = None

    def fit(
        self,
        df: pd.DataFrame,
        target_col: str = "quantity",
        date_col: str = "date",
        entity_cols: list[str] | None = None,
    ) -> "NaiveForecaster":
        self.entity_cols = entity_cols or ["store_id", "sku_id"]
        sorted_df = df.sort_values(by=date_col)
        self.last_date = pd.to_datetime(sorted_df[date_col].max())

        # Grab the latest observed value for each entity
        latest_records = sorted_df.groupby(self.entity_cols).last().reset_index()
        for _, row in latest_records.iterrows():
            key = tuple(row[col] for col in self.entity_cols)
            self.last_values[key] = float(row[target_col])

        self.is_fitted = True
        return self

    def predict(self, horizon_days: int) -> pd.DataFrame:
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before predict() is called.")

        predictions = []
        for h in range(1, horizon_days + 1):
            fc_date = self.last_date + timedelta(days=h)
            for key, val in self.last_values.items():
                record = {col: key[i] for i, col in enumerate(self.entity_cols)}
                record.update({
                    "forecast_date": fc_date.strftime("%Y-%m-%d"),
                    "horizon_step": h,
                    "forecast": max(0.0, float(val)),
                    "model_name": self.name,
                })
                predictions.append(record)

        return pd.DataFrame(predictions)


class SeasonalNaiveForecaster(BaseForecaster):
    """
    Seasonal Naive Forecast Benchmark:
    Forecast(t + h) = Actual(t - P + (h mod P))
    Repeats the exact corresponding seasonal cycle (default weekly: P = 7).
    """

    def __init__(self, seasonal_period: int = 7, name: str | None = None):
        name = name or f"Seasonal_Naive_{seasonal_period}d"
        super().__init__(name=name)
        self.seasonal_period = seasonal_period
        self.seasonal_history: dict[tuple, list[float]] = {}
        self.entity_cols = ["store_id", "sku_id"]
        self.last_date = None

    def fit(
        self,
        df: pd.DataFrame,
        target_col: str = "quantity",
        date_col: str = "date",
        entity_cols: list[str] | None = None,
    ) -> "SeasonalNaiveForecaster":
        self.entity_cols = entity_cols or ["store_id", "sku_id"]
        sorted_df = df.sort_values(by=date_col)
        self.last_date = pd.to_datetime(sorted_df[date_col].max())

        # Extract last P historical values for each entity
        for key, group in sorted_df.groupby(self.entity_cols):
            vals = group[target_col].tail(self.seasonal_period).values.tolist()
            if len(vals) < self.seasonal_period:
                # Pad with mean if series shorter than period
                mean_val = float(group[target_col].mean()) if len(vals) > 0 else 0.0
                vals = [mean_val] * (self.seasonal_period - len(vals)) + vals
            self.seasonal_history[key] = vals

        self.is_fitted = True
        return self

    def predict(self, horizon_days: int) -> pd.DataFrame:
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before predict() is called.")

        predictions = []
        for h in range(1, horizon_days + 1):
            fc_date = self.last_date + timedelta(days=h)
            # Cycle index through the seasonal buffer
            cycle_idx = (h - 1) % self.seasonal_period
            for key, hist in self.seasonal_history.items():
                val = hist[cycle_idx]
                record = {col: key[i] for i, col in enumerate(self.entity_cols)}
                record.update({
                    "forecast_date": fc_date.strftime("%Y-%m-%d"),
                    "horizon_step": h,
                    "forecast": max(0.0, float(val)),
                    "model_name": self.name,
                })
                predictions.append(record)

        return pd.DataFrame(predictions)


class MovingAverageForecaster(BaseForecaster):
    """
    Moving Average Forecast Benchmark:
    Forecast(t + h) = (1 / W) * sum_{i=0}^{W-1} Actual(t - i)
    Calculates the historical rolling average over window W.
    """

    def __init__(self, window: int = 7, name: str | None = None):
        name = name or f"Moving_Average_{window}d"
        super().__init__(name=name)
        self.window = window
        self.ma_values: dict[tuple, float] = {}
        self.entity_cols = ["store_id", "sku_id"]
        self.last_date = None

    def fit(
        self,
        df: pd.DataFrame,
        target_col: str = "quantity",
        date_col: str = "date",
        entity_cols: list[str] | None = None,
    ) -> "MovingAverageForecaster":
        self.entity_cols = entity_cols or ["store_id", "sku_id"]
        sorted_df = df.sort_values(by=date_col)
        self.last_date = pd.to_datetime(sorted_df[date_col].max())

        for key, group in sorted_df.groupby(self.entity_cols):
            window_vals = group[target_col].tail(self.window).values
            ma_val = float(np.mean(window_vals)) if len(window_vals) > 0 else 0.0
            self.ma_values[key] = ma_val

        self.is_fitted = True
        return self

    def predict(self, horizon_days: int) -> pd.DataFrame:
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before predict() is called.")

        predictions = []
        for h in range(1, horizon_days + 1):
            fc_date = self.last_date + timedelta(days=h)
            for key, val in self.ma_values.items():
                record = {col: key[i] for i, col in enumerate(self.entity_cols)}
                record.update({
                    "forecast_date": fc_date.strftime("%Y-%m-%d"),
                    "horizon_step": h,
                    "forecast": max(0.0, round(float(val), 2)),
                    "model_name": self.name,
                })
                predictions.append(record)

        return pd.DataFrame(predictions)
