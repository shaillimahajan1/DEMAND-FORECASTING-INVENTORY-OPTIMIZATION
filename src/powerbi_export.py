"""
Power BI Star Schema Dataset Exporter
Generates clean dimension and fact tables in outputs/powerbi/ for direct Power BI ingestion.
"""

from pathlib import Path
import pandas as pd
from src.utils.logger import logger
from src.utils.helpers import get_project_root, ensure_directory


def generate_powerbi_star_schema() -> dict[str, str]:
    """
    Builds and exports star-schema dimensional model:
    - dim_date
    - dim_product
    - dim_store
    - fact_daily_demand
    - fact_forecast
    - fact_inventory_plan
    - fact_scenario
    """
    root = get_project_root()
    pbi_dir = ensure_directory(root / "outputs" / "powerbi")
    data_path = root / "data" / "processed" / "demand_daily.parquet"
    fc_path = root / "outputs" / "forecasts" / "final_forecasts.csv"
    plan_path = root / "outputs" / "inventory" / "inventory_recommendations.csv"
    scen_path = root / "outputs" / "scenarios" / "scenario_detailed_sku_impact.csv"

    if not data_path.exists() or not fc_path.exists() or not plan_path.exists():
        raise FileNotFoundError("Prerequisite analytical outputs not found. Ensure forecasting and inventory pipelines have completed.")

    logger.info("Building Power BI Star Schema tables...")
    demand_df = pd.read_parquet(data_path)
    fc_df = pd.read_csv(fc_path)
    plan_df = pd.read_csv(plan_path)
    scen_df = pd.read_csv(scen_path) if scen_path.exists() else pd.DataFrame()

    # --- 1. dim_date ---
    min_date = demand_df["date"].min()
    max_date = pd.to_datetime(fc_df["forecast_date"].max())
    all_dates = pd.date_range(min_date, max_date, freq="D")

    dim_date = pd.DataFrame({
        "date_key": all_dates.strftime("%Y%m%d").astype(int),
        "date": all_dates.strftime("%Y-%m-%d"),
        "year": all_dates.year,
        "quarter": "Q" + all_dates.quarter.astype(str),
        "month_number": all_dates.month,
        "month_name": all_dates.strftime("%B"),
        "month_year": all_dates.strftime("%b %Y"),
        "week_of_year": all_dates.isocalendar().week,
        "day_of_month": all_dates.day,
        "day_of_week_num": all_dates.dayofweek + 1,  # 1=Monday, 7=Sunday
        "day_of_week_name": all_dates.strftime("%A"),
        "is_weekend": (all_dates.dayofweek >= 5).astype(int),
    })

    # --- 2. dim_product ---
    # Merge ABC-XYZ segment if in plan_df
    prod_cols = ["sku_id", "sku_name", "category", "sub_category", "unit_price", "unit_cost"]
    dim_product = demand_df[prod_cols].drop_duplicates(subset=["sku_id"]).copy()
    if "abc_xyz_segment" in plan_df.columns:
        abc_sub = plan_df[["sku_id", "abc_class", "xyz_class", "abc_xyz_segment"]].drop_duplicates()
        dim_product = dim_product.merge(abc_sub, on="sku_id", how="left")
    dim_product["gross_margin_pct"] = (
        (dim_product["unit_price"] - dim_product["unit_cost"]) / dim_product["unit_price"] * 100
    ).round(2)

    # --- 3. dim_store ---
    store_cols = ["store_id", "store_name"]
    dim_store = demand_df[store_cols].drop_duplicates().copy()
    # Add geographical/regional enrichment
    region_map = {
        "FC-East": ("East", "New York", "Northeast"),
        "FC-West": ("West", "California", "Pacific"),
        "FC-Central": ("Central", "Illinois", "Midwest"),
    }
    dim_store["region"] = dim_store["store_id"].map(lambda s: region_map.get(s, ("General", "US", "National"))[0])
    dim_store["state"] = dim_store["store_id"].map(lambda s: region_map.get(s, ("General", "US", "National"))[1])
    dim_store["hub_tier"] = "Tier-1 Primary Fulfillment Hub"

    # --- 4. fact_daily_demand ---
    fact_daily_demand = demand_df[[
        "date", "store_id", "sku_id", "quantity", "unit_price", "unit_cost", "revenue", "gross_margin", "promotion_flag"
    ]].copy()
    fact_daily_demand["date_key"] = pd.to_datetime(fact_daily_demand["date"]).dt.strftime("%Y%m%d").astype(int)

    # --- 5. fact_forecast ---
    fact_forecast = fc_df[[
        "forecast_date", "store_id", "sku_id", "horizon_step", "forecast", "lower_bound", "upper_bound", "model_name"
    ]].copy()
    fact_forecast["date_key"] = pd.to_datetime(fact_forecast["forecast_date"]).dt.strftime("%Y%m%d").astype(int)

    # --- 6. fact_inventory_plan ---
    fact_inventory_plan = plan_df[[
        "store_id", "sku_id", "forecast_demand_28d", "avg_daily_demand", "std_daily_demand",
        "lead_time_days", "service_level", "demand_during_lead_time", "safety_stock",
        "reorder_point", "order_up_to_level", "on_hand_inventory", "on_order_inventory",
        "current_inventory_position", "days_of_supply", "reorder_triggered_flag",
        "recommended_order_qty", "recommended_order_value", "stockout_risk_level",
        "is_excess_inventory", "excess_units", "excess_capital_tied_up",
        "annual_excess_holding_cost", "priority_score", "priority_tier"
    ]].copy()

    # --- 7. fact_scenario ---
    fact_scenario = scen_df.copy()

    # Export all tables
    export_map = {
        "dim_date.csv": dim_date,
        "dim_product.csv": dim_product,
        "dim_store.csv": dim_store,
        "fact_daily_demand.csv": fact_daily_demand,
        "fact_forecast.csv": fact_forecast,
        "fact_inventory_plan.csv": fact_inventory_plan,
        "fact_scenario.csv": fact_scenario,
    }

    for fname, table_df in export_map.items():
        out_path = pbi_dir / fname
        table_df.to_csv(out_path, index=False)
        logger.info("Exported Power BI table: %s (%d rows)", fname, len(table_df))

    return {fname: str(pbi_dir / fname) for fname in export_map}


if __name__ == "__main__":
    generate_powerbi_star_schema()
