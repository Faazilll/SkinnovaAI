from __future__ import annotations

import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ml" / "data_model"))

from predict_data import predict_data  # noqa: E402

from app.schemas.models import Questionnaire  # noqa: E402

router = APIRouter(prefix="/predict", tags=["data"])


@router.post("/data")
async def predict_data_endpoint(body: Questionnaire):
    try:
        return predict_data(body.model_dump())
    except Exception as e:
        raise HTTPException(500, f"Data prediction failed: {e}") from e
