"""Image inference → severity, risk %, heuristic skin attributes."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from preprocess import estimate_skin_attributes, load_and_preprocess  # noqa: E402

SEVERITY_TO_RISK = {0: 18.0, 1: 42.0, 2: 68.0, 3: 88.0}
SEVERITY_LABELS = {
    0: "Clear / Mild",
    1: "Moderate",
    2: "Severe",
    3: "Very Severe",
}
PROBLEM_AREA_HINTS = {
    0: ["None significant"],
    1: ["Cheeks", "T-zone"],
    2: ["Cheeks", "Jawline", "Forehead"],
    3: ["Widespread facial involvement", "Jawline", "Cheeks"],
}

_model = None
_model_name = None


def _model_paths() -> list[tuple[str, Path]]:
    d = ROOT / "artifacts" / "image"
    return [
        ("mobilenetv2_acne04_improved", d / "mobilenetv2_acne04_improved.keras"),
        ("mobilenetv2_acne04_improved", d / "mobilenetv2_acne04_improved.h5"),
        ("efficientnetb0_acne04", d / "efficientnetb0_acne04.keras"),
        ("efficientnetb0_acne04", d / "efficientnetb0_acne04.h5"),
        ("mobilenetv2_acne04", d / "mobilenetv2_acne04.keras"),
        ("mobilenetv2_acne04", d / "mobilenetv2_acne04.h5"),
    ]


def _patch_keras_initializers():
    try:
        import keras.initializers
        for cls_name in ["VarianceScaling", "GlorotUniform", "GlorotNormal", "HeNormal", "HeUniform", "TruncatedNormal"]:
            cls = getattr(keras.initializers, cls_name, None)
            if cls is not None and hasattr(cls, "__init__"):
                orig_init = cls.__init__
                if getattr(orig_init, "_is_patched", False):
                    continue
                def _make_patched(orig):
                    def _patched(self, *args, **kwargs):
                        kwargs.pop("input_axes", None)
                        kwargs.pop("output_axes", None)
                        return orig(self, *args, **kwargs)
                    _patched._is_patched = True
                    return _patched
                cls.__init__ = _make_patched(orig_init)
    except Exception:
        pass


def load_model():
    global _model, _model_name
    if _model is not None:
        return _model, _model_name
    _patch_keras_initializers()
    import tensorflow as tf

    for name, p in _model_paths():
        if p.exists():
            try:
                _model = tf.keras.models.load_model(p)
                _model_name = name
                return _model, _model_name
            except Exception as e:
                print(f"Warning: failed loading {p.name}: {e}")
                continue
    return None, None


def _heuristic_severity(rgb) -> tuple[int, list[float]]:
    """Fallback when no trained weights exist — color/texture proxy only."""
    attrs = estimate_skin_attributes(rgb)
    score = (
        0.35 * attrs["redness"]
        + 0.30 * attrs["pores"]
        + 0.20 * attrs["oiliness"]
        + 0.15 * attrs["dark_spots"]
    )
    if score < 28:
        sev = 0
    elif score < 48:
        sev = 1
    elif score < 68:
        sev = 2
    else:
        sev = 3
    # fake softmax-ish distribution centered on sev
    logits = np.array([-abs(i - sev) * 2.2 for i in range(4)], dtype=np.float32)
    e = np.exp(logits - logits.max())
    probs = (e / e.sum()).tolist()
    return sev, probs


def predict_image(
    path_or_bytes,
    require_face: bool = True,
) -> dict:
    rgb, meta = load_and_preprocess(
        path_or_bytes, require_face=require_face, return_meta=True
    )
    attrs = estimate_skin_attributes(rgb)
    model, model_name = load_model()
    method = model_name or "mobilenetv2_acne04"
    if model is None:
        severity, probs = _heuristic_severity(rgb)
        method = "heuristic_fallback_no_trained_weights"
    else:
        x = np.expand_dims(rgb.astype(np.float32), 0)
        probs = model.predict(x, verbose=0)[0].tolist()
        severity = int(np.argmax(probs))

    # Blend class risk with attribute heat for future-risk %
    base_risk = SEVERITY_TO_RISK[severity]
    attr_boost = (
        0.15 * attrs["oiliness"]
        + 0.20 * attrs["redness"]
        + 0.10 * attrs["pores"]
    ) * 0.25
    risk = float(np.clip(base_risk + attr_boost - 8.0, 5, 95))

    return {
        "severity": severity,
        "severity_label": SEVERITY_LABELS[severity],
        "class_probabilities": {
            str(i): round(float(probs[i]), 4) for i in range(4)
        },
        "risk_percent": round(risk, 1),
        "oiliness": attrs["oiliness"],
        "pores": attrs["pores"],
        "redness": attrs["redness"],
        "dark_spots": attrs["dark_spots"],
        "current_skin_condition": SEVERITY_LABELS[severity],
        "problem_areas": PROBLEM_AREA_HINTS[severity],
        "face_detected": bool(meta.get("face_found")),
        "skin_verified": bool(meta.get("skin_verified")),
        "skin_ratio": meta.get("skin_ratio"),
        "method": method,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("image", type=str)
    parser.add_argument("--allow-no-face", action="store_true")
    args = parser.parse_args()
    out = predict_image(args.image, require_face=not args.allow_no_face)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
