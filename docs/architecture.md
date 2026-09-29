# System Architecture & Technical Flow

## 1. Executive Architecture Overview

The **Demand Forecasting & Inventory Optimization** platform bridges statistical time-series forecasting, machine learning, and operational supply chain decision intelligence. Rather than treating forecasting as an isolated algorithmic exercise, the architecture connects consumer demand signals directly to safety stock buffers, reorder thresholds, capital allocation, and executive what-if scenario simulations.

```mermaid
flowchart TD
    subgraph Data_Ingestion["1. Data Ingestion & Quality Layer"]
        A[Raw Sales Transactions CSV] --> B[Data Quality Validator]
        B -->|Completeness, Uniqueness, Validity| C[Clean Daily Demand Grid]
        C --> D[(DuckDB Embedded Datastore)]
    end

    subgraph SQL_Analytics["2. DuckDB SQL Analytical Layer"]
        D --> E[Staging View: stg_sales]
        E --> F[Fact Daily Demand: fct_daily_demand]
        E --> G[Rolling Metrics: agg_rolling_demand]
        E --> H[9-Box Matrix: dim_abc_xyz_segmentation]
        E --> I[Velocity Profiling: agg_sku_location_profile]
    end

    subgraph Forecasting_Backtesting["3. Forecasting & Backtesting Engine"]
        C --> J[Demand Profiler: ADI, CV2, Syntetos-Boylan]
        J --> K[Candidate Model Benchmark]
        K --> L1[Naive Benchmark]
        K --> L2[Seasonal Naive 7D]
        K --> L3[Moving Average 7D / 28D]
        K --> L4[Holt-Winters Exp Smoothing]
        K --> L5[Global LightGBM Multi-Series]
        L1 & L2 & L3 & L4 & L5 --> M[Rolling-Origin Backtester]
        M --> N[Evaluation Engine: WAPE, MAE, RMSE, Bias]
        N --> O[Champion Model Selection & Final 28D Forecast]
    end

    subgraph Inventory_Optimization["4. Inventory Optimization & Operational Policies"]
        O --> P[Safety Stock Engine: Demand & LT Uncertainty]
        P --> Q[Reorder Point ROP & Order-Up-To Level S]
        Q --> R[Inventory Position & Days of Supply]
        R --> S[Stockout Exposure & Excess Capital Analysis]
        S --> T[Replenishment Prioritization Matrix P1-P4]
    end

    subgraph Scenario_Engine["5. What-If Scenario Stress Testing"]
        T --> U[Simulation Engine: Demand +15%, LT +20%, SL 99%, Vol +30%]
        U --> V[Capital & Risk Variance Deltas]
    end

    subgraph BI_Presentation["6. Enterprise BI & Decision Layer"]
        D & O & T & V --> W[Power BI Star Schema Tables]
        W --> X[6-Page Executive Decision Dashboard]
    end
```

---

## 2. Core Architectural Pillars

### Pillar 1: Explicit Data Grain & Separation of Boundaries
The fundamental transactional grain is:
$$\text{Observation} = \text{Date} \times \text{Store ID} \times \text{SKU ID}$$
Crucially, the architecture enforces a strict conceptual wall between:
1. **Observed Historical Transactions**: Actual consumer sales recorded in transactions logs.
2. **Model Forecasts & Prediction Intervals**: Mathematical projections of future mean demand and variance.
3. **Operational Assumptions & Policies**: Target service levels ($Z$), review periods ($R$), and supplier lead times ($L$).
4. **Stress Scenarios**: Synthetic multipliers applied to test portfolio resilience under disruption.

### Pillar 2: High-Performance Embedded SQL Layer (DuckDB)
DuckDB provides zero-copy OLAP query execution directly against Parquet files. Complex analytical window functions, cumulative Pareto revenue shares, and rolling demand statistics execute in milliseconds without external database infrastructure.

### Pillar 3: Leak-Free Rolling-Origin Backtesting
Time series cannot be randomly partitioned. The backtesting framework implements an expanding-window strategy evaluating candidate models across 3 historical origins ($T - 84$, $T - 56$, $T - 28$ days). All lag generation and rolling statistics strictly shift by $t-1$, ensuring zero future leakage.

### Pillar 4: Stochastic Lead-Time Inventory Formulation
Rather than assuming deterministic lead times, safety stocks are computed using the Silver-Pyke-Peterson combined uncertainty equation:
$$SS = Z \cdot \sqrt{L \cdot \sigma_D^2 + \bar{D}^2 \cdot \sigma_L^2}$$
This guarantees that supplier delivery variance directly expands the inventory buffer.
