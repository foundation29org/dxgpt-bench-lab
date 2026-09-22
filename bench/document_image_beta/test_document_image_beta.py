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
from generate_dataset import (  # noqa: E402
    build_mixed_hybrid_cases,
    generate_case,
    load_yaml,
)
from run_classifier import expected_for_policy, route_for_prediction  # noqa: E402


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

    def test_v1_routes_document_text_without_dropping_medical_visuals(self) -> None:
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
            "ocr_plus_image",
        )
        self.assertEqual(
            route_for_prediction(
                "contains_medical_visual", 0.89, 0.9, "v1", mixed
            ),
            "direct_vision",
        )

    def test_v1_gold_routes_standalone_mixed_assets_to_ocr_plus_image(self) -> None:
        self.assertEqual(
            expected_for_policy({"expected_class": "mixed"}, "v1"),
            ("contains_medical_visual", "ocr_plus_image"),
        )
        self.assertEqual(
            expected_for_policy({"expected_class": "medical_image"}, "v1"),
            ("contains_medical_visual", "direct_vision"),
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

    def test_v1_treats_mixed_images_as_ocr_plus_vision(self) -> None:
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
                "expected_route": "ocr_plus_image",
                "predicted_route": "ocr_plus_image",
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
                "predicted_route": "ocr_plus_image",
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
                "expected_route": "ocr_plus_image",
                "predicted_route": "ocr_plus_image",
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

    def test_product_metrics_measure_v1_image_routes(self) -> None:
        records = [
            {
                "case_id": "document-image",
                "status": "success",
                "duration_seconds": 10,
                "inputs": {"images": ["document.png"]},
                "metadata": {
                    "source_case_id": "document-case",
                    "artifact_type": "scan-image",
                    "expected_facts": [],
                },
                "http_response": {
                    "imageRouting": [{
                        "route": "ocr_text",
                        "ocr": {"status": "succeeded"},
                    }],
                },
                "final_response": {"data": []},
            },
            {
                "case_id": "mixed-image",
                "status": "success",
                "duration_seconds": 12,
                "inputs": {"images": ["mixed.png"]},
                "metadata": {
                    "source_case_id": "mixed-case",
                    "artifact_type": "photo-image",
                    "expected_facts": [],
                },
                "http_response": {
                    "imageRouting": [{
                        "route": "vision",
                        "ocrTextUsed": True,
                        "ocr": {"status": "succeeded"},
                    }],
                },
                "final_response": {"data": []},
            },
        ]

        metrics = product_metrics(records, {"mixed-case"})

        self.assertEqual(metrics["image_route_accuracy"], 1.0)
        self.assertEqual(metrics["document_image_ocr_success"], 1.0)
        self.assertEqual(metrics["mixed_image_vision_recall"], 1.0)
        self.assertEqual(metrics["mixed_image_hybrid_success"], 1.0)
        self.assertEqual(metrics["unsafe_mixed_image_ids"], [])


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

    def test_mixed_visual_cases_mark_every_image_route_as_vision(self) -> None:
        cases = load_yaml(ROOT / "cases.yaml")["cases"]
        case = next(
            item for item in cases
            if item["id"] == "community-pneumonia-pattern"
        )
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

            image_cases = [item for item in product_cases if item["images"]]
            self.assertTrue(image_cases)
            self.assertTrue(all(
                item["metadata"]["expected_image_route"] == "vision"
                for item in image_cases
            ))
            self.assertTrue(all(
                item["expected_class"] == "mixed"
                for item in classification_assets
            ))
            hybrid_cases = build_mixed_hybrid_cases(product_cases)
            self.assertEqual(len(hybrid_cases), 3)
            self.assertTrue(all(
                len(item["documents"]) == 1 and len(item["images"]) == 1
                for item in hybrid_cases
            ))
            self.assertTrue(all(
                item["metadata"]["routing_experiment"] == "ocr_plus_image"
                for item in hybrid_cases
            ))


if __name__ == "__main__":
    unittest.main()
