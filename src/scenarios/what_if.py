"""
What-If Scenario Simulation Engine for Supply Chain & Inventory Stress-Testing
Simulates demand shifts, lead-time delays, service level target changes, and volatility spikes.
"""

from typing import Any
import pandas as pd
from src.inventory.safety_stock import calculate_safety_stock
from src.inventory.reorder_point import calculate_reorder_point, calculate_order_up_to_level
from src.inventory.stockout import (
    calculate_inventory_position,
    calculate_recommended_order_quantity,
    calculate_days_of_supply,
    classify_stockout_risk,
    evaluate_excess_and_dead_stock,
)
from src.utils.logger import logger
from src.utils.helpers import get_project_root, ensure_directory


class ScenarioSimulator:
    """
    Executes parameter-driven what-if sensitivity analyses across the SKU portfolio.
    """

    def __init__(self, inventory_plan_base: pd.DataFrame):
        self.base_df = inventory_plan_base.copy()

    def simulate_scenario(
        self,
        scenario_id: str,
        scenario_name: str,
        demand_mult: float = 1.0,
        lead_time_mult: float = 1.0,
        service_level: float = 0.95,
        volatility_mult: float = 1.0,
        review_period_days: float = 7.0,
    ) -> pd.DataFrame:
        """
        Simulate portfolio impact under given scenario multipliers.
        """
        logger.info("Simulating scenario '%s': Demand=%.2fx, LT=%.2fx, SL=%.2f, Vol=%.2fx",
                    scenario_name, demand_mult, lead_time_mult, service_level, volatility_mult)

        records = []
        for _, row in self.base_df.iterrows():
            store_id = row["store_id"]
            sku_id = row["sku_id"]
            sku_name = row.get("sku_name", "")
            category = row.get("category", "")
            unit_cost = float(row.get("unit_cost", 10.0))
            unit_price = float(row.get("unit_price", 25.0))

            # Scenario adjustments
            base_demand = float(row["avg_daily_demand"])
            sim_demand = base_demand * demand_mult

            base_std = float(row["std_daily_demand"])
            sim_std = base_std * volatility_mult

            base_lt = float(row.get("lead_time_days", 7.0))
            sim_lt = base_lt * lead_time_mult
            sim_lt_std = float(row.get("lead_time_std_days", 1.5)) * lead_time_mult

            # Recalculate Inventory Policy
            sim_ss = calculate_safety_stock(
                daily_demand_std=sim_std,
                lead_time_days=sim_lt,
                daily_demand_mean=sim_demand,
                lead_time_std_days=sim_lt_std,
                service_level=service_level,
            )

            sim_ddlt = sim_demand * sim_lt
            sim_rop = round(sim_ddlt + sim_ss, 1)
            sim_order_up_to = calculate_order_up_to_level(
                daily_demand_rate=sim_demand,
                lead_time_days=sim_lt,
                review_period_days=review_period_days,
                safety_stock=sim_ss,
            )

            # Net inventory position (from base input)
            inv_pos = float(row.get("current_inventory_position", row.get("inventory_position", 0.0)))
            sim_roq = calculate_recommended_order_quantity(inv_pos, sim_rop, sim_order_up_to)
            sim_dos = calculate_days_of_supply(inv_pos, sim_demand)
            sim_risk = classify_stockout_risk(sim_dos, inv_pos, sim_ss, sim_rop)

            records.append({
                "scenario_id": scenario_id,
                "scenario_name": scenario_name,
                "store_id": store_id,
                "sku_id": sku_id,
                "sku_name": sku_name,
                "category": category,
                "unit_cost": unit_cost,
                "unit_price": unit_price,
                "sim_daily_demand": round(sim_demand, 2),
                "sim_lead_time_days": round(sim_lt, 1),
                "sim_service_level": service_level,
                "sim_safety_stock": sim_ss,
                "sim_reorder_point": sim_rop,
                "sim_order_up_to": sim_order_up_to,
                "current_inventory_position": inv_pos,
                "sim_recommended_order_qty": sim_roq,
                "sim_recommended_order_value": round(sim_roq * unit_cost, 2),
                "sim_safety_stock_capital": round(sim_ss * unit_cost, 2),
                "sim_days_of_supply": sim_dos,
                "sim_stockout_risk": sim_risk,
            })

        return pd.DataFrame(records)


def run_standard_scenario_suite(inventory_plan_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Execute standard 6-scenario stress testing suite:
    1. Baseline Current State
    2. Demand Surge (+15%)
    3. Supply Chain Disruption (Lead Time +20%)
    4. Service Level Target 99%
    5. Volatility Shock (+30% CV)
    6. Compound Stress (+15% demand, +20% lead time, 98% SL)
    """
    simulator = ScenarioSimulator(inventory_plan_df)
    scenarios_meta = [
        ("SCEN_01", "Baseline Current State", 1.00, 1.00, 0.95, 1.00),
        ("SCEN_02", "Demand Surge (+15%)", 1.15, 1.00, 0.95, 1.00),
        ("SCEN_03", "Lead Time Disruption (+20%)", 1.00, 1.20, 0.95, 1.00),
        ("SCEN_04", "Premium Service Level (99%)", 1.00, 1.00, 0.99, 1.00),
        ("SCEN_05", "Volatility Shock (CV +30%)", 1.00, 1.00, 0.95, 1.30),
        ("SCEN_06", "Compound Stress Test (+15% D, +20% LT, 98% SL)", 1.15, 1.20, 0.98, 1.15),
    ]

    all_detailed = []
    summary_records = []

    # Baseline anchor for computing deltas
    baseline_ss_capital = 0.0
    baseline_roq_value = 0.0

    for sc_id, sc_name, d_mult, lt_mult, sl, vol_mult in scenarios_meta:
        res_df = simulator.simulate_scenario(
            scenario_id=sc_id,
            scenario_name=sc_name,
            demand_mult=d_mult,
            lead_time_mult=lt_mult,
            service_level=sl,
            volatility_mult=vol_mult,
        )
        all_detailed.append(res_df)

        tot_ss_units = float(res_df["sim_safety_stock"].sum())
        tot_ss_capital = float(res_df["sim_safety_stock_capital"].sum())
        tot_roq_units = float(res_df["sim_recommended_order_qty"].sum())
        tot_roq_value = float(res_df["sim_recommended_order_value"].sum())
        critical_risk_count = int((res_df["sim_stockout_risk"] == "Critical").sum())
        high_risk_count = int((res_df["sim_stockout_risk"] == "High").sum())

        if sc_id == "SCEN_01":
            baseline_ss_capital = tot_ss_capital
            baseline_roq_value = tot_roq_value
            delta_ss_cap = 0.0
            delta_roq_val = 0.0
        else:
            delta_ss_cap = round(tot_ss_capital - baseline_ss_capital, 2)
            delta_roq_val = round(tot_roq_value - baseline_roq_value, 2)

        summary_records.append({
            "scenario_id": sc_id,
            "scenario_name": sc_name,
            "demand_multiplier": d_mult,
            "lead_time_multiplier": lt_mult,
            "target_service_level": sl,
            "volatility_multiplier": vol_mult,
            "total_safety_stock_units": round(tot_ss_units, 0),
            "total_safety_stock_capital": round(tot_ss_capital, 2),
            "delta_ss_capital_vs_baseline": delta_ss_cap,
            "total_recommended_order_units": round(tot_roq_units, 0),
            "total_recommended_order_value": round(tot_roq_value, 2),
            "delta_roq_value_vs_baseline": delta_roq_val,
            "critical_stockout_risk_skus": critical_risk_count,
            "high_stockout_risk_skus": high_risk_count,
        })

    detailed_df = pd.concat(all_detailed, ignore_index=True)
    summary_df = pd.DataFrame(summary_records)

    root = get_project_root()
    out_dir = ensure_directory(root / "outputs" / "scenarios")
    summary_path = out_dir / "scenario_comparison_results.csv"
    detailed_path = out_dir / "scenario_detailed_sku_impact.csv"

    summary_df.to_csv(summary_path, index=False)
    detailed_df.to_csv(detailed_path, index=False)
    logger.info("Saved scenario summary to %s and detailed records to %s", summary_path, detailed_path)

    return summary_df, detailed_df
