# Architecture Decision Records (ADRs)

---

## ADR-001: Dataset Selection and Multi-Category Granularity
- **Context**: The analytics platform requires a realistic retail demand footprint demonstrating diverse statistical behaviors: steady staples, seasonal merchandise, trend growth, volatility, and intermittent spare parts.
- **Decision**: Implemented a multi-category daily retail transactional datastore covering 50 curated SKUs across 5 departments, 3 regional distribution hubs, and 731 uninterrupted calendar days (109,650 observations).
- **Alternatives Considered**: Public M5 Walmart dataset (massive size, excessive download dependencies) or UCI Online Retail (sparse transactional timestamps, messy refunds).
- **Trade-offs**: Synthetic simulation grounded in real retail mathematics allows full control over ground-truth variance, lead-time parameters, and reproducible local execution without cloud API barriers.
- **Consequences**: Fast local pipeline execution (< 60s) with 100% reproducible statistical properties.

---

## ADR-002: Forecast Granularity and 28-Day Horizon
- **Context**: Replenishment planners require a forecast window that covers supplier lead times and weekly review cadences.
- **Decision**: Standardized on daily granularity projected over a 28-day forward horizon ($H = 28$).
- **Alternatives Considered**: Weekly aggregation or 90-day horizon.
- **Trade-offs**: Daily granularity requires modeling day-of-week seasonality (7-day cycles) and zero-demand days, but directly enables daily reorder point triggers that weekly models miss.
- **Consequences**: Perfectly matches operational lead times (5 to 10 days) and weekly periodic review ($R = 7$ days).

---

## ADR-003: Baseline Strategy and Non-Parametric Benchmarks
- **Context**: Many machine learning projects deploy complex models without proving superiority over simple baselines.
- **Decision**: Mandated 4 baseline benchmarks: Naive ($t+1 = t$), Seasonal Naive (7-day lag), Moving Average 7-day, and Moving Average 28-day.
- **Alternatives Considered**: Evaluating ML models against random chance or arbitrary train/test splits.
- **Trade-offs**: Modest additional computational time during backtesting.
- **Consequences**: Proved conclusively that Holt-Winters achieved a 24.7% relative WAPE reduction over Naive (29.40% vs 39.06%).

---

## ADR-004: Model Selection Hierarchy & Champion Framework
- **Context**: Balancing statistical interpretability, multi-series cross-learning, and computational efficiency.
- **Decision**: Built a champion-challenger architecture comparing individual statistical models (Holt-Winters) against a global LightGBM gradient boosted tree.
- **Alternatives Considered**: Fitting 150 individual ARIMA/Prophet models (computationally slow, unscalable).
- **Trade-offs**: Holt-Winters excelled on stable/seasonal items; LightGBM captured promotional non-linearities and calendar interactions.
- **Consequences**: Selected Holt-Winters as production champion (29.40% WAPE) with LightGBM serialized as the promo challenger model.

---

## ADR-005: Expanding-Window Rolling-Origin Backtesting
- **Context**: Random k-fold cross-validation is invalid for time series due to temporal autocorrelation and future leakage.
- **Decision**: Implemented expanding-window backtesting across 3 historical cutoff origins ($T-84, T-56, T-28$ days). All rolling statistics and lags are strictly shifted by $t-1$.
- **Alternatives Considered**: Single static train/test split.
- **Trade-offs**: Backtesting takes ~30 seconds across 75,600 evaluation points.
- **Consequences**: Guarantees zero data leakage and defensible, out-of-sample performance numbers.

---

## ADR-006: Stochastic Lead-Time Safety Stock Formulation
- **Context**: Deterministic lead-time formulas ($SS = Z \sigma_D \sqrt{L}$) underestimate inventory risk when supplier transit times fluctuate.
- **Decision**: Adopted the Silver-Pyke-Peterson combined uncertainty formulation:
  $$SS = Z \cdot \sqrt{L \cdot \sigma_D^2 + \bar{D}^2 \cdot \sigma_L^2}$$
- **Alternatives Considered**: Constant lead-time formula or empirical simulation.
- **Trade-offs**: Requires estimating supplier delivery variance $\sigma_L$.
- **Consequences**: Accurately buffers high-velocity items against port and transit congestion.

---

## ADR-007: What-If Scenario Engine and Capital Delta Framework
- **Context**: Executive leadership needs to understand supply chain stress impacts before disruptions occur.
- **Decision**: Engineered a deterministic scenario simulation engine testing 6 distinct supply chain perturbations (Demand Surge +15%, Lead Time Disruption +20%, Premium SL 99%, Volatility +30%, Compound Stress) and reporting capital deltas.
- **Alternatives Considered**: Monte Carlo simulation of arbitrary parameter distributions.
- **Trade-offs**: Discrete scenarios provide clear, actionable boardroom answers rather than complex probability clouds.
- **Consequences**: Clearly demonstrated that elevating service levels to 99% requires +$145K in additional safety stock capital (+41.4%).
