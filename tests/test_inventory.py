"""
Unit tests for inventory optimization formulas: Safety Stock, Reorder Point,
Order-Up-To Level, Stockout Risk, and Replenishment Recommendations.
"""

import pytest
from src.inventory.safety_stock import calculate_safety_stock, get_z_factor
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
)


def test_safety_stock_known_values():
    """
    Verify Safety Stock matches exact analytical calculation:
    Given: sigma_D = 10, L = 4 days, SL = 95% (Z = 1.6449)
    Expected: SS = 1.6449 * 10 * sqrt(4) = 1.6449 * 20 = 32.9 units.
    """
    ss = calculate_safety_stock(
        daily_demand_std=10.0,
        lead_time_days=4.0,
        daily_demand_mean=0.0,
        lead_time_std_days=0.0,
        service_level=0.95,
    )
    assert pytest.approx(ss, abs=0.2) == 32.9


def test_safety_stock_lead_time_uncertainty():
    """Verify that adding supplier lead-time variability strictly increases safety stock."""
    ss_deterministic = calculate_safety_stock(
        daily_demand_std=10.0,
        lead_time_days=7.0,
        daily_demand_mean=20.0,
        lead_time_std_days=0.0,
        service_level=0.95,
    )
    ss_variable_lt = calculate_safety_stock(
        daily_demand_std=10.0,
        lead_time_days=7.0,
        daily_demand_mean=20.0,
        lead_time_std_days=2.0,  # 2 days std dev in supplier deliveries
        service_level=0.95,
    )
    assert ss_variable_lt > ss_deterministic


def test_service_level_monotonicity():
    """Verify that higher service levels strictly demand higher safety stock."""
    ss_90 = calculate_safety_stock(daily_demand_std=12.0, lead_time_days=7.0, service_level=0.90)
    ss_95 = calculate_safety_stock(daily_demand_std=12.0, lead_time_days=7.0, service_level=0.95)
    ss_99 = calculate_safety_stock(daily_demand_std=12.0, lead_time_days=7.0, service_level=0.99)

    assert ss_90 < ss_95 < ss_99


def test_reorder_point_formula():
    """
    Verify ROP = Expected Demand During Lead Time + Safety Stock:
    Given: daily_demand = 25, lead_time = 6 days -> DDLT = 150
    """
    rop, ddlt, ss = calculate_reorder_point(
        daily_demand_rate=25.0,
        daily_demand_std=5.0,
        lead_time_days=6.0,
        lead_time_std_days=0.0,
        service_level=0.95,
    )
    assert ddlt == 150.0
    assert rop == pytest.approx(ddlt + ss, abs=0.1)


def test_recommended_order_quantity_trigger():
    """
    Verify ROQ logic:
    If IP <= ROP -> Order Quantity = S - IP
    If IP > ROP -> Order Quantity = 0
    """
    rop = 100.0
    order_up_to = 180.0

    # Scenario A: Inventory Position below ROP (e.g. 60 units) -> Trigger Replenishment
    roq_triggered = calculate_recommended_order_quantity(
        inventory_position=60.0,
        reorder_point=rop,
        order_up_to_level=order_up_to,
    )
    assert roq_triggered == 120.0  # 180 - 60 = 120

    # Scenario B: Inventory Position above ROP (e.g. 120 units) -> No Order
    roq_not_triggered = calculate_recommended_order_quantity(
        inventory_position=120.0,
        reorder_point=rop,
        order_up_to_level=order_up_to,
    )
    assert roq_not_triggered == 0.0


def test_stockout_risk_classification():
    """Verify operational risk tiers based on Days of Supply and Safety Stock buffers."""
    # Critical: DOS < 3 days
    assert classify_stockout_risk(days_of_supply=2.0, inventory_position=20, safety_stock=50, reorder_point=100) == "Critical"
    # High: DOS < 7 days
    assert classify_stockout_risk(days_of_supply=5.0, inventory_position=45, safety_stock=50, reorder_point=100) == "High"
    # Medium: DOS < 14 days
    assert classify_stockout_risk(days_of_supply=10.0, inventory_position=80, safety_stock=50, reorder_point=100) == "Medium"
    # Low: DOS >= 14 days and IP > ROP
    assert classify_stockout_risk(days_of_supply=20.0, inventory_position=150, safety_stock=50, reorder_point=100) == "Low"
