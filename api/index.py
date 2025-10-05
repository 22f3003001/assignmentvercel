from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from statistics import mean
import math
import json
import os

app = FastAPI()

# ✅ Enable CORS properly
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # Allow all origins
    allow_credentials=False,  # Must be False when using "*"
    allow_methods=["*"],      # Allow all HTTP methods
    allow_headers=["*"],      # Allow all headers
)

# ✅ Load telemetry data
BASE_DIR = os.path.dirname(__file__)
json_path = os.path.join(BASE_DIR, "q-vercel-latency.json")

with open(json_path) as f:
    telemetry = json.load(f)

def percentile(data, percent):
    """Compute the given percentile of a list of numbers."""
    if not data:
        return None
    data_sorted = sorted(data)
    k = (len(data_sorted)-1) * (percent/100)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return data_sorted[int(k)]
    return data_sorted[f] * (c - k) + data_sorted[c] * (k - f)

# ✅ Explicit OPTIONS handler for CORS preflight requests
@app.options("/")
async def preflight_handler(request: Request):
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "*",
    }
    return JSONResponse(content={}, headers=headers)

@app.get("/")
def health_check():
    return {"status": "ok"}

@app.post("/")
async def latency_metrics(payload: dict):
    regions = payload.get("regions", [])
    threshold = payload.get("threshold_ms", 180)
    result = {}

    for region in regions:
        region_data = [r for r in telemetry if r["region"] == region]

        if not region_data:
            result[region] = {
                "avg_latency": None,
                "p95_latency": None,
                "avg_uptime": None,
                "breaches": 0
            }
            continue

        latencies = [r["latency_ms"] for r in region_data]
        uptimes = [r["uptime_pct"] for r in region_data]
        breaches = sum(1 for l in latencies if l > threshold)

        result[region] = {
            "avg_latency": mean(latencies),
            "p95_latency": percentile(latencies, 95),
            "avg_uptime": mean(uptimes),
            "breaches": breaches
        }

    # ✅ Add explicit CORS header to POST response
    headers = {"Access-Control-Allow-Origin": "*"}
    return JSONResponse(content=result, headers=headers)






