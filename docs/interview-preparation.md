# Comprehensive Supply Chain & Forecasting Interview Guide

This guide prepares you to speak authoritatively about the **Demand Forecasting & Inventory Optimization** platform in senior data analyst, analytics engineering, forecasting, and supply chain technical interviews.

---

## 1. Executive Pitches

### 30-Second Recruiter Pitch
> "I engineered an end-to-end demand forecasting and inventory optimization platform in Python and DuckDB that translates historical retail sales into automated replenishment purchase orders. Using an expanding-window backtesting framework across 109,000 daily observations, I benchmarked statistical models and LightGBM against naive baselines, cutting forecast error (WAPE) from 39% down to 29%. I then integrated point forecasts into stochastic safety stock and reorder point models, built a 6-scenario what-if stress engine, and designed an executive 6-page Power BI dashboard that actively flags stockout risks and excess capital lockup."

---

### 2-Minute Architecture & Supply Chain Pitch
> "Most data science portfolio projects stop at training a forecasting model and plotting a curve. In the real world, a forecast is useless unless it guides an operational decision: **How much inventory should we order, and when?**
>
> In this project, I built an end-to-end decision intelligence platform. Starting from 2 years of daily multi-category retail data across 3 distribution hubs, I built an automated data quality pipeline validating completeness, temporal continuity, and physical validity. I designed an analytical DuckDB SQL layer that handles rolling metrics, velocity rankings, and a 9-box ABC-XYZ portfolio matrix.
> 
> To prevent data leakage, I implemented a 3-origin rolling backtesting engine. Holt-Winters achieved the lowest WAPE of 29.4%, outperforming Seasonal Naive by 9 percentage points. I then fed the forecasts into inventory policy formulas that incorporate both demand and supplier lead-time variance using the Silver-Pyke-Peterson equation.
> 
> The system detected $348K trapped in excess inventory across 18 SKUs while identifying 50 SKUs needing immediate replenishment ($411K total spend), with 14 at critical stockout risk (< 3 days of supply). I modeled what-if scenarios—proving that raising service levels from 95% to 99% increases safety stock capital by 41%—and deployed the entire model to an executive Power BI star schema."

---

### 5-Minute Technical Deep Dive
*(See detailed methodology sections in `docs/architecture.md`, `docs/forecasting-methodology.md`, and `docs/inventory-methodology.md` for extended talking points.)*

---

## 2. Core Interview Questions & Answers

### 2.1 SQL Analytics (15 Questions)

1. **How do you calculate a 7-day rolling average without data leakage?**
   - *Answer*: Use window functions with explicit row boundaries: `AVG(quantity) OVER (PARTITION BY store_id, sku_id ORDER BY sale_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)`. If used as a feature for forecasting tomorrow, shift the window to `ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING`.

2. **How did you implement ABC inventory classification in SQL?**
   - *Answer*: Using CTEs and cumulative window sums: calculate SKU revenue, take the cumulative sum ordered by revenue descending (`SUM(revenue) OVER (ORDER BY revenue DESC)`), divide by global revenue (`SUM(revenue) OVER ()`), and classify: $\le 70\%$ as 'A', $70\text{--}90\%$ as 'B', and $> 90\%$ as 'C'.

3. **How do you calculate the Coefficient of Variation in DuckDB SQL?**
   - *Answer*: `STDDEV(quantity) / NULLIF(AVG(quantity), 0)`.

4. **Why use DuckDB instead of traditional PostgreSQL for this project?**
   - *Answer*: DuckDB is an in-process, columnar analytical execution engine optimized for vectorized OLAP queries. It operates directly on Parquet files without network latency, setup overhead, or external database daemon management.

5. **How did you handle missing calendar days in SQL?**
   - *Answer*: We generated a complete Cartesian grid of `(date, store_id, sku_id)` and left-joined transactions, coalescing missing quantities to `0` to explicitly represent true zero demand.

6. **What is the difference between `RANK()`, `DENSE_RANK()`, and `ROW_NUMBER()` in SKU velocity ranking?**
   - *Answer*: `ROW_NUMBER` assigns unique sequential integers. `RANK` assigns identical ranks to ties and skips subsequent numbers (e.g. 1, 2, 2, 4). `DENSE_RANK` assigns identical ranks to ties without skipping (e.g. 1, 2, 2, 3), which is preferred for grouping velocity tiers.

7. **How do you calculate year-over-year demand growth in SQL?**
   - *Answer*: Self-join or use `LAG(quantity, 365) OVER (PARTITION BY store_id, sku_id ORDER BY sale_date)`.

8. **How do you detect duplicate primary keys in DuckDB?**
   - *Answer*: `SELECT date, store_id, sku_id, COUNT(*) FROM table GROUP BY 1,2,3 HAVING COUNT(*) > 1;`

9. **Explain how you calculate Days of Supply directly in SQL.**
   - *Answer*: `inventory_position / NULLIF(avg_daily_demand, 0)`.

10. **How do you compute forecast bias in SQL?**
    - *Answer*: `SUM(forecast - actual) / NULLIF(SUM(actual), 0) * 100`.

11. **How do you handle division by zero in SQL metrics?**
    - *Answer*: Use `NULLIF(denominator, 0)` which converts zeros to `NULL`, preventing query crashes.

12. **What are the performance benefits of partitioning Parquet files by date or category?**
    - *Answer*: Partition pruning allows DuckDB to skip reading irrelevant row groups, dramatically reducing I/O and query execution time.

13. **How do you write a query to identify dead stock?**
    - *Answer*: Filter for SKUs where `SUM(quantity)` over the past 60 days equals 0 while `current_inventory_position > 0`.

14. **How do you calculate reorder triggers in SQL?**
    - *Answer*: `CASE WHEN current_inventory_position <= reorder_point THEN 1 ELSE 0 END`.

15. **What is a CTE and why use it for multi-step inventory metrics?**
    - *Answer*: Common Table Expressions (`WITH ... AS`) break complex multi-step transformations into readable, modular, and maintainable logical blocks.

---

### 2.2 Forecasting & Machine Learning (15 Questions)

1. **Why is WAPE preferred over MAPE in supply chain forecasting?**
   - *Answer*: Retail data has frequent zero-demand days. MAPE calculates $|Y - \hat{Y}| / Y$, which divides by zero and produces infinite errors. WAPE calculates $\sum |Y - \hat{Y}| / \sum Y$, weighting errors by volume and handling intermittent zero-demand periods smoothly.

2. **Why should you never randomly split time-series data into train/test sets?**
   - *Answer*: Random splitting causes future data leakage. Shuffling randomly allows the model to predict past observations using future information, creating unrealistically optimistic validation metrics that collapse in production.

3. **What is expanding-window rolling-origin backtesting?**
   - *Answer*: An evaluation framework where multiple historical cutoff dates are established. For each cutoff origin $T$, the model trains strictly on data $\le T$ and forecasts out $H$ days into the future ($T+1 \dots T+H$). This mimics real-world production deployment.

4. **Why did Holt-Winters outperform LightGBM in your baseline test?**
   - *Answer*: Daily retail sales exhibit strong, stable weekly seasonality (7-day cycles) and smooth trends. Holt-Winters directly isolates level, trend, and seasonal components per series with fewer parameters, avoiding the overfitting and hyperparameter sensitivity of decision trees on non-promoted daily series.

5. **How did you prevent future leakage in LightGBM feature engineering?**
   - *Answer*: All rolling statistics (means, standard deviations) and lag features are strictly computed from $t-1$ and earlier using `shift(1)`. Modifying target $Y$ at date $t$ has zero effect on features calculated at date $t$.

6. **What does a negative forecast bias indicate operationally?**
   - *Answer*: Negative bias ($\sum(\hat{Y} - Y) < 0$) indicates systematic underforecasting. The model consistently projects less demand than actual sales, leading to depleted inventory buffers, stockouts, and lost revenue.

7. **What does a positive forecast bias indicate operationally?**
   - *Answer*: Positive bias ($\sum(\hat{Y} - Y) > 0$) indicates systematic overforecasting, leading to excessive purchase orders, bloated warehouse holding costs, and risk of dead stock.

8. **How does recursive multi-step forecasting work?**
   - *Answer*: At step $h=1$, the model predicts $\hat{Y}_{t+1}$. This prediction is appended to the rolling feature buffer to compute lagged features for step $h=2$, continuing iteratively through horizon $H$.

9. **Why use Seasonal Naive as a benchmark?**
   - *Answer*: In retail, day-of-week demand patterns (e.g. weekend spikes) are strong. A naive model that only carries yesterday's demand forward performs poorly on Mondays following high-volume Sundays. Seasonal Naive ($t-7$) captures this baseline rhythm.

10. **How did you calculate prediction intervals for the final forecast?**
    - *Answer*: We used the empirical residual variance of the champion model across backtesting splits: $\hat{Y} \pm Z \cdot \sigma_{\text{residual}} \cdot \sqrt{1 + (h-1)\cdot 0.03}$, accounting for uncertainty compounding over forward horizon steps.

11. **What is the difference between a confidence interval and a prediction interval?**
    - *Answer*: A confidence interval quantifies uncertainty around the *mean estimate* of a parameter. A prediction interval quantifies uncertainty around an *individual future observation*, incorporating both parameter uncertainty and intrinsic data noise ($\sigma^2$), making prediction intervals much wider.

12. **How do you handle intermittent demand (Croston's quadrant)?**
    - *Answer*: Using Syntetos-Boylan segmentation ($ADI \ge 1.32$ and $CV^2 \ge 0.49$). For lumpy/intermittent items, standard exponential smoothing fails. We separate demand into transaction arrival probability and non-zero order size.

13. **Why did you use 28 days as your forecast horizon?**
    - *Answer*: Because supplier lead times range between 5 and 21 days and inventory reviews occur weekly ($R=7$ days). A 28-day window ensures full coverage over the replenishment lead time plus review period.

14. **How do promotional flags impact demand forecasting?**
    - *Answer*: Promotions induce significant demand elasticity and volume lift. In LightGBM, promotional indicators allow the trees to learn non-linear demand uplifts and subsequent post-promotional dips.

15. **How would you detect forecast drift in production?**
    - *Answer*: Track rolling 14-day and 28-day WAPE and Normalized Bias % against backtest baselines. If WAPE exceeds a 1.5x threshold or bias drifts beyond $\pm 10\%$, trigger an automated retraining alert.

---

### 2.3 Inventory Optimization (15 Questions)

1. **What is the difference between Safety Stock and Reorder Point?**
   - *Answer*: Safety Stock is the static buffer held to absorb random demand and lead-time shocks. Reorder Point is the operational inventory trigger: $ROP = \text{Lead Time Demand} + \text{Safety Stock}$. When inventory position drops to or below ROP, a purchase order must be issued.

2. **Why does supplier lead-time variability matter in safety stock calculations?**
   - *Answer*: In real supply chains, suppliers rarely deliver on exact contract days. If lead time varies with standard deviation $\sigma_L$, safety stock must be expanded: $SS = Z \cdot \sqrt{L \sigma_D^2 + \bar{D}^2 \sigma_L^2}$. The term $\bar{D}^2 \sigma_L^2$ scales quadratically with average demand velocity!

3. **What is Cycle Service Level?**
   - *Answer*: The probability that demand during replenishment lead time will not exceed available stock: $P(\text{Demand in LT} \le ROP)$. A 95% service level implies a 5% stockout probability per replenishment cycle.

4. **Why not target a 99.9% service level on every product?**
   - *Answer*: The normal distribution Z-factor increases non-linearly: $Z_{95\%} = 1.645$, but $Z_{99.9\%} = 3.090$ (nearly double). Targeting 99.9% across slow-moving Class C items ties up immense working capital in holding costs with negligible business benefit.

5. **How do you calculate Recommended Order Quantity (ROQ)?**
   - *Answer*: Under periodic review $(R, S)$, if $IP \le ROP$, $ROQ = S - IP$; otherwise $ROQ = 0$, where $S = \bar{D}(L+R) + SS$.

6. **What is Net Inventory Position ($IP$)?**
   - *Answer*: $IP = \text{On-Hand} + \text{On-Order (Open POs)} - \text{Backorders}$. Using on-hand stock alone causes double-ordering while an existing purchase order is in transit.

7. **How do you define Days of Supply ($DOS$)?**
   - *Answer*: $DOS = IP / \bar{D}$. It represents how many calendar days current stock will last based on expected daily demand.

8. **What threshold defines excess inventory in your system?**
   - *Answer*: $DOS > 45$ days and $IP > S$. This indicates stock exceeding 6 weeks of forward coverage.

9. **What is the annual holding cost rate and how is it used?**
   - *Answer*: Typically 20% to 30% of unit cost (we use 25%), reflecting cost of capital (WACC), warehouse storage, insurance, damage, and obsolescence. Trapped excess capital is multiplied by 25% to compute annual carry cost.

10. **What is dead stock?**
    - *Answer*: Items with positive on-hand inventory but zero consumer demand over 60 consecutive days.

11. **Explain the 9-box ABC-XYZ matrix.**
    - *Answer*: ABC classifies revenue contribution (A=top 70%, B=70-90%, C=tail 10%). XYZ classifies demand variability (X: CV < 0.5, Y: 0.5-1.0, Z: > 1.0). An `AX` item is high revenue and steady (automate replenishment); a `CZ` item is low revenue and erratic (make-to-order or minimal buffer).

12. **How does supplier lead-time delay impact reorder points?**
    - *Answer*: A +20% increase in lead time increases lead-time demand by 20% and expands safety stock, elevating the ROP and requiring earlier reorder triggers.

13. **How does priority scoring ($P1$ to $P4$) help warehouse managers?**
    - *Answer*: Buyers manage hundreds of SKUs daily. A multi-factor priority score (combining revenue class, stockout urgency, and reorder trigger) surfaces the top 10-15 urgent purchase orders requiring immediate approval.

14. **What is the Bullwhip Effect?**
    - *Answer*: The amplification of demand variability as orders move upstream from retailer to distributor to manufacturer. Accurate point-of-sale forecasting and transparent lead-time buffers directly dampen the bullwhip effect.

15. **What happens to safety stock if demand volatility ($\sigma_D$) increases by 30%?**
    - *Answer*: Safety stock scales directly with demand standard deviation. In our scenario engine, a +30% volatility shock increased required safety stock capital from $350K to $394K (+$44K).

---

## 3. Challenge Questions (Direct Defenses)

### Q: "Why LightGBM instead of Prophet or ARIMA?"
> "ARIMA requires fitting separate models per series, which is computationally expensive for hundreds of SKUs and cannot learn cross-series categorical interactions. Prophet is notoriously slow and struggles with daily zero-inflated intermittency. LightGBM trains a unified global model across all series, handles non-linear promotional interactions and calendar features, and runs inference across thousands of points in milliseconds."

### Q: "Why did Holt-Winters win if LightGBM is more advanced?"
> "Because in clean retail panel data without massive promotions, daily demand is dominated by rigid weekly day-of-week seasonality (Friday-Sunday peaks) and smooth level trends. Holt-Winters isolates these three components directly with low variance, whereas decision trees approximate sinusoidal seasonality with step functions, introducing slight discretization errors. We keep LightGBM as the challenger for promotional spikes."

### Q: "How did you prove there is no data leakage?"
> "We enforced strict temporal causality: all rolling features and lags are shifted by $t-1$. In our automated pytest suite (`test_future_leakage_prevention`), we proved that arbitrarily corrupting demand at date $t$ produces zero change in feature vectors at date $t$. Furthermore, our rolling-origin backtesting trains strictly on observations $\le T_{\text{origin}}$."
