"""Generate a reproducible, synthetic document-image benchmark.

The generated files contain no real patient data. Binary artifacts are written
under generated/ and are intentionally ignored by git.
"""

from __future__ import annotations

import argparse
import os
import random
import textwrap
from pathlib import Path
from typing import Any

import yaml
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas


PAGE_SIZE = (1240, 1754)
MARGIN = 105
SEED = 20260921


class GenerationError(RuntimeError):
    """Raised when benchmark assets cannot be generated safely."""


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=root / "cases.yaml")
    parser.add_argument("--output", type=Path, default=root / "generated")
    parser.add_argument(
        "--medreamm-manifest",
        type=Path,
        default=(
            root.parent
            / "multimodal_beta"
            / "datasets"
            / "processed"
            / "medreamm_pilot25"
            / "manifest.yaml"
        ),
        help="Optional source of reviewed real-world routing controls.",
    )
    parser.add_argument(
        "--medreamm-labels",
        type=Path,
        default=root / "medreamm_labels.yaml",
    )
    parser.add_argument("--medreamm-assets", type=int, default=12)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise GenerationError(f"File does not exist: {path}")
    with path.open("r", encoding="utf-8") as stream:
        data = yaml.safe_load(stream)
    if not isinstance(data, dict):
        raise GenerationError(f"Expected a YAML object in {path}")
    return data


def font(size: int, *, italic: bool = False, bold: bool = False) -> ImageFont.ImageFont:
    if bold:
        names = ("DejaVuSans-Bold.ttf", "arialbd.ttf")
    elif italic:
        names = (
            "Inkfree.ttf",
            "segoepr.ttf",
            "DejaVuSans-Oblique.ttf",
            "ariali.ttf",
        )
    else:
        names = ("DejaVuSans.ttf", "arial.ttf")
    candidates = [
        Path(name)
        for name in names
    ] + [
        Path("C:/Windows/Fonts") / name
        for name in names
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(str(candidate), size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


def wrapped_lines(
    draw: ImageDraw.ImageDraw,
    value: str,
    selected_font: ImageFont.ImageFont,
    width: int,
) -> list[str]:
    words = value.split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        candidate = " ".join([*current, word])
        if current and draw.textlength(candidate, font=selected_font) > width:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return lines or [""]


def draw_medical_panel(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    seed: int,
) -> None:
    """Draw a synthetic radiograph-like panel, never a real medical image."""
    rng = random.Random(seed)
    left, top, right, bottom = box
    draw.rounded_rectangle(box, radius=18, fill="#111820", outline="#526170", width=4)
    center = (left + right) // 2
    panel_height = bottom - top
    for side in (-1, 1):
        lung_box = (
            center + side * 25 + (side < 0) * -225,
            top + 55,
            center + side * 220,
            bottom - 70,
        )
        if side < 0:
            lung_box = (center - 225, top + 55, center - 25, bottom - 70)
        draw.ellipse(lung_box, fill="#61707b", outline="#a8b5bd", width=3)
    draw.line((center, top + 45, center, bottom - 45), fill="#c8d0d5", width=12)
    for index in range(8):
        y = top + 75 + index * max(20, panel_height // 10)
        curve = 22 + rng.randint(-4, 4)
        draw.arc((left + 35, y, right - 35, y + curve * 4), 190, 350, fill="#8998a2", width=3)
    draw.text((left + 18, top + 14), "SYNTHETIC IMAGE", font=font(18, bold=True), fill="#d8e1e6")


def render_report_page(
    report: dict[str, Any],
    *,
    seed: int,
    handwritten: bool = False,
) -> Image.Image:
    image = Image.new("RGB", PAGE_SIZE, "white")
    draw = ImageDraw.Draw(image)
    rng = random.Random(seed)
    body_font = font(33, italic=handwritten)
    heading_font = font(39, italic=handwritten, bold=not handwritten)
    title_font = font(47, bold=True)
    small_font = font(24)

    draw.rectangle((0, 0, PAGE_SIZE[0], 74), fill="#16324f")
    draw.text(
        (MARGIN, 20),
        "SYNTHETIC CLINICAL REPORT — NO REAL PATIENT",
        font=small_font,
        fill="white",
    )
    y = 118
    draw.text((MARGIN, y), str(report["title"]), font=title_font, fill="#16222e")
    y += 72
    draw.text((MARGIN, y), f"Report date: {report['date']}", font=body_font, fill="#33485b")
    y += 68
    draw.line((MARGIN, y, PAGE_SIZE[0] - MARGIN, y), fill="#b7c1ca", width=3)
    y += 40

    content_right = PAGE_SIZE[0] - MARGIN
    if report.get("include_mixed"):
        content_right = 720
        draw_medical_panel(draw, (755, 300, 1135, 930), seed)

    max_width = content_right - MARGIN
    for section, entries in (report.get("sections") or {}).items():
        draw.text((MARGIN, y), str(section), font=heading_font, fill="#16324f")
        y += 57
        for entry in entries:
            lines = wrapped_lines(draw, f"• {entry}", body_font, max_width)
            for line in lines:
                jitter = rng.randint(-2, 2) if handwritten else 0
                draw.text((MARGIN + 16 + jitter, y), line, font=body_font, fill="#202932")
                y += 48
            y += 9
        y += 20

    if report.get("include_chart"):
        chart_top = max(y + 20, 1110)
        chart_bottom = min(chart_top + 350, PAGE_SIZE[1] - 100)
        chart_box = (MARGIN, chart_top, PAGE_SIZE[0] - MARGIN, chart_bottom)
        draw.rectangle(chart_box, outline="#657786", width=3)
        draw.text(
            (MARGIN + 20, chart_top + 15),
            "Synthetic trend — values not to scale",
            font=small_font,
            fill="#33485b",
        )
        points = []
        for index, value in enumerate((0.72, 0.48, 0.61, 0.31, 0.42)):
            x = MARGIN + 80 + index * 210
            y_point = chart_top + 90 + int(value * (chart_bottom - chart_top - 130))
            points.append((x, y_point))
        draw.line(points, fill="#b8324a", width=7, joint="curve")
        for point in points:
            draw.ellipse((point[0] - 8, point[1] - 8, point[0] + 8, point[1] + 8), fill="#b8324a")

    draw.text(
        (MARGIN, PAGE_SIZE[1] - 58),
        "Generated benchmark artifact. Not for clinical use.",
        font=small_font,
        fill="#687681",
    )
    return image


def combine_pages(pages: list[Image.Image]) -> Image.Image:
    if not pages:
        raise GenerationError("Cannot combine an empty page list")
    if len(pages) == 1:
        return pages[0].copy()
    gap = 30
    output = Image.new(
        "RGB",
        (max(page.width for page in pages), sum(page.height for page in pages) + gap * (len(pages) - 1)),
        "#c5c8cc",
    )
    y = 0
    for page in pages:
        output.paste(page, (0, y))
        y += page.height + gap
    return output


def make_scan(page: Image.Image) -> Image.Image:
    scan = page.convert("L").filter(ImageFilter.GaussianBlur(radius=0.65))
    scan = ImageEnhance.Contrast(scan).enhance(0.92)
    return scan.convert("RGB")


def make_photo(page: Image.Image, seed: int) -> Image.Image:
    rng = random.Random(seed)
    max_height = 1620
    scale = min(1.0, max_height / page.height)
    resized = page.resize(
        (int(page.width * scale), int(page.height * scale)),
        Image.Resampling.LANCZOS,
    )
    rotated = resized.rotate(rng.uniform(-3.8, 3.8), resample=Image.Resampling.BICUBIC, expand=True)
    desk = Image.new("RGB", (rotated.width + 260, rotated.height + 260), "#6d5744")
    shadow = Image.new("RGBA", rotated.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rectangle((25, 25, rotated.width - 1, rotated.height - 1), fill=(0, 0, 0, 95))
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    desk.paste(shadow, (105, 105), shadow)
    desk.paste(rotated, (90, 80))
    return ImageEnhance.Brightness(desk).enhance(0.94)


def write_native_pdf(path: Path, reports: list[dict[str, Any]]) -> None:
    pdf = canvas.Canvas(str(path), pagesize=A4)
    page_width, page_height = A4
    for report in reports:
        y = page_height - 54
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawString(50, y, "SYNTHETIC CLINICAL REPORT — NO REAL PATIENT")
        y -= 34
        pdf.setFont("Helvetica-Bold", 18)
        pdf.drawString(50, y, str(report["title"]))
        y -= 25
        pdf.setFont("Helvetica", 11)
        pdf.drawString(50, y, f"Report date: {report['date']}")
        y -= 30
        for section, entries in (report.get("sections") or {}).items():
            pdf.setFont("Helvetica-Bold", 13)
            pdf.drawString(50, y, str(section))
            y -= 20
            pdf.setFont("Helvetica", 11)
            for entry in entries:
                lines = textwrap.wrap(f"• {entry}", width=86)
                for line in lines:
                    if y < 55:
                        pdf.showPage()
                        y = page_height - 55
                        pdf.setFont("Helvetica", 11)
                    pdf.drawString(62, y, line)
                    y -= 16
                y -= 5
            y -= 10
        pdf.setFont("Helvetica-Oblique", 8)
        footer = "Generated benchmark artifact. Not for clinical use."
        pdf.drawString(50, 28, footer[: int((page_width - 100) / stringWidth("M", "Helvetica", 8))])
        pdf.showPage()
    pdf.save()


def relative_path(path: Path, manifest_dir: Path) -> str:
    return Path(os.path.relpath(path.resolve(), manifest_dir.resolve())).as_posix()


def product_case(
    case: dict[str, Any],
    case_id: str,
    artifact_type: str,
    path: Path,
    manifest_dir: Path,
    *,
    image: bool,
) -> dict[str, Any]:
    return {
        "id": f"{case_id}-{artifact_type}",
        "text": "",
        "documents": [] if image else [relative_path(path, manifest_dir)],
        "images": [relative_path(path, manifest_dir)] if image else [],
        "gold": case["gold"],
        "metadata": {
            "source_case_id": case_id,
            "artifact_type": artifact_type,
            "synthetic": True,
            "expected_facts": [
                str(value)
                for value in case["expected_facts"]
            ],
        },
    }


def medreamm_assets(
    manifest_path: Path,
    labels_path: Path,
    limit: int,
    output_dir: Path,
) -> list[dict[str, Any]]:
    if limit <= 0 or not manifest_path.is_file() or not labels_path.is_file():
        return []
    manifest = load_yaml(manifest_path)
    labels = load_yaml(labels_path)
    cases_by_id = {
        str(case.get("id")): case
        for case in manifest.get("cases") or []
    }
    candidates: list[dict[str, Any]] = []
    for label in (labels.get("assets") or [])[:limit]:
        source_case_id = str(label.get("case_id") or "")
        case = cases_by_id.get(source_case_id)
        if not case:
            raise GenerationError(
                f"Reviewed MedReaMM case is absent from manifest: {source_case_id}"
            )
        images = case.get("images") or []
        image_index = int(label.get("image_index") or 0)
        if image_index < 0 or image_index >= len(images):
            raise GenerationError(
                f"Invalid image_index for MedReaMM case {source_case_id}"
            )
        modalities = [str(value) for value in (case.get("metadata") or {}).get("modalities") or []]
        source_path = (manifest_path.parent / str(images[image_index])).resolve()
        if not source_path.is_file():
            raise GenerationError(f"Reviewed MedReaMM image is missing: {source_path}")
        expected_class = str(label.get("expected_class") or "")
        if expected_class not in {"document_image", "medical_image", "mixed", "unknown"}:
            raise GenerationError(
                f"Invalid expected_class for MedReaMM case {source_case_id}"
            )
        candidates.append(
            {
                "id": f"medreamm-{case['id']}-{image_index + 1:02d}",
                "path": relative_path(source_path, output_dir),
                "expected_class": expected_class,
                "expected_route": (
                    "ocr_plus_image"
                    if expected_class in {"document_image", "mixed"}
                    else "direct_vision"
                ),
                "source": "MedReaMM MIT",
                "metadata": {
                    "modalities": modalities,
                    "synthetic": False,
                    "review_note": str(label.get("note") or ""),
                },
            }
        )
    return candidates


def generate_case(
    case: dict[str, Any],
    output_dir: Path,
    product_manifest_dir: Path,
    classification_assets: list[dict[str, Any]],
    product_cases: list[dict[str, Any]],
    index: int,
) -> None:
    case_id = str(case["id"])
    case_dir = output_dir / "assets" / case_id
    case_dir.mkdir(parents=True, exist_ok=True)
    reports = case.get("reports") or []
    if not reports:
        raise GenerationError(f"Case {case_id} has no reports")

    pages = [
        render_report_page(report, seed=SEED + index * 100 + page_index)
        for page_index, report in enumerate(reports)
    ]
    handwritten_pages = [
        render_report_page(
            report,
            seed=SEED + index * 100 + page_index,
            handwritten=True,
        )
        for page_index, report in enumerate(reports)
    ]
    combined = combine_pages(pages)
    handwritten = combine_pages(handwritten_pages)
    scan = make_scan(combined)
    photo = make_photo(scan, SEED + index)

    native_pdf = case_dir / "native.pdf"
    scanned_pdf = case_dir / "scanned.pdf"
    scan_path = case_dir / "scan.png"
    photo_path = case_dir / "photo.jpg"
    handwritten_path = case_dir / "handwritten-simulated.jpg"
    write_native_pdf(native_pdf, reports)
    scan.save(scan_path, optimize=True)
    photo.save(photo_path, quality=88, optimize=True)
    handwritten.save(handwritten_path, quality=90, optimize=True)
    scan_pages = [make_scan(page) for page in pages]
    scan_pages[0].save(
        scanned_pdf,
        "PDF",
        resolution=150,
        save_all=True,
        append_images=scan_pages[1:],
    )

    artifacts = (
        ("native-pdf", native_pdf, False),
        ("scanned-pdf", scanned_pdf, False),
        ("scan-image", scan_path, True),
        ("photo-image", photo_path, True),
        ("handwritten-image", handwritten_path, True),
    )
    for artifact_type, path, is_image in artifacts:
        product_cases.append(
            product_case(
                case,
                case_id,
                artifact_type,
                path,
                product_manifest_dir,
                image=is_image,
            )
        )

    for asset_type, path in (
        ("scan", scan_path),
        ("photo", photo_path),
        ("handwritten_simulated", handwritten_path),
    ):
        classification_assets.append(
            {
                "id": f"{case_id}-{asset_type}",
                "path": relative_path(path, product_manifest_dir),
                "expected_class": "document_image",
                "expected_route": "ocr_plus_image",
                "source": "synthetic",
                "metadata": {"source_case_id": case_id, "artifact_type": asset_type},
            }
        )

    if any(report.get("include_mixed") for report in reports):
        mixed_path = case_dir / "mixed.jpg"
        combined.save(mixed_path, quality=90, optimize=True)
        classification_assets.append(
            {
                "id": f"{case_id}-mixed",
                "path": relative_path(mixed_path, product_manifest_dir),
                "expected_class": "mixed",
                "expected_route": "ocr_plus_image",
                "source": "synthetic",
                "metadata": {"source_case_id": case_id, "artifact_type": "mixed"},
            }
        )


def main() -> int:
    args = parse_args()
    output_dir = args.output.resolve()
    if output_dir.exists() and any(output_dir.iterdir()) and not args.overwrite:
        raise GenerationError(
            f"{output_dir} is not empty. Use --overwrite to regenerate it."
        )
    if output_dir.exists() and args.overwrite:
        import shutil

        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    source = load_yaml(args.cases.resolve())
    cases = source.get("cases") or []
    if not cases:
        raise GenerationError("cases.yaml requires a non-empty cases list")

    classification_assets: list[dict[str, Any]] = []
    product_cases: list[dict[str, Any]] = []
    for index, case in enumerate(cases):
        generate_case(
            case,
            output_dir,
            output_dir,
            classification_assets,
            product_cases,
            index,
        )

    classification_assets.extend(
        medreamm_assets(
            args.medreamm_manifest.resolve(),
            args.medreamm_labels.resolve(),
            args.medreamm_assets,
            output_dir,
        )
    )
    classification_manifest = {
        "dataset": {
            "name": source["dataset"]["name"],
            "version": source["dataset"]["version"],
            "task": "document_image_routing",
            "classes": ["document_image", "medical_image", "mixed", "unknown"],
            "ocr_confidence_threshold": 0.9,
            "medreamm_manifest": str(args.medreamm_manifest.resolve()),
            "medreamm_labels": str(args.medreamm_labels.resolve()),
        },
        "assets": classification_assets,
    }
    product_manifest = {
        "dataset": {
            "name": source["dataset"]["name"],
            "version": source["dataset"]["version"],
            "task": "end_to_end_document_fidelity",
            "synthetic": True,
        },
        "cases": product_cases,
    }
    with (output_dir / "classification_manifest.yaml").open("w", encoding="utf-8") as stream:
        yaml.safe_dump(classification_manifest, stream, sort_keys=False, allow_unicode=True)
    with (output_dir / "product_manifest.yaml").open("w", encoding="utf-8") as stream:
        yaml.safe_dump(product_manifest, stream, sort_keys=False, allow_unicode=True)

    print(f"Generated {len(product_cases)} product cases in {output_dir}")
    print(f"Generated {len(classification_assets)} classification assets")
    if not any(asset["expected_class"] == "medical_image" for asset in classification_assets):
        print("WARNING: no reviewed medical-image controls were available")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
