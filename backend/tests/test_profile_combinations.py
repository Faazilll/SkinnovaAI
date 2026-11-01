"""
Automated Verification Suite: Multi-Profile Image & Questionnaire Combinations.
Verifies that Skinova's recommendation system genuinely and dynamically alters
recommendations, rationales, and clinical pathways based on distinct user inputs.
"""

import json
import unittest
from pathlib import Path
import sys

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR / "ml" / "image_model"))
sys.path.insert(0, str(BACKEND_DIR / "ml" / "data_model"))
sys.path.insert(0, str(BACKEND_DIR / "ml" / "fusion"))

from fusion_engine import fuse
from predict_data import predict_data


class TestProfileCombinations(unittest.TestCase):
    def setUp(self):
        # 5 distinct visual image inferences
        self.img_clear = {
            "severity": 0,
            "severity_label": "Clear / Mild",
            "oiliness": 32.0,
            "pores": 28.0,
            "redness": 18.0,
            "dark_spots": 12.0,
            "risk_percent": 15.0,
            "current_skin_condition": "Clear / Mild Comedonal",
            "problem_areas": ["forehead"],
            "face_detected": True,
            "method": "mobilenetv2_acne04_improved",
        }

        self.img_oily_mod = {
            "severity": 1,
            "severity_label": "Moderate",
            "oiliness": 72.0,
            "pores": 68.0,
            "redness": 42.0,
            "dark_spots": 25.0,
            "risk_percent": 44.0,
            "current_skin_condition": "Moderate Inflammatory",
            "problem_areas": ["T-zone", "cheeks"],
            "face_detected": True,
            "method": "mobilenetv2_acne04_improved",
        }

        self.img_severe_pih = {
            "severity": 2,
            "severity_label": "Severe Papulopustular",
            "oiliness": 78.0,
            "pores": 74.0,
            "redness": 66.0,
            "dark_spots": 58.0,
            "risk_percent": 74.0,
            "current_skin_condition": "Severe Papulopustular with Dyschromia",
            "problem_areas": ["cheeks", "jawline"],
            "face_detected": True,
            "method": "mobilenetv2_acne04_improved",
        }

        self.img_pregnant_mod = {
            "severity": 1,
            "severity_label": "Moderate",
            "oiliness": 58.0,
            "pores": 52.0,
            "redness": 48.0,
            "dark_spots": 22.0,
            "risk_percent": 42.0,
            "current_skin_condition": "Moderate Hormonal Acne",
            "problem_areas": ["chin", "jawline"],
            "face_detected": True,
            "method": "mobilenetv2_acne04_improved",
        }

        self.img_dry_smoker = {
            "severity": 0,
            "severity_label": "Clear / Mild",
            "oiliness": 42.0,
            "pores": 45.0,
            "redness": 38.0,
            "dark_spots": 30.0,
            "risk_percent": 24.0,
            "current_skin_condition": "Mild Comedonal with Dehydration",
            "problem_areas": ["perioral", "cheeks"],
            "face_detected": True,
            "method": "mobilenetv2_acne04_improved",
        }

        # 5 distinct questionnaire profiles
        self.quest_baseline = {
            "age": 25,
            "gender": "female",
            "menstrual_cycle": "regular",
            "pcos": False,
            "thyroid_status": "normal",
            "pregnancy": False,
            "medications": "none",
            "sleep_hours": 8.5,
            "diet_quality": "good",
            "water_intake_liters": 2.5,
            "exercise_frequency": "3-4_week",
            "stress_level": 2,
            "smoking": False,
            "alcohol": "none",
            "skincare_consistency": "consistent",
            "location_type": "suburban",
            "pollution_level": "low",
            "sun_exposure": "low",
            "humidity": "moderate",
            "climate": "temperate",
            "outdoor_ratio": 0.2,
            "ac_heating_exposure": "low",
        }

        self.quest_urban_stress = {
            "age": 27,
            "gender": "female",
            "menstrual_cycle": "somewhat_irregular",
            "pcos": False,
            "thyroid_status": "normal",
            "pregnancy": False,
            "medications": "none",
            "sleep_hours": 5.0,
            "diet_quality": "poor",
            "water_intake_liters": 1.2,
            "exercise_frequency": "none",
            "stress_level": 9,
            "smoking": False,
            "alcohol": "moderate",
            "skincare_consistency": "inconsistent",
            "location_type": "urban",
            "pollution_level": "high",
            "sun_exposure": "moderate",
            "humidity": "high",
            "climate": "humid_subtropical",
            "outdoor_ratio": 0.35,
            "ac_heating_exposure": "moderate",
        }

        self.quest_pcos_severe = {
            "age": 24,
            "gender": "female",
            "menstrual_cycle": "irregular",
            "pcos": True,
            "thyroid_status": "hypo",
            "pregnancy": False,
            "medications": "spironolactone",
            "sleep_hours": 6.0,
            "diet_quality": "average",
            "water_intake_liters": 1.8,
            "exercise_frequency": "1-2_week",
            "stress_level": 7,
            "smoking": False,
            "alcohol": "occasional",
            "skincare_consistency": "inconsistent",
            "location_type": "urban",
            "pollution_level": "moderate",
            "sun_exposure": "moderate",
            "humidity": "moderate",
            "climate": "temperate",
            "outdoor_ratio": 0.3,
            "ac_heating_exposure": "moderate",
        }

        self.quest_pregnant = {
            "age": 29,
            "gender": "female",
            "menstrual_cycle": "not_applicable",
            "pcos": False,
            "thyroid_status": "normal",
            "pregnancy": True,
            "medications": "prenatal_vitamins",
            "sleep_hours": 7.0,
            "diet_quality": "good",
            "water_intake_liters": 2.2,
            "exercise_frequency": "1-2_week",
            "stress_level": 4,
            "smoking": False,
            "alcohol": "none",
            "skincare_consistency": "consistent",
            "location_type": "suburban",
            "pollution_level": "low",
            "sun_exposure": "moderate",
            "humidity": "moderate",
            "climate": "temperate",
            "outdoor_ratio": 0.25,
            "ac_heating_exposure": "low",
        }

        self.quest_arid_smoker = {
            "age": 34,
            "gender": "male",
            "menstrual_cycle": "not_applicable",
            "pcos": False,
            "thyroid_status": "normal",
            "pregnancy": False,
            "medications": "none",
            "sleep_hours": 6.5,
            "diet_quality": "average",
            "water_intake_liters": 2.0,
            "exercise_frequency": "5+_week",
            "stress_level": 5,
            "smoking": True,
            "alcohol": "moderate",
            "skincare_consistency": "inconsistent",
            "location_type": "industrial",
            "pollution_level": "moderate",
            "sun_exposure": "high",
            "humidity": "low",
            "climate": "dry_arid",
            "outdoor_ratio": 0.55,
            "ac_heating_exposure": "high",
        }

    def test_combination_1_baseline_optimal(self):
        """Test Combination 1: Clear skin with optimal lifestyle profile."""
        data_out = predict_data(self.quest_baseline)
        fusion_out = fuse(self.img_clear, data_out)
        recs = fusion_out["recommendations"]

        all_texts = " ".join(r["text"] for cat in recs.values() for r in cat)
        all_reasons = " ".join(r["reason"] for cat in recs.values() for r in cat)

        # Baseline optimal profile should NOT trigger urgent escalations or sleep restriction fixes
        self.assertNotIn("sleep and wake routine", all_texts)
        self.assertNotIn("board-certified dermatologist for prescription", all_texts)
        self.assertIn("restorative sleep window", all_texts)
        self.assertIn("Salicylic Acid", all_texts)
        self.assertIn("low-glycemic", all_texts)

    def test_combination_2_urban_stress_high_pollution(self):
        """Test Combination 2: Moderate acne with high stress, poor sleep, and high pollution."""
        data_out = predict_data(self.quest_urban_stress)
        fusion_out = fuse(self.img_oily_mod, data_out)
        recs = fusion_out["recommendations"]

        all_texts = " ".join(r["text"] for cat in recs.values() for r in cat)
        all_reasons = " ".join(r["reason"] for cat in recs.values() for r in cat)

        # Must trigger sleep restriction, stress decompression, pollution antioxidant serum, and double cleanse
        self.assertIn("sleep and wake routine", all_texts)
        self.assertIn("daily decompression periods", all_texts)
        self.assertIn("antioxidant serum", all_texts.lower())
        self.assertIn("double-cleanse", all_texts.lower())
        self.assertIn("adapalene", all_texts.lower())

    def test_combination_3_pcos_severe_grade2(self):
        """Test Combination 3: Severe Grade 2 acne with PCOS and thyroid dysfunction."""
        data_out = predict_data(self.quest_pcos_severe)
        fusion_out = fuse(self.img_severe_pih, data_out)
        recs = fusion_out["recommendations"]

        derm_texts = " ".join(r["text"] for r in recs["When to See a Dermatologist"])
        skincare_texts = " ".join(r["text"] for r in recs["Skin Care Routine"])
        diet_texts = " ".join(r["text"] for r in recs["Diet"])

        # Must trigger Grade 2 dermatologist evaluation AND PCOS endocrinologist referral
        self.assertIn("board-certified dermatologist for prescription", derm_texts)
        self.assertIn("endocrinologist", derm_texts)
        # Grade 2 inflammatory avoidance of physical scrubs
        self.assertIn("physical facial scrubs", skincare_texts)
        # PIH dark spots active (dark_spots = 58%)
        self.assertTrue("azelaic acid" in skincare_texts.lower() or "tranexamic" in skincare_texts.lower())
        # PCOS insulin sensitizing diet
        self.assertIn("insulin-sensitizing", diet_texts)

    def test_combination_4_pregnancy_safety(self):
        """Test Combination 4: Moderate acne with confirmed pregnancy."""
        data_out = predict_data(self.quest_pregnant)
        fusion_out = fuse(self.img_pregnant_mod, data_out)
        recs = fusion_out["recommendations"]

        skincare_texts = " ".join(r["text"] for r in recs["Skin Care Routine"])
        derm_texts = " ".join(r["text"] for r in recs["When to See a Dermatologist"])

        # Strictly contraindicate retinoids and offer azelaic acid
        self.assertNotIn("adapalene", skincare_texts.lower())
        self.assertIn("azelaic acid", skincare_texts.lower())
        self.assertIn("obstetrician", derm_texts.lower())

    def test_combination_5_arid_climate_smoker_athlete(self):
        """Test Combination 5: Arid climate, heavy exercise, high AC, active smoker."""
        data_out = predict_data(self.quest_arid_smoker)
        fusion_out = fuse(self.img_dry_smoker, data_out)
        recs = fusion_out["recommendations"]

        env_texts = " ".join(r["text"] for r in recs["Environmental Protection"])
        lifestyle_texts = " ".join(r["text"] for r in recs["Lifestyle Changes"])
        diet_texts = " ".join(r["text"] for r in recs["Diet"])

        # Humidifier and barrier protection for arid climate (<35% humidity)
        self.assertIn("humidifier", env_texts.lower())
        # Post-exercise rinse for 5+/week training
        self.assertIn("15–20 minutes", lifestyle_texts)
        # Smoking cessation and dietary vitamin C
        self.assertIn("smoking cessation", lifestyle_texts.lower())
        self.assertIn("vitamin c", diet_texts.lower())

    def test_all_combinations_have_high_uniqueness(self):
        """Verifies pairwise differences across all 5 combinations to prove no generic boilerplate."""
        pairs = [
            (self.img_clear, self.quest_baseline),
            (self.img_oily_mod, self.quest_urban_stress),
            (self.img_severe_pih, self.quest_pcos_severe),
            (self.img_pregnant_mod, self.quest_pregnant),
            (self.img_dry_smoker, self.quest_arid_smoker),
        ]

        results = []
        for img, quest in pairs:
            data = predict_data(quest)
            res = fuse(img, data)
            all_recs = set(r["text"] for cat in res["recommendations"].values() for r in cat)
            results.append(all_recs)

        # Test all pairwise intersections
        for i in range(len(results)):
            for j in range(i + 1, len(results)):
                set_i = results[i]
                set_j = results[j]
                diff_i = set_i - set_j
                diff_j = set_j - set_i
                self.assertGreater(
                    len(diff_i), 3,
                    f"Combination {i+1} must have at least 4 unique recommendations compared to Combination {j+1}"
                )
                self.assertGreater(
                    len(diff_j), 3,
                    f"Combination {j+1} must have at least 4 unique recommendations compared to Combination {i+1}"
                )


if __name__ == "__main__":
    unittest.main()
