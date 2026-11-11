#!/usr/bin/env python3
"""
Skinova Random Forest Systemic Data Model Evaluation Script.

Evaluates the active trained Random Forest model artifact on the held-out test split (20%, N=600)
of the synthetic questionnaire dataset (backend/artifacts/data/synthetic_questionnaire.csv).

Discretizes continuous systemic risk scores into 4 Clinical Severity Tiers
(matching the Hayashi Scale: Grade 0 Mild, Grade 1 Moderate, Grade 2 Severe, Grade 3 Very Severe)
and generates:
1. High-resolution annotated confusion matrix PNG (300 DPI)
2. Comprehensive evaluation metrics JSON
3. Detailed classification report CSV
4. Per-sample prediction audit CSV
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    mean_absolute_error,
    precision_recall_fscore_support,
    r2_score,
)
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
DATA_ARTIFACTS_DIR = BACKEND_DIR / "artifacts" / "data"
METRICS_DIR = BACKEND_DIR / "artifacts" / "metrics"
CSV_PATH = DATA_ARTIFACTS_DIR / "synthetic_questionnaire.csv"
MODEL_PATH = DATA_ARTIFACTS_DIR / "data_model_rf.pkl"

NUMERIC = ["age", "sleep_hours", "water_intake_liters", "stress_level", "outdoor_ratio"]
BOOLS = ["pcos", "pregnancy", "smoking"]
CATEGORICAL = [
    "gender", "menstrual_cycle", "thyroid_status", "medications", "diet_quality",
    "exercise_frequency", "alcohol", "skincare_consistency", "location_type",
    "pollution_level", "sun_exposure", "humidity", "climate", "ac_heating_exposure"
]
TARGETS = ["hormonal_score", "lifestyle_score", "environmental_score", "combined_score"]

CLASS_NAMES = {
    0: "Grade 0: Mild Risk (<35)",
    1: "Grade 1: Moderate Risk (35-50)",
    2: "Grade 2: Severe Risk (50-65)",
    3: "Grade 3: Very Severe Risk (>=65)",
}
SHORT_LABELS = ["Grade 0", "Grade 1", "Grade 2", "Grade 3"]
BINS = [0, 35, 50, 65, 101]


def load_and_preprocess_data():
    df = pd.read_csv(CSV_PATH)
    df.columns = df.columns.str.strip()
    for col in df.columns:
        if df[col].dtype == object or str(df[col].dtype).startswith("str"):
            df[col] = df[col].astype(str).str.strip()

    for b in BOOLS:
        df[b] = df[b].map({"True": 1, "False": 0, "1": 1, "0": 0, True: 1, False: 0}).astype(int)

    for num_col in NUMERIC:
        df[num_col] = pd.to_numeric(df[num_col])

    for target_col in TARGETS:
        df[target_col] = pd.to_numeric(df[target_col])

    X = df[NUMERIC + BOOLS + CATEGORICAL]
    y = df[TARGETS]
    return train_test_split(X, y, test_size=0.2, random_state=42)


def main():
    print(f"Loading dataset from {CSV_PATH}...")
    X_train, X_test, y_train, y_test = load_and_preprocess_data()
    print(f"Loaded {len(X_train)} training samples and {len(X_test)} test samples.")

    print(f"Loading model artifact from {MODEL_PATH}...")
    obj = joblib.load(MODEL_PATH)
    pipe = obj["pipeline"]

    print("Running multi-output predictions on test split...")
    y_pred = pipe.predict(X_test)

    # Continuous metrics
    cont_metrics = {}
    for i, t in enumerate(TARGETS):
        mae = float(mean_absolute_error(y_test.iloc[:, i], y_pred[:, i]))
        r2 = float(r2_score(y_test.iloc[:, i], y_pred[:, i]))
        cont_metrics[t] = {"mae": round(mae, 3), "r2": round(r2, 4)}

    # Discretization for combined_score into 4 Clinical Severity Tiers
    y_true_comb = y_test["combined_score"].values
    y_pred_comb = y_pred[:, 3]

    t_cat = pd.cut(y_true_comb, bins=BINS, labels=SHORT_LABELS, right=False)
    p_cat = pd.cut(y_pred_comb, bins=BINS, labels=SHORT_LABELS, right=False)

    cm = confusion_matrix(t_cat, p_cat, labels=SHORT_LABELS)
    acc = float(accuracy_score(t_cat, p_cat))
    precision, recall, f1, support = precision_recall_fscore_support(
        t_cat, p_cat, labels=SHORT_LABELS, average=None, zero_division=0
    )
    macro_p, macro_r, macro_f1, _ = precision_recall_fscore_support(
        t_cat, p_cat, labels=SHORT_LABELS, average="macro", zero_division=0
    )
    weighted_p, weighted_r, weighted_f1, _ = precision_recall_fscore_support(
        t_cat, p_cat, labels=SHORT_LABELS, average="weighted", zero_division=0
    )

    per_class = {}
    for i, lbl in enumerate(SHORT_LABELS):
        per_class[lbl] = {
            "name": CLASS_NAMES[i],
            "support": int(support[i]),
            "precision": round(float(precision[i]), 4),
            "recall": round(float(recall[i]), 4),
            "f1_score": round(float(f1[i]), 4),
        }

    out_metrics = {
        "evaluation_timestamp": datetime.datetime.now().isoformat(),
        "model_file": str(MODEL_PATH),
        "dataset_file": str(CSV_PATH),
        "n_train": len(X_train),
        "n_test": len(X_test),
        "continuous_regression_metrics": cont_metrics,
        "discretization_bins": BINS,
        "overall_classification_metrics": {
            "accuracy": round(acc, 4),
            "accuracy_percent": round(acc * 100, 2),
            "macro_precision": round(float(macro_p), 4),
            "macro_recall": round(float(macro_r), 4),
            "macro_f1": round(float(macro_f1), 4),
            "weighted_precision": round(float(weighted_p), 4),
            "weighted_recall": round(float(weighted_r), 4),
            "weighted_f1": round(float(weighted_f1), 4),
        },
        "per_class_metrics": per_class,
        "confusion_matrix": cm.tolist(),
    }

    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    json_path = METRICS_DIR / "evaluation_metrics_random_forest.json"
    with open(json_path, "w") as f:
        json.dump(out_metrics, f, indent=2)
    print(f"Saved evaluation metrics -> {json_path}")

    # Plot Confusion Matrix
    plt.figure(figsize=(8, 6), dpi=300)
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=SHORT_LABELS,
        yticklabels=SHORT_LABELS,
        cbar=True,
    )
    plt.title("Random Forest Systemic Risk Model — Confusion Matrix (N=600)", fontsize=13, pad=12)
    plt.xlabel("Predicted Severity Grade", fontsize=11)
    plt.ylabel("Actual Severity Grade", fontsize=11)
    plt.tight_layout()
    cm_path = METRICS_DIR / "evaluation_confusion_matrix_random_forest.png"
    plt.savefig(cm_path, dpi=300)
    plt.close()
    print(f"Saved confusion matrix plot -> {cm_path}")

    # Classification report CSV
    report_dict = classification_report(t_cat, p_cat, labels=SHORT_LABELS, output_dict=True, digits=4, zero_division=0)
    rep_df = pd.DataFrame(report_dict).transpose()
    csv_report_path = METRICS_DIR / "evaluation_classification_report_random_forest.csv"
    rep_df.to_csv(csv_report_path)
    print(f"Saved classification report CSV -> {csv_report_path}")

    # Predictions audit CSV
    audit_df = X_test.copy()
    audit_df["true_combined_score"] = y_true_comb
    audit_df["pred_combined_score"] = y_pred_comb
    audit_df["true_grade"] = t_cat
    audit_df["pred_grade"] = p_cat
    audit_df["is_correct"] = t_cat == p_cat
    audit_path = METRICS_DIR / "evaluation_predictions_random_forest.csv"
    audit_df.to_csv(audit_path, index=False)
    print(f"Saved prediction audit CSV -> {audit_path}")
    print("\n=== EVALUATION COMPLETE ===")
    print("Confusion Matrix:\n", cm)
    print(f"Accuracy: {round(acc*100, 2)}%")


if __name__ == "__main__":
    main()
