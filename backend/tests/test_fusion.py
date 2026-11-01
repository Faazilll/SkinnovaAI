"""
Phase 2 automated tests: Transparent Multimodal Fusion Engine.
Tests the exact 0.55/0.45 mathematical weighting formula, skin health bonus logic,
clamping, missing input detection, failure cases, and endpoint response schemas.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

from starlette.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR / "ml" / "image_model"))
sys.path.insert(0, str(BACKEND_DIR / "ml" / "data_model"))
sys.path.insert(0, str(BACKEND_DIR / "ml" / "fusion"))

from app.main import app  # noqa: E402
from fusion_engine import (  # noqa: E402
    DATA_WEIGHT,
    IMAGE_WEIGHT,
    fuse,
    skin_health_score,
)


class TestTransparentMultimodalFusion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.valid_image = {
            "severity": 2,
            "severity_label": "Severe",
            "risk_percent": 68.0,
            "class_probabilities": {"0": 0.05, "1": 0.15, "2": 0.70, "3": 0.10},
            "oiliness": 45.0,
            "pores": 50.0,
            "redness": 60.0,
            "dark_spots": 35.0,
            "face_detected": True,
            "method": "mobilenetv2_acne04_improved",
        }
        cls.valid_data = {
            "hormonal_score": 60.0,
            "lifestyle_score": 50.0,
            "environmental_score": 40.0,
            "combined_score": 51.5,
            "drivers": ["Insufficient sleep", "Elevated stress"],
            "method": "random_forest_on_synthetic_labels",
        }

    def test_01_weights_constant_preservation(self):
        """Ensure the documented weights (0.55 image, 0.45 data) are strictly preserved."""
        self.assertEqual(IMAGE_WEIGHT, 0.55)
        self.assertEqual(DATA_WEIGHT, 0.45)
        self.assertAlmostEqual(IMAGE_WEIGHT + DATA_WEIGHT, 1.0)

    def test_02_exact_fusion_formula_arithmetic(self):
        """Verify the exact formula: FinalRisk = 0.55 * image_risk + 0.45 * data_combined."""
        out = fuse(self.valid_image, self.valid_data)
        expected_risk = round(0.55 * 68.0 + 0.45 * 51.5, 1)  # 37.4 + 23.175 = 60.575 -> 60.6
        self.assertEqual(out["final_risk_percent"], expected_risk)
        self.assertIn("fusion_breakdown", out)
        breakdown = out["fusion_breakdown"]
        self.assertEqual(breakdown["weights"]["image"], 0.55)
        self.assertEqual(breakdown["weights"]["data"], 0.45)
        self.assertIn("68.0% * 0.55", breakdown["arithmetic_steps"][0])

    def test_03_skin_health_bonus_logic(self):
        """
        Verify skin barrier health bonus logic:
        Base = 100 - FinalRisk.
        Bonus added only when lifestyle < 40 or environmental < 40.
        """
        # Case A: Scores >= 40 (no bonus)
        health_no_bonus = skin_health_score(final_risk=60.0, lifestyle=50.0, environmental=50.0)
        self.assertEqual(health_no_bonus, 40.0)

        # Case B: Favorable lifestyle (< 40)
        # Bonus = (40 - 20) * 0.08 = 1.6
        health_with_lifestyle = skin_health_score(final_risk=60.0, lifestyle=20.0, environmental=50.0)
        self.assertEqual(health_with_lifestyle, 41.6)

        # Case C: Favorable environment (< 40)
        # Bonus = (40 - 20) * 0.05 = 1.0
        health_with_env = skin_health_score(final_risk=60.0, lifestyle=50.0, environmental=20.0)
        self.assertEqual(health_with_env, 41.0)

    def test_04_boundary_clamping(self):
        """Verify clamping to [0.0, 100.0] for boundary inputs."""
        # Lower bound
        min_img = {"risk_percent": 0.0, "severity": 0}
        min_data = {"combined_score": 0.0, "lifestyle_score": 0.0, "environmental_score": 0.0}
        out_min = fuse(min_img, min_data)
        self.assertGreaterEqual(out_min["final_risk_percent"], 0.0)

        # Upper bound
        max_img = {"risk_percent": 100.0, "severity": 3}
        max_data = {"combined_score": 100.0, "lifestyle_score": 100.0, "environmental_score": 100.0}
        out_max = fuse(max_img, max_data)
        self.assertLessEqual(out_max["final_risk_percent"], 100.0)

    def test_05_missing_image_rejection(self):
        """Ensure missing or empty image dictionary raises ValueError and returns 422, not silent defaults."""
        with self.assertRaises(ValueError):
            fuse(None, self.valid_data)  # type: ignore

        with self.assertRaises(ValueError):
            fuse({}, self.valid_data)

        # Endpoint test via /predict/fusion
        resp = self.client.post(
            "/predict/fusion",
            json={"image": {}, "data": self.valid_data},
        )
        self.assertEqual(resp.status_code, 422)
        self.assertIn("image", resp.json()["detail"].lower())

    def test_06_missing_questionnaire_rejection(self):
        """Ensure missing questionnaire data raises ValueError and returns 422."""
        with self.assertRaises(ValueError):
            fuse(self.valid_image, None)  # type: ignore

        with self.assertRaises(ValueError):
            fuse(self.valid_image, {})

        resp = self.client.post(
            "/predict/fusion",
            json={"image": self.valid_image, "data": {}},
        )
        self.assertEqual(resp.status_code, 422)
        self.assertIn("systemic", resp.json()["detail"].lower())

    def test_07_component_source_transparency(self):
        """Verify that component sources clearly distinguish CNN from Rule Engine."""
        out = fuse(self.valid_image, self.valid_data)
        sources = out["fusion_breakdown"]["component_sources"]
        self.assertEqual(sources["image"]["source_type"], "Trained Convolutional Neural Network")
        self.assertIn("Rule Engine", sources["data"]["source_type"])
        self.assertIn("mobilenetv2", sources["image"]["model_identifier"])

    def test_08_end_to_end_fusion_upload_endpoint(self):
        """Test full multipart /predict/fusion/upload endpoint returns full transparency payload."""
        sample_path = ROOT / "frontend" / "public" / "sample_face.jpg"
        questionnaire = {
            "age": 22,
            "gender": "female",
            "menstrual_cycle": "regular",
            "pcos": False,
            "sleep_hours": 7.0,
            "diet_quality": "average",
        }
        with open(sample_path, "rb") as f:
            resp = self.client.post(
                "/predict/fusion/upload",
                files={"file": ("face.jpg", f, "image/jpeg")},
                data={
                    "questionnaire_json": json.dumps(questionnaire),
                    "require_face": "false",
                },
            )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("fusion_breakdown", data)
        self.assertIn("final_risk_percent", data)
        self.assertIn("skin_health_score", data)
        self.assertIn("gauges", data)
        self.assertIn("trend", data)
        self.assertIn("recommendations", data)


if __name__ == "__main__":
    unittest.main()
