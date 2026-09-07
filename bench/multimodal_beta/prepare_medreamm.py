"""Download MedReaMM and build a leakage-screened beta cohort."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml
from huggingface_hub import hf_hub_download


REPO_ID = "thomasweiX/MedReaMM"
SUPPORTED_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}
MAX_IMAGES = 5
MAX_TOTAL_BYTES = 20 * 1024 * 1024
MIN_HISTORY_CHARS = 200
STOPWORDS = {
    "acute",
    "chronic",
    "disease",
    "disorder",
    "syndrome",
    "infection",
    "inflammatory",
    "bilateral",
    "unilateral",
    "left",
    "right",
    "upper",
    "lower",
    "patient",
    "history",
    "clinical",
    "finding",
    "findings",
    "image",
    "images",
    "imaging",
    "scan",
    "study",
    "studies",
    "examination",
    "exam",
    "test",
    "tests",
    "result",
    "results",
    "normal",
    "abnormal",
    "present",
    "presented",
    "presenting",
    "year",
    "years",
    "old",
    "male",
    "female",
    "man",
    "woman",
    "with",
    "without",
    "and",
    "the",
    "of",
    "in",
    "on",
    "to",
    "for",
    "due",
    "from",
    "after",
    "before",
    "type",
    "stage",
    "grade",
    "primary",
    "secondary",
    "severe",
    "mild",
    "moderate",
    "carcinoma",
    "adenocarcinoma",
    "sarcoma",
    "lymphoma",
    "adenoma",
    "tumor",
    "tumour",
    "neoplasm",
    "cancer",
    "metastasis",
    "pneumonia",
    "abscess",
    "infarction",
    "hemorrhage",
    "thrombosis",
    "lesion",
}
POST_DIAGNOSIS_MARKERS = (
    "final diagnosis",
    "pathological diagnosis",
    "histopathological diagnosis",
    "confirmed diagnosis",
)


class PrepareError(RuntimeError):
    """Raised when MedReaMM cannot be downloaded or prepared."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare a leakage-screened MedReaMM cohort for DxGPT beta."
    )
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--seed", type=str, default="20260727")
    parser.add_argument(
        "--output-name",
        help="Processed dataset folder name; defaults to medreamm_pilot<LIMIT>.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing processed cohort with the same name.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="multimodal_beta directory.",
    )
    return parser.parse_args()


def stable_bucket(value: str, seed: str, buckets: int) -> int:
    digest = hashlib.sha256(f"{seed}:{value}".encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % buckets


def download_file(filename: str, raw_dir: Path) -> Path:
    path = hf_hub_download(
        repo_id=REPO_ID,
        repo_type="dataset",
        filename=filename.replace("\\", "/"),
        local_dir=str(raw_dir),
    )
    return Path(path)


def load_cases(jsonl_path: Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    with jsonl_path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                cases.append(json.loads(line))
            except json.JSONDecodeError as error:
                raise PrepareError(
                    f"Invalid JSON on line {line_number} of {jsonl_path}"
                ) from error
    if not cases:
        raise PrepareError(f"No cases found in {jsonl_path}")
    return cases


def case_id(raw: dict[str, Any], index: int) -> str:
    for key in ("pmid", "id", "case_id"):
        value = raw.get(key)
        if value:
            return re.sub(r"[^A-Za-z0-9._-]+", "_", str(value))
    return f"case_{index:04d}"


def patient_info(raw: dict[str, Any]) -> dict[str, Any]:
    info = raw.get("patient_info") or {}
    return info if isinstance(info, dict) else {}


def history_text(raw: dict[str, Any]) -> str:
    return str(patient_info(raw).get("basic_info") or "").strip()


def image_records(raw: dict[str, Any]) -> list[dict[str, Any]]:
    supplementary = patient_info(raw).get("supplementary_info") or []
    records: list[dict[str, Any]] = []
    for item in supplementary:
        if not isinstance(item, dict):
            continue
        paths = item.get("path") or []
        if isinstance(paths, str):
            paths = [paths]
        modalities = item.get("modalities") or []
        if isinstance(modalities, str):
            modalities = [modalities]
        for path in paths:
            records.append(
                {
                    "path": str(path).replace("\\", "/"),
                    "caption": str(item.get("caption") or ""),
                    "detailed_caption": str(item.get("detailed_caption") or ""),
                    "modalities": [str(value) for value in modalities if value],
                }
            )
    return records


def raw_diagnosis(raw: dict[str, Any]) -> str:
    info = patient_info(raw)
    return str(info.get("diagnosis") or raw.get("diagnosis") or "").strip()


def diagnosis_entries(raw: dict[str, Any]) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    info = patient_info(raw)
    standardized = info.get("standardized_diagnosis") or raw.get("standardized_diagnosis") or []
    if isinstance(standardized, dict):
        standardized = [standardized]
    for item in standardized:
        if isinstance(item, str):
            entries.append({"name": item, "icd11": "", "role": "unspecified"})
            continue
        if not isinstance(item, dict):
            continue
        name = (
            item.get("original_term")
            or item.get("title")
            or item.get("corrected_term")
            or item.get("name")
            or item.get("diagnosis")
            or item.get("label")
            or ""
        )
        code = (
            item.get("code")
            or item.get("icd11")
            or item.get("icd_11")
            or item.get("icd")
            or ""
        )
        if item.get("primary") is True:
            role = "primary"
        elif item.get("primary") is False:
            role = "secondary"
        else:
            role = str(
                item.get("role")
                or item.get("type")
                or item.get("level")
                or "unspecified"
            ).lower()
            if "primary" in role:
                role = "primary"
            elif "secondary" in role:
                role = "secondary"
        if name or code:
            entries.append(
                {
                    "name": str(name).strip(),
                    "icd11": str(code).strip(),
                    "title": str(item.get("title") or "").strip(),
                    "role": role,
                }
            )
    if not entries and raw_diagnosis(raw):
        entries.append(
            {
                "name": raw_diagnosis(raw),
                "icd11": "",
                "title": "",
                "role": "primary",
            }
        )
    if entries and not any(item["role"] == "primary" for item in entries):
        entries[0]["role"] = "primary"
    return entries


def cancer_aliases(name: str) -> list[str]:
    match = re.match(
        r"(.+?)\s+(cancer|carcinoma|adenocarcinoma)\b",
        name,
        flags=re.I,
    )
    if not match:
        return []
    organ = match.group(1).strip()
    return [f"{organ} {variant}" for variant in ("cancer", "carcinoma", "adenocarcinoma")]


def leakage_terms(entries: list[dict[str, str]], raw_diagnosis: str) -> list[str]:
    terms: list[str] = []
    if raw_diagnosis:
        terms.append(raw_diagnosis.strip())
        for part in re.split(r"[;/|]+|\band\b", raw_diagnosis, flags=re.I):
            if len(part.strip()) >= 6:
                terms.append(part.strip())
    for entry in entries:
        if entry["name"]:
            terms.append(entry["name"])
            terms.extend(cancer_aliases(entry["name"]))
        if entry.get("title"):
            terms.append(entry["title"])
            terms.extend(cancer_aliases(entry["title"]))
        for token in re.findall(r"[A-Za-z][A-Za-z\-]{5,}", entry["name"]):
            if token.lower() not in STOPWORDS:
                terms.append(token)
    unique: list[str] = []
    seen: set[str] = set()
    for term in terms:
        normalized = re.sub(r"\s+", " ", term).strip().lower()
        if len(normalized) < 6 or normalized in seen:
            continue
        seen.add(normalized)
        unique.append(term.strip())
    return unique


def find_leakage(text: str, terms: list[str]) -> list[str]:
    hits: list[str] = []
    haystack = text.lower()
    for term in terms:
        pattern = re.escape(term.lower())
        if " " in term or "-" in term:
            if re.search(pattern, haystack):
                hits.append(term)
        elif re.search(rf"\b{pattern}\b", haystack):
            hits.append(term)
    for marker in POST_DIAGNOSIS_MARKERS:
        if marker in haystack:
            hits.append(marker)
    return sorted(set(hits), key=str.lower)


def copy_selected_images(
    records: list[dict[str, Any]],
    raw_dir: Path,
    dest_dir: Path,
) -> tuple[list[Path], list[str], int]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    copied: list[Path] = []
    modalities: list[str] = []
    total_bytes = 0
    for record in records:
        if len(copied) >= MAX_IMAGES:
            break
        suffix = Path(record["path"]).suffix.lower()
        if suffix not in SUPPORTED_IMAGE_SUFFIXES:
            continue
        source = download_file(record["path"], raw_dir)
        if not source.is_file():
            continue
        size = source.stat().st_size
        if total_bytes + size > MAX_TOTAL_BYTES:
            break
        dest = dest_dir / f"{len(copied) + 1:02d}{suffix}"
        shutil.copy2(source, dest)
        copied.append(dest)
        total_bytes += size
        modalities.extend(record["modalities"])
    return copied, sorted(set(modalities)), total_bytes


def relative_to(path: Path, start: Path) -> str:
    return path.resolve().relative_to(start.resolve()).as_posix()


def dump_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        yaml.safe_dump(data, stream, sort_keys=False, allow_unicode=True, width=100)


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    raw_dir = root / "datasets" / "raw" / "medreamm"
    output_name = args.output_name or f"medreamm_pilot{args.limit}"
    if Path(output_name).name != output_name or output_name in {".", ".."}:
        raise PrepareError("--output-name must be a single safe folder name")
    processed_dir = root / "datasets" / "processed" / output_name
    raw_dir.mkdir(parents=True, exist_ok=True)
    if processed_dir.exists():
        if not args.overwrite:
            raise PrepareError(
                f"Processed cohort already exists: {processed_dir}. "
                "Use --overwrite to replace it."
            )
        shutil.rmtree(processed_dir)
    processed_dir.mkdir(parents=True, exist_ok=True)

    print(f"Downloading {REPO_ID} benchmark.jsonl")
    jsonl_path = download_file("benchmark.jsonl", raw_dir)
    raw_cases = load_cases(jsonl_path)
    print(f"Loaded {len(raw_cases)} MedReaMM cases")

    eligible: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_cases, start=1):
        cid = case_id(raw, index)
        history = history_text(raw)
        images = image_records(raw)
        gold = diagnosis_entries(raw)
        terms = leakage_terms(gold, raw_diagnosis(raw))
        history_hits = find_leakage(history, terms)
        filename_hits = find_leakage(
            " ".join(Path(item["path"]).name for item in images), terms
        )
        reasons: list[str] = []
        if len(history) < MIN_HISTORY_CHARS:
            reasons.append(f"history_too_short:{len(history)}")
        if not gold:
            reasons.append("missing_gold_diagnosis")
        if not images:
            reasons.append("no_images")
        if history_hits:
            reasons.append("history_leakage:" + "; ".join(history_hits[:6]))
        if filename_hits:
            reasons.append("filename_leakage:" + "; ".join(filename_hits[:4]))
        usable_images = [
            item
            for item in images
            if Path(item["path"]).suffix.lower() in SUPPORTED_IMAGE_SUFFIXES
        ]
        if images and not usable_images:
            reasons.append("unsupported_image_format")
        record = {
            "id": cid,
            "raw": raw,
            "history": history,
            "images": usable_images,
            "gold": gold,
            "terms": terms,
            "classification": str(raw.get("classification") or "unspecified"),
            "year": raw.get("year"),
            "reasons": reasons,
        }
        if reasons:
            rejected.append(record)
        else:
            eligible.append(record)

    eligible.sort(
        key=lambda item: (
            stable_bucket(item["id"], args.seed, 10_000),
            item["id"],
        )
    )
    selected: list[dict[str, Any]] = []
    used_classes: dict[str, int] = defaultdict(int)
    # Prefer spreading classifications before filling remaining slots.
    for prefer_new_class in (True, False):
        for item in eligible:
            if item in selected:
                continue
            if prefer_new_class and used_classes[item["classification"]] > 0:
                continue
            selected.append(item)
            used_classes[item["classification"]] += 1
            if len(selected) >= args.limit:
                break
        if len(selected) >= args.limit:
            break

    if len(selected) < args.limit:
        raise PrepareError(
            f"Only {len(selected)} leakage-safe cases available; needed {args.limit}"
        )

    manifest_cases: list[dict[str, Any]] = []
    audit_rows: list[dict[str, Any]] = []
    for item in selected:
        case_dir = processed_dir / item["id"]
        image_dir = case_dir / "images"
        history_path = case_dir / "history.txt"
        history_path.parent.mkdir(parents=True, exist_ok=True)
        history_path.write_text(item["history"] + "\n", encoding="utf-8")
        print(f"Downloading images for {item['id']}")
        copied, modalities, total_bytes = copy_selected_images(
            item["images"], raw_dir, image_dir
        )
        if not copied:
            raise PrepareError(f"No usable images downloaded for {item['id']}")
        gold_path = case_dir / "gold.json"
        gold_path.write_text(
            json.dumps(
                {
                    "diagnosis": raw_diagnosis(item["raw"]),
                    "standardized_diagnosis": item["gold"],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        manifest_cases.append(
            {
                "id": item["id"],
                "text_file": relative_to(history_path, processed_dir),
                "documents": [],
                "images": [relative_to(path, processed_dir) for path in copied],
                "gold": {"diagnoses": item["gold"]},
                "metadata": {
                    "source": REPO_ID,
                    "source_id": item["raw"].get("pmid") or item["id"],
                    "year": item["raw"].get("year"),
                    "classification": item["classification"],
                    "modalities": modalities,
                    "image_count": len(copied),
                    "history_chars": len(item["history"]),
                    "total_file_bytes": total_bytes,
                    "captions_included": False,
                },
            }
        )
        audit_rows.append(
            {
                "id": item["id"],
                "classification": item["classification"],
                "images": len(copied),
                "modalities": modalities,
                "history_chars": len(item["history"]),
                "primary": next(
                    (
                        diagnosis["name"]
                        for diagnosis in item["gold"]
                        if diagnosis["role"] == "primary"
                    ),
                    item["gold"][0]["name"],
                ),
                "leakage_screen": "pass_automatic",
                "manual_review": "pending",
            }
        )

    manifest = {
        "dataset": {
            "name": "MedReaMM",
            "version": output_name,
            "source": f"https://huggingface.co/datasets/{REPO_ID}",
            "selection": {
                "limit": args.limit,
                "seed": args.seed,
                "eligible": len(eligible),
                "rejected": len(rejected),
                "captions_included": False,
            },
        },
        "cases": manifest_cases,
    }
    manifest_path = processed_dir / "manifest.yaml"
    dump_yaml(manifest_path, manifest)
    dump_yaml(
        processed_dir / "audit.yaml",
        {
            "manual_review_required": True,
            "rule": (
                "Read history.txt and look at the images. Reject the case if the "
                "final diagnosis, its synonyms, or post-diagnosis outcome are visible."
            ),
            "selected": audit_rows,
            "rejected_preview": [
                {
                    "id": item["id"],
                    "classification": item["classification"],
                    "reasons": item["reasons"],
                }
                for item in rejected[:50]
            ],
        },
    )
    (processed_dir / "rejected.jsonl").write_text(
        "".join(json.dumps({"id": item["id"], "reasons": item["reasons"]}) + "\n" for item in rejected),
        encoding="utf-8",
    )

    print(f"Eligible leakage-safe cases: {len(eligible)} / {len(raw_cases)}")
    print(f"Rejected: {len(rejected)}")
    print(f"Wrote {len(manifest_cases)} cases to {manifest_path}")
    print("Manual review is still required for the first 10 cases.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PrepareError as error:
        print(f"Prepare error: {error}")
        raise SystemExit(2) from error
