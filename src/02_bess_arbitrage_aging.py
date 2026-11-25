import numpy as np
import pandas as pd
import rainflow
from scipy.optimize import linprog

df_prices = pd.read_csv("data/german_day_ahead_prices.csv")

# BESS Technical Specifications (Utility-Scale LFP/NMC Containerized System)
POWER_MAX_MW = 10.0          # 10 MW inverter rating
ENERGY_CAP_MWH = 20.0        # 20 MWh nameplate capacity (2-hour duration)
ETA_CHARGE = 0.938           # sqrt(0.88) -> 88% round-trip efficiency
ETA_DISCHARGE = 0.938
CAPEX_TOTAL_EUR = 5_600_000  # €280/kWh installed BESS CAPEX (€5.6M)
EOL_SOH_THRESHOLD = 80.0     # End-of-Life defined at 80% State of Health (20% fade)
CALENDAR_FADE_PCT_YR = 1.15  # 1.15% annual calendar aging at 25°C ambient

def simulate_strategy(strategy_name, soc_min_pct, soc_max_pct):
    soc_min = (soc_min_pct / 100.0) * ENERGY_CAP_MWH
    soc_max = (soc_max_pct / 100.0) * ENERGY_CAP_MWH
    soc_current = 0.50 * ENERGY_CAP_MWH  # Start at 50% SoC

    hourly_records = []
    total_revenue_eur = 0.0

    # Optimize day-by-day (24-hour rolling horizon across 365 days)
    for day in range(365):
        day_slice = df_prices.iloc[day * 24 : (day + 1) * 24]
        prices = day_slice["price_eur_mwh"].values
        T = 24

        # Decision variables: [p_ch_0..23, p_dis_0..23] (48 variables)
        # Objective: Minimize sum(price * p_ch - price * p_dis)
        c = np.concatenate([prices, -prices])

        # Bounds: 0 <= p_ch <= POWER_MAX_MW, 0 <= p_dis <= POWER_MAX_MW
        bounds = [(0, POWER_MAX_MW)] * (2 * T)

        # Inequality constraints: soc_min <= soc_t <= soc_max for t = 1..24
        # soc_t = soc_current + sum_{k=0..t-1} (eta_ch * p_ch_k - (1/eta_dis) * p_dis_k)
        A_upper = np.zeros((T, 2 * T))
        b_upper = np.full(T, soc_max - soc_current)

        A_lower = np.zeros((T, 2 * T))
        b_lower = np.full(T, -(soc_min - soc_current))

        for t in range(T):
            for k in range(t + 1):
                A_upper[t, k] = ETA_CHARGE
                A_upper[t, T + k] = -1.0 / ETA_DISCHARGE
                A_lower[t, k] = -ETA_CHARGE
                A_lower[t, T + k] = 1.0 / ETA_DISCHARGE

        A_ub = np.vstack([A_upper, A_lower])
        b_ub = np.concatenate([b_upper, b_lower])

        res = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method="highs")
        p_ch = res.x[:T]
        p_dis = res.x[T:]

        for t in range(T):
            soc_current = soc_current + ETA_CHARGE * p_ch[t] - (1.0 / ETA_DISCHARGE) * p_dis[t]
            hourly_revenue = (p_dis[t] - p_ch[t]) * prices[t]
            total_revenue_eur += hourly_revenue
            hourly_records.append({
                "hour": day * 24 + t,
                "price_eur_mwh": prices[t],
                "charge_mw": round(p_ch[t], 3),
                "discharge_mw": round(p_dis[t], 3),
                "soc_mwh": round(soc_current, 3),
                "soc_pct": round((soc_current / ENERGY_CAP_MWH) * 100.0, 2),
                "revenue_eur": round(hourly_revenue, 2)
            })

    df_sim = pd.DataFrame(hourly_records)

    # Rainflow Cycle Counting on SoC (%) time-series to compute cyclic capacity fade
    # Stress factor follows Wöhler-style power law: fade_per_cycle = k * (DoD ^ 1.45)
    k_stress = 0.00038  # Calibrated to ~3,500 cycles at 80% DoD for 20% fade
    cyclic_fade_pct = 0.0
    equivalent_full_cycles = 0.0

    for rng, mean, count, i_start, i_end in rainflow.extract_cycles(df_sim["soc_pct"].values):
        dod = rng / 100.0
        equivalent_full_cycles += count * dod
        cyclic_fade_pct += count * k_stress * ((dod * 100.0) ** 1.45)

    total_annual_fade_pct = CALENDAR_FADE_PCT_YR + cyclic_fade_pct
    years_to_eol = (100.0 - EOL_SOH_THRESHOLD) / total_annual_fade_pct
    lifetime_gross_profit_eur = total_revenue_eur * years_to_eol
    net_lifetime_profit_eur = lifetime_gross_profit_eur - CAPEX_TOTAL_EUR

    summary = {
        "strategy": strategy_name,
        "soc_window": f"{soc_min_pct}%-{soc_max_pct}%",
        "annual_arbitrage_eur": round(total_revenue_eur, 0),
        "eq_full_cycles_yr": round(equivalent_full_cycles, 1),
        "cyclic_fade_pct_yr": round(cyclic_fade_pct, 2),
        "total_fade_pct_yr": round(total_annual_fade_pct, 2),
        "years_to_80pct_eol": round(years_to_eol, 1),
        "lifetime_revenue_eur": round(lifetime_gross_profit_eur, 0),
        "net_profit_after_capex_eur": round(net_lifetime_profit_eur, 0)
    }
    return df_sim, summary

df_agg, sum_agg = simulate_strategy("Aggressive (5%-95% SoC)", 5, 95)
df_deg, sum_deg = simulate_strategy("Degradation-Aware (20%-80% SoC)", 20, 80)

df_agg.to_csv("data/dispatch_aggressive.csv", index=False)
df_deg.to_csv("data/dispatch_degradation_aware.csv", index=False)

df_comparison = pd.DataFrame([sum_agg, sum_deg])
df_comparison.to_excel("data/bess_strategy_comparison.xlsx", index=False)

print("=== Grid-Scale BESS (10 MW / 20 MWh) Strategy Comparison ===")
print(df_comparison.to_string(index=False))