"""
Phase 3 automated tests: Evidence-Linked Action Plan.
Verifies that educational recommendations and clinical escalation pathways
are deterministically linked to genuine visual AI predictions, user questionnaire inputs,
and documented literature sources.
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
from fusion_engine import fuse, generate_recommendations  # noqa: E402


class TestEvidenceLinkedActionPlan(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_all_recommendations_have_evidence_fields(self):
        """Ensure every recommendation contains text, why_shown, trigger_input, evidence_source, advice_type."""
        mock_img = {"severity": 1, "severity_label": "Moderate", "risk_percent": 42.0, "oiliness": 60.0}
        mock_data = {
            "hormonal_score": 35.0,
            "lifestyle_score": 40.0,
            "environmental_score": 30.0,
            "combined_score": 35.5,
            "drivers": ["Insufficient sleep"],
            "answers": {"sleep_hours": 5.0, "skincare_consistency": "inconsistent"},
        }
        recs = generate_recommendations(mock_img, mock_data, final_risk=40.0)

        for category, items in recs.items():
            self.assertGreater(len(items), 0, f"Category {category} should have items")
            for item in items:
                self.assertIn("text", item)
                self.assertIn("why_shown", item)
                self.assertIn("trigger_input", item)
                self.assertIn("evidence_source", item)
                self.assertIn("advice_type", item)
                self.assertIn(item["advice_type"], ["General Educational Guidance", "Clinical Escalation"])

    def test_02_sleep_deprivation_trigger(self):
        """Verify sleep deprivation recommendation activates only when sleep < 6.5h."""
        mock_img = {"severity": 0, "severity_label": "Clear / Mild", "risk_percent": 18.0}

        # Case A: Poor sleep (5.0 hours)
        poor_sleep_data = {
            "lifestyle_score": 55.0,
            "combined_score": 40.0,
            "drivers": ["Insufficient sleep"],
            "answers": {"sleep_hours": 5.0},
        }
        recs_poor = generate_recommendations(mock_img, poor_sleep_data, final_risk=28.0)
        lifestyle_texts = [r["text"] for r in recs_poor["Lifestyle Changes"]]
        self.assertTrue(any("sleep and wake routine" in t for t in lifestyle_texts))

        # Case B: Adequate sleep (8.0 hours)
        good_sleep_data = {
            "lifestyle_score": 25.0,
            "combined_score": 25.0,
            "drivers": [],
            "answers": {"sleep_hours": 8.0},
        }
        recs_good = generate_recommendations(mock_img, good_sleep_data, final_risk=21.0)
        lifestyle_good_texts = [r["text"] for r in recs_good["Lifestyle Changes"]]
        self.assertFalse(any("sleep and wake routine" in t for t in lifestyle_good_texts))

    def test_03_skincare_inconsistency_trigger(self):
        """Verify skincare routine inconsistency trigger matches user input."""
        mock_img = {"severity": 0, "severity_label": "Clear / Mild", "risk_percent": 18.0}
        data_inconsistent = {
            "lifestyle_score": 30.0,
            "combined_score": 25.0,
            "drivers": [],
            "answers": {"skincare_consistency": "inconsistent"},
        }
        recs = generate_recommendations(mock_img, data_inconsistent, final_risk=21.0)
        skincare_texts = [r["text"] for r in recs["Skin Care Routine"]]
        self.assertTrue(any("consistent, gentle skincare routine" in t for t in skincare_texts))
        matched = [r for r in recs["Skin Care Routine"] if "consistent, gentle skincare routine" in r["text"]][0]
        self.assertIn("skincare inconsistency", matched["why_shown"].lower())

    def test_04_high_severity_clinical_escalation(self):
        """Verify Hayashi Grade 2 or 3 triggers Clinical Escalation to dermatologist."""
        # Severe Grade 2
        sev_img = {"severity": 2, "severity_label": "Severe", "risk_percent": 68.0}
        sev_data = {"hormonal_score": 50.0, "combined_score": 50.0, "drivers": []}
        recs = generate_recommendations(sev_img, sev_data, final_risk=60.0)

        derm_items = recs["When to See a Dermatologist"]
        self.assertTrue(any("board-certified dermatologist" in r["text"] for r in derm_items))
        escalation_item = [r for r in derm_items if "board-certified dermatologist" in r["text"]][0]
        self.assertEqual(escalation_item["advice_type"], "Clinical Escalation")
        self.assertIn("Grade 2", escalation_item["trigger_input"])

    def test_05_pcos_endocrine_referral_trigger(self):
        """Verify positive PCOS flag triggers multidisciplinary endocrine referral."""
        mock_img = {"severity": 1, "severity_label": "Moderate", "risk_percent": 42.0}
        pcos_data = {
            "hormonal_score": 70.0,
            "combined_score": 55.0,
            "drivers": ["PCOS / androgen excess"],
            "answers": {"pcos": True},
        }
        recs = generate_recommendations(mock_img, pcos_data, final_risk=48.0)
        derm_items = recs["When to See a Dermatologist"]
        self.assertTrue(any("endocrinologist" in r["text"].lower() for r in derm_items))
        pcos_rec = [r for r in derm_items if "endocrinologist" in r["text"].lower()][0]
        self.assertIn("Azziz", pcos_rec["evidence_source"])

    def test_06_pollution_antioxidant_trigger(self):
        """Verify high pollution trigger recommends topical antioxidants beneath SPF."""
        mock_img = {"severity": 0, "severity_label": "Clear / Mild", "risk_percent": 18.0}
        pol_data = {
            "environmental_score": 65.0,
            "combined_score": 45.0,
            "drivers": ["High pollution exposure"],
            "answers": {"pollution_level": "high"},
        }
        recs = generate_recommendations(mock_img, pol_data, final_risk=30.0)
        env_items = recs["Environmental Protection"]
        self.assertTrue(any("antioxidant serum" in r["text"].lower() for r in env_items))
        antiox_rec = [r for r in env_items if "antioxidant serum" in r["text"].lower()][0]
        self.assertIn("Krutmann", antiox_rec["evidence_source"])

    def test_07_pregnancy_safety_contraindication_and_alternatives(self):
        """Verify pregnancy strictly avoids retinoids and prescribes pregnancy-safe azelaic acid & OBGYN escalation."""
        mock_img = {"severity": 1, "severity_label": "Moderate", "oiliness": 65.0, "risk_percent": 45.0}
        preg_data = {
            "hormonal_score": 50.0,
            "lifestyle_score": 40.0,
            "environmental_score": 30.0,
            "combined_score": 41.5,
            "drivers": [],
            "answers": {"pregnancy": True, "gender": "female"},
        }
        recs = generate_recommendations(mock_img, preg_data, final_risk=43.0)

        skincare_texts = " ".join(r["text"].lower() for r in recs["Skin Care Routine"])
        # Retinoids/adapalene should NOT be recommended to pregnant individuals
        self.assertNotIn("adapalene", skincare_texts)
        # Azelaic acid should be recommended as pregnancy-safe
        self.assertIn("azelaic acid", skincare_texts)
        # Dermatologist category must contain obstetrician consultation
        derm_texts = " ".join(r["text"].lower() for r in recs["When to See a Dermatologist"])
        self.assertIn("obstetrician", derm_texts)

    def test_08_dynamic_difference_between_distinct_profiles(self):
        """Verify recommendations genuinely differ between contrasting user profiles."""
        mock_img_mild = {"severity": 0, "severity_label": "Clear / Mild", "oiliness": 40.0, "pores": 35.0, "redness": 20.0, "dark_spots": 15.0, "risk_percent": 20.0}
        mock_img_severe = {"severity": 2, "severity_label": "Severe Papulopustular", "oiliness": 75.0, "pores": 70.0, "redness": 65.0, "dark_spots": 55.0, "risk_percent": 72.0}

        # Profile A: Young female with PCOS, high stress, high pollution, irregular cycle
        data_a = {
            "hormonal_score": 75.0,
            "lifestyle_score": 70.0,
            "environmental_score": 68.0,
            "combined_score": 71.5,
            "drivers": ["PCOS / androgen excess", "Elevated stress", "High pollution exposure"],
            "answers": {
                "pcos": True,
                "stress_level": 9,
                "pollution_level": "high",
                "diet_quality": "poor",
                "menstrual_cycle": "irregular",
            },
        }

        # Profile B: Male athlete in arid sunny climate, optimal sleep, good diet, non-smoker
        data_b = {
            "hormonal_score": 25.0,
            "lifestyle_score": 20.0,
            "environmental_score": 45.0,
            "combined_score": 28.5,
            "drivers": [],
            "answers": {
                "pcos": False,
                "gender": "male",
                "stress_level": 2,
                "pollution_level": "low",
                "diet_quality": "good",
                "sleep_hours": 8.5,
                "exercise_frequency": "daily",
                "climate": "dry_arid",
                "humidity": "low",
                "sun_exposure": "high",
                "outdoor_ratio": 0.6,
            },
        }

        recs_a = generate_recommendations(mock_img_severe, data_a, final_risk=71.8)
        recs_b = generate_recommendations(mock_img_mild, data_b, final_risk=23.8)

        texts_a = set(r["text"] for cat in recs_a.values() for r in cat)
        texts_b = set(r["text"] for cat in recs_b.values() for r in cat)

        # Ensure that the two profiles produce markedly distinct recommendation sets
        overlap = texts_a.intersection(texts_b)
        unique_a = texts_a - texts_b
        unique_b = texts_b - texts_a

        self.assertGreater(len(unique_a), 3, "Profile A should have multiple distinct recommendations")
        self.assertGreater(len(unique_b), 3, "Profile B should have multiple distinct recommendations")
        self.assertLess(len(overlap), len(texts_a), "Profiles should not have identical recommendation sets")

    def test_09_recalculate_endpoint_updates_recommendations_on_questionnaire_change(self):
        """Verify the /predict/fusion/recalculate endpoint dynamically updates recommendations."""
        mock_image = {
            "severity": 1,
            "severity_label": "Moderate",
            "oiliness": 60.0,
            "pores": 55.0,
            "redness": 40.0,
            "dark_spots": 30.0,
            "risk_percent": 45.0,
            "problem_areas": ["cheeks"],
            "current_skin_condition": "Moderate Inflammatory",
            "face_detected": True,
            "method": "mobilenetv2_acne04_improved",
        }

        # Step 1: Baseline regular questionnaire
        quest_1 = {
            "age": 25,
            "sleep_hours": 8.0,
            "stress_level": 3,
            "pollution_level": "low",
            "pcos": False,
        }
        resp1 = self.client.post("/predict/fusion/recalculate", json={"image": mock_image, "questionnaire": quest_1})
        self.assertEqual(resp1.status_code, 200)
        recs1 = resp1.json()["recommendations"]
        lifestyle1_texts = " ".join(r["text"] for r in recs1["Lifestyle Changes"])
        self.assertNotIn("sleep and wake routine", lifestyle1_texts)

        # Step 2: Questionnaire changes: sleep drops to 5h, stress jumps to 9, pollution jumps to high
        quest_2 = {
            "age": 25,
            "sleep_hours": 4.5,
            "stress_level": 9,
            "pollution_level": "high",
            "pcos": False,
        }
        resp2 = self.client.post("/predict/fusion/recalculate", json={"image": mock_image, "questionnaire": quest_2})
        self.assertEqual(resp2.status_code, 200)
        recs2 = resp2.json()["recommendations"]
        lifestyle2_texts = " ".join(r["text"] for r in recs2["Lifestyle Changes"])
        env2_texts = " ".join(r["text"].lower() for r in recs2["Environmental Protection"])

        # Recommendations MUST update to reflect the new questionnaire data
        self.assertIn("sleep and wake routine", lifestyle2_texts)
        self.assertIn("antioxidant serum", env2_texts)
        self.assertNotEqual(recs1, recs2)

    def test_10_arid_cold_vs_humid_tropical_climate_differentiation(self):
        """Verify climate/humidity differences produce texture and barrier differentiation."""
        mock_img = {"severity": 0, "severity_label": "Clear / Mild", "oiliness": 45.0, "risk_percent": 25.0}

        # Arid / low humidity
        arid_data = {
            "environmental_score": 40.0,
            "combined_score": 30.0,
            "drivers": [],
            "answers": {"humidity": "low", "climate": "dry_arid"},
        }
        recs_arid = generate_recommendations(mock_img, arid_data, final_risk=27.0)
        env_arid = " ".join(r["text"].lower() for r in recs_arid["Environmental Protection"])
        self.assertIn("humidifier", env_arid)

        # Tropical / high humidity
        tropical_data = {
            "environmental_score": 40.0,
            "combined_score": 30.0,
            "drivers": ["High humidity (follicular occlusion risk)"],
            "answers": {"humidity": "high", "climate": "tropical"},
        }
        recs_trop = generate_recommendations(mock_img, tropical_data, final_risk=27.0)
        env_trop = " ".join(r["text"].lower() for r in recs_trop["Environmental Protection"])
        self.assertIn("light gel or water-based fluid", env_trop)

    def test_11_post_inflammatory_hyperpigmentation_trigger(self):
        """Verify elevated dark spots trigger tyrosinase and post-inflammatory hyperpigmentation care."""
        mock_img_dark_spots = {
            "severity": 1,
            "severity_label": "Moderate",
            "dark_spots": 62.0,
            "oiliness": 50.0,
            "risk_percent": 38.0,
        }
        norm_data = {"hormonal_score": 30.0, "combined_score": 30.0, "drivers": [], "answers": {}}
        recs = generate_recommendations(mock_img_dark_spots, norm_data, final_risk=35.0)
        skincare_texts = " ".join(r["text"].lower() for r in recs["Skin Care Routine"])
        self.assertTrue("azelaic acid" in skincare_texts or "tranexamic acid" in skincare_texts)

    def test_12_exercise_post_sweat_cleansing_trigger(self):
        """Verify frequent exercise triggers 15-20 min post-workout rinse protocol."""
        mock_img = {"severity": 0, "severity_label": "Clear / Mild", "risk_percent": 15.0}
        active_data = {
            "lifestyle_score": 25.0,
            "combined_score": 22.0,
            "drivers": [],
            "answers": {"exercise_frequency": "5+_week"},
        }
        recs = generate_recommendations(mock_img, active_data, final_risk=18.0)
        lifestyle_texts = " ".join(r["text"].lower() for r in recs["Lifestyle Changes"])
        self.assertIn("15–20 minutes", lifestyle_texts)


if __name__ == "__main__":
    unittest.main()

