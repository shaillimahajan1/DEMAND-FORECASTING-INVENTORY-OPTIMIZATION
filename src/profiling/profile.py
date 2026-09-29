"""
Demand Profiling & Time Series Segmentation Module
Classifies SKUs by demand variability, intermittency (Syntetos-Boylan framework), and trend.
"""

from pathlib import Path
import numpy as np
import pandas as pd
from src.utils.logger import logger
from src.utils.helpers import get_project_root, ensure_directory


class DemandProfiler:
    """
    Computes statistical demand profiles, intermittency indices (ADI),
    demand variability (CV, CV^2), and segments products operationally.
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        if not pd.api.types.is_datetime64_any_dtype(self.df["date"]):
            self.df["date"] = pd.to_datetime(self.df["date"])

    def profile_skus(self) -> pd.DataFrame:
        """
        Compute SKU-level summary demand metrics aggregated across locations.
        """
        logger.info("Profiling demand characteristics across SKUs...")
        records = []

        for sku_id, group in self.df.groupby("sku_id", observed=True):
            sku_name = group["sku_name"].iloc[0]
            category = group["category"].iloc[0]
            unit_price = float(group["unit_price"].mean())
            unit_cost = float(group["unit_cost"].iloc[0])

            # Demand series
            daily_demand = group.groupby("date")["quantity"].sum()
            n_obs = len(daily_demand)
            total_qty = int(daily_demand.sum())
            mean_demand = float(daily_demand.mean())
            std_demand = float(daily_demand.std())
            cv = std_demand / mean_demand if mean_demand > 0 else 0.0
            cv2 = cv ** 2

            # Intermittency metrics: Average Demand Interval (ADI)
            non_zero_days = daily_demand[daily_demand > 0]
            n_non_zero = len(non_zero_days)
            zero_days = n_obs - n_non_zero
            zero_pct = round(zero_days / n_obs * 100, 2)
            adi = n_obs / n_non_zero if n_non_zero > 0 else float("inf")

            # Syntetos-Boylan classification:
            # Cutoffs: ADI = 1.32, CV^2 = 0.49
            if adi < 1.32 and cv2 < 0.49:
                sb_category = "Smooth"
            elif adi >= 1.32 and cv2 < 0.49:
                sb_category = "Intermittent"
            elif adi < 1.32 and cv2 >= 0.49:
                sb_category = "Erratic"
            else:
                sb_category = "Lumpy"

            # Trend estimation: Ordinary Least Squares slope over time
            x = np.arange(n_obs)
            slope, _ = np.polyfit(x, daily_demand.values, 1)
            annual_trend_pct = round((slope * 365 / mean_demand) * 100, 2) if mean_demand > 0 else 0.0

            # Operational demand segment
            if adi >= 1.32 or zero_pct > 35:
                operational_segment = "Intermittent"
            elif annual_trend_pct > 15:
                operational_segment = "Growing"
            elif annual_trend_pct < -15:
                operational_segment = "Declining"
            elif cv > 0.50:
                operational_segment = "Volatile"
            elif cv < 0.30:
                operational_segment = "Stable"
            else:
                operational_segment = "Seasonal"

            total_revenue = float(group["revenue"].sum())
            total_margin = float(group["gross_margin"].sum())

            records.append({
                "sku_id": sku_id,
                "sku_name": sku_name,
                "category": category,
                "unit_price": round(unit_price, 2),
                "unit_cost": round(unit_cost, 2),
                "total_demand": total_qty,
                "total_revenue": round(total_revenue, 2),
                "total_margin": round(total_margin, 2),
                "mean_daily_demand": round(mean_demand, 2),
                "std_daily_demand": round(std_demand, 2),
                "cv": round(cv, 3),
                "cv2": round(cv2, 3),
                "adi": round(adi, 2),
                "zero_demand_pct": zero_pct,
                "annual_trend_pct": annual_trend_pct,
                "syntetos_boylan_class": sb_category,
                "operational_segment": operational_segment,
            })

        profile_df = pd.DataFrame(records).sort_values(by="total_revenue", ascending=False).reset_index(drop=True)
        return profile_df


def run_demand_profiling(df: pd.DataFrame, output_dir: str | Path | None = None) -> pd.DataFrame:
    """Execute profiling and write results to CSV."""
    profiler = DemandProfiler(df)
    profile_df = profiler.profile_skus()

    root = get_project_root()
    out_dir = Path(output_dir) if output_dir else root / "outputs" / "reports"
    ensure_directory(out_dir)

    out_csv = out_dir / "demand_profiling_summary.csv"
    profile_df.to_csv(out_csv, index=False)
    logger.info("Saved SKU demand profiling summary to: %s", out_csv)
    return profile_df
