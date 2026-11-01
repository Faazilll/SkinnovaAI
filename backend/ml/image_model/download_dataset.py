"""
Download / prepare ACNE04 dataset.

Acquisition order (Priority 1 continuation prompt):
1. Kaggle API (jincyjis/acne04, nghihuynh/acne04) — requires
   KAGGLE_API_TOKEN, ~/.kaggle/access_token, or legacy ~/.kaggle/kaggle.json
2. Google Drive Classification.tar (xpwu95/LDL) — resumable via gdown
3. Hugging Face ManuelHettich/acne04 mirror — PARTIAL fallback only (~425 unique images)

Requires Kaggle API credentials if using Kaggle. Current Kaggle CLI supports
KAGGLE_API_TOKEN or ~/.kaggle/access_token; legacy kaggle.json is also accepted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tarfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATA = ROOT / "data" / "acne04"
TARGET_IMAGES = 1457
KAGGLE_SLUGS = ("jincyjis/acne04", "nghihuynh/acne04")
GDRIVE_TAR_ID = "1ysutxP3IHKhQA8brdwPlhwbduo-kYt1x"
GDRIVE_TAR_MIN_BYTES = 1_000_000_000  # ~1.1 GB complete


def _find_images(root: Path) -> list[Path]:
    exts = {".jpg", ".jpeg", ".png", ".bmp"}
    skip = {".cache", "organized", "organized_deduped"}
    out: list[Path] = []
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in exts:
            continue
        if any(part in skip for part in p.parts):
            continue
        out.append(p)
    return out


def _file_hash(path: Path, block: int = 65536) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(block):
            h.update(chunk)
    return h.hexdigest()


def _infer_label_from_path(path: Path) -> int | None:
    """
    ACNE04 / Kaggle mirrors encode severity in folder name or filename.
    Hayashi grades: 0 mild, 1 moderate, 2 severe, 3 very severe.
    """
    import re

    parts = [path.parent.name.lower(), path.stem.lower()]
    joined = " ".join(parts)
    mapping = [
        (("acne0", "level0", "grade0", "severity_0", "class_0", "mild", "/0/", "_0_"), 0),
        (("acne1", "level1", "grade1", "severity_1", "class_1", "moderate", "/1/", "_1_"), 1),
        (("acne2", "level2", "grade2", "severity_2", "class_2", "severe", "/2/", "_2_"), 2),
        (
            (
                "acne3",
                "level3",
                "grade3",
                "severity_3",
                "class_3",
                "very_severe",
                "very-severe",
                "/3/",
                "_3_",
            ),
            3,
        ),
    ]
    for keys, label in mapping:
        for k in keys:
            if k in joined or k.strip("/") == path.parent.name:
                return label
    m = re.search(r"lev(?:el|le)[_-]?([0-3])", joined)
    if m:
        return int(m.group(1))
    if path.parent.name.isdigit() and path.parent.name in {"0", "1", "2", "3"}:
        return int(path.parent.name)
    return None


def _kaggle_configured() -> bool:
    kaggle_dir = Path.home() / ".kaggle"
    access_token = kaggle_dir / "access_token"
    kaggle_json = kaggle_dir / "kaggle.json"
    return any(
        [
            bool(os.environ.get("KAGGLE_API_TOKEN")),
            access_token.exists() and access_token.stat().st_size > 0,
            kaggle_json.exists(),
            bool(os.environ.get("KAGGLE_USERNAME") and os.environ.get("KAGGLE_KEY")),
        ]
    )


def _configure_kaggle_token_env() -> None:
    """Bridge ~/.kaggle/access_token into KAGGLE_API_TOKEN for new Kaggle CLI auth."""
    if os.environ.get("KAGGLE_API_TOKEN"):
        return
    access_token = Path.home() / ".kaggle" / "access_token"
    if access_token.exists():
        token = access_token.read_text(encoding="utf-8").strip()
        if token:
            os.environ["KAGGLE_API_TOKEN"] = token


def download_kaggle(dest: Path, dataset: str = "jincyjis/acne04") -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    _configure_kaggle_token_env()
    from kaggle.api.kaggle_api_extended import KaggleApi

    api = KaggleApi()
    api.authenticate()
    api.dataset_download_files(dataset, path=str(dest), unzip=True)
    return dest


def download_gdrive(dest: Path, max_retries: int = 3) -> Path:
    """Original ACNE04 Classification.tar from Wu et al. ICCV 2019 authors."""
    import gdown

    gdir = dest / "gdrive"
    gdir.mkdir(parents=True, exist_ok=True)
    tar_path = gdir / "Classification.tar"
    url = f"https://drive.google.com/uc?id={GDRIVE_TAR_ID}"

    # Clean stale partial files from failed gdown runs (keep .part if same target)
    for stale in gdir.glob("Classification.tar*.part"):
        if stale.name != tar_path.name + ".part":
            try:
                stale.unlink()
            except OSError:
                pass

    if not tar_path.exists() or tar_path.stat().st_size < GDRIVE_TAR_MIN_BYTES:
        # Remove corrupt/partial file so gdown does not skip resume
        if tar_path.exists() and tar_path.stat().st_size < GDRIVE_TAR_MIN_BYTES:
            print(
                f"Removing incomplete tar ({tar_path.stat().st_size} bytes) "
                f"to allow resume..."
            )
            tar_path.unlink(missing_ok=True)
        print(f"Downloading/resuming Classification.tar -> {tar_path}")
        last_err: Exception | None = None
        for attempt in range(1, max_retries + 1):
            try:
                gdown.download(url, str(tar_path), quiet=False, resume=True)
                if tar_path.exists() and tar_path.stat().st_size >= GDRIVE_TAR_MIN_BYTES:
                    break
                last_err = RuntimeError(
                    f"Incomplete tar after attempt {attempt}: "
                    f"{tar_path.stat().st_size if tar_path.exists() else 0} bytes"
                )
            except Exception as e:
                last_err = e
                print(f"GDrive attempt {attempt}/{max_retries} failed: {e}")
        else:
            raise RuntimeError(f"Google Drive download failed after {max_retries} tries: {last_err}")

    extract_marker = gdir / ".classification_extracted"
    extract_root = gdir / "Classification"
    if not extract_marker.exists():
        print(f"Extracting {tar_path} ...")
        with tarfile.open(tar_path, "r") as tf:
            tf.extractall(gdir)
        extract_marker.write_text("ok")
    if extract_root.exists() and _find_images(extract_root):
        return extract_root
    # Some tars extract flat under gdir
    if _find_images(gdir):
        return gdir
    raise RuntimeError("Classification.tar extracted but no images found")


def download_huggingface(dest: Path) -> Path:
    """PARTIAL ACNE04 mirror (~425 unique images) — not full 1,457."""
    from huggingface_hub import snapshot_download

    out = dest / "hf_manuel"
    print(f"Downloading Hugging Face ManuelHettich/acne04 (PARTIAL mirror) -> {out}")
    snapshot_download(
        repo_id="ManuelHettich/acne04",
        repo_type="dataset",
        local_dir=str(out),
    )
    return out


def acquire_dataset(data_dir: Path) -> tuple[Path, dict]:
    """
    Try Kaggle -> GDrive -> HF. Returns (source_path, acquisition_meta).
    """
    meta: dict = {
        "target_images": TARGET_IMAGES,
        "kaggle_configured": _kaggle_configured(),
        "attempts": [],
        "source_type": None,
        "is_full_acne04": False,
    }

    # 1) Kaggle
    if meta["kaggle_configured"]:
        for slug in KAGGLE_SLUGS:
            try:
                print(f"Trying Kaggle: {slug}")
                raw = data_dir / "raw" / slug.replace("/", "_")
                download_kaggle(raw, slug)
                meta["attempts"].append({"source": "kaggle", "slug": slug, "ok": True})
                meta["source_type"] = "kaggle"
                meta["is_full_acne04"] = True
                meta["source_path"] = str(raw)
                return raw, meta
            except Exception as e:
                meta["attempts"].append({"source": "kaggle", "slug": slug, "ok": False, "error": str(e)})
                print(f"Kaggle {slug} failed: {e}")
    else:
        meta["attempts"].append(
            {
                "source": "kaggle",
                "ok": False,
                "error": (
                    "No KAGGLE_API_TOKEN, ~/.kaggle/access_token, "
                    "~/.kaggle/kaggle.json, or KAGGLE_USERNAME/KAGGLE_KEY — skipped"
                ),
            }
        )
        print(
            "KAGGLE NOT CONFIGURED: set KAGGLE_API_TOKEN, place an access_token "
            "or kaggle.json in ~/.kaggle/, or set KAGGLE_USERNAME + KAGGLE_KEY. "
            "Continuing to Google Drive..."
        )

    # 2) Google Drive
    try:
        print("Trying Google Drive Classification.tar (resumable)...")
        src = download_gdrive(data_dir)
        n = len(_find_images(src))
        meta["attempts"].append({"source": "google_drive", "ok": True, "n_images_found": n})
        meta["source_type"] = "google_drive"
        meta["is_full_acne04"] = n >= 1200
        meta["source_path"] = str(src)
        meta["n_images_raw"] = n
        return src, meta
    except Exception as e:
        meta["attempts"].append({"source": "google_drive", "ok": False, "error": str(e)})
        print(f"Google Drive failed: {e}")

    # 3) Hugging Face partial fallback
    hf_local = data_dir / "hf_manuel"
    if hf_local.exists() and _find_images(hf_local):
        src = hf_local
        meta["attempts"].append({"source": "huggingface_existing", "ok": True})
    else:
        try:
            print("Falling back to Hugging Face PARTIAL mirror (NOT full ACNE04)...")
            src = download_huggingface(data_dir)
            meta["attempts"].append({"source": "huggingface", "ok": True})
        except Exception as e:
            meta["attempts"].append({"source": "huggingface", "ok": False, "error": str(e)})
            raise RuntimeError(
                "Could not acquire ACNE04 from any source.\n"
                "Provide Kaggle API key (~/.kaggle/kaggle.json) or complete Google Drive download."
            ) from e

    n = len(_find_images(src))
    meta["source_type"] = "huggingface_partial"
    meta["is_full_acne04"] = False
    meta["source_path"] = str(src)
    meta["n_images_raw"] = n
    meta["warning"] = (
        "PARTIAL dataset only — NOT full ACNE04 (~1,457). "
        "Metrics must not claim full-dataset training."
    )
    return src, meta


def organize_by_severity_deduped(src: Path, dst: Path) -> dict:
    """
    Copy images into severity folders 0-3, deduplicating by SHA-256 hash.
    When duplicates exist across folders, keep first seen label and log conflict.
    """
    if dst.exists():
        shutil.rmtree(dst)
    for i in range(4):
        (dst / str(i)).mkdir(parents=True)

    seen_hash: dict[str, tuple[Path, int]] = {}
    counts = {0: 0, 1: 0, 2: 0, 3: 0, "unlabeled": 0, "duplicate_skipped": 0, "label_conflict": 0}
    images = _find_images(src)

    for img in sorted(images):
        label = _infer_label_from_path(img)
        if label is None:
            counts["unlabeled"] += 1
            continue
        try:
            digest = _file_hash(img)
        except OSError:
            counts["unlabeled"] += 1
            continue

        if digest in seen_hash:
            counts["duplicate_skipped"] += 1
            prev_path, prev_label = seen_hash[digest]
            if prev_label != label:
                counts["label_conflict"] += 1
            continue

        # Unique filename to avoid stem collisions
        target = dst / str(label) / f"{digest[:12]}_{img.name}"
        shutil.copy2(img, target)
        seen_hash[digest] = (target, label)
        counts[label] += 1

    counts["unique_labeled"] = sum(counts[i] for i in range(4))
    counts["unique_total_seen"] = len(seen_hash)
    return counts


def prepare(data_dir: Path | None = None, force: bool = False) -> Path:
    data_dir = Path(data_dir or os.environ.get("SKINOVA_ACNE04_DIR") or DEFAULT_DATA)
    data_dir.mkdir(parents=True, exist_ok=True)
    organized = data_dir / "organized_deduped"
    meta_path = data_dir / "dataset_meta.json"

    if (
        not force
        and organized.exists()
        and any((organized / str(i)).glob("*") for i in range(4))
        and meta_path.exists()
    ):
        existing = json.loads(meta_path.read_text())
        if existing.get("organize_method") == "dedupe_by_hash":
            print(f"Using existing deduped dataset at {organized} ({existing.get('counts', {})})")
            return organized

    src, acq_meta = acquire_dataset(data_dir)
    counts = organize_by_severity_deduped(src, organized)

    meta = {
        "source": str(src),
        "acquisition": acq_meta,
        "organize_method": "dedupe_by_hash",
        "target_images": TARGET_IMAGES,
        "is_full_acne04": acq_meta.get("is_full_acne04", False),
        "counts": counts,
    }
    meta_path.write_text(json.dumps(meta, indent=2))
    print(json.dumps(meta, indent=2))

    labeled = counts.get("unique_labeled", sum(counts[i] for i in range(4)))
    if labeled < 50:
        raise RuntimeError(f"Too few unique labeled images after dedupe: {counts}")

    if not acq_meta.get("is_full_acne04"):
        print(
            f"WARNING: Only {labeled} unique labeled images (target ~{TARGET_IMAGES}). "
            "This is NOT full ACNE04 — label metrics/README accordingly."
        )
    return organized


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=str, default=None)
    parser.add_argument("--force", action="store_true", help="Re-download and re-organize")
    args = parser.parse_args()
    path = prepare(Path(args.data_dir) if args.data_dir else None, force=args.force)
    print(f"Ready: {path}")


if __name__ == "__main__":
    main()
