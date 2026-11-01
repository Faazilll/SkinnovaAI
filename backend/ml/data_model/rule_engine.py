"""
Skinova Data Model — clinically-informed weighted scoring engine.

Ground truth for optional ML wrapper is derived from these rules (with noise),
NOT from real patient outcomes. No public labeled dataset maps questionnaire
answers → acne risk percentages.

Key literature anchors (see reports/METHODOLOGY.md for full citations):
- PCOS / irregular cycles → androgen-driven sebum (Azziz et al.; Rosenfield)
- Sleep deprivation & high-GI diet → inflammatory acne (Chiu et al.; Smith et al.)
- Pollution / humidity → follicular occlusion & barrier stress (Krutmann et al.)
"""

from __future__ import annotations

from typing import Any


SEVERITY_LABELS = {
    0: "Clear / Mild",
    1: "Moderate",
    2: "Severe",
    3: "Very Severe",
}


def _clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, x))


def score_hormonal(answers: dict[str, Any]) -> float:
    """0–100 hormonal acne risk from endocrine-related questionnaire fields."""
    score = 18.0  # baseline population risk contribution

    age = int(answers.get("age", 25))
    if 15 <= age <= 25:
        score += 18
    elif 26 <= age <= 35:
        score += 12
    elif age > 35:
        score += 6
    else:
        score += 10

    gender = str(answers.get("gender", "female")).lower()
    cycle = str(answers.get("menstrual_cycle", "regular")).lower()
    if gender in ("female", "other"):
        if cycle in ("irregular", "absent"):
            score += 22  # androgen/cycle irregularity → sebum
        elif cycle == "somewhat_irregular":
            score += 12

    if _truthy(answers.get("pcos")):
        score += 28  # PCOS strongly linked to androgenic acne

    thyroid = str(answers.get("thyroid_status", "normal")).lower()
    if thyroid in ("hypo", "hyper", "hypothyroid", "hyperthyroid"):
        score += 10

    if _truthy(answers.get("pregnancy")):
        score += 8  # hormonal flux; can worsen or improve

    meds = str(answers.get("medications", "none")).lower()
    if meds in ("steroids", "lithium", "antiepileptics"):
        score += 15
    elif meds in ("contraceptives_androgenic",):
        score += 10
    elif meds in ("isotretinoin", "spironolactone", "contraceptives_antiandrogen"):
        score -= 12  # protective / therapeutic

    return _clamp(score)


def score_lifestyle(answers: dict[str, Any]) -> float:
    """0–100 lifestyle-driven inflammatory / sebum risk."""
    score = 15.0

    sleep = float(answers.get("sleep_hours", 7))
    if sleep < 5:
        score += 22
    elif sleep < 6.5:
        score += 14
    elif sleep < 7.5:
        score += 6
    else:
        score -= 4

    diet = str(answers.get("diet_quality", "average")).lower()
    diet_map = {
        "poor_high_gi": 22,
        "poor": 18,
        "average": 8,
        "good": -4,
        "excellent_low_gi": -10,
    }
    score += diet_map.get(diet, 8)

    water = float(answers.get("water_intake_liters", 2.0))
    if water < 1.5:
        score += 8
    elif water >= 2.5:
        score -= 3

    exercise = str(answers.get("exercise_frequency", "1-2_week")).lower()
    ex_map = {
        "none": 10,
        "1-2_week": 4,
        "3-4_week": -2,
        "5+_week": -5,
    }
    score += ex_map.get(exercise, 4)

    stress = int(answers.get("stress_level", 5))  # 1–10
    score += (stress - 3) * 3.5

    if _truthy(answers.get("smoking")):
        score += 12
    alcohol = str(answers.get("alcohol", "none")).lower()
    if alcohol in ("heavy", "frequent"):
        score += 10
    elif alcohol in ("moderate", "occasional"):
        score += 4

    skincare = str(answers.get("skincare_consistency", "inconsistent")).lower()
    sk_map = {
        "none": 14,
        "inconsistent": 8,
        "consistent_basic": -4,
        "consistent_targeted": -10,
    }
    score += sk_map.get(skincare, 8)

    return _clamp(score)


def score_environmental(answers: dict[str, Any]) -> float:
    """0–100 environmental / exposure risk (pollution, climate, UV)."""
    score = 12.0

    loc = str(answers.get("location_type", "suburban")).lower()
    loc_map = {"urban": 14, "suburban": 6, "rural": 2, "industrial": 18}
    score += loc_map.get(loc, 6)

    pollution = str(answers.get("pollution_level", "moderate")).lower()
    pol_map = {"low": 2, "moderate": 10, "high": 20, "very_high": 28}
    score += pol_map.get(pollution, 10)

    sun = str(answers.get("sun_exposure", "moderate")).lower()
    sun_map = {"low": 2, "moderate": 8, "high": 16, "very_high": 22}
    score += sun_map.get(sun, 8)

    humidity = str(answers.get("humidity", "moderate")).lower()
    hum_map = {"low": 4, "moderate": 6, "high": 14, "very_high": 18}
    score += hum_map.get(humidity, 6)

    climate = str(answers.get("climate", "temperate")).lower()
    clim_map = {
        "tropical": 12,
        "humid_subtropical": 10,
        "arid": 6,
        "temperate": 4,
        "cold": 3,
    }
    score += clim_map.get(climate, 4)

    outdoor = float(answers.get("outdoor_ratio", 0.3))  # 0–1
    score += outdoor * 10

    hvac = str(answers.get("ac_heating_exposure", "moderate")).lower()
    hvac_map = {"low": 1, "moderate": 4, "high": 9}
    score += hvac_map.get(hvac, 4)

    return _clamp(score)


def combined_score(
    hormonal: float, lifestyle: float, environmental: float
) -> float:
    """
    Weighted blend of category scores.
    Hormonal weighted highest (strongest acne etiology signal for many patients),
    then lifestyle, then environment.
    """
    return _clamp(0.40 * hormonal + 0.35 * lifestyle + 0.25 * environmental)


def predict(answers: dict[str, Any]) -> dict[str, Any]:
    h = score_hormonal(answers)
    l = score_lifestyle(answers)
    e = score_environmental(answers)
    c = combined_score(h, l, e)
    return {
        "hormonal_score": round(h, 1),
        "lifestyle_score": round(l, 1),
        "environmental_score": round(e, 1),
        "combined_score": round(c, 1),
        "drivers": _top_drivers(answers, h, l, e),
        "method": "clinically_informed_rule_engine",
    }


def _top_drivers(
    answers: dict[str, Any], h: float, l: float, e: float
) -> list[str]:
    drivers: list[str] = []
    if _truthy(answers.get("pcos")):
        drivers.append("PCOS / androgen excess")
    cycle = str(answers.get("menstrual_cycle", "regular")).lower()
    if cycle in ("irregular", "absent", "somewhat_irregular"):
        drivers.append("Menstrual cycle irregularity")
    if float(answers.get("sleep_hours", 7)) < 6.5:
        drivers.append("Insufficient sleep")
    if int(answers.get("stress_level", 5)) >= 7:
        drivers.append("Elevated stress")
    diet = str(answers.get("diet_quality", "average")).lower()
    if diet in ("poor", "poor_high_gi"):
        drivers.append("High-GI / poor diet quality")
    if str(answers.get("pollution_level", "moderate")).lower() in (
        "high",
        "very_high",
    ):
        drivers.append("High pollution exposure")
    if str(answers.get("humidity", "moderate")).lower() in ("high", "very_high"):
        drivers.append("High humidity (follicular occlusion risk)")
    if _truthy(answers.get("smoking")):
        drivers.append("Smoking")
    # sort by category magnitude contribution hint
    ranked = sorted(
        [("hormonal", h), ("lifestyle", l), ("environmental", e)],
        key=lambda x: x[1],
        reverse=True,
    )
    drivers.append(f"Dominant category: {ranked[0][0]}")
    return drivers[:6]


def _truthy(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    if v is None:
        return False
    return str(v).strip().lower() in ("1", "true", "yes", "y")


# Schema defaults used by API validation / frontend
QUESTIONNAIRE_DEFAULTS: dict[str, Any] = {
    "age": 25,
    "gender": "female",
    "menstrual_cycle": "regular",
    "pcos": False,
    "thyroid_status": "normal",
    "pregnancy": False,
    "medications": "none",
    "sleep_hours": 7.0,
    "diet_quality": "average",
    "water_intake_liters": 2.0,
    "exercise_frequency": "1-2_week",
    "stress_level": 5,
    "smoking": False,
    "alcohol": "none",
    "skincare_consistency": "inconsistent",
    "location_type": "suburban",
    "pollution_level": "moderate",
    "sun_exposure": "moderate",
    "humidity": "moderate",
    "climate": "temperate",
    "outdoor_ratio": 0.3,
    "ac_heating_exposure": "moderate",
}
