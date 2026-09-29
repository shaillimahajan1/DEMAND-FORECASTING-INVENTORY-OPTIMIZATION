# Demand Forecasting Methodology

## 1. Problem Formulation

The core forecasting objective is estimating future daily demand for each product-location pair over a multi-week planning horizon:
$$\hat{Y}_{i,s,t+h} = f\left(\mathcal{H}_{i,s,t}, \mathbf{X}_{i,s,t+h}\right), \quad \forall h \in \{1, 2, \dots, H\}$$
where:
- $i \in \{1, \dots, 50\}$ indexes Stock Keeping Units (SKUs)
- $s \in \{\text{FC-East}, \text{FC-West}, \text{FC-Central}\}$ indexes Regional Fulfillment Hubs
- $t$ is the forecast origin date
- $h$ is the forecast horizon step (configured to $H = 28$ days)
- $\mathcal{H}_{i,s,t} = \{Y_{i,s,\tau} \mid \tau \le t\}$ is the historical demand path observed strictly up to origin $t$
- $\mathbf{X}_{i,s,t+h}$ represents deterministic calendar features and planned exogenous inputs (e.g., pricing, promotional events)

---

## 2. Why a 28-Day Forecast Horizon?

In retail supply chains, procurement decisions operate on cyclical replenishment rhythms:
1. **Supplier Lead Times**: Range between 5 and 21 days across categories.
2. **Review Periods**: Weekly replenishment cycles ($R = 7$ days).
3. **Target Stock Protection**: A 28-day window ($4 \times 7$ days) fully covers the combined lead time plus review period for 98% of the SKU catalog, enabling proactive order generation before stock reaches critical safety thresholds.

---

## 3. Candidate Model Hierarchy

In accordance with forecasting best practices, models progress systematically from simple non-parametric baselines to statistical exponential smoothing and non-linear gradient-boosted trees.

### 3.1 Non-Parametric Baselines
1. **Naive Benchmark**:
   $$\hat{Y}_{t+h} = Y_t$$
   Establishes the minimal performance bar.
2. **Seasonal Naive Benchmark (7-Day Cycle)**:
   $$\hat{Y}_{t+h} = Y_{t - 7 + ((h - 1) \bmod 7) + 1}$$
   Projects the exact corresponding day-of-week demand from the most recent cycle.
3. **Moving Average (7-Day & 28-Day Windows)**:
   $$\hat{Y}_{t+h} = \frac{1}{W} \sum_{j=0}^{W-1} Y_{t-j}$$
   Smooths short-term erratic noise; 7-day captures recent run-rate, 28-day captures monthly level.

### 3.2 Statistical Forecasting: Holt-Winters Exponential Smoothing
For each series exhibiting trend and seasonal patterns, the additive Holt-Winters formulation updates level ($\ell_t$), trend ($b_t$), and seasonal indices ($s_t$ with period $m = 7$):
$$\ell_t = \alpha (Y_t - s_{t-m}) + (1 - \alpha)(\ell_{t-1} + b_{t-1})$$
$$b_t = \beta (\ell_t - \ell_{t-1}) + (1 - \beta) b_{t-1}$$
$$s_t = \gamma (Y_t - \ell_{t-1} - b_{t-1}) + (1 - \gamma) s_{t-m}$$
$$\hat{Y}_{t+h} = \ell_t + h b_t + s_{t - m + ((h - 1) \bmod m) + 1}$$

### 3.3 Machine Learning: Global Multi-Series LightGBM
Rather than fitting 150 isolated models, LightGBM trains a single global decision tree ensemble across all SKU-location time series. This facilitates **cross-series learning**, capturing shared categorical demand dynamics, promotional price elasticity, and macro calendar effects while preserving item-specific idiosyncrasies via target encodings and lagged rollups.

---

## 4. Feature Engineering & Strict Leakage Prevention

To guarantee zero future leakage:
1. **Shifted Lags**: Features at time $t$ utilize $Y_{t-1}, Y_{t-7}, Y_{t-14}, Y_{t-21}, Y_{t-28}$.
2. **Shifted Rolling Window Statistics**:
   $$\text{RollingMean}_{W, t} = \frac{1}{W} \sum_{k=1}^{W} Y_{t-k}$$
   The window strictly looks back from $t-1$, never including $Y_t$.
3. **Sequential Recursive Rollout**: During multi-step out-of-sample inference ($h = 1 \dots 28$), predicted values $\hat{Y}_{t+1}$ dynamically populate the rolling history buffer for subsequent steps $h = 2 \dots 28$, replicating operational reality.

---

## 5. Rolling-Origin Backtesting Architecture

Cross-validation is structured temporally:

```text
Split 1: Train [2023-01-01 to 2024-10-08] --> Test [2024-10-09 to 2024-11-05] (28 Days)
Split 2: Train [2023-01-01 to 2024-11-05] --> Test [2024-11-06 to 2024-12-03] (28 Days)
Split 3: Train [2023-01-01 to 2024-12-03] --> Test [2024-12-04 to 2024-12-31] (28 Days)
```
Each split evaluates 150 series over 28 steps (4,200 points per model per split). Total backtest points across 6 models and 3 splits = **75,600 observations**.

---

## 6. Evaluation Metrics

### 6.1 Weighted Absolute Percentage Error (WAPE)
$$\text{WAPE} = \frac{\sum_{i=1}^N |Y_i - \hat{Y}_i|}{\sum_{i=1}^N Y_i} \times 100\%$$
*Why WAPE over MAPE?* In retail datasets with frequent zero-demand days (especially intermittent and lumpy SKUs), MAPE divides by zero ($|Y - \hat{Y}| / 0 \to \infty$). WAPE aggregates absolute errors across the total volume, providing a numerically robust, volume-weighted error metric.

### 6.2 Forecast Bias
$$\text{Bias} = \sum_{i=1}^N (\hat{Y}_i - Y_i)$$
$$\text{Normalized Bias \%} = \frac{\sum_{i=1}^N (\hat{Y}_i - Y_i)}{\sum_{i=1}^N Y_i} \times 100\%$$
- **Positive Bias ($\hat{Y} > Y$)**: Systematic overforecasting $\to$ excessive inventory accumulation, capital lockup, and holding cost inflation.
- **Negative Bias ($\hat{Y} < Y$)**: Systematic underforecasting $\to$ stockout spikes, lost revenue, and degraded customer service levels.
