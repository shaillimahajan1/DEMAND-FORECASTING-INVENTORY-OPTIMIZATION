"""
Realistic Retail Sales Dataset Generator for Demand Forecasting & Inventory Optimization

Simulates realistic multi-category retail transactions across 50 SKUs, 3 Fulfillment Hubs,
and 2 years of daily records (2023-01-01 to 2024-12-31). Incorporates diverse demand profiles:
- Stable / Low CV
- Seasonal (Weekly & Annual)
- Growing Trend
- Declining Trend
- Volatile / Erratic
- Intermittent / Lumpy (Croston / Syntetos-Boylan quadrant)
"""

import numpy as np
import pandas as pd
from pathlib import Path
from src.utils.logger import logger


def generate_retail_sales_data(
    start_date: str = "2023-01-01",
    end_date: str = "2024-12-31",
    seed: int = 42,
    output_path: str | Path | None = None,
) -> pd.DataFrame:
    """
    Generate synthetic yet statistically grounded daily retail sales data.
    """
    np.random.seed(seed)
    date_range = pd.date_range(start=start_date, end=end_date, freq="D")
    n_days = len(date_range)
    logger.info("Generating retail demand dataset from %s to %s (%d days)...", start_date, end_date, n_days)

    stores = [
        {"store_id": "FC-East", "store_name": "New York Tri-State Hub", "demand_multiplier": 1.25},
        {"store_id": "FC-West", "store_name": "California Pacific Hub", "demand_multiplier": 1.10},
        {"store_id": "FC-Central", "store_name": "Chicago Midwest Hub", "demand_multiplier": 0.85},
    ]

    # Merchandising catalog: 50 SKUs across 5 core categories
    catalog = [
        # --- Electronics (10 SKUs) ---
        {"sku_id": "SKU-ELEC-001", "sku_name": "Pro Wireless Noise-Canceling Earbuds", "category": "Electronics", "sub_category": "Audio", "unit_price": 129.99, "unit_cost": 58.50, "profile": "growing", "base_demand": 22, "volatility": 0.25, "lead_time_mean": 9, "lead_time_std": 1.8},
        {"sku_id": "SKU-ELEC-002", "sku_name": "Ultra-Fast USB-C GaN Charger 65W", "category": "Electronics", "sub_category": "Accessories", "unit_price": 34.99, "unit_cost": 14.20, "profile": "stable", "base_demand": 38, "volatility": 0.18, "lead_time_mean": 6, "lead_time_std": 1.0},
        {"sku_id": "SKU-ELEC-003", "sku_name": "Smart Home Environmental Sensor Hub", "category": "Electronics", "sub_category": "Smart Home", "unit_price": 79.99, "unit_cost": 36.00, "profile": "growing", "base_demand": 14, "volatility": 0.30, "lead_time_mean": 12, "lead_time_std": 2.2},
        {"sku_id": "SKU-ELEC-004", "sku_name": "Braided HDMI 2.1 Ultra High Speed Cable", "category": "Electronics", "sub_category": "Cables", "unit_price": 19.99, "unit_cost": 7.50, "profile": "stable", "base_demand": 45, "volatility": 0.20, "lead_time_mean": 5, "lead_time_std": 0.8},
        {"sku_id": "SKU-ELEC-005", "sku_name": "Mechanical Gaming Keyboard RGB", "category": "Electronics", "sub_category": "Gaming", "unit_price": 109.99, "unit_cost": 52.00, "profile": "seasonal_q4", "base_demand": 18, "volatility": 0.35, "lead_time_mean": 10, "lead_time_std": 2.0},
        {"sku_id": "SKU-ELEC-006", "sku_name": "Portable Bluetooth Rugged Speaker", "category": "Electronics", "sub_category": "Audio", "unit_price": 59.99, "unit_cost": 26.50, "profile": "seasonal_summer", "base_demand": 20, "volatility": 0.30, "lead_time_mean": 8, "lead_time_std": 1.5},
        {"sku_id": "SKU-ELEC-007", "sku_name": "Micro-USB Legacy Charging Cable 2m", "category": "Electronics", "sub_category": "Cables", "unit_price": 8.99, "unit_cost": 3.10, "profile": "declining", "base_demand": 16, "volatility": 0.35, "lead_time_mean": 7, "lead_time_std": 1.2},
        {"sku_id": "SKU-ELEC-008", "sku_name": "4K Ultra-HD Streaming Media Player", "category": "Electronics", "sub_category": "Home Video", "unit_price": 49.99, "unit_cost": 22.00, "profile": "seasonal_q4", "base_demand": 28, "volatility": 0.28, "lead_time_mean": 7, "lead_time_std": 1.4},
        {"sku_id": "SKU-ELEC-009", "sku_name": "Specialty Motherboard Replacement Capacitor Pack", "category": "Electronics", "sub_category": "Components", "unit_price": 45.00, "unit_cost": 15.00, "profile": "intermittent", "base_demand": 4, "volatility": 0.70, "lead_time_mean": 18, "lead_time_std": 3.5},
        {"sku_id": "SKU-ELEC-010", "sku_name": "Enterprise High-Resolution Studio Microphone", "category": "Electronics", "sub_category": "Professional Audio", "unit_price": 249.99, "unit_cost": 115.00, "profile": "volatile", "base_demand": 7, "volatility": 0.65, "lead_time_mean": 14, "lead_time_std": 2.5},

        # --- Home & Kitchen (10 SKUs) ---
        {"sku_id": "SKU-HOME-001", "sku_name": "Cast Iron Pre-Seasoned Skillet 12-Inch", "category": "Home & Kitchen", "sub_category": "Cookware", "unit_price": 39.99, "unit_cost": 16.80, "profile": "stable", "base_demand": 25, "volatility": 0.22, "lead_time_mean": 7, "lead_time_std": 1.2},
        {"sku_id": "SKU-HOME-002", "sku_name": "Stainless Steel Thermal Travel Mug 16oz", "category": "Home & Kitchen", "sub_category": "Drinkware", "unit_price": 24.99, "unit_cost": 9.80, "profile": "seasonal_winter", "base_demand": 32, "volatility": 0.26, "lead_time_mean": 6, "lead_time_std": 1.0},
        {"sku_id": "SKU-HOME-003", "sku_name": "Airtight Glass Food Storage Containers (Set of 8)", "category": "Home & Kitchen", "sub_category": "Storage", "unit_price": 44.99, "unit_cost": 19.50, "profile": "growing", "base_demand": 19, "volatility": 0.24, "lead_time_mean": 9, "lead_time_std": 1.5},
        {"sku_id": "SKU-HOME-004", "sku_name": "Digital Instant-Read Meat Thermometer", "category": "Home & Kitchen", "sub_category": "Kitchen Tools", "unit_price": 18.99, "unit_cost": 7.20, "profile": "seasonal_summer", "base_demand": 21, "volatility": 0.32, "lead_time_mean": 6, "lead_time_std": 1.1},
        {"sku_id": "SKU-HOME-005", "sku_name": "Organic Bamboo Cutting Board 3-Piece Set", "category": "Home & Kitchen", "sub_category": "Kitchen Tools", "unit_price": 29.99, "unit_cost": 12.00, "profile": "stable", "base_demand": 27, "volatility": 0.20, "lead_time_mean": 8, "lead_time_std": 1.4},
        {"sku_id": "SKU-HOME-006", "sku_name": "HEPA Air Purifier Compact Room Model", "category": "Home & Kitchen", "sub_category": "Appliances", "unit_price": 89.99, "unit_cost": 42.00, "profile": "seasonal_winter", "base_demand": 15, "volatility": 0.38, "lead_time_mean": 11, "lead_time_std": 2.0},
        {"sku_id": "SKU-HOME-007", "sku_name": "Countertop Citrus Juicer Manual Press", "category": "Home & Kitchen", "sub_category": "Kitchen Tools", "unit_price": 22.99, "unit_cost": 9.50, "profile": "declining", "base_demand": 10, "volatility": 0.35, "lead_time_mean": 8, "lead_time_std": 1.5},
        {"sku_id": "SKU-HOME-008", "sku_name": "Non-Stick 10-Piece Baking Sheet Set", "category": "Home & Kitchen", "sub_category": "Bakeware", "unit_price": 49.99, "unit_cost": 21.00, "profile": "seasonal_q4", "base_demand": 20, "volatility": 0.40, "lead_time_mean": 9, "lead_time_std": 1.8},
        {"sku_id": "SKU-HOME-009", "sku_name": "Commercial Heavy Duty Stand Mixer Motor Assembly", "category": "Home & Kitchen", "sub_category": "Spare Parts", "unit_price": 159.00, "unit_cost": 68.00, "profile": "intermittent", "base_demand": 3, "volatility": 0.85, "lead_time_mean": 21, "lead_time_std": 4.0},
        {"sku_id": "SKU-HOME-010", "sku_name": "Automatic Touchless Stainless Trash Can 13 Gal", "category": "Home & Kitchen", "sub_category": "Waste & Storage", "unit_price": 74.99, "unit_cost": 33.00, "profile": "volatile", "base_demand": 11, "volatility": 0.55, "lead_time_mean": 12, "lead_time_std": 2.2},

        # --- Apparel & Seasonal (10 SKUs) ---
        {"sku_id": "SKU-APPR-001", "sku_name": "Men's Classic Cotton Crewneck T-Shirt 3-Pack", "category": "Apparel", "sub_category": "Basics", "unit_price": 27.99, "unit_cost": 10.50, "profile": "stable", "base_demand": 50, "volatility": 0.19, "lead_time_mean": 5, "lead_time_std": 0.9},
        {"sku_id": "SKU-APPR-002", "sku_name": "Down-Alternative Insulated Winter Puffer Jacket", "category": "Apparel", "sub_category": "Outerwear", "unit_price": 149.99, "unit_cost": 62.00, "profile": "seasonal_winter", "base_demand": 24, "volatility": 0.55, "lead_time_mean": 14, "lead_time_std": 2.8},
        {"sku_id": "SKU-APPR-003", "sku_name": "Breathable Quick-Dry Athletic Shorts", "category": "Apparel", "sub_category": "Sportswear", "unit_price": 29.99, "unit_cost": 11.20, "profile": "seasonal_summer", "base_demand": 35, "volatility": 0.42, "lead_time_mean": 7, "lead_time_std": 1.3},
        {"sku_id": "SKU-APPR-004", "sku_name": "Seamless Moisture-Wicking Merino Wool Running Socks", "category": "Apparel", "sub_category": "Accessories", "unit_price": 16.99, "unit_cost": 6.10, "profile": "growing", "base_demand": 42, "volatility": 0.22, "lead_time_mean": 6, "lead_time_std": 1.0},
        {"sku_id": "SKU-APPR-005", "sku_name": "Water-Resistant Commuter Backpack with Laptop Sleeve", "category": "Apparel", "sub_category": "Bags", "unit_price": 69.99, "unit_cost": 28.50, "profile": "seasonal_bts", "base_demand": 26, "volatility": 0.38, "lead_time_mean": 10, "lead_time_std": 1.9},
        {"sku_id": "SKU-APPR-006", "sku_name": "Lightweight UV Sun Protection Fishing Hoodie", "category": "Apparel", "sub_category": "Outdoor", "unit_price": 42.99, "unit_cost": 16.50, "profile": "seasonal_summer", "base_demand": 22, "volatility": 0.45, "lead_time_mean": 8, "lead_time_std": 1.5},
        {"sku_id": "SKU-APPR-007", "sku_name": "Vintage Low-Rise Bootcut Denim Jeans", "category": "Apparel", "sub_category": "Denim", "unit_price": 54.99, "unit_cost": 23.00, "profile": "declining", "base_demand": 12, "volatility": 0.40, "lead_time_mean": 9, "lead_time_std": 1.6},
        {"sku_id": "SKU-APPR-008", "sku_name": "Fleece-Lined Thermal Baselayer Leggings", "category": "Apparel", "sub_category": "Base Layer", "unit_price": 34.99, "unit_cost": 13.80, "profile": "seasonal_winter", "base_demand": 28, "volatility": 0.50, "lead_time_mean": 8, "lead_time_std": 1.4},
        {"sku_id": "SKU-APPR-009", "sku_name": "Custom Embroidered Alpine Ski Racing Bib", "category": "Apparel", "sub_category": "Specialty Sport", "unit_price": 120.00, "unit_cost": 48.00, "profile": "intermittent", "base_demand": 3, "volatility": 0.90, "lead_time_mean": 20, "lead_time_std": 3.8},
        {"sku_id": "SKU-APPR-010", "sku_name": "Full-Grain Italian Leather Travel Duffel", "category": "Apparel", "sub_category": "Luxury Bags", "unit_price": 289.99, "unit_cost": 135.00, "profile": "volatile", "base_demand": 5, "volatility": 0.75, "lead_time_mean": 16, "lead_time_std": 3.0},

        # --- Grocery & Pantry (10 SKUs) ---
        {"sku_id": "SKU-GROC-001", "sku_name": "Organic Whole Bean Espresso Roast 2 lb", "category": "Grocery & Pantry", "sub_category": "Coffee & Tea", "unit_price": 21.99, "unit_cost": 9.20, "profile": "stable", "base_demand": 65, "volatility": 0.15, "lead_time_mean": 4, "lead_time_std": 0.7},
        {"sku_id": "SKU-GROC-002", "sku_name": "Raw California Organic Almonds Unsalted 3 lb", "category": "Grocery & Pantry", "sub_category": "Nuts & Snacks", "unit_price": 18.49, "unit_cost": 8.00, "profile": "stable", "base_demand": 48, "volatility": 0.16, "lead_time_mean": 5, "lead_time_std": 0.8},
        {"sku_id": "SKU-GROC-003", "sku_name": "Extra Virgin Cold-Pressed Olive Oil 1 Liter", "category": "Grocery & Pantry", "sub_category": "Oils & Vinegars", "unit_price": 19.99, "unit_cost": 8.50, "profile": "growing", "base_demand": 36, "volatility": 0.20, "lead_time_mean": 6, "lead_time_std": 1.0},
        {"sku_id": "SKU-GROC-004", "sku_name": "Organic Ceremonial Grade Matcha Green Tea 100g", "category": "Grocery & Pantry", "sub_category": "Coffee & Tea", "unit_price": 29.99, "unit_cost": 12.20, "profile": "growing", "base_demand": 24, "volatility": 0.28, "lead_time_mean": 8, "lead_time_std": 1.4},
        {"sku_id": "SKU-GROC-005", "sku_name": "Artisanal Holiday Spiced Hot Cocoa Mix 500g", "category": "Grocery & Pantry", "sub_category": "Seasonal Beverages", "unit_price": 14.99, "unit_cost": 5.60, "profile": "seasonal_q4", "base_demand": 30, "volatility": 0.60, "lead_time_mean": 7, "lead_time_std": 1.3},
        {"sku_id": "SKU-GROC-006", "sku_name": "Electrolyte Enhanced Sparkling Mineral Water (24-Pack)", "category": "Grocery & Pantry", "sub_category": "Beverages", "unit_price": 26.99, "unit_cost": 11.80, "profile": "seasonal_summer", "base_demand": 40, "volatility": 0.32, "lead_time_mean": 5, "lead_time_std": 0.9},
        {"sku_id": "SKU-GROC-007", "sku_name": "Artificially Flavored Breakfast Cereal Marshmallow 18oz", "category": "Grocery & Pantry", "sub_category": "Cereals", "unit_price": 5.49, "unit_cost": 2.20, "profile": "declining", "base_demand": 22, "volatility": 0.30, "lead_time_mean": 5, "lead_time_std": 0.8},
        {"sku_id": "SKU-GROC-008", "sku_name": "Gourmet Dark Chocolate Sea Salt Truffles Gift Box", "category": "Grocery & Pantry", "sub_category": "Confections", "unit_price": 24.99, "unit_cost": 9.90, "profile": "seasonal_q4", "base_demand": 25, "volatility": 0.50, "lead_time_mean": 7, "lead_time_std": 1.2},
        {"sku_id": "SKU-GROC-009", "sku_name": "Bulk Food Grade Citric Acid Crystals 50 lb Sack", "category": "Grocery & Pantry", "sub_category": "Bulk Ingredients", "unit_price": 89.00, "unit_cost": 38.00, "profile": "intermittent", "base_demand": 4, "volatility": 0.80, "lead_time_mean": 15, "lead_time_std": 3.0},
        {"sku_id": "SKU-GROC-010", "sku_name": "Imported White Truffle Infused Olive Oil Reserve 250ml", "category": "Grocery & Pantry", "sub_category": "Gourmet Specialty", "unit_price": 64.99, "unit_cost": 29.00, "profile": "volatile", "base_demand": 6, "volatility": 0.65, "lead_time_mean": 12, "lead_time_std": 2.2},

        # --- Health & Personal Care (10 SKUs) ---
        {"sku_id": "SKU-HLTH-001", "sku_name": "Daily Multivitamin Formula with Zinc & D3 (90 Count)", "category": "Health & Care", "sub_category": "Supplements", "unit_price": 22.99, "unit_cost": 8.90, "profile": "stable", "base_demand": 55, "volatility": 0.16, "lead_time_mean": 5, "lead_time_std": 0.8},
        {"sku_id": "SKU-HLTH-002", "sku_name": "Mineral Broad-Spectrum Sunscreen Lotion SPF 50 6oz", "category": "Health & Care", "sub_category": "Suncare", "unit_price": 17.99, "unit_cost": 6.80, "profile": "seasonal_summer", "base_demand": 38, "volatility": 0.48, "lead_time_mean": 6, "lead_time_std": 1.1},
        {"sku_id": "SKU-HLTH-003", "sku_name": "Grass-Fed Hydrolyzed Collagen Peptides Powder 1 lb", "category": "Health & Care", "sub_category": "Nutrition", "unit_price": 36.99, "unit_cost": 15.50, "profile": "growing", "base_demand": 30, "volatility": 0.24, "lead_time_mean": 7, "lead_time_std": 1.2},
        {"sku_id": "SKU-HLTH-004", "sku_name": "Sonic Electric Toothbrush Replacement Heads (4-Pack)", "category": "Health & Care", "sub_category": "Oral Care", "unit_price": 29.99, "unit_cost": 10.50, "profile": "stable", "base_demand": 34, "volatility": 0.20, "lead_time_mean": 6, "lead_time_std": 1.0},
        {"sku_id": "SKU-HLTH-005", "sku_name": "Elderberry Immune Support Syrup with Vitamin C 8oz", "category": "Health & Care", "sub_category": "Wellness", "unit_price": 19.99, "unit_cost": 7.40, "profile": "seasonal_winter", "base_demand": 26, "volatility": 0.45, "lead_time_mean": 7, "lead_time_std": 1.3},
        {"sku_id": "SKU-HLTH-006", "sku_name": "Natural Sulfate-Free Restorative Hair Mask 250ml", "category": "Health & Care", "sub_category": "Haircare", "unit_price": 24.99, "unit_cost": 9.20, "profile": "growing", "base_demand": 21, "volatility": 0.27, "lead_time_mean": 8, "lead_time_std": 1.5},
        {"sku_id": "SKU-HLTH-007", "sku_name": "Alcohol Hand Sanitizer Gel Discontinued Formula 500ml", "category": "Health & Care", "sub_category": "Sanitation", "unit_price": 6.99, "unit_cost": 2.50, "profile": "declining", "base_demand": 14, "volatility": 0.42, "lead_time_mean": 6, "lead_time_std": 1.2},
        {"sku_id": "SKU-HLTH-008", "sku_name": "Aromatherapy Ultrasonic Essential Oil Diffuser", "category": "Health & Care", "sub_category": "Home Wellness", "unit_price": 39.99, "unit_cost": 16.00, "profile": "seasonal_q4", "base_demand": 18, "volatility": 0.35, "lead_time_mean": 8, "lead_time_std": 1.4},
        {"sku_id": "SKU-HLTH-009", "sku_name": "Medical Grade Continuous Glucose Sensor Transmitter", "category": "Health & Care", "sub_category": "Medical Devices", "unit_price": 185.00, "unit_cost": 82.00, "profile": "intermittent", "base_demand": 3, "volatility": 0.85, "lead_time_mean": 18, "lead_time_std": 3.2},
        {"sku_id": "SKU-HLTH-010", "sku_name": "Clinical LED Infrared Facial Rejuvenation Mask", "category": "Health & Care", "sub_category": "Skincare Tech", "unit_price": 229.99, "unit_cost": 98.00, "profile": "volatile", "base_demand": 6, "volatility": 0.68, "lead_time_mean": 15, "lead_time_std": 2.8},
    ]

    records = []
    # Calendar features helper
    day_indices = np.arange(n_days)
    day_of_week = date_range.dayofweek.values  # 0=Monday, 6=Sunday
    month_of_year = date_range.month.values
    day_of_year = date_range.dayofyear.values

    # Precompute global seasonality curves
    # Summer peak (June, July, August ~ days 152 to 243)
    summer_curve = np.clip(np.sin((day_of_year - 90) * np.pi / 180), 0, 1) ** 2
    # Winter peak (Nov, Dec, Jan ~ days 305 to 365, and 1 to 31)
    winter_curve = np.clip(np.cos((day_of_year) * 2 * np.pi / 365), 0, 1) ** 2
    # Q4 Holiday peak (Nov 15 to Dec 25)
    q4_curve = np.where((month_of_year == 11) | (month_of_year == 12), 1.0, 0.0)
    # Back to School (August - September)
    bts_curve = np.where((month_of_year == 8) | (month_of_year == 9), 1.0, 0.0)

    # Standard retail weekly lift (higher Friday-Sunday)
    weekly_factors = np.array([0.88, 0.90, 0.94, 0.96, 1.12, 1.25, 1.15])

    for store in stores:
        store_id = store["store_id"]
        store_name = store["store_name"]
        store_mult = store["demand_multiplier"]

        for item in catalog:
            sku_id = item["sku_id"]
            sku_name = item["sku_name"]
            cat = item["category"]
            subcat = item["sub_category"]
            price = item["unit_price"]
            cost = item["unit_cost"]
            profile = item["profile"]
            base = item["base_demand"] * store_mult
            vol = item["volatility"]

            # Trend component
            if profile == "growing":
                # +45% growth across the 2-year window
                trend_factor = 1.0 + (day_indices / n_days) * 0.45
            elif profile == "declining":
                # -35% decline across the 2-year window
                trend_factor = 1.0 - (day_indices / n_days) * 0.35
            else:
                trend_factor = 1.0 + (day_indices / n_days) * 0.03  # slight natural inflation/growth

            # Seasonality component
            if profile == "seasonal_summer":
                season_mult = 1.0 + 1.2 * summer_curve
            elif profile == "seasonal_winter":
                season_mult = 1.0 + 1.4 * winter_curve
            elif profile == "seasonal_q4":
                season_mult = 1.0 + 1.6 * q4_curve
            elif profile == "seasonal_bts":
                season_mult = 1.0 + 1.0 * bts_curve
            else:
                season_mult = np.ones(n_days)

            # Weekly day-of-week factor
            day_mult = weekly_factors[day_of_week]

            # Generate promotional event schedule (e.g. 5% random days on promotion with 40% demand boost)
            promo_chance = 0.05
            promo_active = (np.random.rand(n_days) < promo_chance).astype(int)
            promo_boost = 1.0 + promo_active * 0.40

            if profile == "intermittent":
                # Intermittent / Lumpy demand generation
                # Bernoulli arrival probability + Gamma/Poisson order sizes
                # Zero demand on ~65-75% of days
                arrival_prob = 0.28
                arrivals = (np.random.rand(n_days) < arrival_prob).astype(int)
                # Order sizes when active
                raw_quantities = arrivals * np.random.poisson(lam=max(1, base * 2.5), size=n_days)
            else:
                # Continuous / smooth demand generation
                expected_demand = base * trend_factor * season_mult * day_mult * promo_boost
                # Multiplicative lognormal noise to ensure non-negativity and natural skew
                sigma = vol
                noise = np.random.lognormal(mean=-0.5 * (sigma**2), sigma=sigma, size=n_days)
                raw_quantities = np.round(expected_demand * noise).astype(int)
                raw_quantities = np.maximum(0, raw_quantities)

            # Assemble into records
            for d_idx, dt in enumerate(date_range):
                qty = int(raw_quantities[d_idx])
                # Small promo price discount if promo_active
                p_active = int(promo_active[d_idx])
                actual_price = round(price * 0.85 if p_active else price, 2)
                rev = round(qty * actual_price, 2)
                margin = round(rev - (qty * cost), 2)

                records.append({
                    "date": dt.strftime("%Y-%m-%d"),
                    "store_id": store_id,
                    "store_name": store_name,
                    "sku_id": sku_id,
                    "sku_name": sku_name,
                    "category": cat,
                    "sub_category": subcat,
                    "quantity": qty,
                    "unit_price": actual_price,
                    "unit_cost": cost,
                    "revenue": rev,
                    "gross_margin": margin,
                    "promotion_flag": p_active,
                })

    df = pd.DataFrame(records)
    logger.info("Generated %d rows across %d SKUs and %d Stores.", len(df), len(catalog), len(stores))

    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out, index=False)
        logger.info("Saved raw dataset to: %s", out)

    return df


if __name__ == "__main__":
    generate_retail_sales_data(output_path="data/raw/historical_sales.csv")
