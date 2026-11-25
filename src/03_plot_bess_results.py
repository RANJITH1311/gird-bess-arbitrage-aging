import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

df_agg = pd.read_csv("data/dispatch_aggressive.csv")
df_deg = pd.read_csv("data/dispatch_degradation_aware.csv")
df_comp = pd.read_excel("data/bess_strategy_comparison.xlsx")

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10.5, 8.5))

# --- Panel 1: 48-Hour Price Arbitrage & SoC Dispatch Profile ---
window = slice(240, 288)  # 48-hour sample window
hours_w = np.arange(48)

ax1_price = ax1.twinx()
ax1_price.plot(hours_w, df_agg["price_eur_mwh"].iloc[window], color="#7f8c8d", linestyle=":", linewidth=1.8, label="Day-Ahead Price [€/MWh]")
ax1_price.set_ylabel("Day-Ahead Price [€/MWh]", color="#7f8c8d", fontweight="bold")

ax1.plot(hours_w, df_agg["soc_pct"].iloc[window], color="#c0392b", linewidth=2.2, label="Aggressive SoC (5%–95%)")
ax1.plot(hours_w, df_deg["soc_pct"].iloc[window], color="#1f618d", linewidth=2.2, label="Degradation-Aware SoC (20%–80%)")
ax1.set_ylabel("Battery State of Charge (SoC) [%]", fontweight="bold")
ax1.set_xlabel("Simulation Time [Hours over 48h Window]", fontweight="bold")
ax1.set_ylim(0, 105)
ax1.grid(True, linestyle="--", alpha=0.45)
ax1.set_title("1. BESS Intraday Arbitrage Dispatch vs. German Day-Ahead Electricity Prices", fontweight="bold", pad=10)

lines_1, labels_1 = ax1.get_legend_handles_labels()
lines_2, labels_2 = ax1_price.get_legend_handles_labels()
ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc="upper left", fontsize=9)

# --- Panel 2: Multi-Year State of Health (SoH) Trajectory to 80% EoL ---
years = np.linspace(0, 15, 150)
fade_agg = df_comp.loc[0, "total_fade_pct_yr"]
fade_deg = df_comp.loc[1, "total_fade_pct_yr"]

soh_agg = np.maximum(75, 100.0 - fade_agg * years)
soh_deg = np.maximum(75, 100.0 - fade_deg * years)

ax2.plot(years, soh_agg, color="#c0392b", linewidth=2.5, label=f"Aggressive (5%–95%): EoL at {df_comp.loc[0, 'years_to_80pct_eol']} yrs")
ax2.plot(years, soh_deg, color="#1f618d", linewidth=2.5, label=f"Degradation-Aware (20%–80%): EoL at {df_comp.loc[1, 'years_to_80pct_eol']} yrs")
ax2.axhline(80.0, color="black", linestyle="--", linewidth=1.3, label="80% State of Health (End-of-Life Threshold)")

ax2.set_xlabel("Operating Years", fontweight="bold")
ax2.set_ylabel("Battery State of Health (SoH) [%]", fontweight="bold")
ax2.set_ylim(76, 101)
ax2.grid(True, linestyle="--", alpha=0.45)
ax2.set_title("2. Rainflow-Derived Capacity Fade & Asset Lifetime Comparison (10 MW / 20 MWh BESS)", fontweight="bold", pad=10)
ax2.legend(loc="lower left", fontsize=9.5)

fig.tight_layout()
plt.savefig("bess_arbitrage_aging_overview.png", dpi=300)
print("Successfully generated bess_arbitrage_aging_overview.png")