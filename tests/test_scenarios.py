"""
Unit tests for What-If scenario simulations and supply chain stress testing.
"""

import pandas as pd
import pytest
from src.scenarios.what_if import ScenarioSimulator, run_standard_scenario_suite


@pytest.fixture
def mock_inventory_plan():
    """Create a minimal representative inventory plan DataFrame."""
    return pd.DataFrame([
        {
            "store_id": "FC-East",
            "sku_id": "SKU-001",
            "sku_name": "Test SKU 1",
            "category": "Electronics",
            "unit_cost": 50.0,
            "unit_price": 100.0,
            "avg_daily_demand": 20.0,
            "std_daily_demand": 5.0,
            "lead_time_days": 7.0,
            "lead_time_std_days": 1.5,
            "current_inventory_position": 100.0,
        },
        {
            "store_id": "FC-West",
            "sku_id": "SKU-002",
            "sku_name": "Test SKU 2",
            "category": "Apparel",
            "unit_cost": 20.0,
            "unit_price": 50.0,
            "avg_daily_demand": 40.0,
            "std_daily_demand": 12.0,
            "lead_time_days": 10.0,
            "lead_time_std_days": 2.0,
            "current_inventory_position": 250.0,
        },
    ])


def test_scenario_demand_surge(mock_inventory_plan):
    """Verify that a 15% demand surge increases demand and safety stock."""
    sim = ScenarioSimulator(mock_inventory_plan)
    baseline = sim.simulate_scenario("BASE", "Baseline", demand_mult=1.0)
    surge = sim.simulate_scenario("SURGE", "Demand Surge", demand_mult=1.15)

    assert surge["sim_daily_demand"].sum() == pytest.approx(baseline["sim_daily_demand"].sum() * 1.15, rel=1e-2)
    assert surge["sim_safety_stock"].sum() > baseline["sim_safety_stock"].sum()


def test_scenario_lead_time_disruption(mock_inventory_plan):
    """Verify that a 20% lead time disruption increases safety stock requirements."""
    sim = ScenarioSimulator(mock_inventory_plan)
    baseline = sim.simulate_scenario("BASE", "Baseline", lead_time_mult=1.0)
    delay = sim.simulate_scenario("DELAY", "LT Delay", lead_time_mult=1.20)

    assert delay["sim_safety_stock"].sum() > baseline["sim_safety_stock"].sum()
    assert delay["sim_reorder_point"].sum() > baseline["sim_reorder_point"].sum()


def test_scenario_service_level_elevation(mock_inventory_plan):
    """Verify that elevating service level from 95% to 99% increases safety stock capital."""
    sim = ScenarioSimulator(mock_inventory_plan)
    base_95 = sim.simulate_scenario("SL95", "95% SL", service_level=0.95)
    elev_99 = sim.simulate_scenario("SL99", "99% SL", service_level=0.99)

    assert elev_99["sim_safety_stock_capital"].sum() > base_95["sim_safety_stock_capital"].sum()


def test_standard_scenario_suite(mock_inventory_plan):
    """Verify that the full 6-scenario suite returns summary and detailed tables."""
    summary_df, detailed_df = run_standard_scenario_suite(mock_inventory_plan)
    assert len(summary_df) == 6
    assert "delta_ss_capital_vs_baseline" in summary_df.columns
    assert len(detailed_df) == 12  # 2 SKUs x 6 scenarios
