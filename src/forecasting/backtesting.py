"""
Rolling-Origin Time Series Backtesting Framework
Evaluates candidate models across multiple temporal origins without future data leakage.
"""

from datetime import timedelta
from typing import Any
import pandas as pd
from src.forecasting.base import BaseForecaster
from src.utils.logger import logger


class RollingOriginBacktester:
    """
    Executes expanding-window / rolling-origin time-series cross-validation.
    Ensures zero temporal leakage by training strictly on observations prior to each origin date.
    """

    def __init__(
        self,
        horizon_days: int = 28,
        n_splits: int = 3,
        step_days: int = 28,
        date_col: str = "date",
        target_col: str = "quantity",
        entity_cols: list[str] | None = None,
    ):
        self.horizon_days = horizon_days
        self.n_splits = n_splits
        self.step_days = step_days
        self.date_col = date_col
        self.target_col = target_col
        self.entity_cols = entity_cols or ["store_id", "sku_id"]

    def generate_origins(self, max_date: pd.Timestamp) -> list[pd.Timestamp]:
        """
        Generate chronological cutoff origin timestamps.
        Example for 3 splits with 28-day horizon:
        Origin 1: T - 3*28 days
        Origin 2: T - 2*28 days
        Origin 3: T - 1*28 days
        """
        origins = []
        for i in range(self.n_splits, 0, -1):
            origin = max_date - timedelta(days=i * self.step_days)
            origins.append(origin)
        return origins

    def run_backtest(
        self,
        df: pd.DataFrame,
        models: list[BaseForecaster],
    ) -> pd.DataFrame:
        """
        Run backtesting across all models and origins.
        Returns detailed predictions DataFrame.
        """
        working_df = df.copy()
        if not pd.api.types.is_datetime64_any_dtype(working_df[self.date_col]):
            working_df[self.date_col] = pd.to_datetime(working_df[self.date_col])

        max_date = working_df[self.date_col].max()
        origins = self.generate_origins(max_date)

        logger.info(
            "Initiating backtesting: %d origins, horizon = %d days, models = %s",
            len(origins),
            self.horizon_days,
            [m.get_model_name() for m in models],
        )

        all_predictions = []

        for split_idx, origin in enumerate(origins, 1):
            origin_str = origin.strftime("%Y-%m-%d")
            logger.info("Evaluating Origin %d/%d: %s", split_idx, len(origins), origin_str)

            # Training set: strictly observations <= origin
            train_mask = working_df[self.date_col] <= origin
            train_df = working_df[train_mask].copy()

            # Test set: observations > origin and <= origin + horizon
            test_end = origin + timedelta(days=self.horizon_days)
            test_mask = (working_df[self.date_col] > origin) & (working_df[self.date_col] <= test_end)
            test_df = working_df[test_mask].copy()

            # Prepare ground truth actuals lookup
            test_df["date_str"] = test_df[self.date_col].dt.strftime("%Y-%m-%d")
            actuals_map = test_df.set_index([*self.entity_cols, "date_str"])[self.target_col].to_dict()

            for model in models:
                model_name = model.get_model_name()
                logger.info("  Fitting and forecasting: %s", model_name)

                # Fit on historical slice only
                model.fit(
                    train_df,
                    target_col=self.target_col,
                    date_col=self.date_col,
                    entity_cols=self.entity_cols,
                )

                # Generate out-of-sample forecast
                preds = model.predict(horizon_days=self.horizon_days)
                preds["forecast_origin"] = origin_str
                preds["split_index"] = split_idx

                # Attach actuals and calculate point errors
                pred_records = preds.to_dict(orient="records")
                for rec in pred_records:
                    key = tuple(rec[c] for c in self.entity_cols) + (rec["forecast_date"],)
                    act = float(actuals_map.get(key, 0.0))
                    fc = float(rec["forecast"])
                    err = fc - act
                    abs_err = abs(err)
                    pct_err = (abs_err / act * 100.0) if act > 0 else 0.0

                    rec["actual"] = act
                    rec["forecast"] = round(fc, 2)
                    rec["error"] = round(err, 2)
                    rec["absolute_error"] = round(abs_err, 2)
                    rec["percentage_error"] = round(pct_err, 2)
                    all_predictions.append(rec)

        results_df = pd.DataFrame(all_predictions)
        logger.info("Backtesting complete: %d total evaluation points collected.", len(results_df))
        return results_df
