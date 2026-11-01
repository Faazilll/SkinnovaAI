# Skinova — Dual-Model Skin Intelligence & Acne Risk Decision Support

Skinova is a full-stack, multimodal clinical decision-support application. It combines deep visual facial feature analysis (**MobileNetV2 on ACNE04**) with systemic lifestyle, hormonal, and environmental risk assessment (**Multi-Output Random Forest + Rule Engine**) via a multimodal **Fusion Engine** and interactive React dashboard.

> **Disclaimer:** Educational / research prototype only. Skinova is not a certified medical device and does not diagnose or treat disease.

---

## 🏛️ System Architecture

```
┌──────────────────┐        ┌───────────────────────┐
│   Facial Photo   │        │ 21-Biomarker Profile  │
└────────┬─────────┘        └───────────┬───────────┘
         │                              │
         ▼                              ▼
┌──────────────────┐        ┌───────────────────────┐
│ Visual AI Model  │        │ Systemic Data Model   │
│ MobileNetV2 CNN  │        │ Random Forest + Rules │
│ Hayashi 0–3      │        │ Horm / Life / Env     │
└────────┬─────────┘        └───────────┬───────────┘
         │                              │
         └──────────────┬───────────────┘
                        ▼
             ┌─────────────────────┐
             │ Multimodal Fusion   │
             │ 55% Visual / 45% Sys│
             │ 3-Month Trend Curve │
             └──────────┬──────────┘
                        ▼
             Interactive React Dashboard
```

---

## 🚀 Quick Start & Installation

### Prerequisites
- **Python:** 3.11 or 3.12 (Virtualenv recommended)
- **Node.js:** v18+ or v20+
- **NPM:** v9+

### 1. Backend Setup
```powershell
# Navigate to backend
cd backend

# Install dependencies in virtual environment
pip install -r requirements.txt

# Start FastAPI server
uvicorn app.main:app --reload --port 8000
```
* Backend API: [http://127.0.0.1:8000](http://127.0.0.1:8000)
* Interactive Swagger Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* Health Status: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

### 2. Frontend Setup
```powershell
# Navigate to frontend (in a new terminal)
cd frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```
* Open your browser at: **[http://localhost:5173](http://localhost:5173)**

---

## 📊 Verified Model Performance

All metrics are **genuinely evaluated** on the held-out test split of the ACNE04 dataset (213 images):

| Model Component | Architecture / Algorithm | Evaluation Dataset | Test Accuracy | Macro-F1 |
|---|---|---|---|---|
| **Image Model** | MobileNetV2 (`mobilenetv2_acne04_improved.keras`) | 1,419 ACNE04 Images (213 Test) | **69.01%** | **0.6821** |
| **Data Model** | Random Forest Regressor (`data_model_rf.pkl`) | 3,000 Synthetic Questionnaire Rows | Macro MAE: **8.845** | $R^2$: **0.38–0.73** |

---

## 🔑 Three Core Implemented Features

### 1. Smart Skin Scan — Upload + Camera
- **Preserved Upload Pipeline**: Full drag-and-drop file browser, clinical sample presets (`/sample_face.jpg`, `/sample_lesion.jpg`), file type validation (JPEG, PNG, WebP), and file size enforcement (<= 15 MB).
- **Live Camera Capture**: Real-time browser `MediaDevices` video streaming (`navigator.mediaDevices.getUserMedia`) with mirror view, clinical viewfinder HUD overlay, face/lesion alignment framing guide, camera flip controls, instant snapshot review, retake, cancel, and complete hardware stream cleanup upon completion.
- **Unified Backend Inference**: Both uploaded and captured images feed directly into the exact same verified MobileNetV2 inference pipeline (`POST /predict/image` and `POST /predict/fusion/upload`).
- **Visual AI Quick Inspect**: Allows immediate inspection of the raw deep learning prediction (Hayashi classification, 4-class Softmax probability distribution, face detection status, and classical texture attribute proxies).
- **Privacy Protection**: Facial photographs are handled in memory and local session state; raw facial images are not stored in the scan history database.

### 2. Transparent Multimodal Fusion
- **Separation of Component Outputs**: Clear three-layer breakdown:
  1. *Trained Visual AI (MobileNetV2 CNN)*: Direct cutaneous lesion evaluation on ACNE04 dataset.
  2. *Systemic Biomarkers (Multi-Output Random Forest / Rule Engine)*: Endocrine, lifestyle, and exposome evaluation across 21 user-reported fields.
  3. *Multimodal Fusion Synthesis*: Combined decision support score and 3-month predictive trajectory.
- **Real Mathematical Execution**: Displays the real formula executed by the backend:
  $$\text{FinalRisk} = \text{clamp}(0.55 \times \text{ImageRisk} + 0.45 \times \text{DataCombinedScore}, \, 0.0, \, 100.0)$$
- **Step-by-Step Arithmetic**: Exposes exact visual contribution ($0.55 \times \text{ImageRisk}$), systemic contribution ($0.45 \times \text{DataCombinedScore}$), unclamped sum, and clamped final percentage.
- **Strict Input Validation**: Rejects missing components or malformed data with descriptive HTTP 422 errors instead of silently substituting zero or fabricated defaults.
- **Methodological Transparency**: Discloses that the 55%/45% weighting is a transparent heuristic decision-support design choice; mathematical precision does not establish clinical diagnostic validity.

### 3. Evidence-Linked Action Plan
- **Verified Information Linkage**: Recommendations are dynamically generated from verified visual AI inferences, questionnaire inputs, and literature rules.
- **5-Point Structured Rationale**: Every recommendation card provides:
  - *Recommendation*: Actionable self-care or referral instruction.
  - *Why shown*: The biological or educational association.
  - *Trigger input*: The exact user response or model classification that provoked the item.
  - *Evidence source*: Verifiable clinical citation (e.g. *AAD Acne Guidelines 2024*, *Smith et al., Am J Clin Nutr*, *Chiu et al., Acta Derm Venereol*, *Krutmann et al., J Dermatol Sci*, *Azziz et al., Fertil Steril*).
  - *Advice type*: Clearly distinguished as **General Educational Guidance** vs **Clinical Escalation**.
- **No False Causal Claims**: Explicitly distinguishes correlation/association from causality.
- **Clinical Escalation Alerts**: Automatic prioritization and referral guidance for severe cases (Grade $\ge 2$, risk $\ge 70\%$, or PCOS).

---

## 🧪 Automated Testing

Skinova includes a 23-test automated test suite covering all three phases:

```powershell
# Run the complete test suite
python -m unittest discover -s backend/tests -p "test_*.py"

# Or run individual feature suites
python -m unittest backend/tests/test_image.py            # Phase 1: Upload & Camera
python -m unittest backend/tests/test_fusion.py           # Phase 2: Fusion Formula
python -m unittest backend/tests/test_recommendations.py  # Phase 3: Action Plan
```

### Verified Test Results
```text
Ran 23 tests in 8.194s
OK
```

## 📁 Repository Structure

```
skinova/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point & health check
│   │   ├── db.py                # SQLite database, auth & history storage
│   │   ├── validation.py        # Upload limits & MIME validation
│   │   ├── routers/             # API routes (image, data, fusion, auth, history)
│   │   └── schemas/             # Pydantic data schemas
│   ├── ml/
│   │   ├── image_model/         # Preprocessing, face detection & MobileNetV2 inference
│   │   ├── data_model/          # Rule engine & Random Forest regressor
│   │   └── fusion/              # Multimodal fusion engine & recommendation triggers
│   └── artifacts/               # Trained models (.keras, .pkl) & metrics
├── data/
│   └── acne04/                  # ACNE04 dataset (organized_deduped)
├── frontend/
│   ├── src/
│   │   ├── components/          # React components (Navbar, Dashboard, History, etc.)
│   │   ├── api.js               # API service & JWT auth handler
│   │   └── App.jsx              # Main tabbed application
│   └── package.json             # Frontend dependencies
├── SKINOVA_FINAL_AUDIT.md       # Comprehensive 17-phase audit & verification report
└── SKINOVA_MODEL_AND_DATASET.md # Technical specifications of models and datasets
```

---

## 📜 Documentation
- Complete Audit Report: [SKINOVA_FINAL_AUDIT.md](SKINOVA_FINAL_AUDIT.md)
- Model & Dataset Specifications: [SKINOVA_MODEL_AND_DATASET.md](SKINOVA_MODEL_AND_DATASET.md)
- Clinical Methodology: [reports/METHODOLOGY.md](reports/METHODOLOGY.md)
