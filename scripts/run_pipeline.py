"""
Master Orchestration Pipeline: Demand Forecasting & Inventory Optimization
Executes all stages from raw data ingestion through forecasting, backtesting,
inventory optimization, scenario analysis, Power BI tables, and visual charts.
"""

import sys
import time
from pathlib import Path
from typing import Any

# Ensure project root in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from src.data.generator import generate_retail_sales_data
from src.data.loader import process_and_save_dataset
from src.validation.quality import run_data_validation
from src.profiling.profile import run_demand_profiling
from src.sql.duckdb_engine import run_sql_analytics
from scripts.train_forecasts import run_forecasting_pipeline
from scripts.generate_inventory_plan import run_inventory_planning_pipeline
from src.powerbi_export import generate_powerbi_star_schema
from src.visualization import generate_all_charts
from src.utils.logger import logger


def run_full_pipeline() -> dict[str, Any]:
    """
    Executes the end-to-end demand forecasting and inventory optimization pipeline.
    """
    start_time = time.time()
    logger.info("=" * 80)
    logger.info("STARTING END-TO-END DEMAND FORECASTING & INVENTORY OPTIMIZATION PIPELINE")
    logger.info("=" * 80)

    # Stage 1: Data Ingestion & Generation
    logger.info("\n--- STAGE 1: Generating Raw Historical Sales Transactions ---")
    raw_sales_path = "data/raw/historical_sales.csv"
    if not (root_dir / raw_sales_path).exists():
        generate_retail_sales_data(output_path=raw_sales_path)
    else:
        logger.info("Raw sales dataset exists at %s", raw_sales_path)

    # Stage 2: Preprocessing & Complete Temporal Grid
    logger.info("\n--- STAGE 2: Constructing Complete Daily Grid & DuckDB Ingestion ---")
    grid_df, parquet_path, _ = process_and_save_dataset()

    # Stage 3: Data Quality Validation
    logger.info("\n--- STAGE 3: Executing Data Quality Integrity Suite ---")
    val_report = run_data_validation(grid_df)
    if val_report["overall_status"] != "PASSED":
        raise ValueError(f"Data quality checks failed: {val_report['checks']}")

    # Stage 4: Demand Profiling & Intermittency (Syntetos-Boylan)
    logger.info("\n--- STAGE 4: Profiling Demand Variability & Intermittency ---")
    prof_df = run_demand_profiling(grid_df)

    # Stage 5: DuckDB SQL Analytical Transformations & ABC-XYZ Matrix
    logger.info("\n--- STAGE 5: Running DuckDB SQL Analytical Transformations ---")
    sql_res = run_sql_analytics()

    # Stage 6: Rolling-Origin Backtesting & Champion Forecast Generation
    logger.info("\n--- STAGE 6: Model Training, Backtesting & Out-of-Sample Forecasting ---")
    fc_res = run_forecasting_pipeline()

    # Stage 7: Inventory Optimization & What-If Scenario Stress Testing
    logger.info("\n--- STAGE 7: Inventory Policy Optimization & Scenario Engine ---")
    inv_res = run_inventory_planning_pipeline()

    # Stage 8: Power BI Star Schema Tables Export
    logger.info("\n--- STAGE 8: Exporting Power BI Star Schema Tables ---")
    pbi_tables = generate_powerbi_star_schema()

    # Stage 9: Visual Charts Generation
    logger.info("\n--- STAGE 9: Generating Publication-Grade Visual Analytics ---")
    charts = generate_all_charts()

    elapsed = round(time.time() - start_time, 1)
    logger.info("=" * 80)
    logger.info("PIPELINE COMPLETED SUCCESSFULLY IN %.1f SECONDS!", elapsed)
    logger.info("Champion Model: %s (WAPE: %.2f%%)", fc_res["champion_model"], fc_res["champion_wape"])
    logger.info("Inventory Reorders: %d SKU-Locations ($%.2f PO Spend)",
                inv_res["reorder_triggered"], inv_res["total_recommended_order_value"])
    logger.info("Excess Capital Trapped: $%.2f across %d SKUs",
                inv_res["excess_capital"], inv_res["excess_inventory_count"])
    logger.info("=" * 80)

    return {
        "status": "SUCCESS",
        "elapsed_seconds": elapsed,
        "champion_model": fc_res["champion_model"],
        "champion_wape": fc_res["champion_wape"],
        "reorder_triggered": inv_res["reorder_triggered"],
        "total_recommended_order_value": inv_res["total_recommended_order_value"],
        "excess_capital": inv_res["excess_capital"],
    }


if __name__ == "__main__":
    run_full_pipeline()
