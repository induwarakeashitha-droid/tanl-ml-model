# Tank Level Forecast API

FastAPI service that serves the Random Forest tank model trained in Colab. It predicts how full a tank will be in 14 days.

## Files

| File | What it does |
|---|---|
| `main.py` | The API: loads the model, fetches rainfall, returns forecasts |
| `features.py` | `build_features` copied from the notebook. Must match training exactly |
| `tank_model.pkl` | Your model bundle from Colab (you add this) |
| `requirements.txt` | Python packages, pinned to the Colab versions |
| `Dockerfile` | Builds the container |
| `colab_shrink_cell.py` | Colab cell that makes the small model. Not used by the API |
| `express-forecast-route.js` | Route to add to your Express backend. Not used by the API |

## Endpoints

`GET /health` returns `{"status": "ok", "tanks": 43}`

`GET /tanks` returns every tank name the model knows, with lat/lon

`POST /predict`

```json
{
  "tank": "Sorabora",
  "readings": [
    { "date": "2026-10-06", "storage_acft": 24100 },
    { "date": "2026-10-07", "storage_acft": 24250 }
  ]
}
```

Send at least 15 days of readings (20 is safer). The API gets the rainfall from Open-Meteo by itself. You can also send `"rain": [{"date": "...", "mm": 3.2}, ...]` to skip that.

Response:

```json
{
  "tank": "Sorabora",
  "as_of": "2026-10-25",
  "horizon_days": 14,
  "fill_now": 0.497,
  "fill_in_14d": 0.561,
  "change": 0.064,
  "outlook": "rising"
}
```

`fill` is a fraction of full: 0.5 means half full, 1.0 means full.

## Run locally (PowerShell)

```powershell
docker build -t tank-ml-api .
docker run -p 8000:8000 tank-ml-api
```

Open http://localhost:8000/docs

## Deploy on Render

1. Push this folder to a GitHub repo.
2. Render: New > Web Service > connect the repo. It detects the Dockerfile.
3. Instance: Starter ($7/month, never sleeps) or Free (sleeps after 15 min).
4. Environment variable: `API_KEY` = any long random string.
5. Deploy, then open `https://<your-service>.onrender.com/health`.

## Updating the model

Retrain in Colab, run the shrink cell, replace `tank_model.pkl`, push to GitHub. Render rebuilds automatically.

If you change `build_features` in the notebook, copy the change into `features.py` too.
