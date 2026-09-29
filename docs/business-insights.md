# Empirical Business Insights & Executive Findings

All findings below reflect actual computational execution outputs from the end-to-end analytics pipeline on 109,650 historical sales records and 75,600 rolling-origin backtest points.

---

## Insight 1: Demand Concentration & Pareto Merchandising Skew

- **Observation**: Demand and revenue follow an extreme Pareto distribution across the SKU catalog.
- **Evidence**: The ABC classification reveals that top Class A products account for **70.0%** of total realized revenue despite representing only **20.0%** of total product breadth (e.g. `SKU-APPR-002`, `SKU-ELEC-001`, `SKU-ELEC-005`). Class C products account for only **10.0%** of total revenue.
- **Operational Implication**: Equal inventory attention across all SKUs results in misallocated buyer time and working capital. A stockout on a Class A item causes substantial revenue erosion, whereas stockouts on Class C items have minimal financial impact.
- **Recommended Action**: Implement differentiated service level targets: 98% for Class A, 95% for Class B, and 90% for Class C items. Transition Class A replenishment to automated daily continuous review.
- **Assumptions**: Revenue contribution remains stable over the upcoming quarter.
- **Limitation**: Gross revenue does not account for individual customer acquisition costs or strategic gateway basket builders.

---

## Insight 2: Forecasting Benchmark Superiority (24.7% Relative Error Reduction)

- **Observation**: Holt-Winters Exponential Smoothing significantly outperformed both naive baselines and global machine learning models across the 3 rolling backtest origins.
- **Evidence**:
  - `Holt_Winters`: **29.40% WAPE**, MAE = 10.07, RMSE = 17.79
  - `Moving_Average_7d`: **31.44% WAPE**, MAE = 10.77, RMSE = 18.30
  - `Moving_Average_28d`: **31.73% WAPE**, MAE = 10.87, RMSE = 19.08
  - `LightGBM`: **38.03% WAPE**, MAE = 13.03, RMSE = 20.90
  - `Seasonal_Naive_7d`: **38.31% WAPE**, MAE = 13.12, RMSE = 22.23
  - `Naive`: **39.06% WAPE**, MAE = 13.38, RMSE = 22.68
- **Operational Implication**: Holt-Winters delivers a **9.66 percentage point absolute reduction in WAPE** compared to the Naive baseline (a **24.7% relative improvement**), providing tighter inventory buffers and reducing forecast variance.
- **Recommended Action**: Deploy Holt-Winters as the champion production forecasting model for baseline replenishment, with LightGBM maintained as a challenger model for promo-heavy periods.
- **Assumptions**: Additive weekly seasonality persists without macroeconomic regime shifts.
- **Limitation**: Holt-Winters models series independently and does not natively incorporate cross-item cannibalization.

---

## Insight 3: Forecast Error Bias & Directional Inventory Risk

- **Observation**: Candidate models exhibit distinct directional forecast biases that produce diametrically opposed inventory risks.
- **Evidence**:
  - `Holt_Winters` exhibits a slight negative bias of **-4.76%** (-20,554 units across 12,600 test points).
  - `LightGBM` exhibits a positive bias of **+6.06%** (+26,155 units).
  - `Naive` exhibits severe underforecasting with a negative bias of **-13.74%** (-59,308 units).
- **Operational Implication**: LightGBM's positive bias tends to build excess inventory and increase holding costs. Holt-Winters' mild negative bias carries a slight stockout risk, which must be counterbalanced by the safety stock buffer.
- **Recommended Action**: Retain Holt-Winters with an explicit safety stock adjustment factor calibrated to compensate for the -4.76% negative bias on high-velocity Class A items.
- **Assumptions**: Historical residual bias remains stationary over the 28-day out-of-sample window.
- **Limitation**: Residual variance does not account for sudden supplier de-listings or market stockouts.

---

## Insight 4: Working Capital Lockup in Excess Inventory ($348.7K Exposure)

- **Observation**: Substantial working capital is trapped in dormant and slow-moving SKUs.
- **Evidence**: 18 SKU-location pairs exhibit Days of Supply ($DOS$) exceeding 45 days, locking up **$348,713.62** in excess inventory capital and incurring **$87,178.41** in annual holding costs (at 25% cost of carry).
- **Operational Implication**: Trapped capital constrains procurement liquidity needed to fund high-priority stockout replenishment orders.
- **Recommended Action**: Immediately suspend replenishment orders on all 18 excess SKUs. Initiate inter-hub stock transfers from FC-East to FC-West to balance regional supply before placing external purchase orders.
- **Assumptions**: Annual holding cost rate of 25% accurately reflects corporate capital costs and warehouse space.
- **Limitation**: Inventory transfer freight costs are assumed negligible relative to unit holding costs.

---

## Insight 5: Immediate Stockout Exposure ($411.7K Reorder Commitment)

- **Observation**: 50 SKU-location pairs have breached their Reorder Point ($IP \le ROP$), with 14 at Critical Risk ($DOS < 3$ days).
- **Evidence**: Replenishment recommendations indicate an immediate purchase order requirement of **24,798 units** representing **$411,679.10** in procurement spend.
- **Operational Implication**: Failure to release purchase orders within 48 hours will trigger stockouts across high-margin Electronics and Apparel hero items, resulting in lost sales and degraded service levels.
- **Recommended Action**: Procurement buyers should immediately approve and release the 14 `P1 - Critical` purchase orders, followed by the 29 `P2 - High` orders within the current weekly review cycle.
- **Assumptions**: Suppliers can deliver within their standard contracted lead times (5 to 10 days).
- **Limitation**: Assumes suppliers have adequate capacity without manufacturing backlogs.

---

## Insight 6: Non-Linearity of Service Level Working Capital (The 99% SL Penalty)

- **Observation**: Increasing customer service level targets from 95% to 99% incurs severe exponential capital penalties.
- **Evidence**: What-If scenario simulations reveal:
  - Baseline (95% SL): Safety Stock Capital = **$350,113.66**
  - Premium (99% SL): Safety Stock Capital = **$495,176.27**
  - **Capital Delta**: **+$145,062.61 (+41.4% increase)** to capture just 4% additional service availability.
- **Operational Implication**: A blanket 99% service level policy across all merchandise is economically irrational and ties up excessive working capital in low-margin goods.
- **Recommended Action**: Enforce a strict tiered service level architecture: reserve 99% SL strictly for AX hero items (`SKU-ELEC-001`, `SKU-GROC-001`); maintain 95% for Class B, and 90% for Class C.
- **Assumptions**: Normal distribution of lead time demand holds in the distribution tails.
- **Limitation**: Ignores potential volume discounts from bulk procurement.
