# Inventory Optimization & Replenishment Methodology

## 1. Executive Overview

Forecasting estimates the future expected demand $\hat{Y}$; inventory optimization determines the capital required to buffer against uncertainty while meeting target customer service levels.

The inventory engine implements a **Continuous Review $(s, S)$ with Periodic Review $(R, s, S)$ hybrid framework**, translating point demand forecasts and demand/lead-time variances into concrete purchase order recommendations.

---

## 2. Safety Stock Formulations

### 2.1 Formulation A: Deterministic Lead Time
When supplier lead times are guaranteed constant ($L = \text{constant}, \sigma_L = 0$):
$$SS = Z \cdot \sigma_D \cdot \sqrt{L}$$
where:
- $Z$: Service level factor (standard normal distribution inverse cumulative probability $\Phi^{-1}(\text{SL})$)
- $\sigma_D$: Standard deviation of daily consumer demand
- $L$: Replenishment lead time in days

### 2.2 Formulation B: Combined Demand & Lead-Time Uncertainty (Silver-Pyke-Peterson)
In real-world retail supply chains, supplier transit times fluctuate due to port congestion, carrier delays, and customs processing ($\sigma_L > 0$). When both demand and lead time are independent random variables:
$$\text{Var}(\text{Lead Time Demand}) = L \cdot \sigma_D^2 + \bar{D}^2 \cdot \sigma_L^2$$
$$SS = Z \cdot \sqrt{L \cdot \sigma_D^2 + \bar{D}^2 \cdot \sigma_L^2}$$
where:
- $\bar{D}$: Average daily demand rate
- $\sigma_L$: Standard deviation of supplier replenishment lead time

*Operational Significance*: The term $\bar{D}^2 \cdot \sigma_L^2$ demonstrates that high-velocity products ($\bar{D}$) are extraordinarily sensitive to supplier unreliability, requiring substantially higher safety stock buffers even if consumer demand variability $\sigma_D$ is modest.

---

## 3. Customer Service Levels & Z-Factor Mapping

The business specifies Cycle Service Level ($CSL$), defined as the probability of not experiencing a stockout during a replenishment lead-time cycle:
$$P(\text{Demand during Lead Time} \le ROP) = \text{CSL}$$

| Target Service Level | Z-Score Factor | Stockout Cycle Risk Probability | Business Use Case |
| :---: | :---: | :---: | :--- |
| **90.0%** | `1.2816` | 10.0% | Slow-moving Class C tail items; non-critical spare parts |
| **95.0%** | `1.6449` | 5.0% | **Standard Baseline Policy** across most Class B & A catalog |
| **97.5%** | `1.9600` | 2.5% | High-margin core merchandise; promotional hero items |
| **99.0%** | `2.3263` | 1.0% | Mission-critical Class A anchor products; brand reputation items |
| **99.9%** | `3.0902` | 0.1% | Life-critical healthcare products; contractual SLAs |

---

## 4. Reorder Point (ROP) & Order-Up-To Level ($S$)

### 4.1 Reorder Point ($ROP$)
The inventory level that triggers an automated procurement reorder:
$$ROP = \text{Demand During Lead Time} + SS = (\bar{D} \cdot L) + SS$$

### 4.2 Order-Up-To Level ($S$)
Under a periodic review cycle of $R = 7$ days, the target stock ceiling must cover both the lead time and the review cycle until the subsequent order arrives:
$$S = \bar{D} \cdot (L + R) + SS$$

---

## 5. Inventory Position & Replenishment Logic

### 5.1 Net Inventory Position ($IP$)
Purchasing decisions cannot rely solely on physical on-hand stock:
$$IP = \text{On-Hand Inventory} + \text{On-Order Inventory (Open POs)} - \text{Customer Backorders}$$

### 5.2 Recommended Order Quantity ($ROQ$)
$$\text{ROQ} = \begin{cases} 
S - IP & \text{if } IP \le ROP \\
0 & \text{if } IP > ROP 
\end{cases}$$
When triggered, the purchase order value is:
$$\text{Recommended Order Value} = \text{ROQ} \times \text{Unit Cost}$$

---

## 6. Stockout Exposure & Excess Inventory Risk Tiers

### 6.1 Forward Days of Supply ($DOS$)
$$DOS = \frac{IP}{\bar{D}}$$

### 6.2 Stockout Urgency Classification
- **Critical Risk**: $DOS < 3.0\text{ days}$ OR $IP < 0.5 \times SS$. Stockout imminent before emergency replenishment can arrive.
- **High Risk**: $DOS < 7.0\text{ days}$ OR $IP \le SS$. Safety stock is being actively consumed.
- **Medium Risk**: $7.0 \le DOS < 14.0\text{ days}$ OR $IP \le ROP$. Below reorder threshold; order should be placed during normal review.
- **Low Risk**: $DOS \ge 14.0\text{ days}$ AND $IP > ROP$. Healthy operating range.

### 6.3 Excess Inventory & Dead Stock
- **Excess Stock**: Flagged when $DOS > 45.0\text{ days}$ and $IP > S$. Trapped capital is calculated as $(IP - S) \times \text{Unit Cost}$. Annual holding cost is estimated at $25\%$ of trapped capital.
- **Dead Stock**: Defined as SKUs with positive on-hand inventory but zero units demanded over the preceding 60 days.

---

## 7. Multi-Factor Prioritization Framework ($P1$ to $P4$)

To prevent decision fatigue for procurement buyers, every SKU-location pair is assigned an operational priority score (0 to 120 points):
$$\text{Score} = \text{Score}_{\text{ABC}} + \text{Score}_{\text{Stockout}} + \text{Score}_{\text{Trigger}} + \text{Score}_{\text{XYZ}}$$
- **ABC Revenue**: $\text{Class A} = 40$, $\text{Class B} = 25$, $\text{Class C} = 10$
- **Stockout Urgency**: $\text{Critical} = 50$, $\text{High} = 35$, $\text{Medium} = 20$, $\text{Low} = 5$
- **Reorder Trigger**: $+20$ points if $IP \le ROP$
- **XYZ Volatility**: $\text{Class Z} = 10$, $\text{Class Y} = 5$, $\text{Class X} = 0$

### Priority Action Tiers:
- **`P1 - Critical (Immediate PO)`** ($\ge 75$ pts): High-revenue items facing acute stockout. Requires immediate purchase order release.
- **`P2 - High (Replenish This Week)`** ($50 - 74$ pts): Standard reorder cycle items at or below ROP.
- **`P3 - Standard Replenishment`** ($30 - 49$ pts): Moderate velocity items approaching reorder thresholds.
- **`P4 - Stable / Routine Monitor`** ($< 30$ pts): Adequate stock; review during routine monthly cycle.
