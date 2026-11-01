"""
Skinova ACNE04 - EfficientNetB0 training experiment.

Based on the successful 69.01% MobileNetV2 experiment:
- Same verified 1,419 unique ACNE04 images
- No YuNet/Haar face crop during training
- Class weights only; no oversampling
- GPU memory growth
- Batch size 8
- EfficientNetB0 ImageNet transfer learning
- Phase 1 head training + Phase 2 fine-tuning
- Memory-safe test prediction
- Saves a separate model/metrics so previous experiments are untouched
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight

try:
    import seaborn as sns
except ImportError:
    sns = None

# GPU memory protection
try:
    gpus = tf.config.list_physical_devices("GPU")
    for gpu in gpus:
        tf.config.experimental.set_memory_growth(gpu, True)
    print(f"TensorFlow GPUs detected: {gpus}")
except RuntimeError as exc:
    print(f"GPU memory-growth setup skipped: {exc}")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from download_dataset import prepare  # noqa: E402

IMG_SIZE = 224
ARTIFACT_DIR = ROOT / "artifacts" / "image"
METRICS_DIR = ROOT / "artifacts" / "metrics"

SEVERITY_TO_RISK = {0: 18.0, 1: 42.0, 2: 68.0, 3: 88.0}


def load_dataset(organized: Path):
    """Load ACNE04 without aggressive face detection cropping."""
    X, y, paths = [], [], []
    skipped = 0

    for label in range(4):
        folder = organized / str(label)
        if not folder.exists():
            continue

        for p in sorted(folder.glob("*")):
            if p.suffix.lower() not in {".jpg", ".jpeg", ".png", ".bmp"}:
                continue

            try:
                bgr = cv2.imread(str(p), cv2.IMREAD_COLOR)
                if bgr is None:
                    raise ValueError("Could not decode image")

                rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
                h, w = rgb.shape[:2]
                side = min(h, w)
                y0 = max(0, (h - side) // 2)
                x0 = max(0, (w - side) // 2)
                crop = rgb[y0:y0 + side, x0:x0 + side]

                resized = cv2.resize(
                    crop, (IMG_SIZE, IMG_SIZE), interpolation=cv2.INTER_AREA
                )

                X.append(resized)
                y.append(label)
                paths.append(str(p))

                if len(X) % 100 == 0:
                    print(f"Preprocessed {len(X)} images...")

            except Exception as exc:
                skipped += 1
                print(f"Skipping {p.name}: {exc}")

    if not X:
        raise ValueError(f"No loadable images under {organized}")

    if skipped:
        print(f"Skipped {skipped} unreadable images.")

    return (
        np.stack(X).astype(np.float32),
        np.asarray(y, dtype=np.int32),
        paths,
    )


def build_model(num_classes: int = 4, trainable_base: bool = False):
    base = tf.keras.applications.EfficientNetB0(
        input_shape=(IMG_SIZE, IMG_SIZE, 3),
        include_top=False,
        weights="imagenet",
    )
    base.trainable = trainable_base

    inputs = tf.keras.Input(shape=(IMG_SIZE, IMG_SIZE, 3))

    # EfficientNetB0 in Keras includes its own input rescaling.
    x = base(inputs, training=False)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    x = tf.keras.layers.Dropout(0.35)(x)
    x = tf.keras.layers.Dense(128, activation="relu")(x)
    x = tf.keras.layers.Dropout(0.25)(x)
    outputs = tf.keras.layers.Dense(num_classes, activation="softmax")(x)

    return tf.keras.Model(inputs, outputs)


def make_augmenter():
    return tf.keras.Sequential(
        [
            tf.keras.layers.RandomFlip("horizontal"),
            tf.keras.layers.RandomRotation(0.05),
            tf.keras.layers.RandomZoom(0.08),
            tf.keras.layers.RandomContrast(0.10),
            tf.keras.layers.RandomBrightness(0.08),
        ],
        name="train_augmenter",
    )


def find_efficientnet_base(model):
    for layer in model.layers:
        if isinstance(layer, tf.keras.Model) and "efficientnet" in layer.name.lower():
            return layer
    raise RuntimeError("Could not find EfficientNetB0 base layer.")


def train(
    data_dir: Path | None = None,
    epochs_head: int = 20,
    epochs_ft: int = 12,
    batch_size: int = 8,
    force_prepare: bool = False,
):
    t0 = time.time()

    # Reuse the verified organized_deduped dataset.
    organized = prepare(data_dir, force=force_prepare)

    meta_path = (data_dir or ROOT.parent / "data" / "acne04") / "dataset_meta.json"
    dataset_meta = {}
    if meta_path.exists():
        dataset_meta = json.loads(meta_path.read_text())

    X, y, _ = load_dataset(organized)

    unique, counts = np.unique(y, return_counts=True)
    class_counts = {int(c): int(n) for c, n in zip(unique, counts)}

    print(f"Loaded {len(X)} unique images; class counts: {class_counts}")

    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.30, random_state=42, stratify=y
    )

    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.50, random_state=42, stratify=y_temp
    )

    # Class weights only.
    classes = np.unique(y_train)
    weights = compute_class_weight(
        class_weight="balanced",
        classes=classes,
        y=y_train,
    )
    class_weights = {
        int(c): float(w) for c, w in zip(classes, weights)
    }

    print(f"Class weights: {class_weights}")
    print(
        f"Split: train={len(y_train)}, "
        f"val={len(y_val)}, test={len(y_test)}"
    )

    augmenter = make_augmenter()

    def augment(images, labels):
        return augmenter(images, training=True), labels

    train_ds = (
        tf.data.Dataset.from_tensor_slices((X_train, y_train))
        .shuffle(len(X_train), seed=42, reshuffle_each_iteration=True)
        .batch(batch_size)
        .map(augment, num_parallel_calls=tf.data.AUTOTUNE)
        .prefetch(tf.data.AUTOTUNE)
    )

    val_ds = (
        tf.data.Dataset.from_tensor_slices((X_val, y_val))
        .batch(batch_size)
        .prefetch(tf.data.AUTOTUNE)
    )

    model = build_model(trainable_base=False)

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )

    callbacks_head = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_accuracy",
            mode="max",
            patience=5,
            restore_best_weights=True,
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            patience=2,
            factor=0.5,
            min_lr=1e-6,
        ),
    ]

    print(f"Phase 1: EfficientNetB0 head training up to {epochs_head} epochs (GPU)...")

    hist1 = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=epochs_head,
        class_weight=class_weights,
        callbacks=callbacks_head,
        verbose=1,
    )

    base = find_efficientnet_base(model)
    base.trainable = True

    # Fine-tune the last ~40 layers, while keeping BatchNorm frozen.
    for layer in base.layers[:-40]:
        layer.trainable = False

    for layer in base.layers:
        if isinstance(layer, tf.keras.layers.BatchNormalization):
            layer.trainable = False

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-5),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )

    callbacks_ft = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_accuracy",
            mode="max",
            patience=5,
            restore_best_weights=True,
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            patience=2,
            factor=0.5,
            min_lr=1e-7,
        ),
    ]

    print(f"Phase 2: EfficientNetB0 fine-tuning up to {epochs_ft} epochs (GPU)...")

    hist2 = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=epochs_ft,
        class_weight=class_weights,
        callbacks=callbacks_ft,
        verbose=1,
    )

    # Memory-safe evaluation.
    probs = model.predict(X_test, batch_size=4, verbose=0)
    y_pred = probs.argmax(axis=1)

    accuracy = float(accuracy_score(y_test, y_pred))
    macro_f1 = float(f1_score(y_test, y_pred, average="macro"))
    cm = confusion_matrix(y_test, y_pred).tolist()

    report = classification_report(
        y_test,
        y_pred,
        digits=4,
        output_dict=True,
        zero_division=0,
    )

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    METRICS_DIR.mkdir(parents=True, exist_ok=True)

    model_path = ARTIFACT_DIR / "efficientnetb0_acne04.keras"
    model.save(model_path)

    try:
        model.save(ARTIFACT_DIR / "efficientnetb0_acne04.h5")
    except Exception as exc:
        print(f"H5 save skipped: {exc}")

    fig, ax = plt.subplots(figsize=(6, 5))
    cm_arr = np.asarray(cm)

    if sns is not None:
        sns.heatmap(
            cm_arr,
            annot=True,
            fmt="d",
            cmap="Blues",
            xticklabels=[0, 1, 2, 3],
            yticklabels=[0, 1, 2, 3],
            ax=ax,
        )
    else:
        im = ax.imshow(cm_arr, cmap="Blues")
        fig.colorbar(im, ax=ax)
        for i in range(cm_arr.shape[0]):
            for j in range(cm_arr.shape[1]):
                ax.text(j, i, str(cm_arr[i, j]), ha="center", va="center")

    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title("Skinova ACNE04 EfficientNetB0 Confusion Matrix")
    fig.tight_layout()

    cm_path = METRICS_DIR / "confusion_matrix_efficientnetb0.png"
    fig.savefig(cm_path, dpi=150)
    plt.close(fig)

    wall = time.time() - t0

    metrics = {
        "dataset": "ACNE04 full (official Classification.tar or Kaggle)",
        "is_full_acne04": bool(dataset_meta.get("is_full_acne04", True)),
        "organize_counts": dataset_meta.get("counts", {}),
        "n_total": int(len(X)),
        "n_train_raw": int(len(y_train)),
        "n_val": int(len(y_val)),
        "n_test": int(len(y_test)),
        "class_counts_all": class_counts,
        "class_weights": class_weights,
        "oversampling": False,
        "training_device": "GPU (TensorFlow on WSL2)",
        "batch_size": int(batch_size),
        "epochs_head_requested": int(epochs_head),
        "epochs_head_run": int(len(hist1.history.get("loss", []))),
        "epochs_ft_requested": int(epochs_ft),
        "epochs_ft_run": int(len(hist2.history.get("loss", []))),
        "test_accuracy": accuracy,
        "test_macro_f1": macro_f1,
        "confusion_matrix": cm,
        "classification_report": report,
        "severity_to_risk_lookup": SEVERITY_TO_RISK,
        "history_head_val_acc": [
            float(v) for v in hist1.history.get("val_accuracy", [])
        ],
        "history_ft_val_acc": [
            float(v) for v in hist2.history.get("val_accuracy", [])
        ],
        "training_wall_seconds": float(wall),
        "model_path": str(model_path),
        "preprocessing": (
            "RGB conversion, square center crop, 224x224 resize; "
            "no YuNet/Haar face crop during training"
        ),
        "balancing": "class weights only; no oversampling",
        "previous_mobilenet_accuracy": 0.6901408450704225,
        "previous_mobilenet_macro_f1": 0.682140217704458,
    }

    metrics_path = METRICS_DIR / "image_model_metrics_efficientnetb0.json"
    metrics_path.write_text(json.dumps(metrics, indent=2))

    print(
        json.dumps(
            {
                "dataset": metrics["dataset"],
                "n_total": metrics["n_total"],
                "test_accuracy": metrics["test_accuracy"],
                "test_macro_f1": metrics["test_macro_f1"],
                "training_wall_seconds": metrics["training_wall_seconds"],
                "model_path": metrics["model_path"],
                "metrics_path": str(metrics_path),
            },
            indent=2,
        )
    )

    return metrics


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--data-dir", type=str, default=None)
    parser.add_argument("--epochs-head", type=int, default=20)
    parser.add_argument("--epochs-ft", type=int, default=12)
    parser.add_argument("--batch-size", type=int, default=8)

    parser.add_argument(
        "--force-prepare",
        action="store_true",
        help="Re-download/re-organize dataset. Do NOT use for this experiment.",
    )

    args = parser.parse_args()

    train(
        data_dir=Path(args.data_dir) if args.data_dir else None,
        epochs_head=args.epochs_head,
        epochs_ft=args.epochs_ft,
        batch_size=args.batch_size,
        force_prepare=args.force_prepare,
    )


if __name__ == "__main__":
    main()