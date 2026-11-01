
from pathlib import Path
from collections import Counter, defaultdict
import hashlib
import json
import struct

ROOT = Path(__file__).resolve().parent
IMAGE_DIR = ROOT / "acne04" / "raw" / "jincyjis_acne04" / "JPEGImages"
OUTPUT_DIR = ROOT / "acne04" / "reports"

EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def image_dimensions(path):
    """Read image dimensions from common image headers."""
    try:
        with path.open("rb") as file:
            header = file.read(32)

            # PNG
            if header.startswith(b"\x89PNG\r\n\x1a\n"):
                return struct.unpack(">II", header[16:24])

            # JPEG
            if header.startswith(b"\xff\xd8"):
                file.seek(2)
                while True:
                    marker_start = file.read(1)
                    if not marker_start:
                        break
                    if marker_start != b"\xff":
                        continue

                    marker = file.read(1)
                    while marker == b"\xff":
                        marker = file.read(1)

                    if not marker:
                        break

                    code = marker[0]

                    if code in (0xD8, 0xD9, 0x01) or 0xD0 <= code <= 0xD7:
                        continue

                    length_bytes = file.read(2)
                    if len(length_bytes) != 2:
                        break

                    length = struct.unpack(">H", length_bytes)[0]

                    if code in (
                        0xC0, 0xC1, 0xC2, 0xC3,
                        0xC5, 0xC6, 0xC7,
                        0xC9, 0xCA, 0xCB,
                        0xCD, 0xCE, 0xCF,
                    ):
                        data = file.read(5)
                        if len(data) == 5:
                            height, width = struct.unpack(">HH", data[1:5])
                            return width, height
                        break

                    file.seek(length - 2, 1)

    except (OSError, struct.error):
        pass

    return None


def sha256_file(path):
    """Calculate a file hash to identify byte-identical duplicates."""
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def main():
    if not IMAGE_DIR.is_dir():
        raise FileNotFoundError(f"Dataset folder not found: {IMAGE_DIR}")

    files = sorted(
        path for path in IMAGE_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in EXTENSIONS
    )

    class_counts = Counter()
    dimension_counts = Counter()
    unreadable = []
    duplicate_groups = defaultdict(list)

    for index, path in enumerate(files, start=1):
        parts = path.stem.split("_", 1)
        label = parts[0] if len(parts) == 2 else "unknown"
        class_counts[label] += 1

        try:
            digest = sha256_file(path)
            duplicate_groups[digest].append(path.name)
        except OSError:
            unreadable.append(path.name)
            continue

        dimensions = image_dimensions(path)
        if dimensions is None:
            unreadable.append(path.name)
        else:
            width, height = dimensions
            dimension_counts[f"{width}x{height}"] += 1

        if index % 200 == 0:
            print(f"Inspected {index}/{len(files)} images")

    duplicates = [
        names for names in duplicate_groups.values()
        if len(names) > 1
    ]

    report = {
        "dataset_path": str(IMAGE_DIR),
        "total_image_files": len(files),
        "class_counts_from_filenames": dict(sorted(class_counts.items())),
        "dimension_counts": dict(
            sorted(dimension_counts.items())
        ),
        "unreadable_or_unsupported_images": sorted(set(unreadable)),
        "unreadable_count": len(set(unreadable)),
        "byte_identical_duplicate_groups": duplicates,
        "byte_identical_duplicate_extra_files": sum(
            len(group) - 1 for group in duplicates
        ),
        "notes": [
            "Labels were inferred from filenames, not independently verified.",
            "Dimension parsing is a lightweight header check, not full image decoding.",
            "Duplicate detection identifies byte-identical files only.",
            "No original images were modified or deleted.",
        ],
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / "dataset_preprocessing_report.json"
    output_file.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    print("\n--- ACNE04 DATASET REPORT ---")
    print("Total files:", len(files))
    print("Class counts:", dict(sorted(class_counts.items())))
    print("Unreadable/unsupported:", len(set(unreadable)))
    print("Duplicate groups:", len(duplicates))
    print("Report saved to:", output_file)


if __name__ == "__main__":
    main()
