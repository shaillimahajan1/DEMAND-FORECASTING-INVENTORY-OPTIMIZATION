# Data Dictionary & Entity Catalog

## 1. Primary Datasets

### 1.1 `data/processed/demand_daily.parquet` & `demand_daily.csv`
**Grain**: 1 row per `date` $\times$ `store_id` $\times$ `sku_id`  
**Temporal Span**: 2023-01-01 to 2024-12-31 (731 continuous calendar days)  
**Row Count**: 109,650 rows (3 stores $\times$ 50 SKUs $\times$ 731 days)

| Column Name | Physical Type | Description | Unit / Range |
| :--- | :--- | :--- | :--- |
| `date` | Date (YYYY-MM-DD) | Calendar date of transaction/observation | 2023-01-01 to 2024-12-31 |
| `store_id` | String (Category) | Regional Fulfillment Hub identifier | `FC-East`, `FC-West`, `FC-Central` |
| `store_name` | String | Regional distribution hub designation | e.g. `New York Tri-State Hub` |
| `sku_id` | String (Category) | Stock Keeping Unit unique identifier | e.g. `SKU-ELEC-001` |
| `sku_name` | String | Commercial product catalog name | e.g. `Pro Wireless Noise-Canceling Earbuds` |
| `category` | String (Category) | High-level merchandising department | Electronics, Home & Kitchen, Apparel, Grocery, Health |
| `sub_category` | String (Category) | Granular product grouping | Audio, Cookware, Outerwear, Coffee & Tea, etc. |
| `quantity` | Integer | Units demanded / sold (explicit 0 if unobserved) | 0 to 180 units |
| `unit_price` | Float | Transactional selling price | $4.99 to $299.99 USD |
| `unit_cost` | Float | Cost of Goods Sold (procurement unit cost) | $2.20 to $135.00 USD |
| `revenue` | Float | Realized gross sales (`quantity * unit_price`) | USD ($) |
| `gross_margin` | Float | Dollar margin (`revenue - (quantity * unit_cost)`) | USD ($) |
| `promotion_flag` | Integer (Binary) | Marketing promotional campaign indicator (1=active, 0=none) | 0 or 1 |

---

### 1.2 `outputs/forecasts/final_forecasts.csv`
**Grain**: 1 row per `forecast_date` $\times$ `store_id` $\times$ `sku_id`  
**Forecast Horizon**: 28 out-of-sample forward days

| Column Name | Physical Type | Description |
| :--- | :--- | :--- |
| `store_id` | String | Regional Fulfillment Hub |
| `sku_id` | String | Stock Keeping Unit identifier |
| `forecast_date` | Date (YYYY-MM-DD) | Projected calendar day |
| `horizon_step` | Integer | Day offset into forecast horizon ($h \in [1, 28]$) |
| `forecast` | Float | Point demand forecast |
| `model_name` | String | Champion model generating forecast (e.g. `Holt_Winters`) |
| `uncertainty_std` | Float | Forecast standard error at horizon $h$ |
| `lower_bound` | Float | Lower 95% Prediction Interval bound ($\max(0, \hat{y} - 1.96 \cdot \sigma_h)$) |
| `upper_bound` | Float | Upper 95% Prediction Interval bound ($\hat{y} + 1.96 \cdot \sigma_h$) |

---

### 1.3 `outputs/inventory/inventory_recommendations.csv`
**Grain**: 1 row per `store_id` $\times$ `sku_id` (450 operational SKU-location pairs)

| Column Name | Physical Type | Description |
| :--- | :--- | :--- |
| `forecast_demand_28d` | Float | Cumulative 28-day demand forecast |
| `avg_daily_demand` | Float | Expected daily sales rate ($\bar{D}$) |
| `std_daily_demand` | Float | Standard deviation of daily demand ($\sigma_D$) |
| `lead_time_days` | Float | Supplier replenishment lead time ($L$) |
| `lead_time_std_days` | Float | Standard deviation of lead time ($\sigma_L$) |
| `service_level` | Float | Target cycle service level policy (0.95 = 95%) |
| `safety_stock` | Float | Buffer inventory units ($SS = Z \cdot \sqrt{L \sigma_D^2 + \bar{D}^2 \sigma_L^2}$) |
| `reorder_point` | Float | Replenishment trigger ($ROP = \bar{D} \cdot L + SS$) |
| `order_up_to_level` | Float | Base stock level ($S = \bar{D}(L + R) + SS$) |
| `current_inventory_position`| Float | Net inventory ($IP = \text{On-Hand} + \text{On-Order} - \text{Backorders}$) |
| `days_of_supply` | Float | Forward coverage ($DOS = IP / \bar{D}$) |
| `reorder_triggered_flag` | Integer | Binary flag (1 if $IP \le ROP$, 0 otherwise) |
| `recommended_order_qty` | Float | Recommended PO quantity ($\max(0, S - IP)$ if triggered) |
| `recommended_order_value` | Float | Procurement spend commitment ($ROQ \times \text{unit\_cost}$) |
| `stockout_risk_level` | String | Operational tier: `Critical`, `High`, `Medium`, `Low` |
| `is_excess_inventory` | Integer | Binary flag (1 if $DOS > 45$ days and $IP > S$) |
| `excess_capital_tied_up` | Float | Trapped working capital ($(\text{Excess Units}) \times \text{unit\_cost}$) |
| `annual_excess_holding_cost`| Float | Cost of carry at 25% annual holding rate |
| `priority_score` | Integer | Multi-factor operational urgency score (0 to 120) |
| `priority_tier` | String | Action tier: `P1 - Critical`, `P2 - High`, `P3 - Standard`, `P4 - Stable` |
