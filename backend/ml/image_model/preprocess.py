"""Face crop + resize preprocessing for Skinova image model."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

IMG_SIZE = 224

# OpenCV YuNet face detector (works on Python 3.13; MediaPipe 1.x removed solutions API)
_YUNET_URL = (
    "https://github.com/opencv/opencv_zoo/raw/main/models/"
    "face_detection_yunet/face_detection_yunet_2023mar.onnx"
)
_YUNET_PATH = Path(__file__).resolve().parent / "models" / "face_detection_yunet_2023mar.onnx"
_yunet_detector = None
_haar_cascade = None
_haar_unavailable = False


def _ensure_yunet_model() -> Path:
    _YUNET_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not _YUNET_PATH.exists() or _YUNET_PATH.stat().st_size < 100_000:
        import urllib.request

        print(f"Downloading YuNet face model -> {_YUNET_PATH}")
        urllib.request.urlretrieve(_YUNET_URL, _YUNET_PATH)
    return _YUNET_PATH


def _yunet_face_bbox(bgr: np.ndarray) -> tuple[int, int, int, int] | None:
    global _yunet_detector
    try:
        model_path = _ensure_yunet_model()
        h, w = bgr.shape[:2]
        max_detect_dim = 640
        scale = 1.0
        detect_bgr = bgr
        detect_h, detect_w = h, w
        if max(h, w) > max_detect_dim:
            scale = max_detect_dim / float(max(h, w))
            detect_w = max(1, int(round(w * scale)))
            detect_h = max(1, int(round(h * scale)))
            detect_bgr = cv2.resize(
                bgr, (detect_w, detect_h), interpolation=cv2.INTER_AREA
            )

        if _yunet_detector is None:
            _yunet_detector = cv2.FaceDetectorYN.create(
                str(model_path),
                "",
                (detect_w, detect_h),
                score_threshold=0.6,
                nms_threshold=0.3,
                top_k=5000,
            )
        else:
            _yunet_detector.setInputSize((detect_w, detect_h))

        _, faces = _yunet_detector.detect(detect_bgr)
        if faces is None or len(faces) == 0:
            return None
        # faces: [x, y, w, h, ...] — pick largest
        best = max(faces, key=lambda f: float(f[2]) * float(f[3]))
        x = int(round(float(best[0]) / scale))
        y = int(round(float(best[1]) / scale))
        fw = int(round(float(best[2]) / scale))
        fh = int(round(float(best[3]) / scale))
        x2, y2 = x + fw, y + fh
        bw, bh = fw, fh
        x1 = max(0, x - int(0.1 * bw))
        y1 = max(0, y - int(0.15 * bh))
        x2 = min(w, x2 + int(0.1 * bw))
        y2 = min(h, y2 + int(0.1 * bh))
        if x2 - x1 < 40 or y2 - y1 < 40:
            return None
        return x1, y1, x2, y2
    except Exception:
        return None


def _haar_face_bbox(bgr: np.ndarray) -> tuple[int, int, int, int] | None:
    global _haar_cascade, _haar_unavailable
    if _haar_unavailable:
        return None
    try:
        cascade_dir = getattr(cv2.data, "haarcascades", "")
        cascade_path = Path(cascade_dir) / "haarcascade_frontalface_default.xml"
        if not cascade_path.exists():
            _haar_unavailable = True
            return None
        if _haar_cascade is None:
            _haar_cascade = cv2.CascadeClassifier(str(cascade_path))
            if _haar_cascade.empty():
                _haar_unavailable = True
                return None
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        faces = _haar_cascade.detectMultiScale(gray, 1.1, 5, minSize=(80, 80))
        if len(faces) == 0:
            return None
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        return int(x), int(y), int(x + w), int(y + h)
    except Exception:
        return None


def _detect_face_with_method(bgr: np.ndarray) -> tuple[tuple[int, int, int, int] | None, str | None]:
    """Primary: OpenCV YuNet. Fallback: Haar cascade."""
    box = _yunet_face_bbox(bgr)
    if box is not None:
        return box, "yunet"
    box = _haar_face_bbox(bgr)
    if box is not None:
        return box, "haar"
    return None, None


def verify_facial_skin(crop_bgr: np.ndarray) -> tuple[bool, float, str]:
    """
    Verifies that the cropped face contains visible, authentic human facial skin.
    Uses YCrCb and HSV skin tone analysis across all Fitzpatrick phototypes (I-VI).
    """
    if crop_bgr is None or crop_bgr.size == 0:
        return False, 0.0, "Empty facial region"

    h, w = crop_bgr.shape[:2]
    if h < 40 or w < 40:
        return False, 0.0, "Facial area resolution is too low"

    # YCrCb color space skin bounds
    ycrcb = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2YCrCb)
    ycrcb_mask = cv2.inRange(
        ycrcb,
        np.array([20, 133, 77], dtype=np.uint8),
        np.array([250, 175, 127], dtype=np.uint8),
    )

    # HSV color space skin bounds (handles highlights, shadows, diverse undertones)
    hsv = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2HSV)
    hsv_mask1 = cv2.inRange(
        hsv,
        np.array([0, 25, 35], dtype=np.uint8),
        np.array([28, 210, 255], dtype=np.uint8),
    )
    hsv_mask2 = cv2.inRange(
        hsv,
        np.array([168, 25, 35], dtype=np.uint8),
        np.array([180, 210, 255], dtype=np.uint8),
    )
    hsv_mask = cv2.bitwise_or(hsv_mask1, hsv_mask2)

    skin_mask = cv2.bitwise_or(ycrcb_mask, hsv_mask)
    total_px = h * w
    skin_px = int(cv2.countNonZero(skin_mask))
    skin_ratio = float(skin_px) / float(total_px) if total_px > 0 else 0.0

    # In a cropped face, features like hair, eyes, lips, and background exist,
    # but at least 18% of the bounding box must be valid facial skin.
    if skin_ratio < 0.18:
        return (
            False,
            skin_ratio,
            "Insufficient facial skin detected. Please ensure your face is well-lit and not covered by a mask or heavy occlusion",
        )

    return True, skin_ratio, "OK"


def detect_face(bgr: np.ndarray) -> tuple[int, int, int, int] | None:
    box, _ = _detect_face_with_method(bgr)
    return box


def load_and_preprocess(
    path_or_bytes,
    require_face: bool = True,
    return_meta: bool = False,
):
    if isinstance(path_or_bytes, (str, Path)):
        bgr = cv2.imread(str(path_or_bytes))
    else:
        arr = np.frombuffer(path_or_bytes, dtype=np.uint8)
        bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if bgr is None:
        raise ValueError("Could not decode image")

    bbox, detector = _detect_face_with_method(bgr)
    face_found = bbox is not None
    skin_verified = False
    skin_ratio = 0.0

    if require_face and not face_found:
        raise ValueError("No face detected - Skinova strictly scans facial skin only. Please upload or capture a clear front-facing facial photo.")

    if bbox is not None:
        x1, y1, x2, y2 = bbox
        crop = bgr[y1:y2, x1:x2]
        is_skin, ratio, reason = verify_facial_skin(crop)
        skin_verified = is_skin
        skin_ratio = ratio
        if require_face and not is_skin:
            raise ValueError(f"Facial skin validation failed: {reason}")
    else:
        # fallback for pre-cropped dataset/macro test benchmarks when require_face is False
        h, w = bgr.shape[:2]
        side = min(h, w)
        y0 = (h - side) // 2
        x0 = (w - side) // 2
        crop = bgr[y0 : y0 + side, x0 : x0 + side]

    rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
    resized = cv2.resize(rgb, (IMG_SIZE, IMG_SIZE), interpolation=cv2.INTER_AREA)
    meta = {
        "face_found": face_found,
        "skin_verified": skin_verified,
        "skin_ratio": round(skin_ratio, 3),
        "bbox": bbox,
        "detector": detector if detector is not None else "center_crop",
    }
    if return_meta:
        return resized, meta
    return resized


def estimate_skin_attributes(rgb_224: np.ndarray) -> dict[str, float]:
    """
    Lightweight heuristic sub-scores (not separate trained detectors).
    Used to populate oiliness / pores / redness / dark_spots dashboard fields.
    """
    img = rgb_224.astype(np.float32)
    r, g, b = img[:, :, 0], img[:, :, 1], img[:, :, 2]
    redness = float(np.clip(np.mean(np.clip(r - g, 0, None)) / 40.0 * 100.0, 0, 100))
    mx = np.max(img, axis=2)
    mn = np.min(img, axis=2)
    sat = np.zeros_like(mx, dtype=np.float32)
    valid_mx = mx > 1e-6
    sat[valid_mx] = (mx[valid_mx] - mn[valid_mx]) / mx[valid_mx]
    highlights = (mx > 200) & (sat < 0.25)
    oiliness = float(np.clip(highlights.mean() * 400.0 + 25.0, 0, 100))
    gray = cv2.cvtColor(rgb_224, cv2.COLOR_RGB2GRAY)
    lap = cv2.Laplacian(gray, cv2.CV_64F).var()
    pores = float(np.clip((lap - 50) / 8.0, 0, 100))
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    dark = lum < (np.percentile(lum, 25))
    dark_spots = float(np.clip(dark.mean() * 180.0, 0, 100))
    return {
        "oiliness": round(oiliness, 1),
        "pores": round(pores, 1),
        "redness": round(redness, 1),
        "dark_spots": round(dark_spots, 1),
    }
