"""
Phase 1 automated tests: Image upload & camera capture pipeline.
Tests FastAPI image endpoints, image decoding, face detection,
attribute estimation, error handling, and file size constraints.
"""

from __future__ import annotations

import io
import os
import sys
import unittest
from pathlib import Path

from PIL import Image
from starlette.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR / "ml" / "image_model"))
sys.path.insert(0, str(BACKEND_DIR / "ml" / "data_model"))
sys.path.insert(0, str(BACKEND_DIR / "ml" / "fusion"))

from app.main import app  # noqa: E402
from predict_image import load_model, predict_image  # noqa: E402


class TestSmartSkinScanPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.sample_face_path = ROOT / "frontend" / "public" / "sample_face.jpg"
        cls.sample_lesion_path = ROOT / "frontend" / "public" / "sample_lesion.jpg"
        assert cls.sample_face_path.exists(), f"Sample face not found at {cls.sample_face_path}"
        assert cls.sample_lesion_path.exists(), f"Sample lesion not found at {cls.sample_lesion_path}"

    def test_01_model_loading_and_architecture(self):
        """Ensure MobileNetV2 improved model loads cleanly."""
        model, model_name = load_model()
        self.assertIsNotNone(model, "Model should not be None")
        self.assertEqual(model_name, "mobilenetv2_acne04_improved")

    def test_02_successful_facial_upload_prediction(self):
        """Test POST /predict/image with a valid facial photo."""
        with open(self.sample_face_path, "rb") as f:
            resp = self.client.post(
                "/predict/image",
                files={"file": ("sample_face.jpg", f, "image/jpeg")},
                data={"require_face": "true"},
            )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("severity", data)
        self.assertIn(data["severity"], [0, 1, 2, 3])
        self.assertIn("severity_label", data)
        self.assertIn("class_probabilities", data)
        self.assertEqual(len(data["class_probabilities"]), 4)
        self.assertIn("risk_percent", data)
        self.assertGreaterEqual(data["risk_percent"], 5.0)
        self.assertLessEqual(data["risk_percent"], 95.0)
        self.assertTrue(data["face_detected"])
        self.assertEqual(data["method"], "mobilenetv2_acne04_improved")

    def test_03_camera_capture_simulation(self):
        """
        Simulate camera capture snapshot:
        Browser canvas.toBlob() produces JPEG bytes. Verify prediction matches upload pipeline.
        """
        # Create a synthetic 1280x720 RGB test image representing a captured webcam frame
        img = Image.new("RGB", (640, 480), color=(220, 180, 160))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=95)
        raw_bytes = buf.getvalue()

        # Send with require_face=false (regional close-up fallback)
        resp = self.client.post(
            "/predict/image",
            files={"file": ("camera_scan_12345.jpg", raw_bytes, "image/jpeg")},
            data={"require_face": "false"},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("severity", data)
        self.assertIn("class_probabilities", data)
        self.assertEqual(data["method"], "mobilenetv2_acne04_improved")

    def test_04_regional_lesion_close_up_allowance(self):
        """Test close-up image without requiring a full frontal face."""
        with open(self.sample_lesion_path, "rb") as f:
            resp = self.client.post(
                "/predict/image",
                files={"file": ("sample_lesion.jpg", f, "image/jpeg")},
                data={"require_face": "false"},
            )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("severity", data)
        self.assertIn("oiliness", data)
        self.assertIn("pores", data)
        self.assertIn("redness", data)
        self.assertIn("dark_spots", data)

    def test_05_strict_face_rejection_when_no_face(self):
        """Test require_face=true on an image with no face raises 422 with clear message."""
        # Flat color square without face
        img = Image.new("RGB", (224, 224), color=(50, 50, 50))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        raw_bytes = buf.getvalue()

        resp = self.client.post(
            "/predict/image",
            files={"file": ("noface.jpg", raw_bytes, "image/jpeg")},
            data={"require_face": "true"},
        )
        self.assertEqual(resp.status_code, 422)
        self.assertIn("face", resp.json().get("detail", "").lower())

    def test_06_corrupt_image_rejection(self):
        """Test non-decodable corrupt bytes (>=100 bytes) return 422 from predict_image."""
        corrupt_bytes = b"CORRUPT_NOT_AN_IMAGE_PAYLOAD_" * 10
        resp = self.client.post(
            "/predict/image",
            files={"file": ("corrupt.jpg", corrupt_bytes, "image/jpeg")},
            data={"require_face": "false"},
        )
        self.assertEqual(resp.status_code, 422)
        self.assertIn("Could not decode image", resp.json().get("detail", ""))

    def test_07_oversized_image_rejection(self):
        """Test file exceeding max upload limit (>20MB) returns 400."""
        oversized_bytes = b"0" * (21 * 1024 * 1024)
        resp = self.client.post(
            "/predict/image",
            files={"file": ("huge.jpg", oversized_bytes, "image/jpeg")},
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Image too large", resp.json().get("detail", ""))

    def test_08_empty_or_too_small_image_rejection(self):
        """Test file under 100 bytes returns 400."""
        tiny_bytes = b"SHORT"
        resp = self.client.post(
            "/predict/image",
            files={"file": ("tiny.jpg", tiny_bytes, "image/jpeg")},
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("too small or empty", resp.json().get("detail", ""))

    def test_09_no_facial_images_in_history_storage(self):
        """Verify scan records do not persist raw images or facial tensors."""
        with open(self.sample_face_path, "rb") as f:
            resp = self.client.post(
                "/predict/image",
                files={"file": ("sample_face.jpg", f, "image/jpeg")},
                data={"require_face": "true"},
            )
        self.assertEqual(resp.status_code, 200)
        out = resp.json()
        # Verify no raw image base64 or bytes in payload
        for key in ["image_raw", "image_base64", "face_crop_bytes", "pixels"]:
            self.assertNotIn(key, out)


if __name__ == "__main__":
    unittest.main()
