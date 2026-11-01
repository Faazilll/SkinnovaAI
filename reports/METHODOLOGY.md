# Skinova Methodology & Limitations

## 1. Image Model

### Dataset
- **ACNE04** (Wu et al., ICCV 2019): ~1,457 images graded 0–3 by Hayashi criterion.
- Split: stratified train / val / test (70% / 15% / 15% of organized labeled images).
- Class imbalance addressed with **balanced class weights** + light augmentation (flip, rotation, brightness/contrast).

### Architecture
- MobileNetV2 (ImageNet), `include_top=False` → GAP → Dense(128) → Softmax(4).
- Phase 1: freeze base, train head.
- Phase 2: unfreeze last ~40 base layers, fine-tune at low LR.

### Outputs beyond class
- **Future risk %** from severity→risk lookup `{0:18, 1:42, 2:68, 3:88}` plus a small boost from heuristic oiliness/redness/pore stats on the face crop.
- **Oiliness / pores / redness / dark spots** are **color-statistics heuristics**, not separate CNNs — disclosed in API `method` / README.

### Metrics
From the training run checked into `backend/artifacts/metrics/image_model_metrics.json` (do not invent figures):

- **n_total:** 425 images (HF ACNE04 mirror subset; full ACNE04 is ~1,457)
- **Test accuracy:** 0.5156
- **Test macro-F1:** 0.4851
- Confusion matrix and per-class precision/recall are in the same JSON file; plot at `confusion_matrix.png`.

Literature context (not our run): prior work on full ACNE04 reports roughly mid-70s to ~90% accuracy depending on architecture. Our lower figure reflects subset size, short CPU training, and domain factors — disclosed on purpose.

## 2. Data Model

### Why a rule engine?
No public dataset maps hormonal/lifestyle/environmental questionnaire fields to validated acne risk percentages. Pretending otherwise would be scientifically dishonest.

### Scoring logic (summary)
| Category | Examples of positive risk drivers | Literature anchors |
|----------|-----------------------------------|--------------------|
| Hormonal | PCOS, irregular cycles, adolescence, acneigenic meds | Androgen-driven sebum (Rosenfield; Azziz PCOS literature); drug-induced acne |
| Lifestyle | Short sleep, high-GI diet, high stress, smoking | Sleep & acne (Chiu et al.); GI / dairy associations (Smith et al. and follow-ons); stress–HPA–skin axis |
| Environment | Urban pollution, high humidity, high UV | Pollution & skin (Krutmann et al.); climate/humidity follicular occlusion |

Combined score = `0.40*hormonal + 0.35*lifestyle + 0.25*environmental`.

### Optional ML wrapper
- Generate ~3,000 synthetic rows by sampling questionnaire space.
- Label with rule engine + Gaussian noise (σ≈6).
- Train `RandomForestRegressor` multi-output.
- **Metrics = how well RF approximates the rule engine**, not patient outcomes.

## 3. Fusion Engine

```
final_risk = 0.55 * image_risk + 0.45 * data_combined
skin_health = clamp(100 - final_risk + lifestyle/env bonuses)
```

**Rationale:** Image is the direct cutaneous observation (slightly higher weight). Questionnaire captures systemic/exposure drivers that guide recommendations and short-horizon trend.

Trend (Now → 3 months) is a **simple projection** from risk gap and absolute risk — explicitly labeled as estimate, not prognosis.

Recommendations are rule-mapped from drivers + severity.

## 4. Limitations (must disclose)

1. Not a certified medical device; not diagnostic.
2. ACNE04 is relatively small; faces are clinic-style photos — phone selfies may domain-shift.
3. Sub-scores (oiliness etc.) are heuristics.
4. Data model is expert-informed / synthetic — **no real outcome labels**.
5. Fusion weights are design choices, not clinically validated.
6. Trend chart is illustrative.
7. Face detection may fail on extreme poses / occlusions; API can reject or (demo) allow no-face with center crop.

## 5. Citations (starter set)

- Wu et al., ICCV 2019 — ACNE04 / LDL.
- Hayashi et al. — acne severity grading criterion.
- Krutmann et al. — pollution and skin.
- Chiu et al. — sleep quality and acne.
- Reviews on diet (glycemic load) and acne; PCOS–androgen–acne pathways.

Full bibliographic entries should be expanded for the formal report as needed by your course/evaluator.
