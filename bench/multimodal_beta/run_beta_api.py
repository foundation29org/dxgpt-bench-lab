"""Replay DxGPT beta's multipart + WebPubSub diagnostic flow."""

from __future__ import annotations

import argparse
import copy
import json
import os
import re
import ssl
import threading
import time
import uuid
from contextlib import ExitStack
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
import websocket
import yaml
from dotenv import load_dotenv
from requests_toolbelt.multipart.encoder import MultipartEncoder


MAX_DOCUMENTS = 5
MAX_IMAGES = 5
MAX_TOTAL_BYTES = 20 * 1024 * 1024

# Same allowlist as Server/controllers/all/multimodalInput.js
DOCUMENT_MIME_TYPES = {
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xls": "application/vnd.ms-excel",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".txt": "text/plain",
}
IMAGE_MIME_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".bmp": "image/bmp",
    ".tif": "image/tiff",
    ".tiff": "image/tiff",
    ".webp": "image/webp",
}
PRODUCT_SUMMARY_MIN_CHARS = 1000
ENV_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}")


class EvaluationError(RuntimeError):
    """Raised when a case cannot be submitted or completed safely."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def expand_environment(value: Any) -> Any:
    """Expand ${NAME} and ${NAME:-default} recursively in YAML values."""
    if isinstance(value, dict):
        return {key: expand_environment(item) for key, item in value.items()}
    if isinstance(value, list):
        return [expand_environment(item) for item in value]
    if not isinstance(value, str):
        return value

    def replace(match: re.Match[str]) -> str:
        name, default = match.group(1), match.group(2)
        return os.environ.get(name, default or "")

    return ENV_PATTERN.sub(replace, value)


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise EvaluationError(f"File does not exist: {path}")
    with path.open("r", encoding="utf-8") as stream:
        data = yaml.safe_load(stream)
    if not isinstance(data, dict):
        raise EvaluationError(f"Expected a YAML object in {path}")
    return expand_environment(data)


def resolve_case_path(manifest_dir: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    if not path.is_absolute():
        path = manifest_dir / path
    return path.resolve()


def case_text(case: dict[str, Any], manifest_dir: Path) -> str:
    inline_text = str(case.get("text") or "").strip()
    text_file = case.get("text_file")
    if inline_text and text_file:
        raise EvaluationError(
            f"Case {case.get('id')} must use either text or text_file, not both"
        )
    if text_file:
        path = resolve_case_path(manifest_dir, str(text_file))
        if not path.is_file():
            raise EvaluationError(f"Text file does not exist: {path}")
        return path.read_text(encoding="utf-8").strip()
    return inline_text


def case_files(
    case: dict[str, Any], manifest_dir: Path
) -> tuple[list[Path], list[Path]]:
    documents = [
        resolve_case_path(manifest_dir, str(path))
        for path in case.get("documents") or []
    ]
    images = [
        resolve_case_path(manifest_dir, str(path))
        for path in case.get("images") or []
    ]
    return documents, images


def apply_input_condition(
    raw_cases: list[dict[str, Any]], condition: str
) -> list[dict[str, Any]]:
    """Build paired modality conditions without modifying the manifest."""
    cases = copy.deepcopy(raw_cases)
    image_sources = [
        (str(case.get("id") or ""), list(case.get("images") or []))
        for case in raw_cases
    ]
    for index, case in enumerate(cases):
        source_id = str(case.get("id") or "")
        if condition == "T":
            case["documents"] = []
            case["images"] = []
            image_source_id = None
        elif condition == "I":
            case.pop("text", None)
            case.pop("text_file", None)
            case["documents"] = []
            image_source_id = source_id
        elif condition == "T+shuffled-I":
            if len(cases) < 2:
                raise EvaluationError(
                    "T+shuffled-I requires at least two cases"
                )
            image_source_id, shuffled_images = image_sources[
                (index + 1) % len(image_sources)
            ]
            case["images"] = shuffled_images
        else:
            image_source_id = source_id if case.get("images") else None

        case["_evaluation_condition"] = condition
        case["_image_source_case_id"] = image_source_id
    return cases


def validate_case(case: dict[str, Any], manifest_dir: Path) -> dict[str, Any]:
    case_id = str(case.get("id") or "").strip()
    if not case_id:
        raise EvaluationError("Every case requires a non-empty id")

    text = case_text(case, manifest_dir)
    documents, images = case_files(case, manifest_dir)
    if not text and not documents and not images:
        raise EvaluationError(f"Case {case_id} has no text, documents, or images")
    if len(documents) > MAX_DOCUMENTS:
        raise EvaluationError(
            f"Case {case_id} has {len(documents)} documents; beta allows {MAX_DOCUMENTS}"
        )
    if len(images) > MAX_IMAGES:
        raise EvaluationError(
            f"Case {case_id} has {len(images)} images; beta allows {MAX_IMAGES}"
        )

    total_bytes = 0
    for path in documents:
        if not path.is_file():
            raise EvaluationError(f"Document does not exist: {path}")
        if path.suffix.lower() not in DOCUMENT_MIME_TYPES:
            raise EvaluationError(
                f"Unsupported end-to-end document format for {path.name}"
            )
        total_bytes += path.stat().st_size

    for path in images:
        if not path.is_file():
            raise EvaluationError(f"Image does not exist: {path}")
        if path.suffix.lower() not in IMAGE_MIME_TYPES:
            raise EvaluationError(
                f"Unsupported end-to-end image format for {path.name}"
            )
        total_bytes += path.stat().st_size

    if total_bytes > MAX_TOTAL_BYTES:
        raise EvaluationError(
            f"Case {case_id} uploads {total_bytes / 1024 / 1024:.1f} MB; "
            "beta allows 20 MB in total"
        )

    return {
        "id": case_id,
        "text": text,
        "documents": documents,
        "images": images,
        "gold": case.get("gold") or {},
        "metadata": case.get("metadata") or {},
        "evaluation_condition": case.get("_evaluation_condition") or "manifest",
        "image_source_case_id": case.get("_image_source_case_id"),
        "total_file_bytes": total_bytes,
    }


class BetaApiClient:
    def __init__(self, config: dict[str, Any]) -> None:
        api = config.get("api") or {}
        request_config = config.get("request") or {}
        self.base_url = str(api.get("base_url") or "").rstrip("/")
        if not self.base_url:
            raise EvaluationError("api.base_url is required")
        if not self.base_url.endswith("/api"):
            raise EvaluationError("api.base_url must include the final /api prefix")

        self.headers = {
            str(key): str(value)
            for key, value in (api.get("headers") or {}).items()
            if value is not None and str(value).strip()
        }
        if not any(
            name.lower()
            in {
                "x-tenant-id",
                "ocp-apim-subscription-key",
                "x-subscription-id",
            }
            for name in self.headers
        ):
            raise EvaluationError(
                "Configure X-Tenant-Id or an API Management subscription key"
            )

        self.lang = str(request_config.get("lang") or "en")
        self.timezone = str(request_config.get("timezone") or "UTC")
        self.model = str(request_config.get("model") or "").strip()
        self.connect_timeout = float(api.get("connect_timeout_seconds") or 15)
        self.request_timeout = float(api.get("request_timeout_seconds") or 180)
        self.result_timeout = float(api.get("result_timeout_seconds") or 600)
        self.verify_tls = bool(api.get("verify_tls", True))
        self.session = requests.Session()

    def negotiate(self, user_id: str) -> str:
        response = self.session.post(
            f"{self.base_url}/pubsub/negotiate",
            json={"myuuid": user_id},
            headers=self.headers,
            timeout=self.connect_timeout,
            verify=self.verify_tls,
        )
        response.raise_for_status()
        payload = response.json()
        url = payload.get("url")
        if not url:
            raise EvaluationError("PubSub negotiation returned no WebSocket URL")
        return str(url)

    def _listen_for_result(
        self,
        socket: websocket.WebSocket,
        progress: list[dict[str, Any]],
        inbox: dict[str, Any],
        done: threading.Event,
    ) -> None:
        socket.settimeout(5)
        while not done.is_set():
            try:
                raw_message = socket.recv()
            except websocket.WebSocketTimeoutException:
                continue
            except Exception as error:
                inbox["error"] = f"{type(error).__name__}: {error}"
                done.set()
                return
            if isinstance(raw_message, bytes):
                raw_message = raw_message.decode("utf-8")
            message = json.loads(raw_message)
            message_type = message.get("type")
            if message_type == "progress":
                progress.append(message)
                continue
            if message_type == "result":
                inbox["result"] = message.get("data")
                done.set()
                return
            if message_type == "error":
                inbox["error"] = f"WebSocket processing error: {json.dumps(message)}"
                done.set()
                return
            progress.append({"type": "unhandled", "message": message})

    def submit_case(self, case: dict[str, Any]) -> dict[str, Any]:
        user_id = str(uuid.uuid4())
        started_at = utc_now()
        started = time.monotonic()
        progress: list[dict[str, Any]] = []
        http_payload: dict[str, Any] | None = None
        socket: websocket.WebSocket | None = None
        done = threading.Event()
        inbox: dict[str, Any] = {}
        listener: threading.Thread | None = None

        try:
            socket_url = self.negotiate(user_id)
            socket = websocket.create_connection(
                socket_url,
                timeout=self.connect_timeout,
                sslopt=(
                    {"cert_reqs": ssl.CERT_NONE}
                    if not self.verify_tls
                    else {}
                ),
            )
            listener = threading.Thread(
                target=self._listen_for_result,
                args=(socket, progress, inbox, done),
                daemon=True,
            )
            listener.start()

            with ExitStack() as stack:
                fields: list[tuple[str, Any]] = [
                    ("text", case["text"]),
                    ("lang", self.lang),
                    ("myuuid", user_id),
                    ("timezone", self.timezone),
                ]
                if self.model:
                    fields.append(("model", self.model))
                for path in case["documents"]:
                    fields.append(
                        (
                            "document",
                            (
                                path.name,
                                stack.enter_context(path.open("rb")),
                                DOCUMENT_MIME_TYPES[path.suffix.lower()],
                            ),
                        )
                    )
                for path in case["images"]:
                    fields.append(
                        (
                            "image",
                            (
                                path.name,
                                stack.enter_context(path.open("rb")),
                                IMAGE_MIME_TYPES[path.suffix.lower()],
                            ),
                        )
                    )

                multipart = MultipartEncoder(fields=fields)
                # The server awaits diagnose before answering, and PubSub may
                # deliver the result while this POST is still open.
                response = self.session.post(
                    f"{self.base_url}/medical/analyze",
                    data=multipart,
                    headers={
                        **self.headers,
                        "Content-Type": multipart.content_type,
                    },
                    timeout=self.request_timeout,
                    verify=self.verify_tls,
                )
                response.raise_for_status()
                http_payload = response.json()

            if http_payload.get("result") not in {"processing", "success"}:
                raise EvaluationError(
                    f"Unexpected analyze response: {json.dumps(http_payload)}"
                )

            remaining = max(0.1, self.result_timeout - (time.monotonic() - started))
            if not done.wait(timeout=remaining):
                raise EvaluationError(
                    f"No final WebSocket result after {self.result_timeout:.0f} seconds"
                )
            if inbox.get("error"):
                raise EvaluationError(str(inbox["error"]))
            return self._record(
                case=case,
                user_id=user_id,
                started_at=started_at,
                started=started,
                status="success",
                http_payload=http_payload,
                progress=progress,
                final_response=inbox.get("result"),
            )
        except Exception as error:
            response = (
                error.response
                if isinstance(error, requests.HTTPError)
                else None
            )
            rate_limited = response is not None and response.status_code == 429
            retry_after = None
            if rate_limited:
                try:
                    retry_after = float(response.headers.get("Retry-After") or 0)
                except (TypeError, ValueError):
                    retry_after = None
            return self._record(
                case=case,
                user_id=user_id,
                started_at=started_at,
                started=started,
                status="error",
                http_payload=http_payload,
                progress=progress,
                error=f"{type(error).__name__}: {error}",
                rate_limited=rate_limited,
                retry_after_seconds=retry_after,
            )
        finally:
            done.set()
            if socket is not None:
                try:
                    socket.close()
                except Exception:
                    pass
            if listener is not None:
                listener.join(timeout=2)

    @staticmethod
    def _record(
        *,
        case: dict[str, Any],
        user_id: str,
        started_at: str,
        started: float,
        status: str,
        http_payload: dict[str, Any] | None,
        progress: list[dict[str, Any]],
        final_response: Any = None,
        error: str | None = None,
        rate_limited: bool = False,
        retry_after_seconds: float | None = None,
    ) -> dict[str, Any]:
        description = str((http_payload or {}).get("description") or "")
        summarized = (http_payload or {}).get("summarized")
        if summarized is None:
            summarized = bool(case["text"]) and len(case["text"]) > PRODUCT_SUMMARY_MIN_CHARS
        return {
            "case_id": case["id"],
            "status": status,
            "started_at": started_at,
            "duration_seconds": round(time.monotonic() - started, 3),
            "request_id": user_id,
            "inputs": {
                "condition": case["evaluation_condition"],
                "has_text": bool(case["text"]),
                "documents": [path.name for path in case["documents"]],
                "images": [path.name for path in case["images"]],
                "image_source_case_id": case["image_source_case_id"],
                "total_file_bytes": case["total_file_bytes"],
                "text_chars": len(case["text"]),
            },
            "pipeline": {
                "product_summary_min_chars": PRODUCT_SUMMARY_MIN_CHARS,
                "summarized": bool(summarized),
                "description_chars": len(description),
                "requested_model": (http_payload or {}).get("model")
                or (final_response or {}).get("model"),
                "progress_steps": [
                    item.get("step")
                    for item in progress
                    if isinstance(item, dict) and item.get("step")
                ],
            },
            "http_response": http_payload,
            "progress": progress,
            "final_response": final_response,
            "gold": case["gold"],
            "metadata": case["metadata"],
            "error": error,
            "rate_limited": rate_limited,
            "retry_after_seconds": retry_after_seconds,
        }


def completed_case_ids(output_path: Path) -> set[str]:
    if not output_path.is_file():
        return set()
    completed: set[str] = set()
    with output_path.open("r", encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("status") == "success":
                completed.add(str(record.get("case_id")))
    return completed


def default_output_path(config_path: Path, config: dict[str, Any]) -> Path:
    output_root = Path((config.get("run") or {}).get("output_root") or "outputs")
    if not output_root.is_absolute():
        output_root = config_path.parent / output_root
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return output_root / timestamp / "responses.jsonl"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate DxGPT beta through /api/medical/analyze."
    )
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--limit", type=int)
    parser.add_argument(
        "--condition",
        choices=("manifest", "T", "I", "T+I", "T+shuffled-I"),
        default="manifest",
        help="Apply an input-modality condition without rewriting the manifest.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Skip successful case IDs already present in the output JSONL.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate case files and limits without calling DxGPT.",
    )
    return parser.parse_args()


def main() -> int:
    load_dotenv()
    args = parse_args()
    config_path = args.config.resolve()
    manifest_path = args.manifest.resolve()
    config = load_yaml(config_path)
    manifest = load_yaml(manifest_path)
    raw_cases = manifest.get("cases")
    if not isinstance(raw_cases, list) or not raw_cases:
        raise EvaluationError("The manifest requires a non-empty cases list")

    selected_cases = raw_cases[: args.limit] if args.limit else raw_cases
    conditioned_cases = apply_input_condition(selected_cases, args.condition)
    cases = [
        validate_case(case, manifest_path.parent)
        for case in conditioned_cases
    ]
    print(f"Validated {len(cases)} case(s) from {manifest_path.name}")

    if args.dry_run:
        for case in cases:
            print(
                f"{case['id']}: {len(case['documents'])} document(s), "
                f"{len(case['images'])} image(s), "
                f"{case['total_file_bytes'] / 1024 / 1024:.1f} MB"
            )
        return 0

    client = BetaApiClient(config)
    output_path = (
        args.output.resolve()
        if args.output
        else default_output_path(config_path, config)
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    skip_ids = completed_case_ids(output_path) if args.resume else set()
    run_config = config.get("run") or {}
    delay = float(run_config.get("delay_seconds") or 0)
    max_rate_limit_retries = max(
        0, int(run_config.get("rate_limit_max_retries") or 3)
    )
    fallback_retry_seconds = max(
        1.0, float(run_config.get("rate_limit_fallback_seconds") or 905)
    )

    attempted = 0
    failures = 0
    with output_path.open("a", encoding="utf-8") as stream:
        for index, case in enumerate(cases, start=1):
            if case["id"] in skip_ids:
                print(f"[{index}/{len(cases)}] Skipping {case['id']}")
                continue
            print(f"[{index}/{len(cases)}] Running {case['id']}")
            rate_limit_retries = 0
            while True:
                record = client.submit_case(case)
                if (
                    not record.get("rate_limited")
                    or rate_limit_retries >= max_rate_limit_retries
                ):
                    break
                rate_limit_retries += 1
                retry_after = record.get("retry_after_seconds")
                wait_seconds = (
                    max(1.0, float(retry_after) + 1.0)
                    if retry_after
                    else fallback_retry_seconds
                )
                print(
                    f"  rate limited; waiting {wait_seconds:.0f}s "
                    f"before retry {rate_limit_retries}/"
                    f"{max_rate_limit_retries}"
                )
                time.sleep(wait_seconds)
            record["rate_limit_retries"] = rate_limit_retries
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
            stream.flush()
            attempted += 1
            failures += record["status"] != "success"
            print(f"  {record['status']} in {record['duration_seconds']:.1f}s")
            if delay > 0 and index < len(cases):
                time.sleep(delay)

    print(f"Saved {attempted} result(s) to {output_path}")
    return 1 if failures else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except EvaluationError as error:
        print(f"Configuration error: {error}")
        raise SystemExit(2) from error
