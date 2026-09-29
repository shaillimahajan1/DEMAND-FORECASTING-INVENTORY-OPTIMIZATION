# Supply Chain & Forecasting Metrics Reference

This document details the mathematical definitions, computational units, and business interpretations for all analytical metrics utilized across the platform.

---

## 1. Forecast Accuracy & Error Metrics

### 1.1 Weighted Absolute Percentage Error (WAPE)
$$\text{WAPE} = \frac{\sum_{i=1}^N |Y_i - \hat{Y}_i|}{\sum_{i=1}^N Y_i} \times 100\%$$
- **Units**: Percentage (%)
- **Range**: $0\%$ to $\infty$ (Lower is better; $< 30\%$ represents solid retail performance on volatile categories)
- **Supply Chain Interpretation**: Unlike Mean Absolute Percentage Error (MAPE), which divides by individual actuals and explodes on zero-demand days, WAPE weights errors by volume. A 10-unit error on a 100-unit day impacts WAPE far less than a 10-unit error on a 5-unit day.

### 1.2 Mean Absolute Error (MAE)
$$\text{MAE} = \frac{1}{N} \sum_{i=1}^N |Y_i - \hat{Y}_i|$$
- **Units**: Physical Units (e.g., items, boxes)
- **Interpretation**: Represents the expected average daily deviation in physical item units. Linear penalty across all error magnitudes.

### 1.3 Root Mean Squared Error (RMSE)
$$\text{RMSE} = \sqrt{\frac{1}{N} \sum_{i=1}^N (Y_i - \hat{Y}_i)^2}$$
- **Units**: Physical Units
- **Interpretation**: Quadratic penalty that disproportionately punishes large forecasting outliers. When $\text{RMSE} \gg \text{MAE}$, the model makes occasional extreme forecasting blunders that destabilize warehouse labor and transport capacity.

### 1.4 Forecast Bias & Normalized Bias %
$$\text{Net Bias} = \sum_{i=1}^N (\hat{Y}_i - Y_i), \quad \text{Normalized Bias \%} = \frac{\sum (\hat{Y}_i - Y_i)}{\sum Y_i} \times 100\%$$
- **Units**: Units and Percentage (%)
- **Significance**:
  - **Positive Bias (+)**: The model consistently predicts more than consumers purchase $\to$ causes excessive inventory accumulation, trapped working capital, and scrap.
  - **Negative Bias (-)**: The model consistently under-predicts demand $\to$ causes stockouts, missed sales, backorders, and dissatisfied customers.

---

## 2. Demand Profile & Intermittency Metrics

### 2.1 Coefficient of Variation (CV) & $CV^2$
$$CV = \frac{\sigma_D}{\bar{D}}, \quad CV^2 = \left(\frac{\sigma_D}{\bar{D}}\right)^2$$
- **Interpretation**: Standardized measure of demand volatility relative to the mean.
  - $CV < 0.50$: Smooth, steady demand (Class X)
  - $0.50 \le CV < 1.00$: Moderately variable (Class Y)
  - $CV \ge 1.00$: Highly erratic (Class Z)

### 2.2 Average Demand Interval (ADI)
$$ADI = \frac{\text{Total Observed Periods}}{\text{Periods with Non-Zero Demand}}$$
- **Interpretation**: Average number of days between customer transactions.
  - $ADI < 1.32$: Regular, fast-moving demand
  - $ADI \ge 1.32$: Intermittent demand (Croston / Syntetos-Boylan quadrant)

---

## 3. Inventory Optimization & Replenishment Metrics

### 3.1 Safety Stock ($SS$)
$$SS = Z \cdot \sqrt{L \cdot \sigma_D^2 + \bar{D}^2 \cdot \sigma_L^2}$$
- **Units**: Physical buffer units
- **Interpretation**: The inventory held to absorb random demand surges and supplier delivery tardiness at a confidence level of $Z$.

### 3.2 Reorder Point ($ROP$)
$$ROP = (\bar{D} \cdot L) + SS$$
- **Units**: Inventory threshold units
- **Interpretation**: The exact inventory level that triggers automated purchase order placement.

### 3.3 Days of Supply ($DOS$)
$$DOS = \frac{\text{Current Inventory Position}}{\text{Average Daily Demand Rate}}$$
- **Units**: Calendar days of forward coverage
- **Operational Tiers**:
  - $< 3.0\text{ days}$: Critical Stockout Risk
  - $3.0\text{--}7.0\text{ days}$: High Risk
  - $7.0\text{--}14.0\text{ days}$: Normal Reorder Zone
  - $14.0\text{--}45.0\text{ days}$: Healthy Stock
  - $> 45.0\text{ days}$: Excess Inventory
