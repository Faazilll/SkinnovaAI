"""Tests for the Lightweight Image-Questionnaire Validation Layer."""

from __future__ import annotations

import io
import json
import sys
import unittest
from pathlib import Path

import cv2
import numpy as np
from fastapi.testclient import TestClient

TESTS_DIR = Path(__file__).resolve().parent
BACKEND_DIR = TESTS_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent

sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR / "ml" / "image_model"))
sys.path.insert(0, str(BACKEND_DIR / "ml" / "data_model"))
sys.path.insert(0, str(BACKEND_DIR / "ml" / "fusion"))

from app.main import app
from app.validation import validate_image_and_questionnaire

SAMPLE_FACE = PROJECT_ROOT / "frontend" / "public" / "sample_face.jpg"


class TestValidationLayer(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.assertTrue(SAMPLE_FACE.exists(), f"Sample face not found at {SAMPLE_FACE}")
        self.sample_bgr = cv2.imread(str(SAMPLE_FACE))
        self.assertIsNotNone(self.sample_bgr, "Failed to read sample_face.jpg")

    def test_valid_image_clean_shaven_female(self):
        """Clean shaven face with female selection should validate cleanly with no warning."""
        q = {"gender": "female", "age": 24}
        res = validate_image_and_questionnaire(self.sample_bgr, q)
        self.assertTrue(res["valid"])
        self.assertEqual(len(res["errors"]), 0)
        self.assertIsNotNone(res["quality"])
        self.assertTrue(res["quality"]["face_detected"])
        self.assertFalse(res["quality"]["is_blurry"])
        self.assertIsNone(res["consistency_warning"])

    def test_valid_image_male_selection(self):
        """Any valid face with male selection should not trigger an appearance mismatch."""
        q = {"gender": "male", "age": 28}
        res = validate_image_and_questionnaire(self.sample_bgr, q)
        self.assertTrue(res["valid"])
        self.assertEqual(len(res["errors"]), 0)
        self.assertIsNone(res["consistency_warning"])

    def test_blurry_image_rejection(self):
        """Severely blurred image should fail quality validation with a clear message."""
        blurred = cv2.GaussianBlur(self.sample_bgr, (45, 45), 0)
        q = {"gender": "female", "age": 24}
        res = validate_image_and_questionnaire(blurred, q)
        self.assertFalse(res["valid"])
        self.assertTrue(any("blurry" in err.lower() for err in res["errors"]))

    def test_dark_underexposed_image_rejection(self):
        """Severely underexposed image should fail quality validation."""
        dark = (self.sample_bgr * 0.15).astype(np.uint8)
        q = {"gender": "female", "age": 24}
        res = validate_image_and_questionnaire(dark, q)
        self.assertFalse(res["valid"])
        self.assertTrue(
            any("dark" in err.lower() or "underexposed" in err.lower() for err in res["errors"])
        )

    def test_non_face_image_rejection(self):
        """Synthetic geometric pattern with no human face should fail face requirement."""
        blank = np.zeros((300, 300, 3), dtype=np.uint8)
        blank[:, :] = (120, 120, 120)
        q = {"gender": "female", "age": 24}
        res = validate_image_and_questionnaire(blank, q, require_face=True)
        self.assertFalse(res["valid"])
        self.assertTrue(any("no clear, usable human face" in err.lower() for err in res["errors"]))

    def test_validate_endpoint_api(self):
        """POST /predict/validate should return validation payload via HTTP."""
        with open(SAMPLE_FACE, "rb") as f:
            img_bytes = f.read()

        q_json = json.dumps({"gender": "female", "age": 25, "sleep_hours": 7.5})
        response = self.client.post(
            "/predict/validate",
            files={"file": ("sample.jpg", io.BytesIO(img_bytes), "image/jpeg")},
            data={"questionnaire_json": q_json, "require_face": "true"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("valid", data)
        self.assertTrue(data["valid"])
        self.assertIn("quality", data)

    def test_fusion_upload_blocks_invalid_image(self):
        """POST /predict/fusion/upload should reject an invalid non-face image with HTTP 422."""
        blank = np.zeros((200, 200, 3), dtype=np.uint8)
        _, enc = cv2.imencode(".jpg", blank)
        q_json = json.dumps({"gender": "female", "age": 25})
        response = self.client.post(
            "/predict/fusion/upload",
            files={"file": ("blank.jpg", io.BytesIO(enc.tobytes()), "image/jpeg")},
            data={"questionnaire_json": q_json, "require_face": "true"},
        )
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
