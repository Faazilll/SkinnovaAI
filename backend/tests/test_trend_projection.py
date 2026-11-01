import sys
import unittest
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR / "ml" / "image_model"))
sys.path.insert(0, str(BACKEND_DIR / "ml" / "data_model"))
sys.path.insert(0, str(BACKEND_DIR / "ml" / "fusion"))

from fusion_engine import compute_trend_projection, project_trend, fuse


class TestTrendProjection(unittest.TestCase):
    def setUp(self):
        self.image_clear = {
            "severity": 0,
            "severity_label": "Clear / Mild",
            "risk_percent": 18.0,
            "oiliness": 42.0,
            "pores": 35.0,
            "redness": 25.0,
            "dark_spots": 15.0,
            "problem_areas": ["Cheeks"],
            "face_detected": True,
            "method": "mobilenetv2_acne04_improved",
        }

        self.image_severe = {
            "severity": 2,
            "severity_label": "Severe",
            "risk_percent": 74.0,
            "oiliness": 78.0,
            "pores": 82.0,
            "redness": 71.0,
            "dark_spots": 65.0,
            "problem_areas": ["Cheeks", "Jawline"],
            "face_detected": True,
            "method": "mobilenetv2_acne04_improved",
        }

        self.data_healthy = {
            "hormonal_score": 25.0,
            "lifestyle_score": 28.0,
            "environmental_score": 26.0,
            "combined_score": 26.0,
            "drivers": [],
            "answers": {
                "skincare_consistency": "consistent",
                "sunscreen": "daily",
                "stress_level": 2,
                "sleep_hours": 8.0,
                "diet_quality": "optimal",
                "diet_sugar": "low",
                "smoking": False,
                "alcohol": "none",
                "pcos": False,
                "menstrual_cycle": "regular",
                "climate": "temperate",
                "pollution_level": "low",
            },
        }

        self.data_high_risk = {
            "hormonal_score": 78.0,
            "lifestyle_score": 75.0,
            "environmental_score": 68.0,
            "combined_score": 74.0,
            "drivers": ["High stress level (8/10)", "Irregular sleep patterns (<6 hrs)", "High glycemic diet"],
            "answers": {
                "skincare_consistency": "none",
                "sunscreen": "never",
                "stress_level": 9,
                "sleep_hours": 4.5,
                "diet_quality": "poor",
                "diet_sugar": "high",
                "diet_dairy": "high",
                "smoking": True,
                "alcohol": "heavy",
                "pcos": True,
                "menstrual_cycle": "irregular",
                "climate": "arid",
                "pollution_level": "high",
            },
        }

    def test_milestones_and_structure(self):
        """Verify 4 milestones (Now, 1m, 2m, 3m) are returned with correct fields."""
        points, analysis = compute_trend_projection(
            final_risk=50.0,
            data_combined=50.0,
            image=self.image_clear,
            data=self.data_healthy,
        )
        self.assertEqual(len(points), 4)
        expected_labels = ["Now", "Month 1", "Month 2", "Month 3"]
        for i, pt in enumerate(points):
            self.assertEqual(pt["label"], expected_labels[i])
            self.assertEqual(pt["month_offset"], i)
            self.assertIn("risk_percent", pt)
            self.assertIn("adherence_risk_percent", pt)
            self.assertIn("barrier_health", pt)
            self.assertIn("phase", pt)

        # Baseline point 0 must exactly equal final_risk
        self.assertEqual(points[0]["risk_percent"], 50.0)
        self.assertEqual(points[0]["adherence_risk_percent"], 50.0)

        # Analysis payload structure
        self.assertIn("baseline_risk", analysis)
        self.assertIn("month_3_risk", analysis)
        self.assertIn("net_3_month_delta", analysis)
        self.assertIn("monthly_velocity_pct", analysis)
        self.assertIn("trajectory_status", analysis)
        self.assertIn("trajectory_status_code", analysis)
        self.assertIn("primary_escalators", analysis)
        self.assertIn("primary_stabilizers", analysis)
        self.assertIn("methodology_summary", analysis)

    def test_clear_skin_and_healthy_lifestyle_improves(self):
        """Clear skin + disciplined lifestyle yields favorable downward trajectory."""
        final_risk = 0.55 * self.image_clear["risk_percent"] + 0.45 * self.data_healthy["combined_score"]
        points, analysis = compute_trend_projection(
            final_risk=final_risk,
            data_combined=self.data_healthy["combined_score"],
            image=self.image_clear,
            data=self.data_healthy,
        )
        self.assertEqual(analysis["trajectory_status_code"], "improving")
        self.assertLess(analysis["net_3_month_delta"], 0)
        self.assertLess(points[3]["risk_percent"], points[0]["risk_percent"])
        self.assertTrue(len(analysis["primary_stabilizers"]) >= 2)

    def test_severe_skin_and_adverse_lifestyle_escalates(self):
        """Severe acne + high stress/no SPF/smoking yields escalating risk trajectory."""
        final_risk = 0.55 * self.image_severe["risk_percent"] + 0.45 * self.data_high_risk["combined_score"]
        points, analysis = compute_trend_projection(
            final_risk=final_risk,
            data_combined=self.data_high_risk["combined_score"],
            image=self.image_severe,
            data=self.data_high_risk,
        )
        self.assertEqual(analysis["trajectory_status_code"], "escalating")
        self.assertGreater(analysis["net_3_month_delta"], 0)
        self.assertGreater(points[3]["risk_percent"], points[0]["risk_percent"])
        self.assertTrue(len(analysis["primary_escalators"]) >= 2)

    def test_meaningful_difference_between_profiles(self):
        """Verify the trend curves are NOT identical for different inputs."""
        res_healthy = fuse(self.image_clear, self.data_healthy)
        res_severe = fuse(self.image_severe, self.data_high_risk)

        trend_healthy = res_healthy["trend"]
        trend_severe = res_severe["trend"]

        # Month 3 risk should be drastically different
        self.assertNotEqual(trend_healthy[3]["risk_percent"], trend_severe[3]["risk_percent"])
        self.assertLess(trend_healthy[3]["risk_percent"], 20.0)
        self.assertGreater(trend_severe[3]["risk_percent"], 70.0)

        # Statuses should be distinct
        self.assertEqual(res_healthy["trend_analysis"]["trajectory_status_code"], "improving")
        self.assertEqual(res_severe["trend_analysis"]["trajectory_status_code"], "escalating")

    def test_questionnaire_change_updates_trend(self):
        """Verifies that changing a single questionnaire response (e.g. routine consistency) updates trend."""
        import copy
        data_inconsistent = copy.deepcopy(self.data_healthy)
        data_inconsistent["answers"]["skincare_consistency"] = "none"
        data_inconsistent["answers"]["sunscreen"] = "never"
        data_inconsistent["answers"]["stress_level"] = 9

        res_consistent = fuse(self.image_clear, self.data_healthy)
        res_neglected = fuse(self.image_clear, data_inconsistent)

        # The neglected routine should result in a higher Month 3 projected risk than consistent routine
        self.assertGreater(
            res_neglected["trend"][3]["risk_percent"],
            res_consistent["trend"][3]["risk_percent"],
        )
        self.assertGreater(
            res_neglected["trend_analysis"]["monthly_velocity_pct"],
            res_consistent["trend_analysis"]["monthly_velocity_pct"],
        )

    def test_project_trend_wrapper_compatibility(self):
        """Ensures project_trend wrapper returns 4 points list for backward compatibility."""
        points = project_trend(45.0, 48.0, image=self.image_clear, data=self.data_healthy)
        self.assertIsInstance(points, list)
        self.assertEqual(len(points), 4)
        self.assertEqual(points[0]["risk_percent"], 45.0)


if __name__ == "__main__":
    unittest.main()
