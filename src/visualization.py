import sys
from pathlib import Path

# Ensure project root in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from src.utils.logger import logger
from src.utils.helpers import get_project_root, ensure_directory

# Professional styling
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 10,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "figure.titlesize": 14,
})


def generate_all_charts() -> dict[str, str]:
    """Generate and save publication charts."""
    root = get_project_root()
    charts_dir = ensure_directory(root / "outputs" / "charts")

    demand_path = root / "data" / "processed" / "demand_daily.parquet"
    fc_path = root / "outputs" / "forecasts" / "final_forecasts.csv"
    bt_path = root / "outputs" / "forecasts" / "backtest_predictions.csv"
    mc_path = root / "outputs" / "metrics" / "model_comparison.csv"
    abc_path = root / "outputs" / "inventory" / "abc_xyz_analysis.csv"
    inv_path = root / "outputs" / "inventory" / "inventory_recommendations.csv"
    scen_path = root / "outputs" / "scenarios" / "scenario_comparison_results.csv"

    generated = {}

    # --- Chart 1: Historical Demand & 28-Day Forecast with Prediction Intervals ---
    logger.info("Generating Chart 1: Demand History & Forecast...")
    df_demand = pd.read_parquet(demand_path)
    df_fc = pd.read_csv(fc_path)

    df_demand["date"] = pd.to_datetime(df_demand["date"])
    df_fc["forecast_date"] = pd.to_datetime(df_fc["forecast_date"])

    # Aggregate total volume per day across portfolio
    daily_hist = df_demand.groupby("date")["quantity"].sum().reset_index()
    daily_fc = df_fc.groupby("forecast_date").agg(
        forecast=("forecast", "sum"),
        lower_bound=("lower_bound", "sum"),
        upper_bound=("upper_bound", "sum"),
    ).reset_index()

    # Recent 90 days history + 28 days forecast
    recent_hist = daily_hist[daily_hist["date"] >= (daily_hist["date"].max() - pd.Timedelta(days=90))]

    fig, ax = plt.subplots(figsize=(12, 5), dpi=300)
    ax.plot(recent_hist["date"], recent_hist["quantity"], label="Observed Actual Sales", color="#1f77b4", linewidth=2.0)
    ax.plot(daily_fc["forecast_date"], daily_fc["forecast"], label="Champion Forecast (28-Day)", color="#ff7f0e", linewidth=2.2, linestyle="--")
    ax.fill_between(
        daily_fc["forecast_date"],
        daily_fc["lower_bound"],
        daily_fc["upper_bound"],
        color="#ff7f0e",
        alpha=0.25,
        label="95% Prediction Interval",
    )
    ax.set_title("Portfolio Demand History & 28-Day Out-of-Sample Forecast with Uncertainty Bounds", fontweight="bold", pad=12)
    ax.set_xlabel("Date")
    ax.set_ylabel("Total Units Demanded")
    ax.legend(loc="upper left", frameon=True)
    plt.tight_layout()
    c1 = charts_dir / "01_demand_history_and_forecast.png"
    plt.savefig(c1)
    plt.close()
    generated["01_demand_history"] = str(c1)

    # --- Chart 2: Model Performance Comparison (WAPE %) ---
    logger.info("Generating Chart 2: Model Performance WAPE Comparison...")
    df_mc = pd.read_csv(mc_path)

    fig, ax = plt.subplots(figsize=(9, 5), dpi=300)
    colors = ["#2ca02c" if i == 0 else "#4a90e2" for i in range(len(df_mc))]
    bars = ax.barh(df_mc["model_name"][::-1], df_mc["wape_pct"][::-1], color=colors[::-1], height=0.6)
    ax.set_title("Candidate Model Cross-Origin Backtest Performance (WAPE %)", fontweight="bold", pad=12)
    ax.set_xlabel("Weighted Absolute Percentage Error (WAPE % - Lower is Better)")

    for bar in bars:
        w = bar.get_width()
        ax.text(w + 0.5, bar.get_y() + bar.get_height() / 2, f"{w:.2f}%", va="center", ha="left", fontsize=9, fontweight="bold")

    ax.set_xlim(0, max(df_mc["wape_pct"]) * 1.15)
    plt.tight_layout()
    c2 = charts_dir / "02_model_performance_wape_comparison.png"
    plt.savefig(c2)
    plt.close()
    generated["02_model_performance"] = str(c2)

    # --- Chart 3: Forecast Bias by Merchandising Category ---
    logger.info("Generating Chart 3: Forecast Bias Analysis...")
    df_bt = pd.read_csv(bt_path)
    champ_name = df_mc.iloc[0]["model_name"]
    champ_bt = df_bt[df_bt["model_name"] == champ_name].copy()

    # Merge category
    cat_meta = df_demand[["sku_id", "category"]].drop_duplicates()
    champ_bt = champ_bt.merge(cat_meta, on="sku_id", how="left")

    cat_bias = champ_bt.groupby("category").agg(
        actual_sum=("actual", "sum"),
        forecast_sum=("forecast", "sum"),
        bias_units=("error", "sum"),
    ).reset_index()
    cat_bias["normalized_bias_pct"] = (cat_bias["bias_units"] / cat_bias["actual_sum"] * 100).round(2)

    fig, ax = plt.subplots(figsize=(9, 4.5), dpi=300)
    bar_colors = ["#d62728" if b < 0 else "#1f77b4" for b in cat_bias["normalized_bias_pct"]]
    bars = ax.bar(cat_bias["category"], cat_bias["normalized_bias_pct"], color=bar_colors, width=0.55)
    ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
    ax.set_title(f"Normalized Forecast Bias % by Category ({champ_name})", fontweight="bold", pad=12)
    ax.set_ylabel("Normalized Bias % (Underforecast vs Overforecast)")

    for bar in bars:
        h = bar.get_height()
        va = "bottom" if h >= 0 else "top"
        offset = 0.3 if h >= 0 else -0.7
        ax.text(bar.get_x() + bar.get_width() / 2, h + offset, f"{h:+.1f}%", ha="center", va=va, fontsize=9, fontweight="bold")

    plt.xticks(rotation=15, ha="right")
    plt.tight_layout()
    c3 = charts_dir / "03_forecast_bias_by_category.png"
    plt.savefig(c3)
    plt.close()
    generated["03_forecast_bias"] = str(c3)

    # --- Chart 4: ABC-XYZ 9-Box Matrix Distribution ---
    logger.info("Generating Chart 4: ABC-XYZ Portfolio Matrix...")
    df_abc = pd.read_csv(abc_path)
    matrix_counts = df_abc.pivot_table(index="abc_class", columns="xyz_class", values="sku_id", aggfunc="count", fill_value=0)
    matrix_counts = matrix_counts.reindex(index=["A", "B", "C"], columns=["X", "Y", "Z"], fill_value=0)

    fig, ax = plt.subplots(figsize=(7, 5.5), dpi=300)
    sns.heatmap(matrix_counts, annot=True, fmt="d", cmap="Blues", cbar=False, ax=ax, annot_kws={"size": 13, "weight": "bold"})
    ax.set_title("ABC Revenue & XYZ Volatility 9-Box Portfolio Matrix (SKU Count)", fontweight="bold", pad=12)
    ax.set_xlabel("XYZ Volatility Class (X: Stable, Y: Moderate, Z: Erratic)", fontweight="bold")
    ax.set_ylabel("ABC Revenue Class (A: Top 70%, B: 70-90%, C: Tail 10%)", fontweight="bold")
    plt.tight_layout()
    c4 = charts_dir / "04_abc_xyz_portfolio_matrix.png"
    plt.savefig(c4)
    plt.close()
    generated["04_abc_xyz_matrix"] = str(c4)

    # --- Chart 5: Stockout vs Excess Inventory Risk ---
    logger.info("Generating Chart 5: Stockout vs Excess Risk Profile...")
    df_inv = pd.read_csv(inv_path)
    risk_counts = df_inv["stockout_risk_level"].value_counts().reindex(["Critical", "High", "Medium", "Low"], fill_value=0)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), dpi=300)
    # Risk tiers
    palette = ["#d62728", "#ff7f0e", "#bcbd22", "#2ca02c"]
    ax1.bar(risk_counts.index, risk_counts.values, color=palette, width=0.6)
    ax1.set_title("Stockout Risk Exposure (SKU-Location Count)", fontweight="bold")
    ax1.set_ylabel("Number of SKU-Locations")
    for i, v in enumerate(risk_counts.values):
        ax1.text(i, v + 1, str(v), ha="center", fontweight="bold")

    # Capital allocation: Recommended Orders vs Excess Inventory vs Safety Stock
    tot_roq_val = float(df_inv["recommended_order_value"].sum())
    tot_excess_val = float(df_inv["excess_capital_tied_up"].sum())
    tot_ss_val = float((df_inv["safety_stock"] * df_inv["unit_cost"]).sum())

    cap_labels = ["Safety Stock\nCapital", "Recommended\nPO Spend", "Excess Capital\nTrapped"]
    cap_vals = [tot_ss_val, tot_roq_val, tot_excess_val]
    cap_colors = ["#1f77b4", "#2ca02c", "#d62728"]
    bars = ax2.bar(cap_labels, cap_vals, color=cap_colors, width=0.55)
    ax2.set_title("Working Capital Allocation Breakdown ($USD)", fontweight="bold")
    ax2.set_ylabel("Total Capital ($USD)")
    for bar in bars:
        h = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width() / 2, h + (max(cap_vals) * 0.02), f"${h:,.0f}", ha="center", fontweight="bold", fontsize=9)

    plt.tight_layout()
    c5 = charts_dir / "05_stockout_vs_excess_inventory_risk.png"
    plt.savefig(c5)
    plt.close()
    generated["05_stockout_excess"] = str(c5)

    # --- Chart 6: What-If Scenario Stress Testing Capital Impact ---
    logger.info("Generating Chart 6: Scenario Stress Testing Capital Impact...")
    df_scen = pd.read_csv(scen_path)

    fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
    scen_names = [
        "Baseline (95% SL)",
        "Demand (+15%)",
        "Lead Time (+20%)",
        "Premium SL (99%)",
        "Volatility (CV +30%)",
        "Compound Stress",
    ]
    ax.barh(scen_names[::-1], df_scen["total_safety_stock_capital"][::-1], color="#3b528b", height=0.55, label="Total Safety Stock Capital")
    ax.set_title("What-If Scenario Stress Testing: Safety Stock Capital Requirements", fontweight="bold", pad=12)
    ax.set_xlabel("Safety Stock Working Capital ($USD)")

    for i, v in enumerate(df_scen["total_safety_stock_capital"][::-1]):
        delta = df_scen["delta_ss_capital_vs_baseline"].iloc[::-1].iloc[i]
        delta_str = f" (+${delta:,.0f})" if delta > 0 else " (Baseline)"
        ax.text(v + 5000, i, f"${v:,.0f}{delta_str}", va="center", fontsize=9, fontweight="bold")

    ax.set_xlim(0, max(df_scen["total_safety_stock_capital"]) * 1.25)
    plt.tight_layout()
    c6 = charts_dir / "06_what_if_scenario_capital_impact.png"
    plt.savefig(c6)
    plt.close()
    generated["06_scenario_impact"] = str(c6)

    logger.info("All 6 publication charts generated successfully.")
    return generated


if __name__ == "__main__":
    generate_all_charts()
