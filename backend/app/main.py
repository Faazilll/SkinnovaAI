from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ml" / "image_model"))
sys.path.insert(0, str(ROOT / "ml" / "data_model"))
sys.path.insert(0, str(ROOT / "ml" / "fusion"))

from app.db import init_db
from app.routers import auth, data, fusion, history, image  # noqa: E402
from app.schemas.models import HealthResponse  # noqa: E402

app = FastAPI(
    title="Skinova API",
    description=(
        "Educational acne risk decision-support API. "
        "Not a certified medical device."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(image.router)
app.include_router(data.router)
app.include_router(fusion.router)
app.include_router(auth.router)
app.include_router(history.router)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health", response_model=HealthResponse)
def health():
    img_model_name = None
    try:
        from predict_image import load_model as load_img_model
        _, img_model_name = load_img_model()
    except Exception:
        pass

    data_loaded = False
    try:
        from predict_data import _load_ml
        ml_data = _load_ml()
        data_loaded = ml_data is not None
    except Exception:
        pass

    db_ok = (ROOT / "artifacts" / "data" / "skinova.db").exists()

    return HealthResponse(
        status="ok",
        image_model_loaded=img_model_name is not None,
        data_model_loaded=data_loaded,
        active_image_model=img_model_name or "heuristic_fallback",
        active_data_model="random_forest_regressor" if data_loaded else "rule_engine",
        db_connected=db_ok,
    )


@app.get("/")
def root():
    return {
        "name": "Skinova",
        "docs": "/docs",
        "health": "/health",
        "disclaimer": (
            "Educational prototype only — not a medical device or diagnosis."
        ),
    }

