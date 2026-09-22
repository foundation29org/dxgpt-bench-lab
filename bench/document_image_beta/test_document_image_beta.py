"""Focused tests for the synthetic document-image benchmark."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from evaluate import classification_metrics, product_metrics  # noqa: E402
from generate_dataset import generate_case, load_yaml  # noqa: E402
from run_classifier import route_for_prediction  # noqa: E402


EVALUATE_V4_PATH = ROOT.parent / "multimodal_beta" / "evaluate_v4.py"
EVALUATE_V4_SPEC = importlib.util.spec_from_file_location(
    "document_benchmark_evaluate_v4",
    EVALUATE_V4_PATH,
)
if EVALUATE_V4_SPEC is None or EVALUATE_V4_SPEC.loader is None:
    raise RuntimeError(f"Cannot load {EVALUATE_V4_PATH}")
EVALUATE_V4 = importlib.util.module_from_spec(EVALUATE_V4_SPEC)
EVALUATE_V4_SPEC.loader.exec_module(EVALUATE_V4)


class RoutingTests(unittest.TestCase):
    def test_only_high_confidence_documents_enable_ocr(self) -> None:
        self.assertEqual(
            route_for_prediction("document_image", 0.95, 0.9),
            "ocr_plus_image",
        )
        self.assertEqual(
            route_for_prediction("document_image", 0.89, 0.9),
            "direct_vision",
        )
        self.assertEqual(
            route_for_prediction("medical_image", 0.99, 0.9),
            "direct_vision",
        )
        self.assertEqual(
            route_for_prediction("mixed", 0.99, 0.9),
            "ocr_plus_image",
        )
        self.assertEqual(
            route_for_prediction("mixed", 0.80, 0.9),
            "direct_vision",
        )

    def test_v1_only_ocr_routes_consistent_text_only_images(self) -> None:
        document = {
            "has_document_text": True,
            "has_medical_visual": False,
        }
        mixed = {
            "has_document_text": True,
            "has_medical_visual": True,
        }

        self.assertEqual(
            route_for_prediction(
                "document_only", 0.95, 0.9, "v1", document
            ),
            "ocr_text",
        )
        self.assertEqual(
            route_for_prediction(
                "document_only", 0.95, 0.9, "v1", mixed
            ),
            "direct_vision",
        )
        self.assertEqual(
            route_for_prediction(
                "contains_medical_visual", 0.99, 0.9, "v1", mixed
            ),
            "direct_vision",
        )

    def test_safety_metrics_fail_on_medical_image_ocr(self) -> None:
        records = [
            {
                "id": "document",
                "status": "success",
                "expected_class": "document_image",
                "predicted_class": "document_image",
                "expected_route": "ocr_plus_image",
                "predicted_route": "ocr_plus_image",
                "latency_seconds": 1,
            },
            {
                "id": "medical",
                "status": "success",
                "expected_class": "medical_image",
                "predicted_class": "document_image",
                "expected_route": "direct_vision",
                "predicted_route": "ocr_plus_image",
                "latency_seconds": 1,
            },
        ]

        metrics = classification_metrics(records)

        self.assertFalse(metrics["passed"])
        self.assertEqual(metrics["unsafe_medical_ocr_rate"], 1.0)
        self.assertEqual(metrics["unsafe_medical_ids"], ["medical"])

    def test_perfect_safe_routes_pass_acceptance_gates(self) -> None:
        records = [
            {
                "id": "document",
                "status": "success",
                "expected_class": "document_image",
                "predicted_class": "document_image",
                "expected_route": "ocr_plus_image",
                "predicted_route": "ocr_plus_image",
                "latency_seconds": 1,
            },
            {
                "id": "medical",
                "status": "success",
                "expected_class": "medical_image",
                "predicted_class": "medical_image",
                "expected_route": "direct_vision",
                "predicted_route": "direct_vision",
                "latency_seconds": 1,
            },
            {
                "id": "mixed",
                "status": "success",
                "expected_class": "mixed",
                "predicted_class": "mixed",
                "expected_route": "ocr_plus_image",
                "predicted_route": "ocr_plus_image",
                "latency_seconds": 1,
            },
        ]

        metrics = classification_metrics(records)

        self.assertTrue(metrics["passed"])

    def test_v1_treats_mixed_images_as_direct_vision(self) -> None:
        records = [
            {
                "id": "document",
                "status": "success",
                "policy": "v1",
                "expected_class": "document_only",
                "predicted_class": "document_only",
                "expected_route": "ocr_text",
                "predicted_route": "ocr_text",
                "latency_seconds": 1,
            },
            {
                "id": "mixed",
                "status": "success",
                "policy": "v1",
                "expected_class": "contains_medical_visual",
                "predicted_class": "contains_medical_visual",
                "expected_route": "direct_vision",
                "predicted_route": "direct_vision",
                "latency_seconds": 1,
            },
        ]

        metrics = classification_metrics(records)

        self.assertTrue(metrics["passed"])
        self.assertEqual(metrics["route_accuracy"], 1.0)
        self.assertEqual(metrics["unsafe_medical_ocr_rate"], 0.0)

    def test_v1_applies_mixed_source_label_to_all_renderings(self) -> None:
        records = [
            {
                "id": "case-scan",
                "status": "success",
                "policy": "v1",
                "expected_class": "document_only",
                "predicted_class": "contains_medical_visual",
                "expected_route": "ocr_text",
                "predicted_route": "direct_vision",
                "latency_seconds": 1,
                "metadata": {
                    "source_case_id": "mixed-case",
                    "artifact_type": "scan",
                },
            },
            {
                "id": "case-mixed",
                "status": "success",
                "policy": "v1",
                "expected_class": "contains_medical_visual",
                "predicted_class": "contains_medical_visual",
                "expected_route": "direct_vision",
                "predicted_route": "direct_vision",
                "latency_seconds": 1,
                "metadata": {
                    "source_case_id": "mixed-case",
                    "artifact_type": "mixed",
                },
            },
        ]

        metrics = classification_metrics(records)

        self.assertEqual(metrics["route_accuracy"], 1.0)
        self.assertEqual(
            metrics["per_class"]["contains_medical_visual"]["support"],
            2,
        )

    def test_product_metrics_preserve_numeric_facts(self) -> None:
        records = [
            {
                "case_id": "case-scan",
                "status": "success",
                "metadata": {
                    "artifact_type": "scan-image",
                    "expected_facts": ["Hemoglobin 8.4 g/dL", "MCV 68 fL"],
                },
                "http_response": {
                    "description": "Hemoglobin: 8.4 g/dL. MCV was 68 fL."
                },
            }
        ]

        metrics = product_metrics(records)

        self.assertEqual(metrics["technical_success_rate"], 1.0)
        self.assertEqual(metrics["fact_recall_mean"], 1.0)


class StrictEvaluatorTests(unittest.TestCase):
    def test_empty_differential_skips_the_llm_judge(self) -> None:
        evaluator = EVALUATE_V4.StrictMultimodalEvaluator.__new__(
            EVALUATE_V4.StrictMultimodalEvaluator
        )

        result = evaluator._get_llm_judgment("Reference diagnosis", [])

        self.assertEqual(result, {"position": None})


class GenerationTests(unittest.TestCase):
    def test_generates_all_core_artifacts_for_one_case(self) -> None:
        case = load_yaml(ROOT / "cases.yaml")["cases"][0]
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            classification_assets = []
            product_cases = []

            generate_case(
                case,
                output,
                output,
                classification_assets,
                product_cases,
                0,
            )

            case_dir = output / "assets" / case["id"]
            self.assertTrue((case_dir / "native.pdf").is_file())
            self.assertTrue((case_dir / "scanned.pdf").is_file())
            self.assertTrue((case_dir / "scan.png").is_file())
            self.assertTrue((case_dir / "photo.jpg").is_file())
            self.assertTrue((case_dir / "handwritten-simulated.jpg").is_file())
            self.assertEqual(len(product_cases), 5)
            self.assertEqual(len(classification_assets), 3)


if __name__ == "__main__":
    unittest.main()
