"""
Operational Inventory Prioritization Framework
Combines ABC Revenue Rank, Stockout Exposure, XYZ Volatility, and Replenishment Triggers.
"""

from typing import Any
import pandas as pd


def compute_priority_score(
    abc_class: str,
    stockout_risk: str,
    reorder_triggered: bool,
    xyz_class: str = "Y",
) -> tuple[int, str]:
    """
    Deterministic scoring framework to guide procurement decisions:
    - ABC Revenue Impact: A = 40, B = 25, C = 10
    - Stockout Severity: Critical = 50, High = 35, Medium = 20, Low = 5
    - Reorder Trigger: +20 points if inventory position <= ROP
    - XYZ Volatility: Z = 10, Y = 5, X = 0

    Returns:
    - Tuple: (numerical_score [0-120], priority_tier)
    """
    score = 0

    # ABC Revenue Contribution
    if abc_class == "A":
        score += 40
    elif abc_class == "B":
        score += 25
    else:
        score += 10

    # Stockout Urgency
    if stockout_risk == "Critical":
        score += 50
    elif stockout_risk == "High":
        score += 35
    elif stockout_risk == "Medium":
        score += 20
    else:
        score += 5

    # Reorder Trigger
    if reorder_triggered:
        score += 20

    # Volatility buffer
    if xyz_class == "Z":
        score += 10
    elif xyz_class == "Y":
        score += 5

    # Assign Priority Tier
    if score >= 75:
        tier = "P1 - Critical (Immediate PO)"
    elif score >= 50:
        tier = "P2 - High (Replenish This Week)"
    elif score >= 30:
        tier = "P3 - Standard Replenishment"
    else:
        tier = "P4 - Stable / Routine Monitor"

    return score, tier
