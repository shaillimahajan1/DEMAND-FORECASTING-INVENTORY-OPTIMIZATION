"""
End-to-End Inventory Optimization, Replenishment Planning, and Risk Profiling Pipeline
"""

import sys
from pathlib import Path
from typing import Any

# Ensure workspace root is in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import numpy as np
import pandas as pd
from src.inventory.safety_stock import calculate_safety_stock
from src.inventory.reorder_point import (
    calculate_demand_during_lead_time,
    calculate_reorder_point,
    calculate_order_up_to_level,
)
from src.inventory.stockout import (
    calculate_inventory_position,
    calculate_recommended_order_quantity,
    calculate_days_of_supply,
    classify_stockout_risk,
    evaluate_excess_and_dead_stock,
)
from src.inventory.prioritization import compute_priority_score
from src.scenarios.what_if import run_standard_scenario_suite
from src.sql.duckdb_engine import DuckDBAnalyticsEngine
from src.utils.logger import logger
from src.utils.helpers import get_project_root, ensure_directory, load_yaml_config


def run_inventory_planning_pipeline() -> dict[str, Any]:
    """
    Translates demand forecasts into operational safety stock, reorder points,
    stockout exposure risk tiers, and replenishment recommendations.
    """
    root = get_project_root()
    fc_path = root / "outputs" / "forecasts" / "final_forecasts.csv"
    hist_path = root / "data" / "processed" / "demand_daily.parquet"
    abc_path = root / "outputs" / "inventory" / "abc_xyz_analysis.csv"

    if not fc_path.exists():
        raise FileNotFoundError(f"Final forecasts not found at {fc_path}. Run forecasting pipeline first.")

    logger.info("Loading final forecast predictions from %s...", fc_path)
    fc_df = pd.read_csv(fc_path)
    hist_df = pd.read_parquet(hist_path)
    abc_df = pd.read_csv(abc_path) if abc_path.exists() else None

    # Load operational policy assumptions
    policy_config = load_yaml_config("config/inventory_assumptions.yaml")
    policy = policy_config["inventory_policy"]
    service_level = float(policy.get("default_service_level", 0.95))
    review_period_days = float(policy.get("review_period_days", 7.0))
    holding_rate = float(policy.get("annual_holding_cost_rate", 0.25))

    logger.info("Operational Policy: Target Service Level = %.1f%%, Review Period = %.0f days",
                service_level * 100, review_period_days)

    # 1. Aggregate 28-day forecast demand per store-SKU
    fc_agg = fc_df.groupby(["store_id", "sku_id"], as_index=False).agg(
        forecast_demand_28d=("forecast", "sum"),
        forecast_daily_mean=("forecast", "mean"),
    )
    # Attach unique metadata
    sku_meta = fc_df[["sku_id", "sku_name", "category", "sub_category", "unit_price", "unit_cost"]].drop_duplicates(subset=["sku_id"])
    fc_agg = fc_agg.merge(sku_meta, on="sku_id", how="left")

    # 2. Extract recent 90-day demand variance from historical observations
    hist_df["date"] = pd.to_datetime(hist_df["date"])
    recent_cutoff = hist_df["date"].max() - pd.Timedelta(days=90)
    recent_hist = hist_df[hist_df["date"] >= recent_cutoff]

    hist_stats = recent_hist.groupby(["store_id", "sku_id"], as_index=False).agg(
        hist_daily_mean=("quantity", "mean"),
        hist_daily_std=("quantity", "std"),
        zero_demand_count_90d=("quantity", lambda s: (s == 0).sum()),
    )
    hist_stats["hist_daily_std"] = hist_stats["hist_daily_std"].fillna(0.0)

    # Merge forecast and historical demand variance
    plan_df = fc_agg.merge(hist_stats, on=["store_id", "sku_id"], how="left")
    plan_df["avg_daily_demand"] = plan_df["forecast_daily_mean"].round(2)
    plan_df["std_daily_demand"] = plan_df["hist_daily_std"].round(2)

    # 3. Incorporate supplier lead time assumptions per SKU
    # Lead time characteristics mapped realistically by product category
    lead_time_map = {
        "Electronics": (9.0, 1.8),
        "Home & Kitchen": (8.0, 1.4),
        "Apparel": (10.0, 2.0),
        "Grocery & Pantry": (5.0, 0.8),
        "Health & Care": (7.0, 1.2),
    }

    # 4. Generate realistic initial inventory position scenario
    # In a real environment this comes from ERP / WMS on-hand feeds.
    # To demonstrate realistic stockout risks, excess stocks, and urgent reorders,
    # we simulate an operational snapshot based on realistic days of supply.
    np.random.seed(42)
    records = []

    for _, row in plan_df.iterrows():
        cat = row["category"]
        lt_mean, lt_std = lead_time_map.get(cat, (7.0, 1.5))
        d_mean = float(row["avg_daily_demand"])
        d_std = float(row["std_daily_demand"])
        unit_cost = float(row["unit_cost"])
        unit_price = float(row["unit_price"])

        # Safety Stock calculation
        ss = calculate_safety_stock(
            daily_demand_std=d_std,
            lead_time_days=lt_mean,
            daily_demand_mean=d_mean,
            lead_time_std_days=lt_std,
            service_level=service_level,
        )

        # Reorder Point (ROP) & Order-Up-To Level (S)
        rop, ddlt, _ = calculate_reorder_point(
            daily_demand_rate=d_mean,
            daily_demand_std=d_std,
            lead_time_days=lt_mean,
            lead_time_std_days=lt_std,
            service_level=service_level,
        )
        order_up_to = calculate_order_up_to_level(
            daily_demand_rate=d_mean,
            lead_time_days=lt_mean,
            review_period_days=review_period_days,
            safety_stock=ss,
        )

        # Simulated Operational Inventory Position (Snapshot):
        # We assign realistic inventory levels:
        # - 20% of SKUs have low stock (below ROP -> urgent reorder needed)
        # - 65% of SKUs have healthy normal stock (between ROP and Order-up-to)
        # - 15% of SKUs have excess inventory (over 45 days of supply)
        rand_profile = np.random.rand()
        if rand_profile < 0.20:
            # Low / Stockout Risk state
            sim_on_hand = round(d_mean * np.random.uniform(1.0, 5.0), 0)
            sim_on_order = round(d_mean * np.random.uniform(0.0, 2.0), 0)
        elif rand_profile > 0.85:
            # Excess Inventory state
            sim_on_hand = round(d_mean * np.random.uniform(48.0, 65.0), 0)
            sim_on_order = 0.0
        else:
            # Healthy normal operating range
            sim_on_hand = round(d_mean * np.random.uniform(10.0, 22.0), 0)
            sim_on_order = round(d_mean * np.random.uniform(0.0, 5.0), 0)

        inv_position = calculate_inventory_position(on_hand=sim_on_hand, on_order=sim_on_order, backorders=0.0)
        dos = calculate_days_of_supply(inv_position, d_mean)
        stockout_risk = classify_stockout_risk(dos, inv_position, ss, rop)

        reorder_triggered = inv_position <= rop
        roq = calculate_recommended_order_quantity(inv_position, rop, order_up_to)
        order_value = round(roq * unit_cost, 2)

        zero_demand_60d = int(row.get("zero_demand_count_90d", 0)) > 60
        excess_info = evaluate_excess_and_dead_stock(
            inventory_position=inv_position,
            order_up_to_level=order_up_to,
            days_of_supply=dos,
            unit_cost=unit_cost,
            zero_demand_60d=zero_demand_60d,
            annual_holding_rate=holding_rate,
        )

        records.append({
            "store_id": row["store_id"],
            "sku_id": row["sku_id"],
            "sku_name": row["sku_name"],
            "category": row["category"],
            "sub_category": row["sub_category"],
            "unit_cost": unit_cost,
            "unit_price": unit_price,
            "forecast_demand_28d": round(row["forecast_demand_28d"], 1),
            "avg_daily_demand": d_mean,
            "std_daily_demand": d_std,
            "lead_time_days": lt_mean,
            "lead_time_std_days": lt_std,
            "service_level": service_level,
            "demand_during_lead_time": ddlt,
            "safety_stock": ss,
            "reorder_point": rop,
            "order_up_to_level": order_up_to,
            "on_hand_inventory": sim_on_hand,
            "on_order_inventory": sim_on_order,
            "current_inventory_position": inv_position,
            "days_of_supply": dos,
            "reorder_triggered_flag": int(reorder_triggered),
            "recommended_order_qty": roq,
            "recommended_order_value": order_value,
            "stockout_risk_level": stockout_risk,
            "is_excess_inventory": excess_info["is_excess"],
            "excess_units": excess_info["excess_units"],
            "excess_capital_tied_up": excess_info["excess_capital_tied_up"],
            "annual_excess_holding_cost": excess_info["annual_excess_holding_cost"],
            "is_dead_stock": excess_info["is_dead_stock"],
        })

    recommendations_df = pd.DataFrame(records)

    # 5. Join ABC-XYZ segmentation if available and compute priority score
    if abc_df is not None:
        abc_sub = abc_df[["sku_id", "abc_class", "xyz_class", "abc_xyz_segment"]].drop_duplicates()
        recommendations_df = recommendations_df.merge(abc_sub, on="sku_id", how="left")
    else:
        recommendations_df["abc_class"] = "B"
        recommendations_df["xyz_class"] = "Y"
        recommendations_df["abc_xyz_segment"] = "BY"

    priorities = []
    priority_scores = []
    for _, r in recommendations_df.iterrows():
        score, tier = compute_priority_score(
            abc_class=r.get("abc_class", "B"),
            stockout_risk=r["stockout_risk_level"],
            reorder_triggered=bool(r["reorder_triggered_flag"]),
            xyz_class=r.get("xyz_class", "Y"),
        )
        priority_scores.append(score)
        priorities.append(tier)

    recommendations_df["priority_score"] = priority_scores
    recommendations_df["priority_tier"] = priorities

    # Sort by priority score descending
    recommendations_df = recommendations_df.sort_values(by="priority_score", ascending=False).reset_index(drop=True)

    # 6. Export outputs
    out_inv_dir = ensure_directory(root / "outputs" / "inventory")
    out_rep_dir = ensure_directory(root / "outputs" / "reports")

    recs_path = out_inv_dir / "inventory_recommendations.csv"
    plan_path = out_rep_dir / "inventory_plan.csv"
    recommendations_df.to_csv(recs_path, index=False)
    recommendations_df.to_csv(plan_path, index=False)
    logger.info("Saved %d SKU-location replenishment recommendations to %s", len(recommendations_df), recs_path)

    # Ingest into DuckDB
    duck_engine = DuckDBAnalyticsEngine()
    duck_engine.load_table_from_df("fct_inventory_recommendations", recommendations_df, overwrite=True)
    duck_engine.execute_script("sql/inventory/07_safety_stock_rop.sql")
    duck_engine.execute_script("sql/inventory/08_stockout_excess_risk.sql")
    duck_engine.close()
    logger.info("Materialized fct_inventory_recommendations and risk views in DuckDB.")

    # 7. Execute What-If Scenario Suite
    logger.info("Executing What-If Scenario sensitivity suite...")
    scenario_summary, scenario_detailed = run_standard_scenario_suite(recommendations_df)

    # Stockout vs Excess summary statistics
    n_total = len(recommendations_df)
    n_critical = int((recommendations_df["stockout_risk_level"] == "Critical").sum())
    n_high = int((recommendations_df["stockout_risk_level"] == "High").sum())
    n_excess = int((recommendations_df["is_excess_inventory"] == 1).sum())
    n_reorder = int((recommendations_df["reorder_triggered_flag"] == 1).sum())
    total_order_value = float(recommendations_df["recommended_order_value"].sum())
    total_excess_capital = float(recommendations_df["excess_capital_tied_up"].sum())

    summary_stats = pd.DataFrame([{
        "total_sku_locations": n_total,
        "reorder_triggered_count": n_reorder,
        "critical_stockout_risk_count": n_critical,
        "high_stockout_risk_count": n_high,
        "excess_inventory_count": n_excess,
        "total_recommended_order_value_usd": round(total_order_value, 2),
        "total_excess_capital_usd": round(total_excess_capital, 2),
    }])
    summary_stats.to_csv(out_inv_dir / "stockout_excess_summary.csv", index=False)

    logger.info("=== Inventory Planning Summary ===")
    logger.info("Total SKU-Locations: %d", n_total)
    logger.info("Reorders Triggered (IP <= ROP): %d (Total Value: $%.2f)", n_reorder, total_order_value)
    logger.info("Stockout Exposure: %d Critical, %d High Risk", n_critical, n_high)
    logger.info("Excess Stock: %d SKUs ($%.2f tied up capital)", n_excess, total_excess_capital)

    return {
        "status": "SUCCESS",
        "total_recommendations": n_total,
        "reorder_triggered": n_reorder,
        "total_recommended_order_value": total_order_value,
        "excess_inventory_count": n_excess,
        "excess_capital": total_excess_capital,
    }


if __name__ == "__main__":
    run_inventory_planning_pipeline()
