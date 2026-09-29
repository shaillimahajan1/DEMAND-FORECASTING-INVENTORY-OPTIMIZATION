# Data Quality & Validation Report

**Generated:** 2026-09-29T15:51:28.032966  
**Overall Validation Status:** **PASSED**

---

## 1. Executive Summary

| Metric | Measured Value |
| :--- | :--- |
| **Total Observations** | 109,650 rows |
| **Unique Products (SKUs)** | 50 |
| **Regional Distribution Hubs** | 3 |
| **Merchandising Categories** | 5 |
| **Historical Range** | 2023-01-01 to 2024-12-31 (731 days) |
| **Explicit Zero-Demand Periods** | 7,947 (7.25%) |

---

## 2. Integrity Checks Breakdown

### 2.1 Completeness Check: `PASSED`
- **Null values detected:** 0 columns.
- **Finding:** No missing records found across required dimensions and metrics.

### 2.2 Uniqueness Check: `PASSED`
- **Grain:** `date x store_id x sku_id`
- **Duplicate Records:** 0

### 2.3 Value Domain Validity Check: `PASSED`
- **Negative Demand Quantities:** 0
- **Non-Positive Unit Prices:** 0
- **Non-Positive Unit Costs:** 0

### 2.4 Temporal Integrity Check: `PASSED`
- **Full Continuous Sequence:** 731 calendar days per series.
- **Series with Missing Date Gaps:** 0
