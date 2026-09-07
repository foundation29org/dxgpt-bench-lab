"""Build local clinical-review packets from multimodal evaluation outputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a Markdown review packet beside evaluation outputs."
    )
    parser.add_argument("--evaluation-dir", type=Path, required=True)
    parser.add_argument("--responses", type=Path, required=True)
    parser.add_argument("--case-root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--title", required=True)
    parser.add_argument("--label", default="run")
    parser.add_argument("--compare-evaluation-dir", type=Path)
    parser.add_argument("--compare-responses", type=Path)
    parser.add_argument("--compare-label", default="comparison")
    return parser.parse_args()


def load_details(evaluation_dir: Path) -> list[dict[str, Any]]:
    path = evaluation_dir / "evaluation_details.txt"
    if not path.is_file():
        raise FileNotFoundError(f"Evaluation details not found: {path}")
    return [
        json.loads(block)
        for block in path.read_text(encoding="utf-8").split("\n---\n")
        if block.strip()
    ]


def load_responses(path: Path) -> dict[str, dict[str, Any]]:
    if not path.is_file():
        raise FileNotFoundError(f"Responses not found: {path}")
    records: dict[str, dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        case_id = str(row.get("case_id") or "")
        if row.get("status") == "success" or case_id not in records:
            records[case_id] = row
    return records


def position(result: dict[str, Any]) -> int | None:
    raw = (
        (result.get("eval_details") or {}).get("final_resolution") or {}
    ).get("position")
    if raw is None:
        return None
    return int(str(raw).removeprefix("P"))


def resolution_method(result: dict[str, Any]) -> str:
    return str(
        (
            (result.get("eval_details") or {}).get("final_resolution")
            or {}
        ).get("method")
        or ""
    )


def best_bert(result: dict[str, Any]) -> tuple[int | None, float | None]:
    candidates = []
    for trace in (result.get("eval_details") or {}).get(
        "evaluation_trace", []
    ):
        best = (trace.get("semantic_check") or {}).get("bert_best") or {}
        score = best.get("score")
        if score is not None:
            candidates.append((int(best.get("position") or 0), float(score)))
    if not candidates:
        return None, None
    return max(candidates, key=lambda item: item[1])


def gold_names(result: dict[str, Any]) -> list[str]:
    return [
        str(item.get("name") or "")
        for item in result.get("gdx_details") or []
        if item.get("name")
    ]


def prediction_names(result: dict[str, Any]) -> list[str]:
    return [
        str(item.get("name") or "")
        for item in result.get("ddx_details") or []
        if item.get("name")
    ]


def technical_triage(result: dict[str, Any]) -> str:
    predictions = prediction_names(result)
    _, score = best_bert(result)
    if not predictions:
        return "Lista vacía: fallo end-to-end prioritario."
    if score is None:
        return "Sin puntuación BERT utilizable: revisar manualmente."
    if score >= 0.75:
        return (
            "Prioridad alta: similitud BERT elevada; posible problema de "
            "equivalencia, granularidad o gold."
        )
    if score >= 0.60:
        return "Prioridad media: resultado fronterizo; requiere criterio clínico."
    return (
        "Similitud semántica baja; posible error diagnóstico sustantivo, "
        "pendiente de confirmación clínica."
    )


def case_context(
    case_id: str,
    response: dict[str, Any],
    case_root: Path,
) -> list[str]:
    final = response.get("final_response") or {}
    pipeline = response.get("pipeline") or {}
    inputs = response.get("inputs") or {}
    condition = inputs.get("condition")
    if not condition:
        has_text = bool(inputs.get("has_text"))
        has_images = bool(inputs.get("images"))
        condition = (
            "T+I"
            if has_text and has_images
            else "T"
            if has_text
            else "I"
            if has_images
            else "unknown"
        )
    return [
        f"- Historia e imágenes: `{(case_root / case_id).as_posix()}`",
        f"- Condición: `{condition}`",
        f"- Modelo real: `{final.get('model') or pipeline.get('requested_model') or 'unknown'}`",
        f"- Resumido: `{bool(pipeline.get('summarized'))}`",
    ]


def render_result(
    result: dict[str, Any],
    response: dict[str, Any],
    case_root: Path,
    include_reviewer_fields: bool = True,
) -> list[str]:
    case_id = str(result["case_id"])
    pos = position(result)
    bert_position, bert_score = best_bert(result)
    lines = [
        f"### {case_id}",
        "",
        f"- Gold: **{' / '.join(gold_names(result))}**",
        f"- Resolución automática: `{resolution_method(result) or 'NO_MATCH'}`",
        f"- Posición aceptada: `{pos if pos is not None else 0}`",
    ]
    lines.extend(case_context(case_id, response, case_root))
    if bert_score is not None:
        lines.append(
            f"- Mejor BERT: P{bert_position}, puntuación {bert_score:.3f}"
        )
    lines.append(f"- Pretriaje técnico: {technical_triage(result)}")
    lines.extend(["", "Propuestas:"])
    predictions = prediction_names(result)
    if predictions:
        lines.extend(
            f"{index}. {name}"
            for index, name in enumerate(predictions, start=1)
        )
    else:
        lines.append("- Ninguna.")
    if include_reviewer_fields:
        lines.extend(
            [
                "",
                "Respuesta clínica:",
                "",
                "- Primera posición equivalente:",
                "- Veredicto del evaluador:",
                "- Calidad/granularidad del gold:",
                "- Justificación:",
                "- Confianza:",
            ]
        )
    lines.append("")
    return lines


def write_single_packet(args: argparse.Namespace) -> None:
    evaluation_dir = args.evaluation_dir.resolve()
    details = load_details(evaluation_dir)
    responses = load_responses(args.responses.resolve())
    unmatched = [result for result in details if position(result) is None]
    llm_matches = [
        result
        for result in details
        if resolution_method(result) == "LLM_JUDGMENT"
    ]
    lines = [
        f"# {args.title}",
        "",
        "Paquete local generado automáticamente. El pretriaje es técnico y no",
        "sustituye el veredicto del revisor médico.",
        "",
        "## Resumen",
        "",
        f"- Casos evaluados: {len(details)}.",
        f"- Casos sin match: {len(unmatched)}.",
        f"- Matches decididos por el juez LLM: {len(llm_matches)}.",
        "",
        "## Casos sin match",
        "",
    ]
    for result in unmatched:
        lines.extend(
            render_result(
                result,
                responses.get(str(result["case_id"]), {}),
                args.case_root,
            )
        )
    lines.extend(
        [
            "## Matches del juez LLM que deben muestrearse",
            "",
            "Estos casos sirven para estimar falsos positivos del juez strict.",
            "",
        ]
    )
    for result in llm_matches:
        lines.extend(
            render_result(
                result,
                responses.get(str(result["case_id"]), {}),
                args.case_root,
            )
        )
    output = args.output or evaluation_dir / "clinical_review.md"
    output.resolve().parent.mkdir(parents=True, exist_ok=True)
    output.resolve().write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote clinical review packet to {output.resolve()}")


def write_comparison_packet(args: argparse.Namespace) -> None:
    if not args.compare_responses:
        raise ValueError("--compare-responses is required for a comparison")
    primary = load_details(args.evaluation_dir.resolve())
    comparison = load_details(args.compare_evaluation_dir.resolve())
    primary_by_id = {str(result["case_id"]): result for result in primary}
    comparison_by_id = {
        str(result["case_id"]): result for result in comparison
    }
    if primary_by_id.keys() != comparison_by_id.keys():
        raise ValueError("Comparison evaluations contain different case IDs")
    primary_responses = load_responses(args.responses.resolve())
    comparison_responses = load_responses(args.compare_responses.resolve())
    discordant = [
        case_id
        for case_id in primary_by_id
        if (position(primary_by_id[case_id]) is None)
        != (position(comparison_by_id[case_id]) is None)
    ]
    lines = [
        f"# {args.title}",
        "",
        "Comparación clínica ciega recomendada. El orden mostrado no implica",
        "que una condición sea la referencia correcta.",
        "",
        "## Resumen",
        "",
        f"- Casos totales: {len(primary_by_id)}.",
        f"- Casos discordantes por match: {len(discordant)}.",
        f"- Condición A: `{args.label}`.",
        f"- Condición B: `{args.compare_label}`.",
        "",
    ]
    for case_id in discordant:
        first = primary_by_id[case_id]
        second = comparison_by_id[case_id]
        lines.extend(
            [
                f"## Caso {case_id}",
                "",
                f"- Gold: **{' / '.join(gold_names(first))}**",
                (
                    "- Historia e imágenes: "
                    f"`{(args.case_root / case_id).as_posix()}`"
                ),
                "",
                f"### Lista A — {args.label}",
                "",
                f"- Match automático: `{position(first) or 0}`",
            ]
        )
        lines.extend(
            f"{index}. {name}"
            for index, name in enumerate(
                prediction_names(first), start=1
            )
        )
        lines.extend(
            [
                "",
                f"### Lista B — {args.compare_label}",
                "",
                f"- Match automático: `{position(second) or 0}`",
            ]
        )
        lines.extend(
            f"{index}. {name}"
            for index, name in enumerate(
                prediction_names(second), start=1
            )
        )
        lines.extend(
            [
                "",
                "Respuesta clínica:",
                "",
                "- Lista clínicamente mejor —A/B/empate/ninguna—:",
                "- ¿La imagen aporta evidencia útil para el gold?:",
                "- ¿Los matches automáticos son correctos?:",
                "- Justificación:",
                "- Confianza:",
                "",
            ]
        )
    output = args.output
    if output is None:
        raise ValueError("--output is required for a comparison packet")
    output.resolve().parent.mkdir(parents=True, exist_ok=True)
    output.resolve().write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote paired clinical review packet to {output.resolve()}")


def main() -> int:
    args = parse_args()
    if args.compare_evaluation_dir:
        write_comparison_packet(args)
    else:
        write_single_packet(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
