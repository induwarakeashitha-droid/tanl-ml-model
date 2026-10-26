import os
from datetime import date, timedelta

import joblib
import pandas as pd
import requests
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from features import build_features

MODEL_PATH = os.getenv("MODEL_PATH", "tank_model.pkl")
API_KEY = os.getenv("API_KEY")

bundle = joblib.load(MODEL_PATH)
model = bundle["model"]
FEATURES = bundle["features"]
HORIZON = bundle["horizon_days"]
TANKS = bundle["tanks"]

app = FastAPI(title="Tank Level Forecast API")
rain_cache = {}


class Reading(BaseModel):
    date: date
    storage_acft: float


class RainDay(BaseModel):
    date: date
    mm: float


class PredictRequest(BaseModel):
    tank: str
    readings: list[Reading] = Field(min_length=15)
    rain: list[RainDay] | None = None


def check_key(x_api_key):
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(401, "Invalid or missing API key")


def get_rain(lat, lon, end):
    key = (round(lat, 1), round(lon, 1), end)
    if key in rain_cache:
        return rain_cache[key]

    start = end - timedelta(days=90)
    params = {
        "latitude": round(lat, 1),
        "longitude": round(lon, 1),
        "daily": "precipitation_sum",
        "timezone": "Asia/Colombo",
    }
    if end >= date.today() - timedelta(days=30):
        url = "https://api.open-meteo.com/v1/forecast"
        params.update(past_days=92, forecast_days=1)
    else:
        url = "https://archive-api.open-meteo.com/v1/archive"
        params.update(start_date=str(start), end_date=str(end))

    try:
        data = requests.get(url, params=params, timeout=20).json()
        s = pd.Series(data["daily"]["precipitation_sum"], index=pd.to_datetime(data["daily"]["time"]))
    except Exception:
        raise HTTPException(502, "Could not get rainfall from Open-Meteo")

    s = s.fillna(0).loc[str(start):str(end)]
    rain_cache[key] = s
    return s


def forecast(tank, readings, rain_series):
    info = TANKS[tank]
    d = readings.rename(columns={"storage_acft": "storage"})
    d["date"] = pd.to_datetime(d["date"])
    d = d.sort_values("date").drop_duplicates("date", keep="last")
    d = d.set_index("date").storage.asfreq("D").ffill(limit=3).to_frame("storage")
    d = d.assign(tank=tank, lat=info["lat"], lon=info["lon"],
                 fill_ref=info["fill_ref"], is_major=info["is_major"]).reset_index()

    F = build_features(d, pd.DataFrame({tank: rain_series}), horizon=HORIZON)
    row = F[F[FEATURES].notna().all(axis=1)].tail(1)
    if row.empty:
        raise HTTPException(422, "Not enough data. Send at least 15 days of readings in a row "
                                 "and make sure rainfall covers the 60 days before the last reading.")

    change = float(model.predict(row[FEATURES])[0])
    now = float(row.fill.iloc[0])
    later = min(max(now + change, 0), 1.2)
    return {
        "tank": tank,
        "as_of": str(row.index[0].date()),
        "horizon_days": HORIZON,
        "fill_now": round(now, 3),
        f"fill_in_{HORIZON}d": round(later, 3),
        "change": round(change, 3),
        "outlook": "rising" if change > .03 else "falling" if change < -.03 else "steady",
    }


@app.get("/health")
def health():
    return {"status": "ok", "tanks": len(TANKS)}


@app.get("/tanks")
def list_tanks(x_api_key: str | None = Header(None)):
    check_key(x_api_key)
    return [{"name": name, "lat": float(t["lat"]), "lon": float(t["lon"]),
             "fill_ref": float(t["fill_ref"]), "is_major": int(t["is_major"])}
            for name, t in TANKS.items()]


@app.post("/predict")
def predict(req: PredictRequest, x_api_key: str | None = Header(None)):
    check_key(x_api_key)
    if req.tank not in TANKS:
        raise HTTPException(404, f"Unknown tank '{req.tank}'. See /tanks for valid names.")

    readings = pd.DataFrame([r.model_dump() for r in req.readings])

    if req.rain:
        rain = pd.DataFrame([r.model_dump() for r in req.rain])
        rain_series = pd.Series(rain.mm.values, index=pd.to_datetime(rain.date)).sort_index()
    else:
        info = TANKS[req.tank]
        rain_series = get_rain(info["lat"], info["lon"], readings.date.max())

    return forecast(req.tank, readings, rain_series)
