#!/usr/bin/env python3
"""Convenience: train data model, optionally image model if ACNE04 is present."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.check_call(cmd, cwd=str(BACKEND))


def main() -> None:
    run([sys.executable, "ml/data_model/generate_synthetic.py", "--n", "3000"])
    run([sys.executable, "ml/data_model/train.py"])
    try:
        run([sys.executable, "ml/image_model/download_dataset.py"])
        run(
            [
                sys.executable,
                "ml/image_model/train.py",
                "--epochs-head",
                "8",
                "--epochs-ft",
                "6",
            ]
        )
    except Exception as e:
        print("Image model training skipped:", e)
        print(
            "Place ACNE04 under skinova/data/acne04 or add ~/.kaggle/kaggle.json, then rerun."
        )


if __name__ == "__main__":
    main()
