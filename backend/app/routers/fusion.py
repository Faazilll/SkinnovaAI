from __future__ import annotations

import sys
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.validation import read_upload_limited, validate_image_and_questionnaire  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ml" / "image_model"))
sys.path.insert(0, str(ROOT / "ml" / "data_model"))
sys.path.insert(0, str(ROOT / "ml" / "fusion"))

from fusion_engine import fuse  # noqa: E402
from predict_data import predict_data  # noqa: E402
from predict_image import predict_image  # noqa: E402

from app.schemas.models import FusionRequest, Questionnaire, RecalculateRequest  # noqa: E402

router = APIRouter(prefix="/predict", tags=["fusion"])


@router.post("/fusion")
async def fusion_from_json(body: FusionRequest):
    try:
        return fuse(body.image, body.data)
    except ValueError as e:
        raise HTTPException(422, str(e)) from e
    except Exception as e:
        raise HTTPException(500, f"Fusion failed: {e}") from e



@router.post("/fusion/recalculate")
async def fusion_recalculate(body: RecalculateRequest):
    """Re-executes systemic risk inference and multimodal fusion when questionnaire data changes."""
    try:
        data_out = predict_data(body.questionnaire)
        return fuse(body.image, data_out)
    except ValueError as e:
        raise HTTPException(422, str(e)) from e
    except Exception as e:
        raise HTTPException(500, f"Recalculation failed: {e}") from e



@router.post("/validate")
async def validate_input_endpoint(
    file: UploadFile = File(...),
    questionnaire_json: str = Form(...),
    require_face: bool = Form(True),
):
    """Lightweight Image-Questionnaire Validation Layer.
    Verifies image clarity, usable face presence, skin authenticity,
    and checks consistency with biological sex without auto-determining or rejecting.
    """
    import json

    try:
        raw = await read_upload_limited(file)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e

    try:
        answers = json.loads(questionnaire_json)
    except Exception as e:
        raise HTTPException(422, f"Invalid questionnaire JSON: {e}") from e

    return validate_image_and_questionnaire(raw, answers, require_face=require_face)


@router.post("/fusion/upload")
async def fusion_from_upload(
    file: UploadFile = File(...),
    questionnaire_json: str = Form(...),
    require_face: bool = Form(True),
):
    """One-shot: image + questionnaire → full dashboard payload."""
    import json

    try:
        answers = Questionnaire(**json.loads(questionnaire_json)).model_dump()
    except Exception as e:
        raise HTTPException(422, f"Invalid questionnaire JSON: {e}") from e

    try:
        raw = await read_upload_limited(file)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e

    # Apply image quality verification before heavy model inference
    val_res = validate_image_and_questionnaire(raw, answers, require_face=require_face)
    if not val_res["valid"]:
        raise HTTPException(422, val_res["errors"][0])

    try:
        image_out = predict_image(raw, require_face=require_face)
    except ValueError as e:
        raise HTTPException(422, str(e)) from e
    except Exception:
        raise HTTPException(500, "Image prediction failed") from None

    data_out = predict_data(answers)
    return fuse(image_out, data_out)
