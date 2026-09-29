"""
Reorder Point (ROP) & Order-Up-To Level (S) Calculation Engine
"""

from src.inventory.safety_stock import calculate_safety_stock


def calculate_demand_during_lead_time(
    daily_demand_rate: float,
    lead_time_days: float,
) -> float:
    """
    Expected demand during supplier replenishment cycle:
    DDLT = D_bar * Lead_Time
    """
    return float(round(daily_demand_rate * lead_time_days, 1))


def calculate_reorder_point(
    daily_demand_rate: float,
    daily_demand_std: float,
    lead_time_days: float,
    lead_time_std_days: float = 0.0,
    service_level: float = 0.95,
) -> tuple[float, float, float]:
    """
    Reorder Point (ROP) = Expected Demand During Lead Time + Safety Stock

    Returns:
    - Tuple: (reorder_point, demand_during_lead_time, safety_stock)
    """
    ddlt = calculate_demand_during_lead_time(daily_demand_rate, lead_time_days)
    ss = calculate_safety_stock(
        daily_demand_std=daily_demand_std,
        lead_time_days=lead_time_days,
        daily_demand_mean=daily_demand_rate,
        lead_time_std_days=lead_time_std_days,
        service_level=service_level,
    )
    rop = float(round(ddlt + ss, 1))
    return rop, ddlt, ss


def calculate_order_up_to_level(
    daily_demand_rate: float,
    lead_time_days: float,
    review_period_days: float,
    safety_stock: float,
) -> float:
    """
    Periodic Review (R, S) Order-Up-To Level:
    S = D_bar * (Lead_Time + Review_Period) + Safety_Stock
    """
    coverage_demand = daily_demand_rate * (lead_time_days + review_period_days)
    order_up_to = coverage_demand + safety_stock
    return float(round(order_up_to, 1))
