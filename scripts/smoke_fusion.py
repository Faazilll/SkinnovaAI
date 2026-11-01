"""Quick end-to-end fusion smoke test."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
img = next((ROOT / "data" / "acne04" / "organized" / "1").glob("*.jpg"))
q = {
    "age": 24,
    "gender": "female",
    "menstrual_cycle": "irregular",
    "pcos": True,
    "sleep_hours": 5.5,
    "stress_level": 8,
    "diet_quality": "poor_high_gi",
    "pollution_level": "high",
    "humidity": "high",
    "location_type": "urban",
}
with img.open("rb") as f:
    r = httpx.post(
        "http://127.0.0.1:8000/predict/fusion/upload",
        files={"file": ("face.jpg", f, "image/jpeg")},
        data={"questionnaire_json": json.dumps(q), "require_face": "false"},
        timeout=120.0,
    )
print("status", r.status_code)
r.raise_for_status()
out = r.json()
print(
    json.dumps(
        {
            "skin_health_score": out["skin_health_score"],
            "final_risk_percent": out["final_risk_percent"],
            "gauges": out["gauges"],
            "trend": out["trend"],
            "image_method": out["image"]["method"],
            "data_method": out["data"]["method"],
        },
        indent=2,
    )
)
print("recommendation categories:", list(out["recommendations"].keys()))
sys.exit(0)
