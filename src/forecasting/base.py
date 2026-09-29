"""
Base Interface for Time-Series Forecasting Models
"""

from abc import ABC, abstractmethod
import pandas as pd


class BaseForecaster(ABC):
    """Abstract base class for all baseline, statistical, and ML forecasting models."""

    def __init__(self, name: str):
        self.name = name
        self.is_fitted = False

    @abstractmethod
    def fit(
        self,
        df: pd.DataFrame,
        target_col: str = "quantity",
        date_col: str = "date",
        entity_cols: list[str] | None = None,
    ) -> "BaseForecaster":
        """Fit the forecasting model on historical training data."""
        pass

    @abstractmethod
    def predict(self, horizon_days: int) -> pd.DataFrame:
        """
        Generate out-of-sample demand forecast for the specified horizon.
        Returns a DataFrame containing entity_cols, forecast_date, horizon_step, and forecast.
        """
        pass

    def get_model_name(self) -> str:
        """Return the descriptive model identifier."""
        return self.name
