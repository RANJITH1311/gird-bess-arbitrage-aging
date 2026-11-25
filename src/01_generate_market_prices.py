import os
import numpy as np
import pandas as pd

os.makedirs("data", exist_ok=True)
np.random.seed(42)

hours = np.arange(8760)
day_of_year = hours // 24
hour_of_day = hours % 24

# Base seasonal price (€/MWh): higher in winter, lower in summer
base_price = 82.0 + 18.0 * np.cos(2 * np.pi * (day_of_year - 15) / 365)

# Double-hump duck-curve intraday pattern: morning peak (~8h), midday solar dip (~13h), evening peak (~19h)
morning_peak = 28.0 * np.exp(-0.5 * ((hour_of_day - 8.5) / 1.8) ** 2)
midday_solar_dip = -42.0 * np.exp(-0.5 * ((hour_of_day - 13.5) / 2.2) ** 2) * (0.6 + 0.4 * np.sin(2 * np.pi * (day_of_year - 80) / 365))
evening_peak = 45.0 * np.exp(-0.5 * ((hour_of_day - 19.5) / 2.0) ** 2)

# Stochastic volatility spikes
noise = np.random.normal(0, 11.0, size=8760)
prices_eur_mwh = np.round(base_price + morning_peak + midday_solar_dip + evening_peak + noise, 2)

df_prices = pd.DataFrame({
    "hour": hours,
    "day": day_of_year + 1,
    "hour_of_day": hour_of_day,
    "price_eur_mwh": prices_eur_mwh
})

df_prices.to_csv("data/german_day_ahead_prices.csv", index=False)
print(f"Generated 8,760 hourly German electricity prices.")
print(f"Mean Price: €{df_prices['price_eur_mwh'].mean():.2f}/MWh | Min: €{df_prices['price_eur_mwh'].min():.2f}/MWh | Max: €{df_prices['price_eur_mwh'].max():.2f}/MWh")