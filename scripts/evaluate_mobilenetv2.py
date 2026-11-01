#!/usr/bin/env python3
"""
Skinova MobileNetV2 ACNE04 Model Evaluation Script.

Evaluates the active trained MobileNetV2 model artifact on the held-out test split (15%)
of the verified ACNE04 dataset (acne04/organized_deduped).

Generates:
1. High-resolution annotated confusion matrix PNG (300 DPI)
2. Comprehensive evaluation metrics JSON
3. Detailed classification report CSV
4. Per-sample prediction audit CSV
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys
import time
from collections import Counter
from pathlib import Path

import cv2
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
    precision_recall_fscore_support,
)
from sklearn.model_selection import train_test_split

# Project root resolution
ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
IMAGE_ARTIFACTS_DIR = BACKEND_DIR / "artifacts" / "image"
METRICS_DIR = BACKEND_DIR / "artifacts" / "metrics"
DEFAULT_DATA_DIR = ROOT / "acne04" / "organized_deduped"

CLASS_NAMES = {
    0: "Grade 0 (Clear / Mild)",
    1: "Grade 1 (Moderate)",
    2: "Grade 2 (Severe)",
    3: "Grade 3 (Very Severe)",
}
SHORT_LABELS = ["Grade 0", "Grade 1", "Grade 2", "Grade 3"]
IMG_SIZE = 224


def _patch_keras_initializers():
    """Ensure backward/cross-version compatibility when loading Keras models."""
    try:
        import keras.initializers

        for cls_name in [
            "VarianceScaling",
            "GlorotUniform",
            "GlorotNormal",
            "HeNormal",
            "HeUniform",
            "TruncatedNormal",
        ]:
            cls = getattr(keras.initializers, cls_name, None)
            if cls is not None and hasattr(cls, "__init__"):
                orig_init = cls.__init__
                if getattr(orig_init, "_is_patched", False):
                    continue

                def _make_patched(orig):
                    def _patched(self, *args, **kwargs):
                        kwargs.pop("input_axes", None)
                        kwargs.pop("output_axes", None)
                        return orig(self, *args, **kwargs)

                    _patched._is_patched = True
                    return _patched

                cls.__init__ = _make_patched(orig_init)
    except Exception:
        pass


def load_trained_model(preferred_path: Path | None = None):
    """Load the trained MobileNetV2 model artifact."""
    _patch_keras_initializers()
    import tensorflow as tf

    candidates = []
    if preferred_path:
        candidates.append(preferred_path)
    candidates.extend(
        [
            IMAGE_ARTIFACTS_DIR / "mobilenetv2_acne04_improved.keras",
            IMAGE_ARTIFACTS_DIR / "mobilenetv2_acne04_improved.h5",
            IMAGE_ARTIFACTS_DIR / "mobilenetv2_acne04.keras",
            IMAGE_ARTIFACTS_DIR / "mobilenetv2_acne04.h5",
        ]
    )

    for p in candidates:
        if p.exists():
            print(f"Loading trained model from: {p.resolve()}")
            try:
                model = tf.keras.models.load_model(p)
                print(f"Model successfully loaded. Input shape: {model.input_shape}, Output shape: {model.output_shape}")
                return model, p
            except Exception as e:
                print(f"Failed loading {p.name}: {e}")

    raise FileNotFoundError("No valid MobileNetV2 model artifact found in backend/artifacts/image/")


def load_dataset_split(data_dir: Path):
    """
    Load dataset paths and labels, then replicate the exact verified stratified split.
    Split protocol:
    1. 70% Train, 30% Temp (random_state=42, stratify=y)
    2. 15% Val, 15% Held-out Test (random_state=42, stratify=y_temp)
    """
    paths = []
    y = []

    for label in range(4):
        folder = data_dir / str(label)
        if not folder.exists():
            continue
        for p in sorted(folder.glob("*")):
            if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp"}:
                paths.append(str(p))
                y.append(label)

    if not paths:
        raise FileNotFoundError(f"No valid image files found under {data_dir}")

    paths = np.array(paths)
    y = np.array(y, dtype=np.int32)
    total_count = len(y)
    class_counts_all = {int(k): int(v) for k, v in Counter(y).items()}

    print(f"Total dataset images found: {total_count}")
    print(f"Class distribution across all classes: {class_counts_all}")

    # Step 1: 70% Train / 30% Temp
    paths_train, paths_temp, y_train, y_temp = train_test_split(
        paths, y, test_size=0.30, random_state=42, stratify=y
    )

    # Step 2: 15% Val / 15% Test
    paths_val, paths_test, y_val, y_test = train_test_split(
        paths_temp, y_temp, test_size=0.50, random_state=42, stratify=y_temp
    )

    print(f"Dataset partitions: Train={len(y_train)}, Val={len(y_val)}, Test={len(y_test)}")
    test_class_counts = {int(k): int(v) for k, v in sorted(Counter(y_test).items())}
    print(f"Held-out test set class counts: {test_class_counts}")

    return {
        "paths_test": paths_test,
        "y_test": y_test,
        "total_count": total_count,
        "class_counts_all": class_counts_all,
        "test_class_counts": test_class_counts,
        "n_train": len(y_train),
        "n_val": len(y_val),
        "n_test": len(y_test),
    }


def preprocess_image(path_str: str) -> np.ndarray:
    """Aspect-ratio preserving square center-crop and bilinear resize to 224x224 RGB."""
    bgr = cv2.imread(path_str, cv2.IMREAD_COLOR)
    if bgr is None:
        raise ValueError(f"Could not read image at {path_str}")

    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    h, w = rgb.shape[:2]
    side = min(h, w)
    y0 = max(0, (h - side) // 2)
    x0 = max(0, (w - side) // 2)
    crop = rgb[y0 : y0 + side, x0 : x0 + side]

    resized = cv2.resize(crop, (IMG_SIZE, IMG_SIZE), interpolation=cv2.INTER_AREA)
    return resized.astype(np.float32)


def evaluate(
    model_path: Path | None = None,
    data_dir: Path | None = None,
    batch_size: int = 16,
):
    """Run model inference and generate evaluation metrics & visualizations."""
    t0 = time.time()
    data_path = data_dir or DEFAULT_DATA_DIR
    if not data_path.exists():
        raise FileNotFoundError(f"Dataset directory not found: {data_path.resolve()}")

    # 1. Load model and test dataset
    model, loaded_model_path = load_trained_model(model_path)
    split_info = load_dataset_split(data_path)
    paths_test = split_info["paths_test"]
    y_true = split_info["y_test"]
    n_test = len(y_true)

    # 2. Batch inference
    print(f"\nRunning inference on {n_test} test images (batch size {batch_size})...")
    all_probs = []
    
    for i in range(0, n_test, batch_size):
        batch_paths = paths_test[i : i + batch_size]
        batch_imgs = np.stack([preprocess_image(p) for p in batch_paths])
        probs = model.predict(batch_imgs, verbose=0)
        all_probs.append(probs)
        processed = min(i + batch_size, n_test)
        print(f"Processed {processed}/{n_test} images ({processed / n_test * 100:.1f}%)")

    all_probs = np.vstack(all_probs)
    y_pred = np.argmax(all_probs, axis=1)

    inference_time = time.time() - t0
    print(f"Inference complete in {inference_time:.2f} seconds.")

    # 3. Calculate statistical evaluation metrics
    acc = float(accuracy_score(y_true, y_pred))
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1, 2, 3])

    # Per-class metrics
    prec_per_class, rec_per_class, f1_per_class, support_per_class = precision_recall_fscore_support(
        y_true, y_pred, labels=[0, 1, 2, 3], zero_division=0
    )

    # Macro & Weighted metrics
    macro_prec, macro_rec, macro_f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="macro", zero_division=0
    )
    weighted_prec, weighted_rec, weighted_f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="weighted", zero_division=0
    )

    clf_report_dict = classification_report(
        y_true,
        y_pred,
        labels=[0, 1, 2, 3],
        target_names=SHORT_LABELS,
        output_dict=True,
        zero_division=0,
    )

    print("\n" + "=" * 65)
    print("               SKINOVA MOBILENETV2 EVALUATION REPORT             ")
    print("=" * 65)
    print(f"Overall Test Accuracy:     {acc * 100:.2f}% ({acc:.4f})")
    print(f"Macro Average Precision:   {macro_prec * 100:.2f}%")
    print(f"Macro Average Recall:      {macro_rec * 100:.2f}%")
    print(f"Macro Average F1-Score:    {macro_f1 * 100:.2f}% ({macro_f1:.4f})")
    print(f"Weighted Average F1-Score: {weighted_f1 * 100:.2f}% ({weighted_f1:.4f})")
    print("-" * 65)
    print("Per-Class Breakdown:")
    for c in range(4):
        print(
            f"  {CLASS_NAMES[c]:<25}: "
            f"Precision={prec_per_class[c]*100:5.2f}% | "
            f"Recall={rec_per_class[c]*100:5.2f}% | "
            f"F1={f1_per_class[c]*100:5.2f}% | "
            f"Support={support_per_class[c]}"
        )
    print("-" * 65)
    print("Confusion Matrix:")
    print("                 Pred 0   Pred 1   Pred 2   Pred 3   Total")
    for r in range(4):
        row_str = f"Actual Grade {r}:"
        for c in range(4):
            row_str += f"   {cm[r, c]:>5}"
        row_str += f"   {np.sum(cm[r, :]):>5}"
        print(row_str)
    print("=" * 65)

    # 4. Export Artifacts
    METRICS_DIR.mkdir(parents=True, exist_ok=True)

    # Output A: High-Resolution Confusion Matrix Heatmap PNG
    cm_png_path = METRICS_DIR / "evaluation_confusion_matrix_mobilenetv2.png"
    plt.figure(figsize=(8, 6.5), dpi=300)

    # Calculate normalized recall percentages for annotation
    cm_norm = cm.astype("float") / cm.sum(axis=1)[:, np.newaxis]
    annot_matrix = np.empty_like(cm, dtype=object)
    for i in range(4):
        for j in range(4):
            annot_matrix[i, j] = f"{cm[i, j]}\n({cm_norm[i, j]*100:.1f}%)"

    sns.heatmap(
        cm,
        annot=annot_matrix,
        fmt="",
        cmap="Blues",
        xticklabels=SHORT_LABELS,
        yticklabels=SHORT_LABELS,
        cbar=True,
        linewidths=1.2,
        linecolor="#e2e8f0",
        annot_kws={"fontsize": 11, "fontweight": "bold"},
    )
    plt.title(
        f"Skinova MobileNetV2 - ACNE04 Held-Out Test Confusion Matrix\n"
        f"Test Accuracy: {acc*100:.2f}% | Macro-F1: {macro_f1*100:.2f}% (N = {n_test})",
        fontsize=12,
        fontweight="bold",
        pad=16,
    )
    plt.xlabel("Predicted Severity Grade", fontsize=11, fontweight="bold", labelpad=10)
    plt.ylabel("Actual Hayashi Ground Truth", fontsize=11, fontweight="bold", labelpad=10)
    plt.tight_layout()
    plt.savefig(cm_png_path, dpi=300)
    plt.close()
    print(f"\n[1/4] Saved high-resolution confusion matrix plot -> {cm_png_path}")

    # Output B: Comprehensive Metrics JSON
    metrics_json_path = METRICS_DIR / "evaluation_metrics_mobilenetv2.json"
    metrics_payload = {
        "evaluation_timestamp": datetime.datetime.now().isoformat(),
        "model_file": str(loaded_model_path.resolve()),
        "dataset_directory": str(data_path.resolve()),
        "dataset_summary": {
            "total_images": split_info["total_count"],
            "class_counts_all": split_info["class_counts_all"],
            "split_distribution": {
                "n_train": split_info["n_train"],
                "n_val": split_info["n_val"],
                "n_test": split_info["n_test"],
            },
            "test_class_counts": split_info["test_class_counts"],
        },
        "overall_metrics": {
            "test_accuracy": round(acc, 6),
            "test_accuracy_percentage": round(acc * 100, 2),
            "macro_precision": round(float(macro_prec), 6),
            "macro_recall": round(float(macro_rec), 6),
            "macro_f1": round(float(macro_f1), 6),
            "weighted_precision": round(float(weighted_prec), 6),
            "weighted_recall": round(float(weighted_rec), 6),
            "weighted_f1": round(float(weighted_f1), 6),
            "n_test_samples": n_test,
        },
        "per_class_metrics": {
            str(c): {
                "class_name": CLASS_NAMES[c],
                "precision": round(float(prec_per_class[c]), 6),
                "recall": round(float(rec_per_class[c]), 6),
                "f1_score": round(float(f1_per_class[c]), 6),
                "support": int(support_per_class[c]),
            }
            for c in range(4)
        },
        "confusion_matrix": cm.tolist(),
        "classification_report": clf_report_dict,
    }
    metrics_json_path.write_text(json.dumps(metrics_payload, indent=2))
    print(f"[2/4] Saved metrics JSON -> {metrics_json_path}")

    # Output C: Classification Report CSV
    report_csv_path = METRICS_DIR / "evaluation_classification_report_mobilenetv2.csv"
    report_rows = []
    for c in range(4):
        report_rows.append(
            {
                "class_id": c,
                "class_name": CLASS_NAMES[c],
                "precision": round(float(prec_per_class[c]), 4),
                "recall": round(float(rec_per_class[c]), 4),
                "f1_score": round(float(f1_per_class[c]), 4),
                "support": int(support_per_class[c]),
            }
        )
    # Append macro and weighted summary rows
    report_rows.append(
        {
            "class_id": "macro_avg",
            "class_name": "Macro Average",
            "precision": round(float(macro_prec), 4),
            "recall": round(float(macro_rec), 4),
            "f1_score": round(float(macro_f1), 4),
            "support": n_test,
        }
    )
    report_rows.append(
        {
            "class_id": "weighted_avg",
            "class_name": "Weighted Average",
            "precision": round(float(weighted_prec), 4),
            "recall": round(float(weighted_rec), 4),
            "f1_score": round(float(weighted_f1), 4),
            "support": n_test,
        }
    )
    pd.DataFrame(report_rows).to_csv(report_csv_path, index=False)
    print(f"[3/4] Saved classification report CSV -> {report_csv_path}")

    # Output D: Detailed Predictions Audit CSV
    predictions_csv_path = METRICS_DIR / "evaluation_predictions_mobilenetv2.csv"
    pred_rows = []
    for idx, (p, true_l, pred_l, probs) in enumerate(zip(paths_test, y_true, y_pred, all_probs)):
        pred_rows.append(
            {
                "sample_index": idx,
                "image_path": str(p),
                "filename": Path(p).name,
                "true_label": int(true_l),
                "true_class_name": CLASS_NAMES[int(true_l)],
                "pred_label": int(pred_l),
                "pred_class_name": CLASS_NAMES[int(pred_l)],
                "is_correct": bool(true_l == pred_l),
                "confidence": round(float(probs[pred_l]), 4),
                "prob_grade0": round(float(probs[0]), 4),
                "prob_grade1": round(float(probs[1]), 4),
                "prob_grade2": round(float(probs[2]), 4),
                "prob_grade3": round(float(probs[3]), 4),
            }
        )
    pd.DataFrame(pred_rows).to_csv(predictions_csv_path, index=False)
    print(f"[4/4] Saved per-sample predictions audit CSV -> {predictions_csv_path}")

    return metrics_payload


def main():
    parser = argparse.ArgumentParser(description="Evaluate Skinova MobileNetV2 Model on ACNE04 Test Set")
    parser.add_argument("--model", type=str, default=None, help="Path to .keras or .h5 model file")
    parser.add_argument("--data", type=str, default=None, help="Path to acne04/organized_deduped folder")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size for inference")
    args = parser.parse_args()

    model_p = Path(args.model) if args.model else None
    data_p = Path(args.data) if args.data else None

    evaluate(model_path=model_p, data_dir=data_p, batch_size=args.batch_size)


if __name__ == "__main__":
    main()

