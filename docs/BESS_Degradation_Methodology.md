# Technical Modeling Note: Utility BESS Arbitrage & Rainflow Degradation

## 1. Linear Programming Arbitrage Formulation
For each 24-hour day-ahead horizon, the BESS controller maximizes net energy trading revenue subject to power inverter bounds ($P_{\max} = 10\text{ MW}$), round-trip efficiency losses ($\eta_{\text{rt}} = \eta_{\text{ch}} \cdot \eta_{\text{dis}} = 0.88$), and State-of-Charge energy limits:

$$\max_{P_{\text{ch}}, P_{\text{dis}}} \sum_{t=1}^{24} \lambda_t \left(P_{\text{dis}, t} - P_{\text{ch}, t}\right) \Delta t$$

$$\text{SoC}_t = \text{SoC}_{t-1} + \eta_{\text{ch}} P_{\text{ch}, t} \Delta t - \frac{1}{\eta_{\text{dis}}} P_{\text{dis}, t} \Delta t$$

## 2. Rainflow Cycle Counting & Capacity Fade Model
Irregular partial charge/discharge cycles are decomposed using the ASTM E1049-85 **Rainflow counting algorithm** (`rainflow.extract_cycles`) on the hourly $\text{SoC}(t)$ time-series. Total annual State-of-Health ($\text{SoH}$) loss combines calendar aging ($1.15\%/\text{yr}$ at $25^\circ\text{C}$) with non-linear Depth-of-Discharge ($\text{DoD}$) cycle stress:

$$\Delta \text{SoH}_{\text{annual}} = \Delta \text{SoH}_{\text{calendar}} + \sum_{i} n_i \cdot k \cdot (\text{DoD}_i)^{1.45}$$

## 3. Economic Takeaway
Restricting operation to a **$20\%\text{–}80\%$ SoC window** slightly lowers annual gross trading revenue compared to aggressive $5\%\text{–}95\%$ cycling, but extends asset lifetime to the $80\%$ End-of-Life threshold by **+3 to +4 years**, yielding higher cumulative net profit over the battery's lifespan.