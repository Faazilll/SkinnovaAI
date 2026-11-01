from __future__ import annotations

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
_IMG_MODEL_DIR = str(ROOT / "ml" / "image_model")
if _IMG_MODEL_DIR not in sys.path:
    sys.path.insert(0, _IMG_MODEL_DIR)

from preprocess import _detect_face_with_method, _ensure_yunet_model, verify_facial_skin  # noqa: E402

MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # 20 MB
ALLOWED_IMAGE_PREFIXES = ("image/",)


async def read_upload_limited(file, max_bytes: int = MAX_UPLOAD_BYTES) -> bytes:
    """Read upload with size cap; reject non-image content types."""
    if file.content_type and not file.content_type.startswith(ALLOWED_IMAGE_PREFIXES):
        raise ValueError("Upload must be an image file (JPEG, PNG, etc.)")
    raw = await file.read(max_bytes + 1)
    if len(raw) > max_bytes:
        raise ValueError(f"Image too large (max {max_bytes // (1024 * 1024)} MB)")
    if len(raw) < 100:
        raise ValueError("Image file too small or empty")
    return raw


def validate_image_and_questionnaire(
    img_bytes_or_bgr: bytes | np.ndarray,
    questionnaire: dict[str, Any],
    require_face: bool = True,
) -> dict[str, Any]:
    """Lightweight Image-Questionnaire Validation Layer.

    Checks:
    1. Decoding & minimum dimensions (>= 80x80).
    2. Usable face presence & bounding box size.
    3. Sharpness / blurriness via Laplacian variance.
    4. Lighting / illumination (underexposed or overexposed).
    5. Skin authenticity & coverage via dual-space YCrCb/HSV filter.
    6. Facial appearance vs questionnaire consistency (biological sex confirmation signal).
    """
    if isinstance(img_bytes_or_bgr, np.ndarray):
        bgr = img_bytes_or_bgr
    else:
        arr = np.frombuffer(img_bytes_or_bgr, dtype=np.uint8)
        bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)

    if bgr is None:
        return {
            "valid": False,
            "errors": [
                "Could not decode image file. Please provide a valid JPEG, PNG, or WebP photo."
            ],
            "quality": None,
            "consistency_warning": None,
        }

    h, w = bgr.shape[:2]
    if h < 80 or w < 80:
        return {
            "valid": False,
            "errors": [
                "Image resolution is too low for clinical dermatological analysis (minimum 80x80 pixels required)."
            ],
            "quality": None,
            "consistency_warning": None,
        }

    bbox, detector_name = _detect_face_with_method(bgr)
    face_detected = bbox is not None

    if require_face and not face_detected:
        return {
            "valid": False,
            "errors": [
                "No clear, usable human face was detected in the photograph. Skinova requires a front-facing facial photo for accurate dermatological assessment."
            ],
            "quality": {"face_detected": False},
            "consistency_warning": None,
        }

    if bbox is not None:
        x1, y1, x2, y2 = bbox
        fw, fh = x2 - x1, y2 - y1
        if fw < 40 or fh < 40:
            return {
                "valid": False,
                "errors": [
                    "The detected face is too small in the frame for accurate lesion evaluation. Please upload a closer portrait photo."
                ],
                "quality": {"face_detected": True, "detector": detector_name},
                "consistency_warning": None,
            }
        crop = bgr[y1:y2, x1:x2]
    else:
        side = min(h, w)
        y0 = (h - side) // 2
        x0 = (w - side) // 2
        crop = bgr[y0 : y0 + side, x0 : x0 + side]

    gray_crop = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    clarity_score = float(cv2.Laplacian(gray_crop, cv2.CV_64F).var())
    lum_mean = float(np.mean(gray_crop))
    lum_std = float(np.std(gray_crop))

    is_skin, skin_ratio, skin_reason = verify_facial_skin(crop)

    errors: list[str] = []
    if clarity_score < 20.0:
        errors.append(
            f"The photograph is excessively blurry or out of focus (clarity score: {round(clarity_score, 1)}). Please provide a sharper, focused image."
        )
    if lum_mean < 25.0:
        errors.append(
            f"The photograph is severely underexposed or too dark (brightness: {round(lum_mean, 1)}/255). Please capture under adequate ambient lighting."
        )
    elif lum_mean > 235.0:
        errors.append(
            f"The photograph is overexposed or washed out by harsh glare (brightness: {round(lum_mean, 1)}/255). Please avoid direct flash or glare."
        )
    if lum_std < 12.0:
        errors.append(
            "The photograph has insufficient visual contrast. Please provide a clearly lit photo."
        )
    if require_face and not is_skin:
        errors.append(skin_reason)

    quality = {
        "face_detected": face_detected,
        "detector": detector_name,
        "clarity_score": round(clarity_score, 1),
        "is_blurry": clarity_score < 20.0,
        "brightness": round(lum_mean, 1),
        "contrast": round(lum_std, 1),
        "is_underexposed": lum_mean < 25.0,
        "is_overexposed": lum_mean > 235.0,
        "skin_verified": is_skin,
        "skin_ratio": round(skin_ratio, 3),
    }

    if len(errors) > 0:
        return {
            "valid": False,
            "errors": errors,
            "quality": quality,
            "consistency_warning": None,
        }

    # Biological sex and facial appearance consistency check
    consistency_warning = None
    gender = str(questionnaire.get("gender", "")).lower().strip()

    # Note: We do not auto-determine sex or reject users based on appearance.
    # Only if a reliable signal is present (e.g., prominent androgenic facial hair
    # combined with female biological sex selection), we ask for neutral confirmation.
    if gender == "female" and face_detected:
        try:
            model_path = _ensure_yunet_model()
            det = cv2.FaceDetectorYN.create(str(model_path), "", (w, h), score_threshold=0.5)
            _, faces = det.detect(bgr)
            if faces is not None and len(faces) > 0:
                best = max(faces, key=lambda f: float(f[2]) * float(f[3]))
                fx, fy, fw, fh = [int(v) for v in best[:4]]
                r_eye = (int(best[4]), int(best[5]))
                nose = (int(best[8]), int(best[9]))
                r_m = (int(best[10]), int(best[11]))
                l_m = (int(best[12]), int(best[13]))
                mouth_y = int((r_m[1] + l_m[1]) / 2)
                m_x1 = min(r_m[0], l_m[0])
                m_x2 = max(r_m[0], l_m[0])

                ref_y1 = max(0, r_eye[1])
                ref_y2 = min(h - 1, max(ref_y1 + 5, nose[1]))
                ref_x1 = max(0, fx + int(0.08 * fw))
                ref_x2 = min(w - 1, m_x1 - 4)

                full_gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
                ref_roi = (
                    full_gray[ref_y1:ref_y2, ref_x1:ref_x2]
                    if (ref_y2 > ref_y1 and ref_x2 > ref_x1)
                    else full_gray[fy : r_eye[1], fx : fx + fw]
                )
                ref_mean = float(np.mean(ref_roi)) if ref_roi.size > 0 else 128.0
                ref_std = float(np.std(ref_roi)) if ref_roi.size > 0 else 15.0

                # Mustache region: between nose tip and upper lip
                m_y1 = min(h - 1, max(0, nose[1] + max(2, int(0.15 * (mouth_y - nose[1])))))
                m_y2 = min(h - 1, max(m_y1 + 2, mouth_y - 2))
                mustache_roi = full_gray[m_y1:m_y2, m_x1:m_x2]

                # Chin / jaw region: below mouth
                c_y1 = min(h - 1, mouth_y + max(4, int(0.15 * (fy + fh - mouth_y))))
                c_y2 = min(h - 1, fy + fh)
                c_x1 = max(0, fx + int(0.2 * fw))
                c_x2 = min(w - 1, fx + int(0.8 * fw))
                chin_roi = full_gray[c_y1:c_y2, c_x1:c_x2]

                dark_thresh = max(10, ref_mean - max(16.0, 1.1 * ref_std))
                mus_dark_ratio = (
                    float(np.mean(mustache_roi < dark_thresh)) if mustache_roi.size > 0 else 0.0
                )
                chin_dark_ratio = (
                    float(np.mean(chin_roi < dark_thresh)) if chin_roi.size > 0 else 0.0
                )

                sobel = np.abs(cv2.Sobel(full_gray, cv2.CV_64F, 1, 1))
                ref_edge = (
                    float(np.mean(sobel[ref_y1:ref_y2, ref_x1:ref_x2]))
                    if ref_roi.size > 0
                    else 1.0
                )
                mus_edge = (
                    float(np.mean(sobel[m_y1:m_y2, m_x1:m_x2]))
                    if mustache_roi.size > 0
                    else 0.0
                )
                edge_ratio = mus_edge / max(1.0, ref_edge)

                has_mustache = (mus_dark_ratio > 0.22) and (edge_ratio > 1.2)
                has_chin = chin_dark_ratio > 0.25
                confidence = min(
                    1.0, max(mus_dark_ratio, chin_dark_ratio) * 0.7 + (edge_ratio / 3.0) * 0.3
                )

                if (has_mustache or has_chin) and (confidence >= 0.40):
                    consistency_warning = {
                        "has_warning": True,
                        "warning_type": "biological_sex_confirmation",
                        "title": "Biological Sex Selection Confirmation",
                        "message": (
                            "The clinical questionnaire currently has Biological Sex set to 'Female', "
                            "while facial image analysis detected prominent facial hair patterns. "
                            "Because systemic endocrine baselines and acne risk modeling differ between "
                            "female and male physiological profiles, please confirm if 'Female' is your intended selection."
                        ),
                        "detected_feature": "Prominent facial hair pattern detected",
                        "questionnaire_value": "Female",
                        "can_proceed": True,
                    }
        except Exception:
            # If signal extraction encounters an issue, gracefully do not make a mismatch claim
            consistency_warning = None

    return {
        "valid": True,
        "errors": [],
        "quality": quality,
        "consistency_warning": consistency_warning,
    }

