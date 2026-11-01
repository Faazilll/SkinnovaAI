# Skinova Model & Dataset Technical Specification

This document details the **two primary data/model sources** utilized in the Skinova project, their exact repository locations, architectures, and verification status.

---

## 1. Primary Source A: ACNE04 Dataset & MobileNetV2 Image Model

### A. Dataset Details
* **Exact Folder Path:** `data/acne04/organized_deduped/`
* **Original Reference:** Wu et al., *Joint Acne Image Grading and Counting via Label Distribution Learning*, ICCV 2019.
* **Exact Contents:** **1,419 unique labeled images** organized into severity class folders:
  * `0/`: 487 images (Clear / Mild)
  * `1/`: 617 images (Moderate)
  * `2/`: 179 images (Severe)
  * `3/`: 136 images (Very Severe)
* **Deduplication Method:** Exact SHA-256 content hashing to eliminate duplicates from raw Kaggle mirrors.
* **Usage:** Used for model training, stratified validation, and final test set evaluation.

### B. Image Model Details
* **Exact File Path:** `backend/artifacts/image/mobilenetv2_acne04_improved.keras` (24.92 MB)
* **Fallback Files Present:** `mobilenetv2_acne04.keras`, `efficientnetb0_acne04.keras`
* **Architecture:** MobileNetV2 with ImageNet transfer learning weights + Global Average Pooling + Dropout(0.35) + Dense(128, ReLU) + Dropout(0.25) + Dense(4, Softmax).
* **Input Tensor Shape:** `(1, 224, 224, 3)` normalized float32.
* **Loading Code:** `backend/ml/image_model/predict_image.py:load_model()`.
* **Preprocessing Pipeline:**
  1. Input decoded to BGR via OpenCV.
  2. OpenCV YuNet ONNX face detection (with center-crop fallback for regional close-ups).
  3. Bounding box expansion (10% width, 15% height).
  4. BGR to RGB conversion and bilinear resize to $224 \times 224$.
* **Connection to Application:** Directly executed on every facial scan upload (`POST /predict/image` and `POST /predict/fusion/upload`).
* **Verification Status:** **VERIFIED**. Evaluated on the held-out 15% test split (213 images) with a verified test accuracy of **69.01%** and macro-F1 of **0.6821**.

---

## 2. Primary Source B: Synthetic Clinical Questionnaire Dataset & Random Forest Data Model

### A. Dataset Details
* **Exact File Path:** `backend/artifacts/data/synthetic_questionnaire.csv` (663.8 KB) + `synthetic_questionnaire.meta.json`
* **Contents:** 3,000 synthetic clinical questionnaire vectors across 21 input features (demographic, hormonal, lifestyle, and environmental factors).
* **Ground Truth Derivation:** Labeled using Skinova's expert rule engine (`backend/ml/data_model/rule_engine.py`) grounded in published dermatological literature (PCOS androgen mechanisms, sleep deprivation cytokines, high glycemic index diet IGF-1 signaling, and particulate matter pollution) with Gaussian noise ($\sigma = 6.0$).
* **Usage:** Used for training the multi-output Random Forest regressor.

### B. Data Model Details
* **Exact File Path:** `backend/artifacts/data/data_model_rf.pkl` (14.01 MB)
* **Underlying Logic / Pipeline:**
  * `ColumnTransformer`: `StandardScaler` for numeric/boolean fields, `OneHotEncoder` for categorical factors.
  * `RandomForestRegressor`: 200 estimators, max depth 12, min samples leaf 3.
* **Target Outputs:**
  1. `hormonal_score` (0–100)
  2. `lifestyle_score` (0–100)
  3. `environmental_score` (0–100)
  4. `combined_score` (0–100)
* **Loading Code:** `backend/ml/data_model/predict_data.py:predict_data()`.
* **Connection to Application:** Executed on every questionnaire submission (`POST /predict/data` and `POST /predict/fusion/upload`).
* **Deterministic Fallback:** If the `.pkl` artifact is unavailable, `rule_engine.py` directly executes the mathematical rules.
* **Verification Status:** **VERIFIED**. Tested with both low-risk and high-risk vectors, confirming dynamic multi-target score calculations and driver rankings.

---

## 3. Inactive / Obsolete Datasets & Models

| Path | Category | Status | Notes |
|---|---|---|---|
| `data/acne04/organized/` | Dataset | **DELETED** | Obsolete 425-image partial mirror. Safely removed. |
| `data/acne04/gdrive/Classification.tar.backup` | Archive | **DELETED** | Redundant duplicate archive. Safely removed. |
| `data/acne04/hf_manuel/` | Dataset | NOT USED | Inactive Hugging Face partial snapshot. |
| `backend/artifacts/image/mobilenetv2_acne04.keras` | Model | INACTIVE | Superseded by `mobilenetv2_acne04_improved.keras`. |
| `backend/artifacts/image/efficientnetb0_acne04.keras` | Model | INACTIVE | Standby model artifact (60.09% test accuracy). |
