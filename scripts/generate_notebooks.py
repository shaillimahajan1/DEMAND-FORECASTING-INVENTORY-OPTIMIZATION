"""
Jupyter Notebooks Generator for Demand Forecasting & Inventory Optimization
Creates standard, clean, runnable .ipynb files in notebooks/
"""

import json
from pathlib import Path


def make_notebook(cells: list[dict]) -> dict:
    return {
        "cells": cells,
        "metadata": {
            "language_info": {
                "name": "python",
                "version": "3.11"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def md_cell(source: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in source.split("\n")],
    }


def code_cell(source: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line + "\n" for line in source.split("\n")],
    }


def generate_all_notebooks():
    nb_dir = Path("notebooks")
    nb_dir.mkdir(parents=True, exist_ok=True)

    # 1. 01_data_quality.ipynb
    nb1 = make_notebook([
        md_cell("# 01 - Data Ingestion, Integrity & Quality Validation\n\nThis notebook loads raw transactions, inspects data types, and validates the complete temporal grid."),
        code_cell("import pandas as pd\nfrom src.data.loader import load_raw_sales, ensure_complete_temporal_grid\nfrom src.validation.quality import DataQualityValidator\n\ndf_raw = load_raw_sales()\nprint(f'Loaded {len(df_raw)} records.')\ndf_raw.head()"),
        code_cell("grid_df = ensure_complete_temporal_grid(df_raw)\nvalidator = DataQualityValidator(grid_df)\nreport = validator.run_all_checks()\nprint('Validation Status:', report['overall_status'])\nreport['checks']"),
    ])
    with open(nb_dir / "01_data_quality.ipynb", "w", encoding="utf-8") as f:
        json.dump(nb1, f, indent=2)

    # 2. 02_demand_analysis.ipynb
    nb2 = make_notebook([
        md_cell("# 02 - Demand Analytics, Profiling & ABC-XYZ Segmentation\n\nAnalyzes demand variability, intermittency (Syntetos-Boylan), and generates the 9-box ABC-XYZ portfolio matrix."),
        code_cell("import pandas as pd\nfrom src.profiling.profile import run_demand_profiling\nfrom src.sql.duckdb_engine import DuckDBAnalyticsEngine\n\ndf = pd.read_parquet('data/processed/demand_daily.parquet')\nprofile_df = run_demand_profiling(df)\nprofile_df.head(10)"),
        code_cell("engine = DuckDBAnalyticsEngine()\nabc_xyz = engine.query('SELECT * FROM dim_abc_xyz_segmentation LIMIT 15')\nengine.close()\nabc_xyz"),
    ])
    with open(nb_dir / "02_demand_analysis.ipynb", "w", encoding="utf-8") as f:
        json.dump(nb2, f, indent=2)

    # 3. 03_forecasting.ipynb
    nb3 = make_notebook([
        md_cell("# 03 - Demand Forecasting: Baselines, Holt-Winters & LightGBM\n\nDemonstrates baseline models and fits the champion forecaster with prediction intervals."),
        code_cell("import pandas as pd\nimport matplotlib.pyplot as plt\nfrom src.forecasting.baselines import MovingAverageForecaster\nfrom src.forecasting.statistical import HoltWintersForecaster\n\ndf = pd.read_parquet('data/processed/demand_daily.parquet')\nfinal_fc = pd.read_csv('outputs/forecasts/final_forecasts.csv')\nfinal_fc.head(10)"),
        code_cell("# Visualize sample SKU forecast\nsample = final_fc[(final_fc['sku_id'] == 'SKU-ELEC-001') & (final_fc['store_id'] == 'FC-East')]\nplt.figure(figsize=(10, 4))\nplt.plot(pd.to_datetime(sample['forecast_date']), sample['forecast'], label='Forecast', color='orange')\nplt.fill_between(pd.to_datetime(sample['forecast_date']), sample['lower_bound'], sample['upper_bound'], color='orange', alpha=0.3, label='95% PI')\nplt.title('SKU-ELEC-001 Forecast Trajectory (FC-East)')\nplt.legend()\nplt.show()"),
    ])
    with open(nb_dir / "03_forecasting.ipynb", "w", encoding="utf-8") as f:
        json.dump(nb3, f, indent=2)

    # 4. 04_backtesting.ipynb
    nb4 = make_notebook([
        md_cell("# 04 - Expanding-Window Rolling-Origin Backtesting & Model Evaluation\n\nCompares candidate models across 3 historical origins to select the champion model."),
        code_cell("import pandas as pd\n\nmc = pd.read_csv('outputs/metrics/model_comparison.csv')\nmc"),
        code_cell("bt = pd.read_csv('outputs/forecasts/backtest_predictions.csv')\nprint(f'Total backtest evaluation points: {len(bt)}')\nbt.groupby('model_name')[['absolute_error', 'actual', 'forecast']].mean()"),
    ])
    with open(nb_dir / "04_backtesting.ipynb", "w", encoding="utf-8") as f:
        json.dump(nb4, f, indent=2)

    # 5. 05_inventory_optimization.ipynb
    nb5 = make_notebook([
        md_cell("# 05 - Inventory Optimization, Replenishment Decisions & What-If Scenarios\n\nTranslates forecasts into safety stock buffers, reorder points, stockout risk tiers, and what-if stress tests."),
        code_cell("import pandas as pd\n\nplan_df = pd.read_csv('outputs/inventory/inventory_recommendations.csv')\nprint(f'Total SKU-Locations: {len(plan_df)}')\nplan_df[['sku_id', 'sku_name', 'avg_daily_demand', 'safety_stock', 'reorder_point', 'current_inventory_position', 'recommended_order_qty', 'stockout_risk_level', 'priority_tier']].head(10)"),
        code_cell("scen_df = pd.read_csv('outputs/scenarios/scenario_comparison_results.csv')\nscen_df"),
    ])
    with open(nb_dir / "05_inventory_optimization.ipynb", "w", encoding="utf-8") as f:
        json.dump(nb5, f, indent=2)

    print("All 5 Jupyter notebooks generated successfully in notebooks/")


if __name__ == "__main__":
    generate_all_notebooks()
