"""
Safety Stock Calculation Engine
Implements deterministic and stochastic lead-time safety stock formulas
across configurable customer service levels (90% to 99.9%).
"""

import numpy as np
from scipy.stats import norm
from src.utils.logger import logger

# Standard normal distribution Z-factor lookup table
SERVICE_LEVEL_Z_FACTORS = {
    0.85: 1.0364,
    0.90: 1.2816,
    0.95: 1.6449,
    0.975: 1.9600,
    0.98: 2.0537,
    0.99: 2.3263,
    0.999: 3.0902,
}


def get_z_factor(service_level: float = 0.95) -> float:
    """
    Retrieve exact Z-score corresponding to target cycle service level.
    Uses exact scipy inverse CDF (ppf) if not in lookup.
    """
    if service_level in SERVICE_LEVEL_Z_FACTORS:
        return SERVICE_LEVEL_Z_FACTORS[service_level]
    return float(norm.ppf(service_level))


def calculate_safety_stock(
    daily_demand_std: float,
    lead_time_days: float,
    daily_demand_mean: float = 0.0,
    lead_time_std_days: float = 0.0,
    service_level: float = 0.95,
) -> float:
    """
    Calculate Safety Stock units.

    Formulations:
    1. Demand uncertainty only (when lead_time_std_days == 0):
       SS = Z * sigma_D * sqrt(L)

    2. Combined demand and lead-time uncertainty (Silver-Pyke-Peterson):
       SS = Z * sqrt( L * sigma_D^2 + D_bar^2 * sigma_L^2 )

    Parameters:
    - daily_demand_std (sigma_D): Standard deviation of daily demand
    - lead_time_days (L): Average replenishment supplier lead time
    - daily_demand_mean (D_bar): Average daily demand
    - lead_time_std_days (sigma_L): Standard deviation of supplier lead time
    - service_level: Target cycle service level (e.g. 0.95 for 95%)

    Returns:
    - Float safety stock units (rounded to 1 decimal place).
    """
    z = get_z_factor(service_level)

    if lead_time_std_days <= 0.0 or daily_demand_mean <= 0.0:
        # Constant lead time formula
        variance = lead_time_days * (daily_demand_std ** 2)
    else:
        # Variable lead time and variable demand formula
        variance = (lead_time_days * (daily_demand_std ** 2)) + ((daily_demand_mean ** 2) * (lead_time_std_days ** 2))

    ss = z * np.sqrt(max(0.0, variance))
    return float(round(ss, 1))
