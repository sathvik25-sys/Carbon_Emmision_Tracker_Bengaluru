"""
FastAPI Application for Bengaluru Carbon Emission Tracker.
Serves interactive single-page web UI, REST API endpoints, and handles calculations and ML predictions.
"""

import os
from typing import Dict, Any
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from config import (
    EMISSION_FACTORS,
    MODE_METADATA,
    GRID_EMISSION_FACTOR_KWH,
    CONGESTION_MAX_PENALTY,
    DEMO_PRESETS,
    INDIA_NATIONAL_MONTHLY_BENCHMARK,
    BENGALURU_URBAN_MONTHLY_BENCHMARK,
    GLOBAL_MONTHLY_BENCHMARK,
)
from calculator import CommuterInput, compute_carbon_estimate
from ml_engine import ml_engine

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(
    title="Bengaluru Carbon Emission Tracker",
    description="Machine Learning & Factor-Based Carbon Emission Estimation for Daily Activities",
    version="1.0.0",
)

# Mount static and templates directories
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


@app.get("/", response_class=HTMLResponse)
async def serve_index(request: Request):
    """Renders the main single-page application."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "modes": MODE_METADATA,
            "presets": DEMO_PRESETS,
            "grid_factor": GRID_EMISSION_FACTOR_KWH,
            "bengaluru_avg": BENGALURU_URBAN_MONTHLY_BENCHMARK,
            "india_avg": INDIA_NATIONAL_MONTHLY_BENCHMARK,
        }
    )


@app.get("/api/config", response_class=JSONResponse)
async def get_config() -> Dict[str, Any]:
    """Returns configuration metadata, emission factors, and benchmarks."""
    return {
        "emission_factors": EMISSION_FACTORS,
        "modes": MODE_METADATA,
        "grid_factor_kwh": GRID_EMISSION_FACTOR_KWH,
        "congestion_penalties": CONGESTION_MAX_PENALTY,
        "benchmarks": {
            "bengaluru_urban_monthly_kg": BENGALURU_URBAN_MONTHLY_BENCHMARK,
            "india_national_monthly_kg": INDIA_NATIONAL_MONTHLY_BENCHMARK,
            "global_monthly_kg": GLOBAL_MONTHLY_BENCHMARK,
        }
    }


@app.get("/api/presets", response_class=JSONResponse)
async def get_presets() -> Dict[str, Any]:
    """Returns demo commuter profiles for instant demonstration."""
    return DEMO_PRESETS


@app.post("/api/calculate", response_class=JSONResponse)
async def calculate_carbon(payload: CommuterInput) -> Dict[str, Any]:
    """
    Computes deterministic Tier-1 factor-based carbon footprint,
    itemized receipt details, what-if alternatives, and actionable recommendations.
    """
    try:
        result = compute_carbon_estimate(payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/predict", response_class=JSONResponse)
async def predict_carbon_ml(payload: CommuterInput) -> Dict[str, Any]:
    """
    Generates Machine Learning regression estimate using Gradient Boosting Regressor
    trained on synthetic Bengaluru commuter activity dataset.
    """
    try:
        input_dict = payload.model_dump()
        # Compute ML prediction
        ml_result = ml_engine.predict(input_dict)
        # Compute factor baseline for comparison
        baseline_result = compute_carbon_estimate(payload)

        factor_monthly = baseline_result["summary"]["monthly_total_co2_kg"]
        ml_monthly = ml_result["predicted_monthly_co2_kg"]
        delta_kg = round(ml_monthly - factor_monthly, 2)
        delta_pct = round((delta_kg / factor_monthly * 100.0), 1) if factor_monthly > 0 else 0.0

        return {
            "status": "success",
            "ml_prediction": ml_result,
            "factor_baseline": {
                "monthly_total_co2_kg": factor_monthly,
                "daily_average_co2_kg": baseline_result["summary"]["daily_average_co2_kg"],
            },
            "comparison": {
                "delta_kg": delta_kg,
                "delta_pct": delta_pct,
                "explanation": (
                    "The ML model incorporates non-linear interaction terms between rush-hour congestion "
                    "exposure, engine wear degradation, and household per-capita energy scaling. "
                    f"Difference from factor baseline is {abs(delta_kg)} kg CO2e ({abs(delta_pct)}%)."
                )
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/health", response_class=JSONResponse)
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "ml_loaded": ml_engine.model is not None,
        "ml_status": ml_engine.metadata.get("model_type") if ml_engine.metadata else "fallback",
    }


if __name__ == "__main__":
    import uvicorn
    print("Starting Bengaluru Carbon Tracker on http://127.0.0.1:8000 ...")
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
