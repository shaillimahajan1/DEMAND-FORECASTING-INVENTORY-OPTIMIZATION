# System & Methodology Limitations

## 1. Censored Demand vs. True Consumer Demand
In retail transactional databases, recorded sales represent **constrained demand** (sales realized given available stock). When an item experiences a stockout, demand is artificially recorded as zero units rather than true unconstrained consumer appetite. In the absence of lost-sale tracking or web impressions, models trained on recorded sales slightly underestimate true potential velocity.

## 2. Supplier Lead-Time Endogeneity
While the model incorporates stochastic lead times ($\sigma_L > 0$), it assumes supplier delivery transit times are independent and identically distributed. In reality:
- Extreme weather, port strikes, and global supply chain disruptions introduce macro correlation across all suppliers simultaneously.
- Supplier lead times often expand endogenously during peak holiday periods (Q4) when factory capacity is constrained.

## 3. Inventory Position Data Boundaries
Current on-hand and on-order inventory figures are modeled through an explicit operational scenario snapshot. While statistically calibrated to realistic retail inventory dynamics (20% low stock, 65% normal, 15% excess), production deployment requires continuous bidirectional integration with an enterprise ERP (SAP, Oracle NetSuite, Manhattan Associates WMS).

## 4. Constant Holding & Procurement Unit Economics
The model applies a standardized 25% annual holding cost rate and fixed ordering cost ($50/PO). In practice:
- Refrigerated/perishable grocery SKUs have higher holding and spoilage costs than ambient electronics.
- Suppliers frequently offer tiered volume price breaks (e.g. 5% discount for ordering > 500 units), which may alter economic order quantities.

## 5. Non-Stationary Economic Regimes
Backtesting was conducted across 2 years of daily data (2023-2024). Substantial macroeconomic regime shifts (e.g. sudden inflationary shocks, rapid interest rate shifts, consumer sentiment collapses) would require retraining with adaptive window discounting.
