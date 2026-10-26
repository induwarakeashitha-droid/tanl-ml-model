import numpy as np
import pandas as pd


# Copied exactly from the Colab notebook. If you change it there, change it here too.
def build_features(daily, rain, horizon=14):
    rows = []
    for tank, g in daily.groupby("tank"):
        g = g.sort_values("date").set_index("date")
        r = rain[tank]
        fill = (g.storage / g.fill_ref).rolling(3, min_periods=1).median()
        f = pd.DataFrame(index=g.index)
        f["fill"] = fill
        for k in (3, 7, 14):
            f[f"fill_chg{k}"] = fill - fill.shift(k)
        f["near_full"] = (fill > 0.95).astype(int)
        for k in (1, 2, 3):
            f[f"rain_lag{k}"] = r.shift(k).reindex(f.index)
        for w in (3, 7, 14, 30, 60):
            f[f"rain_sum{w}"] = r.rolling(w).sum().reindex(f.index)
        f["doy_sin"] = np.sin(2 * np.pi * f.index.dayofyear / 365)
        f["doy_cos"] = np.cos(2 * np.pi * f.index.dayofyear / 365)
        f["cap_ref"], f["lat"], f["lon"], f["is_major"] = g.fill_ref, g.lat, g.lon, g.is_major
        f["target"] = fill.shift(-horizon) - fill
        f["tank"] = tank
        rows.append(f)
    out = pd.concat(rows)
    return out[out.fill.between(0, 1.5)]
