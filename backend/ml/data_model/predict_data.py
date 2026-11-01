"""Inference for questionnaire → risk scores (ML if available, else rule engine)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from rule_engine import QUESTIONNAIRE_DEFAULTS, predict as rule_predict  # noqa: E402

ARTIFACT = ROOT / "artifacts" / "data" / "data_model_rf.pkl"


def _load_ml():
    if not ARTIFACT.exists():
        return None
    import joblib

    return joblib.load(ARTIFACT)


def predict_data(answers: dict[str, Any], prefer_ml: bool = True) -> dict[str, Any]:
    merged = {**QUESTIONNAIRE_DEFAULTS, **answers}
    rule_out = rule_predict(merged)

    bundle = _load_ml() if prefer_ml else None
    if bundle is None:
        rule_out["answers"] = merged
        return rule_out

    pipe = bundle["pipeline"]
    numeric = bundle["numeric"]
    bools = bundle["bools"]
    categorical = bundle["categorical"]
    targets = bundle["targets"]

    row = {**merged}
    for b in bools:
        row[b] = int(bool(row.get(b)))
    X = pd.DataFrame([{k: row[k] for k in numeric + bools + categorical}])
    pred = pipe.predict(X)[0]
    out = {t: round(float(pred[i]), 1) for i, t in enumerate(targets)}
    out["drivers"] = rule_out["drivers"]
    out["method"] = "random_forest_on_synthetic_labels"
    out["answers"] = merged
    out["rule_engine_reference"] = {
        k: rule_out[k]
        for k in (
            "hormonal_score",
            "lifestyle_score",
            "environmental_score",
            "combined_score",
        )
    }
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", type=str, help="Path to questionnaire JSON")
    parser.add_argument("--stdin", action="store_true")
    args = parser.parse_args()
    if args.json:
        answers = json.loads(Path(args.json).read_text())
    elif args.stdin:
        answers = json.load(sys.stdin)
    else:
        answers = dict(QUESTIONNAIRE_DEFAULTS)
    print(json.dumps(predict_data(answers), indent=2))


if __name__ == "__main__":
    main()
