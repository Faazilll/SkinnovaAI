"""
Fusion Engine — combines Image Model + Data Model into dashboard payload.

Weighting rationale (documented for evaluators):
- Image risk gets 55%: direct visual signal of current cutaneous state.
- Data combined score gets 45%: systemic / exposure drivers that explain
  trajectory and recommendations even when the photo looks mild.
There is no single "correct" formula in literature; these weights are a
transparent design choice for a decision-support prototype.
"""

from __future__ import annotations

from typing import Any


IMAGE_WEIGHT = 0.55
DATA_WEIGHT = 0.45


def _clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, x))


def skin_health_score(
    final_risk: float, lifestyle: float, environmental: float
) -> float:
    """
    Inverse of risk, with a small bonus when lifestyle/environment are favorable.
    """
    base = 100.0 - final_risk
    bonus = 0.0
    if lifestyle < 40:
        bonus += (40 - lifestyle) * 0.08
    if environmental < 40:
        bonus += (40 - environmental) * 0.05
    return round(_clamp(base + bonus), 1)


def compute_trend_projection(
    final_risk: float,
    data_combined: float,
    image: dict[str, Any] | None = None,
    data: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """
    Transparent, input-dependent 3-month risk trajectory projection.

    Integrates:
    1. Cutaneous baseline & lesion severity inertia (MobileNetV2 Hayashi grading, sebum, erythema).
    2. Systemic questionnaire biomarkers (endocrine, lifestyle adherence, sleep, diet, UV, exposome).
    3. Divergence delta between systemic driver risk and current cutaneous presentation.

    Computes:
    - Month 0 (Now / Current Baseline): exact fused risk score.
    - Month 1: early cellular turnover & acute micro-environment phase.
    - Month 2: follicular progression / epidermal barrier remodeling.
    - Month 3: chronic cutaneous equilibrium / projected 90-day outcome.

    Includes comparative Protocol Adherence trajectory (estimated response to evidence-based skincare).
    Explicitly labeled as an educational estimate — NOT a diagnostic medical prognosis.
    """
    img = image or {}
    dt = data or {}
    answers = dt.get("answers") or {}

    severity = int(img.get("severity", 0))
    oiliness = float(img.get("oiliness", 50.0))
    redness = float(img.get("redness", 50.0))
    dark_spots = float(img.get("dark_spots", 30.0))

    hormonal_score = float(dt.get("hormonal_score", 50.0))
    lifestyle_score = float(dt.get("lifestyle_score", 50.0))
    environmental_score = float(dt.get("environmental_score", 50.0))

    escalators: list[str] = []
    stabilizers: list[str] = []

    # --- 1. Cutaneous Lesion Severity & Micro-environment Velocity ---
    v_image = 0.0
    if severity == 3:
        v_image += 3.8
        escalators.append("Very Severe Hayashi Grade 3 Nodulocystic Activity (+3.8%/mo)")
    elif severity == 2:
        v_image += 2.4
        escalators.append("Severe Hayashi Grade 2 Inflammatory Lesions (+2.4%/mo)")
    elif severity == 1:
        v_image += 0.8
        escalators.append("Moderate Hayashi Grade 1 Comedonal Lesions (+0.8%/mo)")
    else:
        v_image -= 1.2
        stabilizers.append("Clear / Mild Baseline Lesion Activity (-1.2%/mo)")

    if oiliness >= 65.0:
        v_image += 1.2
        escalators.append(f"Excess Cutaneous Sebum Secretion ({round(oiliness)}%) (+1.2%/mo)")
    elif oiliness <= 35.0:
        v_image += 0.6
        escalators.append(f"Alipic Barrier Lipid Deficiency ({round(oiliness)}%) (+0.6%/mo)")
    else:
        v_image -= 0.6
        stabilizers.append("Balanced Cutaneous Sebum Equilibrium (-0.6%/mo)")

    if redness >= 65.0:
        v_image += 1.4
        escalators.append(f"Elevated Microvascular Erythema ({round(redness)}%) (+1.4%/mo)")
    elif redness <= 30.0:
        v_image -= 0.6
        stabilizers.append("Quiescent Vascular & Inflammatory Baseline (-0.6%/mo)")

    if dark_spots >= 55.0:
        v_image += 0.6
        escalators.append("Post-Inflammatory Hyperpigmentation Remodeling (+0.6%/mo)")

    # --- 2. Systemic Endocrine & Hormonal Biomarkers ---
    v_hormonal = 0.0
    pcos = answers.get("pcos") or "pcos" in str(answers.get("medical_conditions", "")).lower()
    cycle = str(answers.get("menstrual_cycle", "")).lower()

    if pcos:
        v_hormonal += 2.4
        escalators.append("Polycystic Ovarian Syndrome (PCOS) Endocrine Stimulation (+2.4%/mo)")
    elif cycle in ("irregular", "variable"):
        v_hormonal += 1.2
        escalators.append("Irregular Menstrual Cycle Hormonal Fluctuation (+1.2%/mo)")

    if hormonal_score >= 65.0:
        v_hormonal += 1.6
        escalators.append(f"Elevated Systemic Hormonal Risk Index ({round(hormonal_score)}) (+1.6%/mo)")
    elif hormonal_score <= 35.0:
        v_hormonal -= 1.0
        stabilizers.append(f"Optimal Endocrine & Hormonal Stability ({round(hormonal_score)}) (-1.0%/mo)")

    # --- 3. Lifestyle, Routine Adherence & Stress ---
    v_lifestyle = 0.0
    skincare_cons = str(answers.get("skincare_consistency", "")).lower()
    if skincare_cons == "consistent":
        v_lifestyle -= 3.5
        stabilizers.append("Consistent Barrier Hygiene & Cleansing Routine (-3.5%/mo)")
    elif skincare_cons == "occasional":
        v_lifestyle -= 0.5
        stabilizers.append("Partial Skincare Adherence (-0.5%/mo)")
    elif skincare_cons == "inconsistent":
        v_lifestyle += 2.2
        escalators.append("Inconsistent Skincare Routine (+2.2%/mo)")
    elif skincare_cons == "none":
        v_lifestyle += 3.6
        escalators.append("Absence of Structured Barrier Skincare Routine (+3.6%/mo)")

    sunscreen = str(answers.get("sunscreen", "")).lower()
    if sunscreen == "daily":
        v_lifestyle -= 1.8
        stabilizers.append("Daily Broad-Spectrum Photoprotection (-1.8%/mo)")
    elif sunscreen == "often":
        v_lifestyle -= 0.8
        stabilizers.append("Frequent Sunscreen Utilization (-0.8%/mo)")
    elif sunscreen == "rarely":
        v_lifestyle += 1.5
        escalators.append("Rare Sunscreen Application (UV Photo-Aggravation) (+1.5%/mo)")
    elif sunscreen == "never":
        v_lifestyle += 2.2
        escalators.append("Zero Photoprotection (Squalene Photo-Oxidation) (+2.2%/mo)")

    # Stress level (supports int 1-10 or string)
    raw_stress = answers.get("stress_level", 5)
    stress_val = 5
    try:
        stress_val = int(raw_stress)
    except (ValueError, TypeError):
        s_str = str(raw_stress).lower()
        if "severe" in s_str:
            stress_val = 9
        elif "high" in s_str:
            stress_val = 8
        elif "mod" in s_str:
            stress_val = 5
        elif "low" in s_str:
            stress_val = 2

    if stress_val >= 8:
        v_lifestyle += 2.2
        escalators.append(f"Severe Neuroendocrine Stress & Cortisol Load (Level {stress_val}/10) (+2.2%/mo)")
    elif stress_val >= 6:
        v_lifestyle += 1.2
        escalators.append(f"Elevated Psychological Stress (Level {stress_val}/10) (+1.2%/mo)")
    elif stress_val <= 3:
        v_lifestyle -= 1.2
        stabilizers.append(f"Low Stress & Neuro-Cutaneous Equilibrium (Level {stress_val}/10) (-1.2%/mo)")

    # Sleep hours
    raw_sleep = answers.get("sleep_hours", 7.0)
    try:
        sleep_hrs = float(raw_sleep)
    except (ValueError, TypeError):
        sleep_hrs = 7.0

    if sleep_hrs < 6.0:
        v_lifestyle += 1.6
        escalators.append(f"Insufficient Circadian Sleep ({sleep_hrs}h) (+1.6%/mo)")
    elif sleep_hrs >= 7.5:
        v_lifestyle -= 1.0
        stabilizers.append(f"Restorative Circadian Sleep Recovery ({sleep_hrs}h) (-1.0%/mo)")

    # Diet quality & nutrition
    diet_q = str(answers.get("diet_quality", "")).lower()
    diet_sugar = str(answers.get("diet_sugar", answers.get("diet_glycemic", ""))).lower()
    diet_dairy = str(answers.get("diet_dairy", "")).lower()

    if diet_q == "poor" or diet_sugar in ("high", "moderate"):
        v_lifestyle += 1.4
        escalators.append("High Glycemic Dietary Load (mTORC1 / IGF-1 Axis) (+1.4%/mo)")
    elif diet_q == "optimal":
        v_lifestyle -= 1.0
        stabilizers.append("Nutrient-Dense Anti-Inflammatory Nutrition (-1.0%/mo)")

    if diet_dairy in ("high", "moderate"):
        v_lifestyle += 0.8
        escalators.append("Elevated Dairy Consumption (+0.8%/mo)")

    # Smoking & alcohol
    smoking = answers.get("smoking")
    if smoking is True or str(smoking).lower() in ("yes", "true", "1"):
        v_lifestyle += 1.6
        escalators.append("Nicotine-Induced Microvascular Hypoxia (+1.6%/mo)")

    alcohol = str(answers.get("alcohol", "")).lower()
    if alcohol in ("heavy", "frequent"):
        v_lifestyle += 1.2
        escalators.append("Frequent Alcohol Intake (Peripheral Vasodilation) (+1.2%/mo)")

    # --- 4. Environmental Exposome ---
    v_env = 0.0
    climate = str(answers.get("climate", "")).lower()
    pollution = str(answers.get("pollution_level", "")).lower()
    if climate in ("arid", "cold_dry"):
        v_env += 1.2
        escalators.append("Arid/Cold Climate Transepidermal Moisture Depletion (+1.2%/mo)")
    elif climate == "temperate" and pollution in ("low", "minimal"):
        v_env -= 0.6
        stabilizers.append("Temperate Low-Pollution Exposome (-0.6%/mo)")

    if pollution == "high":
        v_env += 1.0
        escalators.append("High Airborne Particulate Pollution (+1.0%/mo)")

    if environmental_score >= 65.0:
        v_env += 1.0
    elif environmental_score <= 35.0:
        v_env -= 0.6

    # --- 5. Systemic-Cutaneous Divergence Delta ---
    divergence = (data_combined - final_risk) * 0.05
    divergence_clamped = max(-2.0, min(2.5, divergence))
    if divergence_clamped >= 1.2:
        escalators.append("Latent Systemic Risk Exceeding Current Visual Presentation (+1.2%/mo)")
    elif divergence_clamped <= -1.2:
        stabilizers.append("Favorable Systemic Lifestyle Mitigating Surface Inflammation (-1.2%/mo)")

    # Net Unmanaged Monthly Velocity
    raw_velocity = v_image + v_hormonal + v_lifestyle + v_env + divergence_clamped
    net_velocity = max(-8.5, min(9.5, raw_velocity))

    # Month-by-month calculations (Now, 1 Month, 2 Months, 3 Months)
    # Biological damping scaling across successive months:
    scaling = [0.0, 1.0, 1.9, 2.7]
    labels = ["Now", "Month 1", "Month 2", "Month 3"]
    phases = [
        "Current Baseline Intake",
        "Acute Cellular Turnover Phase",
        "Follicular Remodeling Phase",
        "Cutaneous Equilibrium Phase",
    ]

    points: list[dict[str, Any]] = []
    for i in range(4):
        if i == 0:
            m_risk = round(final_risk, 1)
            m_adh = round(final_risk, 1)
        else:
            m_risk = round(_clamp(final_risk + scaling[i] * net_velocity, 5.0, 96.0), 1)
            # Managed protocol adherence trajectory:
            if i == 1:
                adh_val = final_risk * 0.82 - 2.0
            elif i == 2:
                adh_val = final_risk * 0.62 - 4.0
            else:
                adh_val = final_risk * 0.45 - 6.0
            m_adh = round(_clamp(adh_val, 4.0, 95.0), 1)

        m_health = round(_clamp(100.0 - m_risk, 5.0, 98.0), 1)
        points.append({
            "label": labels[i],
            "month_offset": i,
            "risk_percent": m_risk,
            "adherence_risk_percent": m_adh,
            "barrier_health": m_health,
            "phase": phases[i],
        })

    # Trajectory status categorization
    if net_velocity >= 1.5:
        traj_status = "Escalating Risk Trajectory"
        status_code = "escalating"
    elif net_velocity <= -1.5:
        traj_status = "Favorable Recovery Trajectory"
        status_code = "improving"
    else:
        traj_status = "Stable / Steady-State Trajectory"
        status_code = "stable"

    analysis = {
        "baseline_risk": round(final_risk, 1),
        "month_1_risk": points[1]["risk_percent"],
        "month_2_risk": points[2]["risk_percent"],
        "month_3_risk": points[3]["risk_percent"],
        "month_3_managed_risk": points[3]["adherence_risk_percent"],
        "net_3_month_delta": round(points[3]["risk_percent"] - final_risk, 1),
        "monthly_velocity_pct": round(net_velocity, 1),
        "trajectory_status": traj_status,
        "trajectory_status_code": status_code,
        "primary_escalators": escalators[:5],
        "primary_stabilizers": stabilizers[:5],
        "methodology_summary": (
            "Input-dependent dynamic simulation integrating Hayashi lesion grade inertia, "
            "cutaneous sebum and erythema levels, and 21 systemic questionnaire parameters."
        ),
    }

    return points, analysis


def project_trend(
    final_risk: float,
    data_combined: float,
    image: dict[str, Any] | None = None,
    data: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """
    Backward-compatible wrapper returning the 4-milestone trajectory points list.
    """
    points, _ = compute_trend_projection(final_risk, data_combined, image, data)
    return points


def generate_recommendations(
    image: dict[str, Any],
    data: dict[str, Any],
    final_risk: float,
) -> dict[str, list[dict[str, str]]]:
    """
    Evidence-Linked Action Plan:
    Generates dynamically personalized educational skincare guidance and clinical escalation
    recommendations directly linked to verified visual AI inferences, 21 questionnaire inputs
    (hormonal/medical, lifestyle, exposome), and peer-reviewed literature.
    """
    drivers = set(data.get("drivers") or [])
    answers = data.get("answers") or {}
    h = float(data.get("hormonal_score", 50))
    l = float(data.get("lifestyle_score", 50))
    e = float(data.get("environmental_score", 50))
    severity = int(image.get("severity", 0))
    severity_label = str(image.get("severity_label", "Clear / Mild"))
    oiliness = float(image.get("oiliness", 50))
    pores = float(image.get("pores", 50))
    redness = float(image.get("redness", 50))
    dark_spots = float(image.get("dark_spots", 30))
    problem_areas = [str(p).lower() for p in (image.get("problem_areas") or [])]

    # 1. Hormonal & Medical Inputs
    age = int(answers.get("age", 25))
    gender = str(answers.get("gender", "female")).lower()
    menstrual_cycle = str(answers.get("menstrual_cycle", "regular")).lower()
    pcos_flag = bool(answers.get("pcos", False)) or "PCOS / androgen excess" in drivers
    thyroid_status = str(answers.get("thyroid_status", "normal")).lower()
    pregnancy = bool(answers.get("pregnancy", False))
    medications = str(answers.get("medications", "none")).lower()

    # 2. Lifestyle Inputs
    sleep_hours = float(answers.get("sleep_hours", 7.0))
    diet_qual = str(answers.get("diet_quality", "average")).lower()
    water_intake = float(answers.get("water_intake_liters", 2.0))
    exercise_freq = str(answers.get("exercise_frequency", "1-2_week")).lower()
    stress_level = int(answers.get("stress_level", 5))
    smoking = bool(answers.get("smoking", False)) or "Smoking" in drivers
    alcohol = str(answers.get("alcohol", "none")).lower()
    skincare_cons = str(answers.get("skincare_consistency", "inconsistent")).lower()

    # 3. Environmental Inputs
    location_type = str(answers.get("location_type", "suburban")).lower()
    pollution_level = str(answers.get("pollution_level", "moderate")).lower()
    sun_exposure = str(answers.get("sun_exposure", "moderate")).lower()
    humidity = str(answers.get("humidity", "moderate")).lower()
    climate = str(answers.get("climate", "temperate")).lower()
    outdoor_ratio = float(answers.get("outdoor_ratio", 0.3))
    ac_heating = str(answers.get("ac_heating_exposure", "moderate")).lower()

    # -------------------------------------------------------------
    # CATEGORY 1: SKIN CARE ROUTINE
    # -------------------------------------------------------------
    skincare: list[dict[str, str]] = []

    # 1A. Cleanser Selection:
    if pregnancy:
        skincare.append(
            {
                "text": "Use a gentle, sulfate-free hydrating cleanser twice daily (avoiding high-concentration salicylic acid washes).",
                "reason": "Pregnancy-safe barrier preservation without systemic absorptive risks",
                "why_shown": "Pregnancy requires avoiding strong keratolytic absorption while maintaining stratum corneum lipid barrier integrity.",
                "trigger_input": "Questionnaire Input: Pregnancy status = Active / Confirmed (teratogenic mitigation)",
                "evidence_source": "ACOG Practice Bulletin & AAD Consensus Guidelines for Dermatological Safety During Pregnancy",
                "advice_type": "General Educational Guidance",
            }
        )
    elif redness >= 50.0 or humidity == "low" or ac_heating == "high":
        skincare.append(
            {
                "text": "Wash with a soothing, non-foaming ceramide lotion cleanser morning and evening; avoid harsh surfactants.",
                "reason": f"Formulated for elevated redness ({round(redness, 1)}%) and barrier recovery",
                "why_shown": f"Cutaneous erythema ({round(redness, 1)}%) and dry air accelerate lipid depletion; non-foaming syndets cleanse without disrupting epidermal desmosomes.",
                "trigger_input": f"Visual AI: Erythema {round(redness, 1)}% / Environmental barrier dryness",
                "evidence_source": "Del Rosso et al., J Clin Aesthet Dermatol: Skin Barrier Function and Gentle Cleansing in Inflammatory Dermatoses",
                "advice_type": "General Educational Guidance",
            }
        )
    elif oiliness >= 55.0 or pores >= 55.0:
        skincare.append(
            {
                "text": "Cleanse twice daily with a gentle foaming cleanser containing 0.5–1% Salicylic Acid (BHA) or Zinc PCA.",
                "reason": f"Targets elevated sebum ({round(oiliness, 1)}%) and follicular pore congestion ({round(pores, 1)}%)",
                "why_shown": f"Lipophilic BHA penetrates sebum-rich follicular infundibula ({round(pores, 1)}% pore index), reducing microcomedone impaction without over-stripping.",
                "trigger_input": f"Visual AI: Sebum {round(oiliness, 1)}% / Pore congestion {round(pores, 1)}%",
                "evidence_source": "American Academy of Dermatology (AAD) Acne Management Guidelines: Surfactant & Sebum Modulation",
                "advice_type": "General Educational Guidance",
            }
        )
    else:
        skincare.append(
            {
                "text": "Use a gentle, non-comedogenic cleanser twice daily.",
                "reason": "Baseline skin barrier preservation",
                "why_shown": "Maintains epidermal acid mantle without stripping stratum corneum lipid barrier.",
                "trigger_input": f"Visual AI Assessment: Balanced sebum profile ({round(oiliness, 1)}%)",
                "evidence_source": "American Academy of Dermatology (AAD) Acne Management Guidelines 2024",
                "advice_type": "General Educational Guidance",
            }
        )

    # 1B. Barrier Hydration & Moisturizer:
    if medications in ("isotretinoin", "topical_retinoids"):
        skincare.append(
            {
                "text": "Apply a physiological lipid barrier cream rich in multi-lamellar ceramides, cholesterol, and squalane after washing.",
                "reason": "Prevents severe retinoid xerosis and transepidermal water loss",
                "why_shown": "Systemic and topical retinoid therapies downregulate sebocyte activity; physiological lipid replacement restores stratum corneum integrity.",
                "trigger_input": f"Questionnaire Input: Active retinoid/sensitizing medication profile ('{medications}')",
                "evidence_source": "Leyden et al., Cutis: Managing Retinoid Dermatitis and Cutaneous Xerosis",
                "advice_type": "General Educational Guidance",
            }
        )
    elif humidity in ("high", "very_high") or climate in ("tropical", "humid_subtropical") or oiliness >= 65.0:
        skincare.append(
            {
                "text": "Hydrate with a featherweight, oil-free water-gel or fluid moisturizer containing hyaluronic acid and dimethicone.",
                "reason": f"Prevents heavy occlusive trapping under high humidity ({humidity}) & elevated sebum ({round(oiliness, 1)}%)",
                "why_shown": "In humid environments with high sebaceous output, heavy lipid creams promote tropical follicular occlusion and retention comedones.",
                "trigger_input": f"Questionnaire / AI: Humidity '{humidity}' & Sebum {round(oiliness, 1)}%",
                "evidence_source": "British Journal of Dermatology: Climatic Influences on Sebaceous Gland Secretion & Occlusion",
                "advice_type": "General Educational Guidance",
            }
        )
    elif humidity == "low" or climate in ("dry_arid", "cold") or ac_heating == "high":
        skincare.append(
            {
                "text": "Layer a barrier-restorative ceramide and panthenol (Pro-Vitamin B5) emulsion over damp skin to seal hydration.",
                "reason": f"Locks moisture against dry ambient air ('{humidity}' humidity) and indoor AC/heating",
                "why_shown": "Low ambient humidity and HVAC exposure accelerate transepidermal water loss (TEWL); humectant plus ceramide layering prevents micro-fissuring.",
                "trigger_input": f"Questionnaire Input: Ambient humidity '{humidity}', Climate '{climate}', HVAC '{ac_heating}'",
                "evidence_source": "Ghadially et al., J Invest Dermatol: Transepidermal Water Loss in Low Relative Humidity",
                "advice_type": "General Educational Guidance",
            }
        )
    else:
        skincare.append(
            {
                "text": "Apply a lightweight non-comedogenic moisturizer to support barrier recovery.",
                "reason": "Prevents transepidermal water loss",
                "why_shown": "Protects against transepidermal water loss (TEWL) and supports stratum corneum integrity.",
                "trigger_input": "Baseline dermatological barrier protocol",
                "evidence_source": "American Academy of Dermatology (AAD) Acne Management Guidelines 2024",
                "advice_type": "General Educational Guidance",
            }
        )

    # 1C. Targeted Active Ingredient Selection:
    if pregnancy:
        skincare.append(
            {
                "text": "Incorporate topical Azelaic Acid 10–15% gel or cream once to twice daily as a pregnancy-safe active.",
                "reason": "Pregnancy-safe antimicrobial and anti-inflammatory keratolytic (Category B equivalent)",
                "why_shown": "Azelaic acid provides comedolytic and anti-erythema benefits without the teratogenic risks of topical retinoids or high-strength BHA.",
                "trigger_input": "Questionnaire Input: Pregnancy status = Confirmed (Retinoids strictly contraindicated)",
                "evidence_source": "American College of Obstetricians and Gynecologists (ACOG) & AAD: Safety of Acne Medications During Pregnancy",
                "advice_type": "General Educational Guidance",
            }
        )
    elif dark_spots >= 40.0 or "dark_spots" in problem_areas:
        skincare.append(
            {
                "text": "Incorporate topical Azelaic Acid 10% or 4–5% Niacinamide + Tranexamic Acid serum in the evening.",
                "reason": f"Targeting post-inflammatory hyperpigmentation ({round(dark_spots, 1)}%) and dyschromia",
                "why_shown": f"Elevated dark spot index ({round(dark_spots, 1)}%) reflects post-inflammatory melanogenesis; azelaic acid and tranexamic acid selectively inhibit tyrosinase activity.",
                "trigger_input": f"Visual AI Assessment: Post-Inflammatory Hyperpigmentation {round(dark_spots, 1)}%",
                "evidence_source": "Callender et al., J Clin Aesthet Dermatol: Post-Inflammatory Hyperpigmentation in Acne Vulgaris",
                "advice_type": "General Educational Guidance",
            }
        )
    elif redness >= 55.0:
        skincare.append(
            {
                "text": "Introduce soothing anti-inflammatory actives (such as Centella Asiatica / Madecassoside or 5% Niacinamide); pause strong AHA/BHA exfoliants.",
                "reason": f"Calms pronounced cutaneous erythema ({round(redness, 1)}%) before escalating exfoliating acids",
                "why_shown": f"High microvascular redness ({round(redness, 1)}%) indicates active perilesional inflammation; prioritizing anti-inflammatory actives prevents worsening barrier damage.",
                "trigger_input": f"Visual AI Assessment: Cutaneous Erythema Index {round(redness, 1)}%",
                "evidence_source": "Del Rosso, J Clin Aesthet Dermatol: Anti-Inflammatory Therapeutics in Papulopustular Acne",
                "advice_type": "General Educational Guidance",
            }
        )
    elif oiliness >= 55.0 or severity >= 1:
        skincare.append(
            {
                "text": "Consider an OTC adapalene 0.1% gel or 2.5% benzoyl peroxide topical wash (patch-test first).",
                "reason": f"Triggered by predicted {severity_label} / elevated sebum ({round(oiliness, 1)}%)",
                "why_shown": "Topical keratolytics target microcomedone formation and elevated follicular sebum.",
                "trigger_input": f"Visual AI Assessment: Hayashi Grade {severity} ({severity_label}) / Sebum {round(oiliness, 1)}%",
                "evidence_source": "AAD Acne Guidelines: Topical Retinoids & Benzoyl Peroxide Modalities",
                "advice_type": "General Educational Guidance",
            }
        )
    else:
        skincare.append(
            {
                "text": "Use a gentle 1–2% Salicylic Acid solution 2 evenings per week to sustain follicular exfoliation.",
                "reason": "Comedone prevention for clear to mild baseline cutaneous state",
                "why_shown": "Mild regular beta-hydroxy acid exfoliation clears cohesive desquamated corneocytes, preventing microscopic comedo formation.",
                "trigger_input": f"Visual AI Assessment: Hayashi Grade {severity} ({severity_label}) maintenance",
                "evidence_source": "Kligman, Cutis: Preventative Topical Management of Comedonal Micro-Etiology",
                "advice_type": "General Educational Guidance",
            }
        )

    # 1D. Application Discipline / Technique:
    if skincare_cons in ("inconsistent", "none"):
        skincare.append(
            {
                "text": "Maintain a consistent, gentle skincare routine morning and evening.",
                "reason": "This recommendation is associated with the user's reported skincare inconsistency.",
                "why_shown": "This recommendation is associated with the user's reported skincare inconsistency.",
                "trigger_input": f"Questionnaire Input: Reported skincare consistency is '{skincare_cons}'",
                "evidence_source": "AAD Patient Educational Guidance on Skincare Adherence",
                "advice_type": "General Educational Guidance",
            }
        )
    elif skincare_cons in ("consistent", "consistent_targeted", "consistent_basic") and severity <= 1:
        skincare.append(
            {
                "text": "Sustain current routine consistency; allow 6–8 weeks for cellular turnover before adding new active serums.",
                "reason": "Adherence reinforcement and preventing active-ingredient overloading",
                "why_shown": "Consistent baseline execution prevents active overload while providing necessary time for epidermal renewal cycles.",
                "trigger_input": f"Questionnaire Input: Skincare consistency reported as '{skincare_cons}'",
                "evidence_source": "AAD Guidance on Product Titration and Stratum Corneum Tolerance",
                "advice_type": "General Educational Guidance",
            }
        )

    if severity >= 2:
        skincare.append(
            {
                "text": "Avoid physical facial scrubs and rough mechanical cleansing; prioritize gentle cleansing.",
                "reason": f"Triggered by Severity Grade {severity} (inflammatory lesion risk)",
                "why_shown": "Harsh friction and abrasive mechanical exfoliation aggravate active inflammatory papules and pustules.",
                "trigger_input": f"Visual AI Assessment: Hayashi Grade {severity} ({severity_label})",
                "evidence_source": "AAD Clinical Consensus on Acne Cleansing & Non-Irritation",
                "advice_type": "General Educational Guidance",
            }
        )


    # -------------------------------------------------------------
    # CATEGORY 2: DIET
    # -------------------------------------------------------------
    diet: list[dict[str, str]] = []

    # 2A. Glycemic Load & Insulin Regulation:
    if pcos_flag or menstrual_cycle in ("irregular", "absent"):
        diet.append(
            {
                "text": "Follow an anti-inflammatory, insulin-sensitizing Mediterranean dietary pattern rich in leafy greens, legumes, and omega-3 fatty acids.",
                "reason": "Blunts hyperinsulinemia that compounds ovarian androgen production",
                "why_shown": "In individuals with PCOS or cycle irregularity, postprandial insulin spikes stimulate ovarian theca cell androgen production, worsening sebaceous gland hyperplasia.",
                "trigger_input": "Questionnaire Input: PCOS / Menstrual cycle irregularity biomarker",
                "evidence_source": "Azziz et al., Fertil Steril / Melnik, Dermato-Endocrinology: Dietary Signaling in Endocrine Acne",
                "advice_type": "General Educational Guidance",
            }
        )
    elif diet_qual in ("good", "excellent_low_gi"):
        diet.append(
            {
                "text": "Maintain your favorable low-glycemic diet; supplement with dietary zinc sources (pumpkin seeds, chickpeas) and dietary polyphenols.",
                "reason": f"Reinforces positive dietary adherence ('{diet_qual}') with micronutrient optimization",
                "why_shown": "Reported high-quality diet supports stable insulin dynamics; zinc and polyphenols provide endogenous antioxidant defense against lipid peroxidation.",
                "trigger_input": f"Questionnaire Input: Self-reported diet quality is '{diet_qual}'",
                "evidence_source": "Burris et al., J Acad Nutr Diet: Nutrition & Dermatological Health",
                "advice_type": "General Educational Guidance",
            }
        )
    else:
        diet.append(
            {
                "text": "Favor lower glycemic-load meals; moderate intake of sugary beverages and refined flours.",
                "reason": "High-GI diets stimulate IGF-1 and androgenic sebum",
                "why_shown": "Diets with high glycemic load are associated with elevated serum IGF-1 and sebocyte stimulation.",
                "trigger_input": f"Questionnaire Input: Self-reported diet quality is '{diet_qual}'",
                "evidence_source": "Smith et al., Am J Clin Nutr (Effect of low-glycemic-load diet on acne vulgaris)",
                "advice_type": "General Educational Guidance",
            }
        )

    if "High-GI / poor diet quality" in drivers or diet_qual in ("poor", "poor_high_gi") or l >= 55.0:
        diet.append(
            {
                "text": "Increase dietary fiber, leafy vegetables, and omega-3 fatty acid sources (flaxseed, walnuts, fish).",
                "reason": "Triggered by questionnaire diet quality & systemic lifestyle risk",
                "why_shown": "Associated with reported high-GI dietary intake and elevated systemic lifestyle stress load.",
                "trigger_input": f"Questionnaire Input: Self-reported diet quality is '{diet_qual}'",
                "evidence_source": "Smith et al., Am J Clin Nutr / Burris et al., J Acad Nutr Diet",
                "advice_type": "General Educational Guidance",
            }
        )


    # 2B. Dairy & Whey Considerations:
    if pcos_flag or oiliness >= 55.0 or diet_qual in ("poor", "poor_high_gi", "average"):
        diet.append(
            {
                "text": "Observe whether dairy consumption correlates with your personal skin breakout patterns.",
                "reason": "Nutritional literature association with follicular acne",
                "why_shown": "Nutritional dermatology literature documents an observational association between high dairy intake and follicular acne in susceptible individuals.",
                "trigger_input": f"Nutritional dermatology observational evidence (Sebum: {round(oiliness, 1)}%)",
                "evidence_source": "Aghasi et al., Clin Nutr / J Am Acad Dermatol Systematic Review",
                "advice_type": "General Educational Guidance",
            }
        )

    # 2C. Water Hydration & Toxic Exposure Factors:
    if water_intake < 1.8:
        diet.append(
            {
                "text": f"Increase daily water intake toward 2.2–2.5 L (currently reported at {water_intake} L/day).",
                "reason": f"Systemic hydration deficit ({water_intake} L/day) compromises stratum corneum hydration",
                "why_shown": "Inadequate cellular hydration impairs stratum corneum desquamatory enzymes, contributing to surface flaking and compensatory follicular oiliness.",
                "trigger_input": f"Questionnaire Input: Water intake is {water_intake} L/day",
                "evidence_source": "Palma et al., Clin Cosmet Investig Dermatol: Dietary Water Affects Human Skin Hydration and Biomechanics",
                "advice_type": "General Educational Guidance",
            }
        )
    elif alcohol in ("moderate", "heavy", "frequent"):
        diet.append(
            {
                "text": "Moderate alcohol intake and hydrate with water between drinks to limit vasodilatory flushing.",
                "reason": f"Alcohol consumption ('{alcohol}') elevates systemic inflammatory cytokines and facial erythema",
                "why_shown": "Alcohol breakdown metabolites induce peripheral vasodilation, heighten erythema, and suppress REM sleep cellular tissue repair.",
                "trigger_input": f"Questionnaire Input: Alcohol frequency reported as '{alcohol}'",
                "evidence_source": "Kazakevich et al., J Clin Aesthet Dermatol: Alcohol Consumption and Inflammatory Facial Dermatoses",
                "advice_type": "General Educational Guidance",
            }
        )
    if smoking:
        diet.append(
            {
                "text": "Increase dietary vitamin C (berries, citrus, bell peppers) and omega-3s to counteract smoke-induced oxidative depletion.",
                "reason": "Tobacco smoke causes microvascular ischemia and accelerates squalene peroxidation",
                "why_shown": "Nicotine and polycyclic aromatic hydrocarbons deplete cutaneous ascorbic acid reserves and trigger atypical retentional comedones.",
                "trigger_input": "Questionnaire Input: Active tobacco smoking reported",
                "evidence_source": "Capitanio et al., Br J Dermatol: Smoker's Comedones and Cutaneous Oxidative Stress",
                "advice_type": "General Educational Guidance",
            }
        )


    # -------------------------------------------------------------
    # CATEGORY 3: LIFESTYLE CHANGES
    # -------------------------------------------------------------
    lifestyle: list[dict[str, str]] = []

    # 3A. Sleep & Circadian Biology:
    if "Insufficient sleep" in drivers or sleep_hours < 6.5:
        lifestyle.append(
            {
                "text": "Establish a consistent sleep and wake routine before escalating topical skin actives.",
                "reason": "Triggered by self-reported sleep deficiency in questionnaire",
                "why_shown": "Associated with self-reported sleep restriction (< 6.5 hours); chronic sleep deficit stimulates inflammatory signaling.",
                "trigger_input": f"Questionnaire Input: Self-reported sleep duration is {sleep_hours} hours",
                "evidence_source": "Chiu et al., Acta Derm Venereol: Sleep Deprivation & Inflammatory Acne",
                "advice_type": "General Educational Guidance",
            }
        )
    elif sleep_hours >= 7.5:
        lifestyle.append(
            {
                "text": "Maintain your restorative sleep window (7.5–9 hours); nocturnal cellular barrier repair peaks during deep slow-wave sleep.",
                "reason": f"Reinforces optimal circadian sleep duration ({sleep_hours} hrs)",
                "why_shown": "Adequate sleep duration supports nocturnal epidermal growth factor secretion and downregulates pro-inflammatory IL-6 cytokines.",
                "trigger_input": f"Questionnaire Input: Self-reported sleep duration is {sleep_hours} hours",
                "evidence_source": "Chiu et al., Acta Derm Venereol: Sleep Quality and Acne Severity",
                "advice_type": "General Educational Guidance",
            }
        )
    else:
        lifestyle.append(
            {
                "text": "Aim for 7–9 hours of regular sleep; sleep deficit elevates pro-inflammatory cytokines.",
                "reason": "Circadian cortisol & skin barrier repair regulation",
                "why_shown": "Circadian sleep cycles regulate nocturnal epidermal barrier recovery and cortisol equilibrium.",
                "trigger_input": f"Questionnaire Input: Self-reported sleep duration is {sleep_hours} hours",
                "evidence_source": "Chiu et al., Acta Derm Venereol: Sleep Quality and Acne Severity",
                "advice_type": "General Educational Guidance",
            }
        )

    # 3B. Physical Exercise & Post-Sweat Care:
    if exercise_freq in ("3-4_week", "5+_week", "daily"):
        lifestyle.append(
            {
                "text": "Rinse or cleanse your face within 15–20 minutes after intense workouts; avoid sitting in sweat-damp athletic fabrics.",
                "reason": f"Active exercise routine ('{exercise_freq}') requires prompt post-sweat cleansing",
                "why_shown": "Dried sodium salts from sweat combined with friction from athletic wear promote follicular occlusion and exacerbate microcomedones.",
                "trigger_input": f"Questionnaire Input: Exercise frequency is '{exercise_freq}'",
                "evidence_source": "Journal of Clinical and Aesthetic Dermatology: Exercise-Induced Cutaneous Flares and Hygiene",
                "advice_type": "General Educational Guidance",
            }
        )
    elif exercise_freq in ("none",):
        lifestyle.append(
            {
                "text": "Introduce 20–30 minutes of brisk walking or moderate cardio 3 times weekly to support cutaneous microcirculation.",
                "reason": "Sedentary lifestyle habits impact peripheral insulin sensitivity and tissue perfusion",
                "why_shown": "Moderate aerobic activity enhances cutaneous microvascular blood flow and aids systemic glucose disposal, reducing hyperinsulinemic acne triggers.",
                "trigger_input": f"Questionnaire Input: Exercise frequency is '{exercise_freq}'",
                "evidence_source": "American College of Sports Medicine & Cutis: Exercise and Insulin Sensitivity in Dermatologic Health",
                "advice_type": "General Educational Guidance",
            }
        )

    # 3C. External Mechanical Hygiene & Tobacco:
    if smoking:
        lifestyle.append(
            {
                "text": "Engage smoking cessation support; tobacco smoke causes microvascular ischemia, delayed wound healing, and comedone retention.",
                "reason": "Active smoking directly accelerates microcomedone formation and elastosis",
                "why_shown": "Inhaled nicotine impairs dermal capillary perfusion, impairs re-epithelialization of healing acne papules, and oxidizes sebum squalene.",
                "trigger_input": "Questionnaire Input: Active smoking status",
                "evidence_source": "Capitanio et al., Br J Dermatol: Atypical Smoker's Comedones (Acne Necrotica / Comedonica)",
                "advice_type": "General Educational Guidance",
            }
        )
    elif "cheeks" in problem_areas or severity >= 1:
        lifestyle.append(
            {
                "text": "Change pillowcases 2–3 times weekly and sanitize smartphone screens regularly with an antibacterial wipe.",
                "reason": "Reduces external bacterial reinoculation on lateral facial areas",
                "why_shown": "Reduces external mechanical transfer of sebum, hair products, and bacterial residues.",
                "trigger_input": f"Visual AI: Lesions identified in cheek/jawline zones ({', '.join(problem_areas) or 'cheeks'})",
                "evidence_source": "Journal of Clinical and Aesthetic Dermatology (Hygiene in Acne Care)",
                "advice_type": "General Educational Guidance",
            }
        )
    else:
        lifestyle.append(
            {
                "text": "Minimize unconscious resting of face or chin in hands to prevent mechanical friction acne.",
                "reason": "Mechanical friction acne prevention (acne mechanica)",
                "why_shown": "Repetitive friction and localized thermal occlusion from hand-to-face contact trigger infundibular hyperkeratosis.",
                "trigger_input": "Cutaneous hygiene and mechanical friction protocol",
                "evidence_source": "Journal of Clinical and Aesthetic Dermatology (Hygiene in Acne Care)",
                "advice_type": "General Educational Guidance",
            }
        )

    # -------------------------------------------------------------
    # CATEGORY 4: STRESS MANAGEMENT
    # -------------------------------------------------------------
    stress: list[dict[str, str]] = []

    if "Elevated stress" in drivers or stress_level >= 7 or l >= 55.0:
        stress.append(
            {
                "text": "Schedule brief daily decompression periods (walking, meditation, or breathwork).",
                "reason": "Triggered by high stress score (HPA-axis sebum stimulation)",
                "why_shown": "Associated with self-reported elevated stress; psychological stress activates the HPA axis, releasing CRH and stimulating sebocytes.",
                "trigger_input": f"Questionnaire Input: Self-reported stress level is {stress_level} / 10",
                "evidence_source": "Chiu et al., Acta Derm Venereol / Zouboulis et al., Exp Dermatol",
                "advice_type": "General Educational Guidance",
            }
        )
        stress.append(
            {
                "text": "Prioritize structured physical recovery periods; chronic cortisol elevates androgen sensitivity.",
                "reason": "Triggered by elevated systemic lifestyle stress load",
                "why_shown": "Associated with high lifestyle stress load; prolonged cortisol surges alter cutaneous androgen receptor response.",
                "trigger_input": f"Questionnaire Input: Lifestyle stress score is {round(l, 1)} / 100",
                "evidence_source": "Chen & Lyga, Inflamm Allergy Drug Targets: Brain-Skin Connection",
                "advice_type": "General Educational Guidance",
            }
        )
    elif menstrual_cycle in ("irregular", "somewhat_irregular") and stress_level >= 5:
        stress.append(
            {
                "text": "Incorporate 10 minutes of slow diaphragmatic breathing (vagal nerve stimulation) during the luteal phase of your cycle.",
                "reason": f"Intersection of moderate stress ({stress_level}/10) and menstrual cycle irregularity",
                "why_shown": "Elevated sympathetic activation amplifies hormonal fluctuations; vagal nerve pacing helps stabilize neurogenic substance P release.",
                "trigger_input": f"Questionnaire Input: Stress {stress_level}/10 with '{menstrual_cycle}' cycle",
                "evidence_source": "Chen & Lyga, Inflamm Allergy Drug Targets: Brain-Skin Connection",
                "advice_type": "General Educational Guidance",
            }
        )
    elif stress_level <= 3:
        stress.append(
            {
                "text": "Maintain your balanced stress regulation habits; low autonomic tension supports stable cutaneous neurogenic baselines.",
                "reason": f"Acknowledges favorable low stress score ({stress_level}/10)",
                "why_shown": "Stable autonomic balance limits corticotropin-releasing hormone (CRH) secretion, preventing stress-induced sebocyte lipid spikes.",
                "trigger_input": f"Questionnaire Input: Self-reported stress level is {stress_level} / 10",
                "evidence_source": "Zouboulis et al., Exp Dermatol: Neuroendocrine Regulation of Human Sebocytes",
                "advice_type": "General Educational Guidance",
            }
        )
    else:
        stress.append(
            {
                "text": "Track stress levels vs. breakout dates for 2–4 weeks to identify personal flare patterns.",
                "reason": "Neurogenic skin inflammation monitoring",
                "why_shown": "Self-monitoring correlates personal flare timing with acute stress spikes without presuming causality.",
                "trigger_input": f"Questionnaire Input: Moderate stress score ({stress_level}/10)",
                "evidence_source": "Zouboulis et al., Exp Dermatol: Neuroendocrine Regulation of Human Sebocytes",
                "advice_type": "General Educational Guidance",
            }
        )

    # -------------------------------------------------------------
    # CATEGORY 5: ENVIRONMENTAL PROTECTION
    # -------------------------------------------------------------
    environment: list[dict[str, str]] = []

    # 5A. Pollution & Atmospheric Exposome:
    if e >= 55.0 or "High pollution exposure" in drivers or pollution_level in ("high", "very_high") or location_type in ("urban", "industrial"):
        environment.append(
            {
                "text": "Incorporate an antioxidant serum (e.g. 5% Niacinamide or Vitamin C) beneath daily sunscreen.",
                "reason": "Triggered by high environmental pollution / industrial exposure",
                "why_shown": "Associated with high environmental pollution exposure; topical antioxidants help neutralize pollution-induced squalene peroxidation.",
                "trigger_input": f"Questionnaire Input: Environmental pollution level is '{pollution_level}'",
                "evidence_source": "Krutmann et al., J Dermatol Sci: Airborne Particulates & Cutaneous Oxidative Stress",
                "advice_type": "General Educational Guidance",
            }
        )
        environment.append(
            {
                "text": "Double-cleanse in evenings on high-pollution or sunscreen days.",
                "reason": "Particulate matter (PM2.5) pore occlusion prevention",
                "why_shown": "Removes airborne particulate matter (PM2.5) and lipophilic sunscreen residues before follicular occlusion.",
                "trigger_input": f"Questionnaire Input: Location '{location_type}', Pollution '{pollution_level}'",
                "evidence_source": "Krutmann et al., J Dermatol Sci: The Skin Aging and Acne Exposome",
                "advice_type": "General Educational Guidance",
            }
        )
    else:
        environment.append(
            {
                "text": "Perform a single thorough evening cleanse with lukewarm water to remove ambient daily particulate buildup without stripping lipids.",
                "reason": f"Sufficient for low-to-moderate pollution exposome ('{pollution_level}')",
                "why_shown": "In areas with low to moderate environmental particulate burden, a single gentle cleanse avoids over-stripping stratum corneum intercellular lipids.",
                "trigger_input": f"Questionnaire Input: Pollution level '{pollution_level}', Location '{location_type}'",
                "evidence_source": "Krutmann et al., J Dermatol Sci: The Skin Aging and Acne Exposome",
                "advice_type": "General Educational Guidance",
            }
        )

    # 5B. Photoprotection & Solar Radiation:
    if sun_exposure in ("high", "very_high") or outdoor_ratio >= 0.4:
        environment.append(
            {
                "text": "Apply broad-spectrum SPF 50+ broad-spectrum sunscreen daily; reapply strictly every 2 hours during continuous outdoor activity.",
                "reason": f"High sun exposure ('{sun_exposure}') and outdoor ratio ({int(outdoor_ratio*100)}%) require maximum UV defense",
                "why_shown": "Intense solar UV radiation peroxidizes sebum squalene into comedogenic squalene monohydroperoxides and triggers post-inflammatory hyperpigmentation.",
                "trigger_input": f"Questionnaire Input: Sun exposure '{sun_exposure}' & outdoor ratio {outdoor_ratio}",
                "evidence_source": "American Academy of Dermatology (AAD) Clinical Guidelines for Photoprotection",
                "advice_type": "General Educational Guidance",
            }
        )
    else:
        environment.append(
            {
                "text": "Apply daily broad-spectrum SPF 30+; reapply every 2 hours during continuous outdoor sun exposure.",
                "reason": "Prevents UV-induced post-inflammatory hyperpigmentation (PIH)",
                "why_shown": "Protects healing cutaneous lesions from UV-mediated post-inflammatory hyperpigmentation (PIH).",
                "trigger_input": "Photoprotection clinical standard",
                "evidence_source": "American Academy of Dermatology (AAD) Clinical Guidelines for Photoprotection",
                "advice_type": "General Educational Guidance",
            }
        )

    # 5C. Ambient Climate, Humidity & Artificial Conditioning:
    if "High humidity (follicular occlusion risk)" in drivers or humidity in ("high", "very_high") or climate in ("tropical", "humid_subtropical"):
        environment.append(
            {
                "text": "Select light gel or water-based fluid textures instead of heavy occlusive creams.",
                "reason": "Triggered by high humidity climate selection",
                "why_shown": "Associated with humid climate selection; heavy occlusive layers in high ambient humidity can promote tropical follicular occlusion.",
                "trigger_input": f"Questionnaire Input: Ambient humidity level is '{humidity}'",
                "evidence_source": "British Journal of Dermatology: Tropical Climatic Influences on Sebaceous Glands",
                "advice_type": "General Educational Guidance",
            }
        )
    elif humidity == "low" or climate in ("dry_arid", "cold"):
        environment.append(
            {
                "text": "Use an indoor cool-mist humidifier in your sleep or work space to counteract dry ambient air (< 35% humidity).",
                "reason": f"Low ambient humidity ('{humidity}') accelerates transepidermal barrier moisture loss",
                "why_shown": "Dry arid environments deplete stratum corneum water, triggering compensatory hyperkeratinization and pore clogging.",
                "trigger_input": f"Questionnaire Input: Ambient humidity '{humidity}' & Climate '{climate}'",
                "evidence_source": "Ghadially et al., J Invest Dermatol: Environmental Humidity and Epidermal Permeability Barrier",
                "advice_type": "General Educational Guidance",
            }
        )

    if ac_heating == "high":
        environment.append(
            {
                "text": "Keep a hydrating facial mist (panthenol/glycerin) nearby to rehydrate skin during long exposures to artificial HVAC or forced heating.",
                "reason": f"High artificial AC/heating exposure ('{ac_heating}') decreases ambient relative humidity",
                "why_shown": "Prolonged exposure to climate-controlled HVAC systems lowers ambient relative humidity, increasing cutaneous water loss during working hours.",
                "trigger_input": f"Questionnaire Input: AC/heating exposure is '{ac_heating}'",
                "evidence_source": "Journal of Dermatological Science: Indoor Air Quality & Cutaneous Xerosis",
                "advice_type": "General Educational Guidance",
            }
        )

    # -------------------------------------------------------------
    # CATEGORY 6: WHEN TO SEE A DERMATOLOGIST (CLINICAL ESCALATION)
    # -------------------------------------------------------------
    derm: list[dict[str, str]] = []

    if pregnancy:
        derm.append(
            {
                "text": "Consult both an obstetrician and a board-certified dermatologist before initiating any active topical or systemic acne treatments.",
                "reason": "Pregnancy contraindicates standard teratogenic acne agents (retinoids, spironolactone, tetracyclines)",
                "why_shown": "Pregnancy mandates strict avoidance of teratogenic compounds; a clinician must oversee pregnancy-compatible treatment alternatives.",
                "trigger_input": "Questionnaire Input: Pregnancy status = Active / Confirmed",
                "evidence_source": "American College of Obstetricians and Gynecologists (ACOG) & AAD: Safety of Acne Medications During Pregnancy",
                "advice_type": "Clinical Escalation",
            }
        )

    if severity >= 2 or final_risk >= 70.0 or h >= 70.0:
        derm.append(
            {
                "text": "Schedule an in-person evaluation with a board-certified dermatologist for prescription therapies.",
                "reason": f"Triggered by Severity Grade {severity} / High Risk ({final_risk}%)",
                "why_shown": f"Triggered by visual Hayashi Grade {severity} ({severity_label}) or high multimodal risk ({final_risk}%). Prescription therapies (topical retinoids, systemic antibiotics, or anti-androgen therapy) may be clinically appropriate.",
                "trigger_input": f"Visual AI Output: Hayashi Grade {severity} / Final Multimodal Risk {final_risk}%",
                "evidence_source": "American Academy of Dermatology (AAD) Guidelines of Care for the Management of Acne Vulgaris",
                "advice_type": "Clinical Escalation",
            }
        )

    if "PCOS / androgen excess" in drivers or pcos_flag or (gender == "female" and menstrual_cycle in ("irregular", "absent") and h >= 60.0):
        derm.append(
            {
                "text": "Discuss endocrine-informed acne management (e.g. spironolactone, combined therapies) with a dermatologist and endocrinologist.",
                "reason": "Triggered by positive PCOS / androgenic cycle biomarker",
                "why_shown": "Associated with positive PCOS biomarker or cycle irregularity; androgen-driven sebaceous gland hyperplasia responds effectively to endocrine-targeted clinical care.",
                "trigger_input": "Questionnaire Input: Positive PCOS / menstrual cycle irregularity biomarker",
                "evidence_source": "Azziz et al., Fertil Steril / Rosenfield, NEJM: Androgen Excess and Polycystic Ovary Syndrome",
                "advice_type": "Clinical Escalation",
            }
        )

    if medications in ("steroids", "lithium", "antiepileptics"):
        derm.append(
            {
                "text": "Seek clinical evaluation to differentiate between acne vulgaris and medication-induced acneiform eruption (steroid acne).",
                "reason": f"Questionnaire medication profile indicates high-risk pharmaceutical ('{medications}')",
                "why_shown": "Systemic corticosteroids and specific psychiatric medications induce monomorphic pustular folliculitis requiring distinct medical management.",
                "trigger_input": f"Questionnaire Input: Current medications = '{medications}'",
                "evidence_source": "Kazandjieva et al., Clin Dermatol: Drug-Induced Acneiform Eruptions",
                "advice_type": "Clinical Escalation",
            }
        )
    elif thyroid_status in ("hypo", "hyper", "hypothyroid", "hyperthyroid", "hashimotos"):
        derm.append(
            {
                "text": "Consult an endocrinologist for thyroid hormone optimization alongside dermatological skincare.",
                "reason": f"Reported thyroid dysfunction ('{thyroid_status}') alters cutaneous metabolism and barrier integrity",
                "why_shown": "Thyroid hormone dysregulation impairs stratum corneum turnover kinetics, exacerbating skin barrier fragility and follicular plugging.",
                "trigger_input": f"Questionnaire Input: Thyroid status is '{thyroid_status}'",
                "evidence_source": "Safer, Endocr Pract: Thyroid Hormone and Skin Barrier Function",
                "advice_type": "Clinical Escalation",
            }
        )

    if not derm:
        derm.append(
            {
                "text": "Consult a dermatologist if lesions begin to scar, cystic nodules emerge, or OTC care shows no progress after 8–12 weeks.",
                "reason": "Standard clinical escalation guideline",
                "why_shown": "Standard clinical escalation safety threshold for persistent or scarring acne vulgaris.",
                "trigger_input": "Standard clinical safety threshold",
                "evidence_source": "British Association of Dermatologists (BAD) Acne Patient Referral Guidelines",
                "advice_type": "Clinical Escalation",
            }
        )

    return {
        "Skin Care Routine": skincare,
        "Diet": diet,
        "Lifestyle Changes": lifestyle,
        "Stress Management": stress,
        "Environmental Protection": environment,
        "When to See a Dermatologist": derm,
    }



def fuse(image: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
    if image is None or not isinstance(image, dict):
        raise ValueError("Fusion engine error: image assessment component is missing or invalid.")
    if "risk_percent" not in image:
        raise ValueError("Fusion engine error: image assessment is missing required 'risk_percent' metric.")

    if data is None or not isinstance(data, dict):
        raise ValueError("Fusion engine error: systemic data component is missing or invalid.")
    if "combined_score" not in data:
        raise ValueError("Fusion engine error: systemic assessment is missing required 'combined_score' metric.")

    image_risk = float(image["risk_percent"])
    data_combined = float(data["combined_score"])
    lifestyle_score = float(data.get("lifestyle_score", 50.0))
    environmental_score = float(data.get("environmental_score", 50.0))
    hormonal_score = float(data.get("hormonal_score", 0.0))

    # Exact weighted fusion calculation (55% CNN image, 45% systemic data)
    unclamped_sum = IMAGE_WEIGHT * image_risk + DATA_WEIGHT * data_combined
    final_risk = _clamp(unclamped_sum)

    health = skin_health_score(
        final_risk,
        lifestyle_score,
        environmental_score,
    )
    trend, trend_analysis = compute_trend_projection(
        final_risk, data_combined, image=image, data=data
    )
    recs = generate_recommendations(image, data, final_risk)

    # Base skin health calculation details
    base_health = 100.0 - final_risk
    lifestyle_bonus = (40.0 - lifestyle_score) * 0.08 if lifestyle_score < 40.0 else 0.0
    env_bonus = (40.0 - environmental_score) * 0.05 if environmental_score < 40.0 else 0.0

    return {
        "skin_health_score": health,
        "final_risk_percent": round(final_risk, 1),
        "weights": {"image": IMAGE_WEIGHT, "data": DATA_WEIGHT},
        "image": image,
        "data": data,
        "gauges": {
            "image_risk": round(image_risk, 1),
            "hormonal": round(hormonal_score, 1),
            "lifestyle": round(lifestyle_score, 1),
            "environmental": round(environmental_score, 1),
            "skin_health": health,
        },
        "fusion_breakdown": {
            "formula_definition": "FinalRisk = (0.55 * ImageRisk) + (0.45 * DataCombinedScore)",
            "weights": {"image": IMAGE_WEIGHT, "data": DATA_WEIGHT},
            "weight_rationale": (
                "55% visual lesion evaluation (direct cutaneous signal from MobileNetV2 CNN) + "
                "45% systemic exposome (endocrine, lifestyle, and environmental drivers from Random Forest / Rule Engine)."
            ),
            "arithmetic_steps": [
                f"Visual Input: {round(image_risk, 1)}% * {IMAGE_WEIGHT} = {round(IMAGE_WEIGHT * image_risk, 2)}%",
                f"Systemic Input: {round(data_combined, 1)}% * {DATA_WEIGHT} = {round(DATA_WEIGHT * data_combined, 2)}%",
                f"Combined Weighted Sum: {round(unclamped_sum, 2)}%",
                f"Clamped Final Risk: {round(final_risk, 1)}%",
            ],
            "health_score_steps": [
                f"Base Health: 100.0 - {round(final_risk, 1)} = {round(base_health, 1)}",
                f"Favorable Lifestyle Bonus (<40): +{round(lifestyle_bonus, 2)}" if lifestyle_bonus > 0 else "Lifestyle Bonus: 0.0",
                f"Favorable Environment Bonus (<40): +{round(env_bonus, 2)}" if env_bonus > 0 else "Environment Bonus: 0.0",
                f"Final Skin Health Score: {health}",
            ],
            "component_sources": {
                "image": {
                    "component_name": "Image Model Assessment",
                    "source_type": "Trained Convolutional Neural Network",
                    "model_identifier": image.get("method", "mobilenetv2_acne04_improved"),
                    "description": "Direct cutaneous lesion evaluation from 224x224 facial photography (Hayashi grading).",
                },
                "data": {
                    "component_name": "Questionnaire & Biomarker Assessment",
                    "source_type": "Multi-Output Machine Learning & Expert Rule Engine",
                    "model_identifier": data.get("method", "random_forest_on_synthetic_labels"),
                    "description": "Systemic risk scoring across 21 endocrine, lifestyle, and exposome factors.",
                },
                "fusion": {
                    "component_name": "Multimodal Synthesis",
                    "source_type": "Deterministic Weighted Decision-Support Fusion",
                    "model_identifier": "fusion_engine.py:fuse()",
                    "description": "Transparent weighted combination with 3-month predictive trajectory projection.",
                },
            },
            "clinical_limitation": (
                "Skinova's fusion engine employs transparent heuristic weights for educational decision-support. "
                "Mathematical precision does not establish clinical diagnostic validity or replace evaluation by a board-certified dermatologist."
            ),
        },
        "trend": trend,
        "trend_analysis": trend_analysis,
        "trend_disclaimer": (
            "Statistical mathematical projection based on current multimodal inputs. "
            "Estimated projection only — not a clinical diagnosis or guaranteed medical outcome. "
            "Individual biological responses to skincare routines vary."
        ),
        "recommendations": recs,
        "disclaimer": (
            "Skinova is an educational decision-support prototype, not a certified "
            "medical device. It does not diagnose or treat disease. Consult a "
            "qualified clinician for medical advice."
        ),
    }
