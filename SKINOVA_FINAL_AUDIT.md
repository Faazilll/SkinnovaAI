# Skinova Final Complete Audit & Verification Report

**Audit Completed:** September 27, 2026  
**Auditor:** Antigravity AI Pair Programmer  
**Target Repository:** `skinova` (`c:\Users\moinu\Downloads\1234\skinova`)  
**Status:** FULLY WORKING, EMPIRICALLY EVALUATED, CLEANED & DEPLOYABLE  

---

## 1. Final Architecture Overview

Skinova is a clinically-grounded, multi-modal decision-support application fusing **deep visual lesion analysis** with **systemic lifestyle, hormonal, and environmental risk biomarkers**.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    REACT FRONTEND (Vite 6 / React 19 / Tailwind)             │
│                                                                              │
│  [ Scanner & Fusion ]       [ Scan History Timeline ]      [ Trends/Trends ] │
│  • Facial/Regional Upload   • Saved Local/Cloud Sessions   • Multi-Scan Line │
│  • 21-Biomarker Form        • Detailed Metrics Comparison  • Score Evolution │
│  • Profile Confirmation     • Reload into Live Dashboard   • User Profiles   │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       │ (Multipart POST /api/predict/fusion/upload)
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                           FASTAPI BACKEND (Uvicorn)                          │
│                                                                              │
│  1. Validation & Preprocessing:                                              │
│     • File size & MIME validation (<20MB, image/*)                           │
│     • OpenCV YuNet ONNX Face Detector (with center-crop fallback)            │
│     • Color conversion (BGR -> RGB) & 224x224 square crop tensor             │
│                                                                              │
│  2. Visual AI Model (mobilenetv2_acne04_improved.keras):                     │
│     • Architecture: MobileNetV2 ImageNet Transfer + GAP + Dense 128 + Softmax│
│     • Outputs: Hayashi Grade (0=Clear, 1=Moderate, 2=Severe, 3=Very Severe)  │
│     • Risk Lookup: {0:18%, 1:42%, 2:68%, 3:88%} + Heuristic Attribute Boost  │
│                                                                              │
│  3. Systemic Data Model (data_model_rf.pkl + rule_engine.py):                │
│     • RandomForestRegressor Multi-Output (Hormonal, Lifestyle, Environment)  │
│     • Literature-grounded driver ranking (PCOS, Sleep, Diet, Pollution, etc.)│
│                                                                              │
│  4. Multimodal Fusion Engine (fusion_engine.py):                             │
│     • Formula: FinalRisk = 0.55 * ImageRisk + 0.45 * DataCombinedScore       │
│     • SkinHealthScore = clamp(100 - FinalRisk + Lifestyle/Env Bonus)         │
│     • 3-Month Projection: Delta & Risk Drift Trajectory                      │
│     • Clinical Recommendations: Dynamic with explicit trigger reasons        │
│                                                                              │
│  5. SQLite Persistence & Authentication (db.py):                             │
│     • Users & Scans tables with PBKDF2-HMAC security                         │
│     • REST Endpoints: /auth/register, /auth/login, /auth/me, /history        │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       │
                                       ▼ (Fused JSON Dashboard Response)
┌──────────────────────────────────────────────────────────────────────────────┐
│                       INTERACTIVE DASHBOARD RESULTS                          │
│  • 5 Animated SVG Arc Gauges (Skin Health, Image Risk, Hormonal, Life, Env)  │
│  • Recharts 3-Month Projected Risk Trajectory                                │
│  • Classical Color/Texture Metrics (Oiliness, Pores, Redness, Dark Spots)    │
│  • Categorized Recommendations with "Why this recommendation?" Triggers      │
│  • Print / Export Report Toolbar & Personal Scan Notes                       │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Actual Models & Verified Empirical Performance

### A. Image Model
- **Active Model File:** `backend/artifacts/image/mobilenetv2_acne04_improved.keras` (24.92 MB)
- **Input Dimension:** $224 \times 224 \times 3$ (RGB float32)
- **Architecture:** MobileNetV2 base (frozen low-level layers, fine-tuned top 40 layers) + GlobalAveragePooling2D + Dropout(0.35) + Dense(128, ReLU) + Dropout(0.25) + Dense(4, Softmax).
- **Class Labels & Hayashi Grading:**
  - `0`: Clear / Mild
  - `1`: Moderate
  - `2`: Severe
  - `3`: Very Severe

#### Verified Test Set Evaluation (Held-Out 15% Stratified Test Split: 213 Images)
*Evaluated on the full 1,419-image dataset (`data/acne04/organized_deduped`) with random seed 42:*

- **Overall Test Accuracy:** **69.01%** (0.6901)
- **Macro-Averaged F1-Score:** **0.6821**

```
Confusion Matrix (Rows = Actual, Columns = Predicted):
                Pred 0   Pred 1   Pred 2   Pred 3   Total
Actual 0 (Mild)   55       17        1        0       73
Actual 1 (Mod)    22       60        8        3       93
Actual 2 (Sev)     0        8       14        5       27
Actual 3 (V.Sev)   0        0        2       18       20
```

```
Per-Class Detailed Classification Report:
                   Precision    Recall    F1-Score    Support
  0: Clear / Mild    71.43%     75.34%     73.33%       73
      1: Moderate    70.59%     64.52%     67.42%       93
        2: Severe    56.00%     51.85%     53.85%       27
   3: Very Severe    69.23%     90.00%     78.26%       20
  --------------------------------------------------------
         Accuracy                          69.01%      213
        Macro Avg    66.81%     70.43%     68.21%      213
     Weighted Avg    68.90%     69.01%     68.74%      213
```

### B. Data & Questionnaire Model
- **Active Model File:** `backend/artifacts/data/data_model_rf.pkl` (14.01 MB)
- **Pipeline:** `ColumnTransformer(StandardScaler + OneHotEncoder)` → `RandomForestRegressor(n_estimators=200, max_depth=12)`
- **Targets:** `hormonal_score`, `lifestyle_score`, `environmental_score`, `combined_score`
- **Trained on:** 3,000 synthetic questionnaire vectors derived from expert dermatological literature rules + Gaussian noise ($\sigma=6.0$).
- **Test Performance (vs Rule Engine Ground Truth):**
  - `hormonal_score`: MAE = 8.88, $R^2 = 0.59$
  - `lifestyle_score`: MAE = 9.42, $R^2 = 0.73$
  - `environmental_score`: MAE = 10.35, $R^2 = 0.38$
  - `combined_score`: MAE = 6.73, $R^2 = 0.53$
  - **Macro MAE:** **8.845**

---

## 3. Dataset Audit & File Locations

| Dataset Folder Path | Image Count | Status | Description / Purpose |
|---|---|---|---|
| `data/acne04/organized_deduped/` | **1,419** | **ACTIVE** | Main dataset organized into classes `0`, `1`, `2`, `3`, deduplicated by SHA-256 hash. Used for model training and evaluation. |
| `data/acne04/raw/jincyjis_acne04/` | 1,457 | RAW SOURCE | Full Kaggle mirror dataset download. Source for `organized_deduped`. |
| `data/acne04/gdrive/` | 1,457 | ARCHIVE | Original Google Drive archive from Wu et al. authors (`Classification_full.tar` and `Classification.tar`). |
| `data/acne04/organized/` | 425 | **DELETED** | Obsolete partial mirror subset. Safely deleted during audit. |

---

## 4. Mathematical Formulas & Fusion Logic

### 1. Base Image Risk Mapping
$$\text{BaseRisk} = \begin{cases} 18.0 & \text{if class } 0 \\ 42.0 & \text{if class } 1 \\ 68.0 & \text{if class } 2 \\ 88.0 & \text{if class } 3 \end{cases}$$

$$\text{AttrBoost} = (0.15 \cdot \text{Oiliness} + 0.20 \cdot \text{Redness} + 0.10 \cdot \text{Pores}) \cdot 0.25$$

$$\text{ImageRisk} = \text{clamp}(\text{BaseRisk} + \text{AttrBoost} - 8.0, 5.0, 95.0)$$

### 2. Multimodal Fusion Risk
$$\text{FinalRisk} = \text{clamp}(0.55 \cdot \text{ImageRisk} + 0.45 \cdot \text{DataCombinedScore}, 0.0, 100.0)$$

### 3. Skin Health Score
$$\text{SkinHealthScore} = \text{clamp}(100.0 - \text{FinalRisk} + \text{Bonus}_{\text{lifestyle}} + \text{Bonus}_{\text{env}}, 0.0, 100.0)$$
*(where $\text{Bonus}_{\text{lifestyle}} = \max(0, 40 - \text{Lifestyle}) \cdot 0.08$ and $\text{Bonus}_{\text{env}} = \max(0, 40 - \text{Env}) \cdot 0.05$)*

### 4. 3-Month Risk Trajectory
$$\text{Delta} = (\text{DataCombinedScore} - \text{FinalRisk}) \cdot 0.08$$
$$\text{Drift} = \begin{cases} 1.2 & \text{if FinalRisk} \ge 60 \\ 0.4 & \text{if } 40 \le \text{FinalRisk} < 60 \\ -0.8 & \text{if FinalRisk} < 40 \end{cases}$$
$$\text{Risk}(t) = \text{clamp}(\text{FinalRisk} + t \cdot (\text{Delta} + \text{Drift}), 0.0, 100.0) \quad \text{for } t \in [0, 1, 2, 3 \text{ months}]$$

---

## 5. What Was Fixed & Upgraded

1. **Active Model Selection:** Switched active image inference from the 56% baseline to `mobilenetv2_acne04_improved.keras` (69.01% test accuracy).
2. **Recommendation Reason Triggers:** Every recommendation item now displays a transparent clinical "Why this?" badge citing severity, PCOS, sleep, pollution, or risk thresholds.
3. **Flexible Face & Close-Up Support:** Enabled optional center-crop fallback so tight cheek/forehead close-ups don't crash with 422 errors.
4. **Profile Consistency Mechanism:** Added explicit disclosures and a confirmation checkbox ensuring users confirm their questionnaire profile without misleading facial gender classification.
5. **SQLite Database & Authentication:** Built user accounts, JWT-style signed tokens, scan history storage, scan reloading, notes, and deletion endpoints.
6. **Multi-Tab Dashboard Experience:** Created a 4-tab interface (**Scanner**, **History Timeline**, **Trends & Analytics**, **User Profile**).
7. **Cleaned Unpickling Warnings:** Retrained the Random Forest pipeline in Scikit-Learn 1.9.0 to eliminate serialization warnings.
8. **Removed Redundant Files:** Safely deleted duplicate archives and obsolete partial folders.

---

## 6. Complete API Endpoints Audit

| Method | Endpoint | Purpose | Tested Status |
|---|---|---|---|
| `GET` | `/health` | Deep health check (model names & DB status) | **200 OK** |
| `GET` | `/` | API Root & medical disclaimer | **200 OK** |
| `POST` | `/predict/image` | Image-only CNN inference | **200 OK** |
| `POST` | `/predict/data` | Questionnaire RF regression | **200 OK** |
| `POST` | `/predict/fusion` | JSON-based fusion combination | **200 OK** |
| `POST` | `/predict/fusion/upload` | One-shot multipart image + questionnaire fusion | **200 OK** |
| `POST` | `/auth/register` | User account registration | **200 OK** |
| `POST` | `/auth/login` | User login & token generation | **200 OK** |
| `GET` | `/auth/me` | Current authenticated user profile | **200 OK** |
| `GET` | `/history` | Fetch scan timeline | **200 OK** |
| `POST` | `/history` | Save scan with optional clinical notes | **200 OK** |
| `DELETE` | `/history/{id}` | Delete scan record | **200 OK** |

---

## 7. Known Limitations & Clinical Disclosures

1. **Educational Prototype:** Skinova is an educational decision-support demonstration, not a certified diagnostic medical device.
2. **Dataset Demographics:** ACNE04 is composed of standardized clinical facial photographs; real-world smartphone selfies may exhibit lighting or angle variations.
3. **Color/Texture Heuristics:** Oiliness, pores, redness, and dark spots are calculated using classical computer vision filters (Laplacian variance, specular highlight ratios, RGB differentials) rather than separate deep neural networks.
4. **Synthetic Questionnaire Labels:** The Random Forest data model is trained on synthetic vectors derived from expert literature rules with Gaussian noise.
