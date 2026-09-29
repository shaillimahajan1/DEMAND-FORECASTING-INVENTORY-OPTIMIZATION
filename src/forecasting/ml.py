"""
Machine Learning Global Forecasting Model using LightGBM
Features: Lags, Rolling Window Statistics, Calendar Effects, Merchandising Attributes,
and Exogenous Pricing/Promotions. Strictly prevents future leakage via lagged rollups.
"""

from datetime import timedelta
from pathlib import Path
from typing import Any
import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd
from src.forecasting.base import BaseForecaster
from src.utils.logger import logger
from src.utils.helpers import get_project_root, ensure_directory


class LightGBMForecaster(BaseForecaster):
    """
    Global LightGBM Regressor trained across all SKUs and store locations.
    Leverages cross-series learning while preserving granular item-location distinctions.
    """

    def __init__(
        self,
        name: str = "LightGBM",
        params: dict[str, Any] | None = None,
    ):
        super().__init__(name=name)
        default_params = {
            "objective": "regression",
            "metric": "rmse",
            "boosting_type": "gbdt",
            "n_estimators": 250,
            "learning_rate": 0.05,
            "num_leaves": 31,
            "min_child_samples": 20,
            "subsample": 0.85,
            "colsample_bytree": 0.85,
            "random_state": 42,
            "verbose": -1,
            "n_jobs": -1,
        }
        if params:
            default_params.update(params)
        self.params = default_params
        self.model: lgb.LGBMRegressor | None = None
        self.feature_names: list[str] = []
        self.categorical_features: list[str] = ["store_id", "sku_id", "category"]
        self.entity_cols = ["store_id", "sku_id"]
        self.meta_lookup: dict[tuple, dict[str, Any]] = {}
        self.history_buffers: dict[tuple, list[float]] = {}
        self.last_date: pd.Timestamp | None = None

    def _extract_calendar_features(self, dates: pd.Series) -> pd.DataFrame:
        """Extract temporal calendar features."""
        dt = pd.to_datetime(dates)
        return pd.DataFrame({
            "day_of_week": dt.dt.dayofweek.astype("int8"),
            "day_of_month": dt.dt.day.astype("int8"),
            "month": dt.dt.month.astype("int8"),
            "is_weekend": (dt.dt.dayofweek >= 5).astype("int8"),
            "day_of_year": dt.dt.dayofyear.astype("int16"),
        }, index=dates.index)

    def build_features(self, df: pd.DataFrame, target_col: str = "quantity", is_training: bool = True) -> pd.DataFrame:
        """
        Build leak-free feature matrix from historical panel data.
        Rolling statistics are shifted by 1 to strictly utilize past information.
        """
        data = df.sort_values(by=["store_id", "sku_id", "date"]).copy()
        if not pd.api.types.is_datetime64_any_dtype(data["date"]):
            data["date"] = pd.to_datetime(data["date"])

        # Grouped lags (t-1, t-7, t-14, t-21, t-28)
        grouped_target = data.groupby(self.entity_cols, observed=True)[target_col]
        data["lag_1"] = grouped_target.shift(1)
        data["lag_7"] = grouped_target.shift(7)
        data["lag_14"] = grouped_target.shift(14)
        data["lag_21"] = grouped_target.shift(21)
        data["lag_28"] = grouped_target.shift(28)

        # Shifted rolling statistics (t-1 window)
        shifted = grouped_target.shift(1)
        data["rolling_mean_7d"] = shifted.groupby(data[self.entity_cols].apply(tuple, axis=1)).rolling(7, min_periods=3).mean().values
        data["rolling_std_7d"] = shifted.groupby(data[self.entity_cols].apply(tuple, axis=1)).rolling(7, min_periods=3).std().values
        data["rolling_mean_14d"] = shifted.groupby(data[self.entity_cols].apply(tuple, axis=1)).rolling(14, min_periods=5).mean().values
        data["rolling_mean_28d"] = shifted.groupby(data[self.entity_cols].apply(tuple, axis=1)).rolling(28, min_periods=7).mean().values

        # Calendar features
        cal_df = self._extract_calendar_features(data["date"])
        for col in cal_df.columns:
            data[col] = cal_df[col]

        # Categorical encodings
        for cat_col in self.categorical_features:
            if cat_col in data.columns:
                data[cat_col] = data[cat_col].astype("category")

        # Exogenous features
        if "unit_price" not in data.columns:
            data["unit_price"] = 25.0
        if "promotion_flag" not in data.columns:
            data["promotion_flag"] = 0

        # During training, drop warm-up rows containing NaNs in lag_28
        if is_training:
            data = data.dropna(subset=["lag_28", "rolling_mean_28d"]).reset_index(drop=True)

        return data

    def fit(
        self,
        df: pd.DataFrame,
        target_col: str = "quantity",
        date_col: str = "date",
        entity_cols: list[str] | None = None,
    ) -> "LightGBMForecaster":
        self.entity_cols = entity_cols or ["store_id", "sku_id"]
        working_df = df.copy()
        if not pd.api.types.is_datetime64_any_dtype(working_df[date_col]):
            working_df[date_col] = pd.to_datetime(working_df[date_col])

        self.last_date = working_df[date_col].max()

        # Build metadata and history buffer for recursive out-of-sample simulation
        self.meta_lookup.clear()
        self.history_buffers.clear()

        sorted_df = working_df.sort_values(by=date_col)
        for key, group in sorted_df.groupby(self.entity_cols, observed=True):
            last_row = group.iloc[-1]
            self.meta_lookup[key] = {
                "category": last_row.get("category", "General"),
                "unit_price": float(last_row.get("unit_price", 25.0)),
                "unit_cost": float(last_row.get("unit_cost", 10.0)),
            }
            # Keep last 60 days of history for rolling features
            self.history_buffers[key] = group[target_col].tail(60).values.tolist()

        logger.info("Constructing feature matrix for LightGBM training...")
        feat_df = self.build_features(working_df, target_col=target_col, is_training=True)

        self.feature_names = [
            "lag_1", "lag_7", "lag_14", "lag_21", "lag_28",
            "rolling_mean_7d", "rolling_std_7d", "rolling_mean_14d", "rolling_mean_28d",
            "day_of_week", "day_of_month", "month", "is_weekend", "day_of_year",
            "unit_price", "promotion_flag",
            *self.categorical_features,
        ]
        # Keep only existing features
        self.feature_names = [f for f in self.feature_names if f in feat_df.columns]

        X_train = feat_df[self.feature_names]
        y_train = feat_df[target_col].values

        logger.info("Fitting LightGBM model on %d rows and %d features...", len(X_train), len(self.feature_names))
        self.model = lgb.LGBMRegressor(**self.params)
        self.model.fit(X_train, y_train)

        self.is_fitted = True
        return self

    def predict(self, horizon_days: int) -> pd.DataFrame:
        """
        Generate multi-step forecasts using sequential recursive rollout.
        Updates lags and rolling statistics step-by-step from previous predictions.
        """
        if not self.is_fitted or self.model is None:
            raise RuntimeError("Model must be fitted before predict() is called.")

        predictions = []
        # Clone history buffer for rollout simulation
        sim_buffers = {k: list(v) for k, v in self.history_buffers.items()}

        for h in range(1, horizon_days + 1):
            fc_date = self.last_date + timedelta(days=h)
            dt = pd.to_datetime(fc_date)
            step_rows = []
            keys_in_step = []

            for key, buf in sim_buffers.items():
                store_id, sku_id = key
                meta = self.meta_lookup[key]

                # Lag features from buffer
                l1 = buf[-1] if len(buf) >= 1 else 0.0
                l7 = buf[-7] if len(buf) >= 7 else l1
                l14 = buf[-14] if len(buf) >= 14 else l7
                l21 = buf[-21] if len(buf) >= 21 else l14
                l28 = buf[-28] if len(buf) >= 28 else l21

                # Rolling stats
                r7 = buf[-7:] if len(buf) >= 7 else buf
                r14 = buf[-14:] if len(buf) >= 14 else buf
                r28 = buf[-28:] if len(buf) >= 28 else buf

                rm7 = float(np.mean(r7))
                rs7 = float(np.std(r7)) if len(r7) > 1 else 0.0
                rm14 = float(np.mean(r14))
                rm28 = float(np.mean(r28))

                row = {
                    "store_id": store_id,
                    "sku_id": sku_id,
                    "category": meta["category"],
                    "lag_1": l1,
                    "lag_7": l7,
                    "lag_14": l14,
                    "lag_21": l21,
                    "lag_28": l28,
                    "rolling_mean_7d": rm7,
                    "rolling_std_7d": rs7,
                    "rolling_mean_14d": rm14,
                    "rolling_mean_28d": rm28,
                    "day_of_week": dt.dayofweek,
                    "day_of_month": dt.day,
                    "month": dt.month,
                    "is_weekend": 1 if dt.dayofweek >= 5 else 0,
                    "day_of_year": dt.dayofyear,
                    "unit_price": meta["unit_price"],
                    "promotion_flag": 0,
                }
                step_rows.append(row)
                keys_in_step.append(key)

            step_df = pd.DataFrame(step_rows)
            for c in self.categorical_features:
                if c in step_df.columns:
                    step_df[c] = step_df[c].astype("category")

            X_step = step_df[self.feature_names]
            step_preds = self.model.predict(X_step)
            step_preds = np.maximum(0.0, np.round(step_preds, 2))

            for i, key in enumerate(keys_in_step):
                val = float(step_preds[i])
                sim_buffers[key].append(val)

                predictions.append({
                    "store_id": key[0],
                    "sku_id": key[1],
                    "forecast_date": fc_date.strftime("%Y-%m-%d"),
                    "horizon_step": h,
                    "forecast": val,
                    "model_name": self.name,
                })

        return pd.DataFrame(predictions)

    def get_feature_importances(self) -> pd.DataFrame:
        """Return feature importance ranking."""
        if not self.is_fitted or self.model is None:
            raise RuntimeError("Model is not fitted.")
        imp = self.model.feature_importances_
        df = pd.DataFrame({"feature": self.feature_names, "importance": imp})
        return df.sort_values(by="importance", ascending=False).reset_index(drop=True)

    def save(self, filepath: str | Path) -> None:
        """Serialize model and metadata to disk."""
        path = Path(filepath)
        ensure_directory(path.parent)
        payload = {
            "model": self.model,
            "feature_names": self.feature_names,
            "params": self.params,
            "meta_lookup": self.meta_lookup,
            "history_buffers": self.history_buffers,
            "last_date": self.last_date,
        }
        joblib.dump(payload, path)
        logger.info("Saved serialized LightGBM model to: %s", path)

    @classmethod
    def load(cls, filepath: str | Path) -> "LightGBMForecaster":
        """Load serialized model."""
        payload = joblib.load(filepath)
        forecaster = cls(name="LightGBM", params=payload["params"])
        forecaster.model = payload["model"]
        forecaster.feature_names = payload["feature_names"]
        forecaster.meta_lookup = payload["meta_lookup"]
        forecaster.history_buffers = payload["history_buffers"]
        forecaster.last_date = payload["last_date"]
        forecaster.is_fitted = True
        return forecaster
