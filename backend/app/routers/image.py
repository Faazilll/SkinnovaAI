from __future__ import annotations

import sys
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.validation import read_upload_limited  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ml" / "image_model"))

from predict_image import predict_image  # noqa: E402

router = APIRouter(prefix="/predict", tags=["image"])


@router.post("/image")
async def predict_image_endpoint(
    file: UploadFile = File(...),
    require_face: bool = Form(True),
):
    try:
        raw = await read_upload_limited(file)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    try:
        result = predict_image(raw, require_face=require_face)
    except ValueError as e:
        raise HTTPException(422, str(e)) from e
    except Exception:
        raise HTTPException(500, "Image prediction failed") from None
    return result
