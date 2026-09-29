# Data Architecture & Dictionary

## 1. Overview

This directory contains the raw and processed transactional data utilized by the **Demand Forecasting & Inventory Optimization** analytics platform.

### Critical Boundary Principle
In compliance with enterprise supply-chain analytics best practices:
1. **Observed Historical Sales**: Daily transaction records capturing actual consumer purchases (`date`, `store_id`, `sku_id`, `quantity`, `unit_price`, `revenue`).
2. **Operational Scenario Assumptions**: Supply-chain parameters (`supplier_lead_time_days`, `target_service_level`, `holding_cost_rate`, `initial_inventory_position`) are loaded from configuration and clearly tagged as **Assumptions**, not observed fact.

---

## 2. Data Grain

The analytical grain of this dataset is:
```text
Daily Observation per Fulfillment Center (Store) per Stock Keeping Unit (SKU):
Grain = date x store_id x sku_id
```

Every product/location pair is represented across an uninterrupted calendar sequence, preventing hidden missingness and distinguishing between **True Zero Demand** and unobserved periods.

---

## 3. Directory Layout

```text
data/
├── raw/
│   └── historical_sales.csv         # Raw transactional sales log (2023-01-01 to 2024-12-31)
├── processed/
│   ├── analytics.duckdb             # DuckDB embedded analytical datastore
│   ├── demand_daily.parquet         # Clean analytical dataset with zero-filled continuous dates
│   └── demand_daily.csv             # Exported CSV version for portability
└── README.md                        # Documentation
```

---

## 4. Entity Schema

### `historical_sales.csv` (Raw)
| Column Name | Data Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `transaction_id` | String | Unique transaction identifier | `TXN-20230101-00101` |
| `date` | Date (YYYY-MM-DD) | Calendar date of transaction | `2023-01-01` |
| `store_id` | String | Regional Fulfillment Hub (`FC-East`, `FC-West`, `FC-Central`) | `FC-East` |
| `store_name` | String | Regional store designation | `New York Tri-State Hub` |
| `sku_id` | String | Unique Stock Keeping Unit code | `SKU-ELEC-001` |
| `sku_name` | String | Human readable product title | `Pro Wireless Noise-Canceling Earbuds` |
| `category` | String | High-level merchandising category | `Electronics` |
| `sub_category` | String | Granular product grouping | `Audio & Accessories` |
| `quantity` | Integer | Units purchased (demand quantity) | `18` |
| `unit_price` | Float | Transactional sale price ($USD) | `129.99` |
| `unit_cost` | Float | Standard supplier procurement cost ($USD) | `58.50` |
| `revenue` | Float | `quantity * unit_price` ($USD) | `2339.82` |
| `gross_margin` | Float | `revenue - (quantity * unit_cost)` ($USD) | `1286.82` |
| `promotion_flag` | Integer | Binary indicator (1 = promotional pricing active, 0 = baseline) | `0` |

---

## 5. Merchandising Categories & SKU Profiles

The SKU population reflects 5 distinct retail categories exhibiting diverse statistical properties:

1. **Electronics (10 SKUs)**: High value, moderate demand volatility, steady positive technology adoption trends.
2. **Home & Kitchen (10 SKUs)**: Steady baseline demand, prominent weekend buying patterns, moderate holding cost.
3. **Apparel & Seasonal (10 SKUs)**: High seasonality (winter coats vs summer t-shirts), high weather sensitivity.
4. **Grocery & Pantry (10 SKUs)**: High velocity, low unit price, stable replenishment with low coefficient of variation.
5. **Health & Personal Care (10 SKUs)**: Moderate velocity, periodic purchase cycles, featuring intermittent replacement items.
