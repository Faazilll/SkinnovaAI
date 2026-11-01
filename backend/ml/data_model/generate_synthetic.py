"""Generate synthetic questionnaire rows labeled by the rule engine + noise."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import numpy as np
import pandas as pd

from rule_engine import predict

GENDERS = ["female", "male", "other"]
CYCLES = ["regular", "somewhat_irregular", "irregular", "absent", "na"]
THYROID = ["normal", "hypo", "hyper"]
MEDS = [
    "none",
    "steroids",
    "lithium",
    "isotretinoin",
    "spironolactone",
    "contraceptives_antiandrogen",
    "contraceptives_androgenic",
]
DIETS = ["poor_high_gi", "poor", "average", "good", "excellent_low_gi"]
EXERCISE = ["none", "1-2_week", "3-4_week", "5+_week"]
ALCOHOL = ["none", "occasional", "moderate", "heavy"]
SKINCARE = ["none", "inconsistent", "consistent_basic", "consistent_targeted"]
LOC = ["urban", "suburban", "rural", "industrial"]
LEVELS = ["low", "moderate", "high", "very_high"]
CLIMATE = ["tropical", "humid_subtropical", "arid", "temperate", "cold"]
HVAC = ["low", "moderate", "high"]


def _sample_row(rng: random.Random) -> dict:
    gender = rng.choice(GENDERS)
    cycle = "na" if gender == "male" else rng.choice(CYCLES[:-1])
    return {
        "age": rng.randint(14, 45),
        "gender": gender,
        "menstrual_cycle": cycle,
        "pcos": rng.random() < 0.12 and gender != "male",
        "thyroid_status": rng.choices(THYROID, weights=[0.85, 0.1, 0.05])[0],
        "pregnancy": rng.random() < 0.03 and gender == "female",
        "medications": rng.choices(MEDS, weights=[0.7, 0.05, 0.02, 0.05, 0.06, 0.07, 0.05])[0],
        "sleep_hours": round(rng.uniform(4.0, 9.5), 1),
        "diet_quality": rng.choice(DIETS),
        "water_intake_liters": round(rng.uniform(0.8, 4.0), 1),
        "exercise_frequency": rng.choice(EXERCISE),
        "stress_level": rng.randint(1, 10),
        "smoking": rng.random() < 0.18,
        "alcohol": rng.choice(ALCOHOL),
        "skincare_consistency": rng.choice(SKINCARE),
        "location_type": rng.choice(LOC),
        "pollution_level": rng.choice(LEVELS),
        "sun_exposure": rng.choice(LEVELS),
        "humidity": rng.choice(LEVELS),
        "climate": rng.choice(CLIMATE),
        "outdoor_ratio": round(rng.uniform(0.05, 0.9), 2),
        "ac_heating_exposure": rng.choice(HVAC),
    }


def generate(n: int = 3000, seed: int = 42, noise_std: float = 6.0) -> pd.DataFrame:
    rng = random.Random(seed)
    np_rng = np.random.default_rng(seed)
    rows = []
    for _ in range(n):
        ans = _sample_row(rng)
        out = predict(ans)
        # Label = rule scores + Gaussian noise → ML learns approximate mapping
        row = {**ans}
        for key in (
            "hormonal_score",
            "lifestyle_score",
            "environmental_score",
            "combined_score",
        ):
            noisy = float(out[key]) + float(np_rng.normal(0, noise_std))
            row[key] = float(np.clip(noisy, 0, 100))
        rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=3000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--out",
        type=str,
        default=str(
            Path(__file__).resolve().parents[2]
            / "artifacts"
            / "data"
            / "synthetic_questionnaire.csv"
        ),
    )
    args = parser.parse_args()
    df = generate(args.n, args.seed)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    meta = {
        "n_rows": len(df),
        "seed": args.seed,
        "labeling": "rule_engine_plus_gaussian_noise",
        "note": "NOT real patient outcomes — transparent synthetic ground truth",
    }
    out.with_suffix(".meta.json").write_text(json.dumps(meta, indent=2))
    print(f"Wrote {len(df)} rows -> {out}")


if __name__ == "__main__":
    main()
