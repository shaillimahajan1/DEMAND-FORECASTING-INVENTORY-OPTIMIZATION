# Enterprise Power BI DAX Measures Library

This document specifies the complete DAX calculation logic powering the **Demand Forecasting & Inventory Optimization** Power BI Executive Suite.

---

## 1. Historical Demand & Revenue Measures

### `[Total Actual Demand Units]`
```dax
Total Actual Demand Units = 
SUM(fact_daily_demand[quantity])
```

### `[Total Actual Revenue]`
```dax
Total Actual Revenue = 
SUM(fact_daily_demand[revenue])
```

### `[Total Gross Margin]`
```dax
Total Gross Margin = 
SUM(fact_daily_demand[gross_margin])
```

### `[Gross Margin %]`
```dax
Gross Margin % = 
DIVIDE([Total Gross Margin], [Total Actual Revenue], 0)
```

### `[Average Daily Sales (90D)]`
```dax
Average Daily Sales (90D) = 
CALCULATE(
    AVERAGE(fact_daily_demand[quantity]),
    DATESINPERIOD(dim_date[date], MAX(dim_date[date]), -90, DAY)
)
```

---

## 2. Demand Forecasting & Uncertainty Measures

### `[Forecast Demand Units]`
```dax
Forecast Demand Units = 
SUM(fact_forecast[forecast])
```

### `[Forecast Demand Value ($)]`
```dax
Forecast Demand Value ($) = 
SUMX(
    fact_forecast,
    fact_forecast[forecast] * RELATED(dim_product[unit_price])
)
```

### `[Forecast Lower Bound Units]`
```dax
Forecast Lower Bound Units = 
SUM(fact_forecast[lower_bound])
```

### `[Forecast Upper Bound Units]`
```dax
Forecast Upper Bound Units = 
SUM(fact_forecast[upper_bound])
```

### `[Forecast Uncertainty Bandwidth]`
```dax
Forecast Uncertainty Bandwidth = 
[Forecast Upper Bound Units] - [Forecast Lower Bound Units]
```

---

## 3. Backtesting & Forecast Accuracy Diagnostics

### `[Forecast Absolute Error]`
```dax
Forecast Absolute Error = 
SUM(fct_backtest_predictions[absolute_error])
```

### `[WAPE %]`
```dax
WAPE % = 
DIVIDE(
    SUM(fct_backtest_predictions[absolute_error]),
    SUM(fct_backtest_predictions[actual]),
    0
) * 100
```

### `[RMSE]`
```dax
RMSE = 
SQRT(
    AVERAGEX(
        fct_backtest_predictions,
        (fct_backtest_predictions[actual] - fct_backtest_predictions[forecast]) ^ 2
    )
)
```

### `[Forecast Bias Units]`
```dax
Forecast Bias Units = 
SUM(fct_backtest_predictions[error])
```

### `[Normalized Bias %]`
```dax
Normalized Bias % = 
DIVIDE(
    [Forecast Bias Units],
    SUM(fct_backtest_predictions[actual]),
    0
) * 100
```

---

## 4. Operational Inventory & Replenishment Measures

### `[Current Inventory Position]`
```dax
Current Inventory Position = 
SUM(fact_inventory_plan[current_inventory_position])
```

### `[Inventory Capital Tied Up ($)]`
```dax
Inventory Capital Tied Up ($) = 
SUMX(
    fact_inventory_plan,
    fact_inventory_plan[current_inventory_position] * RELATED(dim_product[unit_cost])
)
```

### `[Total Safety Stock Units]`
```dax
Total Safety Stock Units = 
SUM(fact_inventory_plan[safety_stock])
```

### `[Safety Stock Capital ($)]`
```dax
Safety Stock Capital ($) = 
SUMX(
    fact_inventory_plan,
    fact_inventory_plan[safety_stock] * RELATED(dim_product[unit_cost])
)
```

### `[Recommended Reorder Units]`
```dax
Recommended Reorder Units = 
SUM(fact_inventory_plan[recommended_order_qty])
```

### `[Recommended Reorder Spend ($)]`
```dax
Recommended Reorder Spend ($) = 
SUM(fact_inventory_plan[recommended_order_value])
```

### `[Average Days of Supply]`
```dax
Average Days of Supply = 
AVERAGE(fact_inventory_plan[days_of_supply])
```

---

## 5. Risk Exposure & Prioritization KPIs

### `[Critical Stockout SKUs]`
```dax
Critical Stockout SKUs = 
CALCULATE(
    DISTINCTCOUNT(fact_inventory_plan[sku_id]),
    fact_inventory_plan[stockout_risk_level] = "Critical"
)
```

### `[High Stockout SKUs]`
```dax
High Stockout SKUs = 
CALCULATE(
    DISTINCTCOUNT(fact_inventory_plan[sku_id]),
    fact_inventory_plan[stockout_risk_level] = "High"
)
```

### `[Reorder Triggered SKUs]`
```dax
Reorder Triggered SKUs = 
CALCULATE(
    DISTINCTCOUNT(fact_inventory_plan[sku_id]),
    fact_inventory_plan[reorder_triggered_flag] = 1
)
```

### `[Excess Inventory Capital ($)]`
```dax
Excess Inventory Capital ($) = 
SUM(fact_inventory_plan[excess_capital_tied_up])
```

### `[Annual Excess Holding Cost ($)]`
```dax
Annual Excess Holding Cost ($) = 
SUM(fact_inventory_plan[annual_excess_holding_cost])
```

---

## 6. What-If Scenario Sensitivity Measures

### `[Simulated Safety Stock Units]`
```dax
Simulated Safety Stock Units = 
SUM(fact_scenario[sim_safety_stock])
```

### `[Simulated Safety Stock Capital ($)]`
```dax
Simulated Safety Stock Capital ($) = 
SUM(fact_scenario[sim_safety_stock_capital])
```

### `[Delta SS Capital vs Baseline ($)]`
```dax
Delta SS Capital vs Baseline ($) = 
VAR BaselineCapital = 
    CALCULATE(
        [Simulated Safety Stock Capital ($)],
        fact_scenario[scenario_id] = "SCEN_01"
    )
RETURN
    [Simulated Safety Stock Capital ($)] - BaselineCapital
```

### `[Simulated Reorder Spend ($)]`
```dax
Simulated Reorder Spend ($) = 
SUM(fact_scenario[sim_recommended_order_value])
```
