"""Gate for the not_medical image route: medical images must never be discarded.

build  -> writes the two manifests that run_classifier.py consumes.
report -> summarizes run_classifier.py outputs (policy v2).
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
EVAL_ROOT = ROOT.parents[1]
GENERATED = ROOT / "generated"
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}

MEDREAMM_DIR = EVAL_ROOT / "bench" / "multimodal_beta" / "datasets" / "processed" / "medreamm_pilot250"
MEDREAMM_MANIFEST = GENERATED / "medreamm_pilot250_images_manifest.yaml"
# Real non-medical images already on disk. Not copied into the repo.
NOT_MEDICAL_SOURCES = {
    "client_assets": EVAL_ROOT.parent / "Client" / "src" / "assets" / "img",
    "windows_wallpaper": Path("C:/Windows/Web"),
}
NOT_MEDICAL_MIN_BYTES = 3 * 1024
NOT_MEDICAL_MANIFEST = GENERATED / "not_medical_manifest.yaml"


def images_under(folder: Path, min_bytes: int = 0) -> list[Path]:
    return sorted(
        path for path in folder.rglob("*")
        if path.suffix.lower() in IMAGE_SUFFIXES and path.stat().st_size >= min_bytes
    )


def write_manifest(path: Path, assets: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        yaml.safe_dump({"assets": assets}, stream, allow_unicode=True, sort_keys=False)
    print(f"{path.name}: {len(assets)} image(s)")


def build() -> None:
    write_manifest(MEDREAMM_MANIFEST, [
        {
            "id": f"medreamm-{path.parent.parent.name}-{path.stem}",
            "path": str(path),
            "expected_class": "medical_image",
            "source": "medreamm_pilot250",
            "metadata": {"source_case_id": path.parent.parent.name},
        }
        for path in images_under(MEDREAMM_DIR)
    ])
    not_medical = []
    for source, folder in NOT_MEDICAL_SOURCES.items():
        for path in images_under(folder, NOT_MEDICAL_MIN_BYTES):
            not_medical.append({
                "id": f"{source}-{len(not_medical):03d}-{path.stem}",
                "path": str(path),
                "expected_class": "not_medical",
                "source": source,
                "metadata": {"file": path.name},
            })
    write_manifest(NOT_MEDICAL_MANIFEST, not_medical)


def load(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def report(medical_results: list[Path], not_medical_results: list[Path]) -> int:
    medical = [record for path in medical_results for record in load(path)]
    negatives = [record for path in not_medical_results for record in load(path)]
    errors = sum(record["status"] == "error" for record in medical + negatives)

    discarded_medical = [r for r in medical if r["predicted_route"] == "discarded"]
    discarded_negatives = sum(r["predicted_route"] == "discarded" for r in negatives)

    print(f"Medical images: {len(medical)}")
    print("  routes:", dict(Counter(r["predicted_route"] for r in medical)))
    print(f"  discarded (must be 0): {len(discarded_medical)}")
    for record in discarded_medical:
        print(f"    {record['id']} conf={record['confidence']} evidence={record.get('evidence')}")
    print(f"Non-medical images: {len(negatives)}")
    print("  classes:", dict(Counter(r["predicted_class"] for r in negatives)))
    if negatives:
        print(f"  discarded: {discarded_negatives}/{len(negatives)} "
              f"({discarded_negatives / len(negatives):.0%})")
    kept = [r for r in negatives if r["predicted_route"] != "discarded"]
    for record in kept:
        print(f"    kept {record['id']}: {record['predicted_class']} "
              f"conf={record['confidence']} evidence={record.get('evidence')}")
    print(f"Classifier errors: {errors}")
    return 1 if discarded_medical or errors else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("build")
    report_parser = commands.add_parser("report")
    report_parser.add_argument("--medical", type=Path, nargs="+", required=True)
    report_parser.add_argument("--not-medical", type=Path, nargs="+", required=True)
    args = parser.parse_args()
    if args.command == "build":
        build()
        return 0
    return report(args.medical, args.not_medical)


if __name__ == "__main__":
    raise SystemExit(main())
