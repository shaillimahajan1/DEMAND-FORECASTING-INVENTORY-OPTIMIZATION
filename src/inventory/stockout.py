"""
Stockout Exposure, Excess Inventory, and Recommended Order Quantity (ROQ) Engine
"""

from typing import Any
import numpy as np
import pandas as pd


def calculate_inventory_position(on_hand: float, on_order: float = 0.0, backorders: float = 0.0) -> float:
    """
    Effective Net Inventory Position:
    IP = On_Hand + On_Order - Backorders
    """
    return float(round(max(0.0, on_hand + on_order - backorders), 1))


def calculate_recommended_order_quantity(
    inventory_position: float,
    reorder_point: float,
    order_up_to_level: float,
) -> float:
    """
    Replenishment Recommendation:
    If Inventory Position <= Reorder Point (ROP):
        Order Quantity = max(0, Order_Up_To_Level - Inventory_Position)
    Else:
        Order Quantity = 0 (Stock is currently above reorder threshold)
    """
    if inventory_position <= reorder_point:
        roq = max(0.0, order_up_to_level - inventory_position)
        return float(round(roq, 0))
    return 0.0


def calculate_days_of_supply(inventory_position: float, daily_demand_rate: float) -> float:
    """
    Days of Supply (DOS) = Inventory Position / Daily Demand Rate
    """
    if daily_demand_rate <= 0:
        return 999.0 if inventory_position > 0 else 0.0
    return float(round(inventory_position / daily_demand_rate, 1))


def classify_stockout_risk(
    days_of_supply: float,
    inventory_position: float,
    safety_stock: float,
    reorder_point: float,
) -> str:
    """
    Assign interpretable operational risk tier:
    - Critical: DOS < 3.0 days OR inventory position < 50% of Safety Stock
    - High: DOS < 7.0 days OR inventory position <= Safety Stock
    - Medium: DOS < 14.0 days OR inventory position <= Reorder Point
    - Low: DOS >= 14.0 days AND inventory position > Reorder Point
    """
    if days_of_supply < 3.0 or inventory_position < (0.5 * safety_stock):
        return "Critical"
    elif days_of_supply < 7.0 or inventory_position <= safety_stock:
        return "High"
    elif days_of_supply < 14.0 or inventory_position <= reorder_point:
        return "Medium"
    else:
        return "Low"


def evaluate_excess_and_dead_stock(
    inventory_position: float,
    order_up_to_level: float,
    days_of_supply: float,
    unit_cost: float,
    zero_demand_60d: bool = False,
    annual_holding_rate: float = 0.25,
) -> dict[str, Any]:
    """
    Evaluate excess inventory exposure and dead stock indicators.
    """
    is_excess = days_of_supply > 45.0 and inventory_position > order_up_to_level
    excess_units = max(0.0, inventory_position - order_up_to_level) if is_excess else 0.0
    excess_capital = round(excess_units * unit_cost, 2)
    annual_holding_cost = round(excess_capital * annual_holding_rate, 2)

    is_dead_stock = zero_demand_60d and inventory_position > 0

    return {
        "is_excess": int(is_excess),
        "excess_units": round(excess_units, 1),
        "excess_capital_tied_up": excess_capital,
        "annual_excess_holding_cost": annual_holding_cost,
        "is_dead_stock": int(is_dead_stock),
    }
