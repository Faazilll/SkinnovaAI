"""Train Random Forest on synthetic questionnaire labels (rule-engine derived)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ARTIFACT_DIR = Path(__file__).resolve().parents[2] / "artifacts" / "data"
METRICS_DIR = Path(__file__).resolve().parents[2] / "artifacts" / "metrics"

NUMERIC = [
    "age",
    "sleep_hours",
    "water_intake_liters",
    "stress_level",
    "outdoor_ratio",
]
BOOLS = ["pcos", "pregnancy", "smoking"]
CATEGORICAL = [
    "gender",
    "menstrual_cycle",
    "thyroid_status",
    "medications",
    "diet_quality",
    "exercise_frequency",
    "alcohol",
    "skincare_consistency",
    "location_type",
    "pollution_level",
    "sun_exposure",
    "humidity",
    "climate",
    "ac_heating_exposure",
]
TARGETS = [
    "hormonal_score",
    "lifestyle_score",
    "environmental_score",
    "combined_score",
]


def build_pipeline() -> Pipeline:
    pre = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERIC + BOOLS),
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                CATEGORICAL,
            ),
        ]
    )
    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=12,
        min_samples_leaf=3,
        random_state=42,
        n_jobs=-1,
    )
    return Pipeline([("pre", pre), ("rf", model)])


def prepare_xy(df: pd.DataFrame):
    df = df.copy()
    for b in BOOLS:
        df[b] = df[b].astype(int)
    X = df[NUMERIC + BOOLS + CATEGORICAL]
    y = df[TARGETS]
    return X, y


def train(csv_path: Path) -> dict:
    df = pd.read_csv(csv_path)
    X, y = prepare_xy(df)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    pipe = build_pipeline()
    pipe.fit(X_train, y_train)
    pred = pipe.predict(X_test)

    metrics: dict = {"targets": {}, "n_train": len(X_train), "n_test": len(X_test)}
    for i, t in enumerate(TARGETS):
        mae = float(mean_absolute_error(y_test.iloc[:, i], pred[:, i]))
        r2 = float(r2_score(y_test.iloc[:, i], pred[:, i]))
        metrics["targets"][t] = {"mae": round(mae, 3), "r2": round(r2, 4)}
    metrics["macro_mae"] = round(
        float(np.mean([metrics["targets"][t]["mae"] for t in TARGETS])), 3
    )
    metrics["labeling_note"] = (
        "Trained on synthetic labels from clinically-informed rule engine + noise. "
        "Metrics reflect fidelity to the rule engine, NOT clinical predictive accuracy."
    )

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    model_path = ARTIFACT_DIR / "data_model_rf.pkl"
    joblib.dump(
        {
            "pipeline": pipe,
            "numeric": NUMERIC,
            "bools": BOOLS,
            "categorical": CATEGORICAL,
            "targets": TARGETS,
        },
        model_path,
    )
    metrics_path = METRICS_DIR / "data_model_metrics.json"
    metrics_path.write_text(json.dumps(metrics, indent=2))
    print(json.dumps(metrics, indent=2))
    print(f"Saved model -> {model_path}")
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--csv",
        type=str,
        default=str(ARTIFACT_DIR / "synthetic_questionnaire.csv"),
    )
    args = parser.parse_args()
    csv_path = Path(args.csv)
    if not csv_path.exists():
        from generate_synthetic import generate

        df = generate(3000)
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(csv_path, index=False)
        print(f"Generated synthetic data -> {csv_path}")
    train(csv_path)


if __name__ == "__main__":
    main()
