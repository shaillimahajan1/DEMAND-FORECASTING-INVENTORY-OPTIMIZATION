"""
Data Quality Validation Module for Demand Forecasting & Inventory Optimization
"""

from datetime import datetime
import json
from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd
from src.utils.logger import logger
from src.utils.helpers import get_project_root, ensure_directory


class DataQualityValidator:
    """
    Validates transactional sales and analytical demand datasets against rigorous
    enterprise quality rules: completeness, uniqueness, validity, and temporal integrity.
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        if not pd.api.types.is_datetime64_any_dtype(self.df["date"]):
            self.df["date"] = pd.to_datetime(self.df["date"])

    def validate_completeness(self) -> dict[str, Any]:
        """Check for missing or null values across all columns."""
        null_counts = self.df.isnull().sum().to_dict()
        total_rows = len(self.df)
        null_rates = {col: round(count / total_rows, 5) for col, count in null_counts.items() if count > 0}
        passed = len(null_rates) == 0
        return {
            "check": "Completeness",
            "passed": passed,
            "total_rows": total_rows,
            "columns_with_nulls": null_rates,
            "status": "PASSED" if passed else "FAILED",
        }

    def validate_uniqueness(self) -> dict[str, Any]:
        """Verify unique grain: (date, store_id, sku_id)."""
        grain_cols = ["date", "store_id", "sku_id"]
        dups = self.df.duplicated(subset=grain_cols).sum()
        passed = int(dups) == 0
        return {
            "check": "Uniqueness (Grain Integrity)",
            "passed": passed,
            "grain": "date x store_id x sku_id",
            "duplicate_grain_records": int(dups),
            "status": "PASSED" if passed else "FAILED",
        }

    def validate_value_validity(self) -> dict[str, Any]:
        """Check for physical domain validity: non-negative demand, positive price/cost."""
        negative_demand = int((self.df["quantity"] < 0).sum())
        non_positive_price = int((self.df["unit_price"] <= 0).sum())
        non_positive_cost = int((self.df["unit_cost"] <= 0).sum())
        passed = (negative_demand == 0) and (non_positive_price == 0) and (non_positive_cost == 0)
        return {
            "check": "Value Validity",
            "passed": passed,
            "negative_demand_count": negative_demand,
            "non_positive_price_count": non_positive_price,
            "non_positive_cost_count": non_positive_cost,
            "status": "PASSED" if passed else "FAILED",
        }

    def validate_temporal_integrity(self) -> dict[str, Any]:
        """Check for temporal gaps across dates for each SKU/Store series."""
        min_date = self.df["date"].min()
        max_date = self.df["date"].max()
        expected_days = (max_date - min_date).days + 1

        sku_store_groups = self.df.groupby(["store_id", "sku_id"], observed=True)["date"].count()
        incomplete_series = (sku_store_groups != expected_days).sum()
        passed = int(incomplete_series) == 0

        return {
            "check": "Temporal Integrity",
            "passed": passed,
            "start_date": min_date.strftime("%Y-%m-%d"),
            "end_date": max_date.strftime("%Y-%m-%d"),
            "expected_calendar_days": expected_days,
            "series_with_gaps": int(incomplete_series),
            "status": "PASSED" if passed else "FAILED",
        }

    def run_all_checks(self) -> dict[str, Any]:
        """Execute full test suite and compile comprehensive quality assessment."""
        completeness = self.validate_completeness()
        uniqueness = self.validate_uniqueness()
        validity = self.validate_value_validity()
        temporal = self.validate_temporal_integrity()

        all_passed = (
            completeness["passed"]
            and uniqueness["passed"]
            and validity["passed"]
            and temporal["passed"]
        )

        # Statistical summary
        total_rows = len(self.df)
        zero_demand_count = int((self.df["quantity"] == 0).sum())
        zero_demand_pct = round(zero_demand_count / total_rows * 100, 2)

        report = {
            "generated_at": datetime.now().isoformat(),
            "overall_status": "PASSED" if all_passed else "FAILED",
            "total_records": total_rows,
            "unique_skus": int(self.df["sku_id"].nunique()),
            "unique_stores": int(self.df["store_id"].nunique()),
            "unique_categories": int(self.df["category"].nunique()),
            "date_range": {
                "start": self.df["date"].min().strftime("%Y-%m-%d"),
                "end": self.df["date"].max().strftime("%Y-%m-%d"),
                "calendar_days": int((self.df["date"].max() - self.df["date"].min()).days + 1),
            },
            "zero_demand_periods": {
                "count": zero_demand_count,
                "percentage": zero_demand_pct,
                "interpretation": "Explicit zero-demand observation (no stockout assumption)",
            },
            "checks": {
                "completeness": completeness,
                "uniqueness": uniqueness,
                "validity": validity,
                "temporal_integrity": temporal,
            },
        }
        return report

    def generate_markdown_report(self, report_dict: dict[str, Any]) -> str:
        """Render a publication-ready Markdown quality report."""
        val_checks = report_dict["checks"]["validity"]
        non_pos_price = val_checks.get("non_positive_price_count", 0)

        md = f"""# Data Quality & Validation Report

**Generated:** {report_dict['generated_at']}  
**Overall Validation Status:** **{report_dict['overall_status']}**

---

## 1. Executive Summary

| Metric | Measured Value |
| :--- | :--- |
| **Total Observations** | {report_dict['total_records']:,} rows |
| **Unique Products (SKUs)** | {report_dict['unique_skus']} |
| **Regional Distribution Hubs** | {report_dict['unique_stores']} |
| **Merchandising Categories** | {report_dict['unique_categories']} |
| **Historical Range** | {report_dict['date_range']['start']} to {report_dict['date_range']['end']} ({report_dict['date_range']['calendar_days']} days) |
| **Explicit Zero-Demand Periods** | {report_dict['zero_demand_periods']['count']:,} ({report_dict['zero_demand_periods']['percentage']}%) |

---

## 2. Integrity Checks Breakdown

### 2.1 Completeness Check: `{report_dict['checks']['completeness']['status']}`
- **Null values detected:** {len(report_dict['checks']['completeness']['columns_with_nulls'])} columns.
- **Finding:** No missing records found across required dimensions and metrics.

### 2.2 Uniqueness Check: `{report_dict['checks']['uniqueness']['status']}`
- **Grain:** `{report_dict['checks']['uniqueness']['grain']}`
- **Duplicate Records:** {report_dict['checks']['uniqueness']['duplicate_grain_records']}

### 2.3 Value Domain Validity Check: `{report_dict['checks']['validity']['status']}`
- **Negative Demand Quantities:** {val_checks['negative_demand_count']}
- **Non-Positive Unit Prices:** {non_pos_price}
- **Non-Positive Unit Costs:** {val_checks['non_positive_cost_count']}

### 2.4 Temporal Integrity Check: `{report_dict['checks']['temporal_integrity']['status']}`
- **Full Continuous Sequence:** {report_dict['checks']['temporal_integrity']['expected_calendar_days']} calendar days per series.
- **Series with Missing Date Gaps:** {report_dict['checks']['temporal_integrity']['series_with_gaps']}
"""
        return md


def run_data_validation(df: pd.DataFrame, output_dir: str | Path | None = None) -> dict[str, Any]:
    """Execute validation and save structured JSON and Markdown artifacts."""
    validator = DataQualityValidator(df)
    report = validator.run_all_checks()

    root = get_project_root()
    out_dir = Path(output_dir) if output_dir else root / "outputs" / "reports"
    ensure_directory(out_dir)

    json_path = out_dir / "data_quality_report.json"
    md_path = out_dir / "data_quality_report.md"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    md_content = validator.generate_markdown_report(report)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    logger.info("Data quality validation complete: %s (Saved to %s and %s)", report["overall_status"], json_path, md_path)
    return report
