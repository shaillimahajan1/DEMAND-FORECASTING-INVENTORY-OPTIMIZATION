"""
Statistical Forecasting Models: Holt-Winters Exponential Smoothing
Captures baseline level, additive/multiplicative trend, and seasonal components.
"""

from datetime import timedelta
import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from src.forecasting.base import BaseForecaster
from src.utils.logger import logger


class HoltWintersForecaster(BaseForecaster):
    """
    Holt-Winters Exponential Smoothing model fitted on individual SKU-Store series.
    Uses weekly seasonal period (seasonal_periods = 7).
    Falls back gracefully to Simple Exponential Smoothing if data length is short or convergence fails.
    """

    def __init__(self, seasonal_periods: int = 7, name: str = "Holt_Winters"):
        super().__init__(name=name)
        self.seasonal_periods = seasonal_periods
        self.entity_cols = ["store_id", "sku_id"]
        self.last_date = None
        self.models: dict[tuple, Any] = {}
        self.last_history: dict[tuple, np.ndarray] = {}

    def fit(
        self,
        df: pd.DataFrame,
        target_col: str = "quantity",
        date_col: str = "date",
        entity_cols: list[str] | None = None,
    ) -> "HoltWintersForecaster":
        self.entity_cols = entity_cols or ["store_id", "sku_id"]
        sorted_df = df.sort_values(by=date_col)
        self.last_date = pd.to_datetime(sorted_df[date_col].max())

        self.models.clear()
        self.last_history.clear()

        for key, group in sorted_df.groupby(self.entity_cols):
            series = group[target_col].values.astype(float)
            self.last_history[key] = series[-14:]  # backup buffer

            # Fit HW only if sufficient history exists
            if len(series) >= 2 * self.seasonal_periods:
                try:
                    # Use additive trend and seasonal components
                    hw = ExponentialSmoothing(
                        series,
                        trend="add",
                        seasonal="add",
                        seasonal_periods=self.seasonal_periods,
                        initialization_method="estimated",
                    ).fit(optimized=True)
                    self.models[key] = hw
                except Exception:
                    # Fallback to simple moving average or simple exponential smoothing
                    self.models[key] = None
            else:
                self.models[key] = None

        self.is_fitted = True
        return self

    def predict(self, horizon_days: int) -> pd.DataFrame:
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before predict() is called.")

        predictions = []
        for key, model in self.models.items():
            if model is not None:
                try:
                    fc_vals = model.forecast(horizon_days)
                    fc_vals = np.maximum(0.0, np.round(fc_vals, 2))
                except Exception:
                    # Fallback to average of recent history
                    mean_val = float(np.mean(self.last_history[key]))
                    fc_vals = np.full(horizon_days, max(0.0, round(mean_val, 2)))
            else:
                mean_val = float(np.mean(self.last_history[key])) if len(self.last_history[key]) > 0 else 0.0
                fc_vals = np.full(horizon_days, max(0.0, round(mean_val, 2)))

            for h in range(1, horizon_days + 1):
                fc_date = self.last_date + timedelta(days=h)
                record = {col: key[i] for i, col in enumerate(self.entity_cols)}
                record.update({
                    "forecast_date": fc_date.strftime("%Y-%m-%d"),
                    "horizon_step": h,
                    "forecast": float(fc_vals[h - 1]),
                    "model_name": self.name,
                })
                predictions.append(record)

        return pd.DataFrame(predictions)
