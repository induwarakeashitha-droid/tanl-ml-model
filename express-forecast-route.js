// Add to your Express app. Needs these in .env:
// ML_API_URL=https://your-service.onrender.com
// ML_API_KEY=the same value you set as API_KEY on Render

app.post("/api/forecast", async (req, res) => {
  const { tank, readings } = req.body;

  try {
    const response = await fetch(`${process.env.ML_API_URL}/predict`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": process.env.ML_API_KEY,
      },
      body: JSON.stringify({ tank, readings }),
      signal: AbortSignal.timeout(90_000),
    });

    const data = await response.json();
    if (!response.ok) return res.status(response.status).json(data);
    res.json(data);
  } catch (err) {
    res.status(502).json({ error: "Forecast service unavailable" });
  }
});

app.get("/api/tanks", async (req, res) => {
  try {
    const response = await fetch(`${process.env.ML_API_URL}/tanks`, {
      headers: { "x-api-key": process.env.ML_API_KEY },
      signal: AbortSignal.timeout(90_000),
    });
    res.status(response.status).json(await response.json());
  } catch (err) {
    res.status(502).json({ error: "Forecast service unavailable" });
  }
});
