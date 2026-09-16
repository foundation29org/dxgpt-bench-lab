"""Build a clinician review form for cases where strict judges disagree."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--labeled-input", type=Path, required=True)
    parser.add_argument(
        "--run",
        action="append",
        required=True,
        metavar="LABEL=EVALUATION_DETAILS",
    )
    parser.add_argument(
        "--priority-pair",
        metavar="LABEL_A|LABEL_B",
        help=(
            "Put disagreements between these two decision-critical runs first."
        ),
    )
    output_mode = parser.add_mutually_exclusive_group()
    output_mode.add_argument(
        "--blind",
        action="store_true",
        help="Omit all automatic judge decisions from the clinician form.",
    )
    output_mode.add_argument(
        "--compact-answer-key",
        action="store_true",
        help="Write only the automatic decisions, without clinical histories.",
    )
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def load_details(path: Path) -> dict[str, tuple[bool, int | None]]:
    decisions: dict[str, tuple[bool, int | None]] = {}
    for block in path.read_text(encoding="utf-8").split("\n---\n"):
        if not block.strip():
            continue
        row = json.loads(block)
        case_id = str(row.get("case_id") or row.get("id") or "")
        evaluation = row.get("eval_details") or {}
        resolution = evaluation.get("final_resolution") or {}
        raw_position = resolution.get("position")
        position = None
        if raw_position:
            position = int(str(raw_position).lstrip("Pp"))
        decisions[case_id] = (
            bool(evaluation.get("best_match_found")),
            position,
        )
    return decisions


def parse_runs(values: list[str]) -> dict[str, dict[str, tuple[bool, int | None]]]:
    runs = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"Invalid --run value: {value!r}")
        label, raw_path = value.split("=", 1)
        label = label.strip()
        if not label or label in runs:
            raise ValueError(f"Run label must be non-empty and unique: {label!r}")
        runs[label] = load_details(Path(raw_path).resolve())
    return runs


def diagnosis_names(details: Any) -> list[str]:
    if isinstance(details, dict):
        return [str(name) for name in details]
    if isinstance(details, list):
        return [
            str(item.get("name") or "")
            for item in details
            if isinstance(item, dict) and item.get("name")
        ]
    return []


def decision_text(decision: tuple[bool, int | None]) -> str:
    matched, position = decision
    return f"P{position}" if matched and position is not None else "0 (ninguna)"


def decision_with_diagnosis(
    decision: tuple[bool, int | None],
    options: list[str],
) -> str:
    text = decision_text(decision)
    _, position = decision
    if position is None or not 1 <= position <= len(options):
        return text
    return f"{text} — {options[position - 1]}"


def render_answer_key(
    disagreements: list[str],
    labels: dict[str, dict[str, Any]],
    runs: dict[str, dict[str, tuple[bool, int | None]]],
) -> str:
    lines = [
        "# Clave interna — Pro vs Flash sin thinking",
        "",
        "**No enviar a David antes de completar la revisión ciega.**",
        "",
        "Estas no son soluciones clínicas confirmadas. Son las decisiones",
        "automáticas que originaron la tarea y se conservan para recalcular",
        "métricas después de recibir la revisión.",
        "",
        f"**Alcance:** {len(disagreements)} discrepancias exactas.",
        "",
    ]
    for index, case_id in enumerate(disagreements, start=1):
        label = labels.get(case_id) or {}
        gold = diagnosis_names(label.get("gdx_details"))
        options = diagnosis_names(label.get("ddx_details"))
        lines.extend(
            [
                f"## {index}. {case_id}",
                "",
                f"- Referencia: {'; '.join(gold) or '—'}",
            ]
        )
        lines.extend(
            f"- {run_label}: `{decision_with_diagnosis(run[case_id], options)}`"
            for run_label, run in runs.items()
        )
        lines.append("")
    return "\n".join(lines)


def render_review(
    dataset: list[dict[str, Any]],
    labeled: list[dict[str, Any]],
    runs: dict[str, dict[str, tuple[bool, int | None]]],
    priority_pair: tuple[str, str] | None,
    *,
    blind: bool,
    compact_answer_key: bool,
) -> str:
    cases = {str(row.get("id") or row.get("case_id")): row for row in dataset}
    labels = {
        str(row.get("id") or row.get("case_id")): row
        for row in labeled
    }
    common_ids = set.intersection(*(set(run) for run in runs.values()))
    disagreements = [
        case_id
        for case_id in common_ids
        if len({run[case_id] for run in runs.values()}) > 1
    ]
    order = {
        str(row.get("id") or row.get("case_id")): index
        for index, row in enumerate(dataset)
    }
    priority_ids: set[str] = set()
    if priority_pair is not None:
        first, second = priority_pair
        priority_ids = {
            case_id
            for case_id in disagreements
            if runs[first][case_id] != runs[second][case_id]
        }
    disagreements.sort(
        key=lambda case_id: (
            case_id not in priority_ids,
            order.get(case_id, len(order)),
        )
    )
    if compact_answer_key:
        return render_answer_key(disagreements, labels, runs)

    lines = [
        "# Tarea clínica ciega — Pro vs Flash sin thinking en all_256_clean",
        "",
        "**Estado:** New",
        "",
        "**Responsable sugerido:** David o cualquier clínico que no haya visto",
        "las respuestas automáticas antes de aplicar la regla.",
        "",
        "**Contexto:** David ya terminó la ronda 2 original de MedReaMM. Esta es",
        "una tarea nueva sobre `all_256_clean`, creada por discrepancias encontradas",
        "después al comparar jueces.",
        "",
        "## Objetivo",
        "",
        "Decidir qué opción diagnóstica, si alguna, representa la misma enfermedad",
        "que el diagnóstico de referencia. Solo se incluyen casos donde los jueces",
        "automáticos dieron resultados finales distintos.",
        "",
        f"**Alcance:** {len(disagreements)} casos de 256. No hay que revisar los demás.",
        (
            f"**Prioridad A:** {len(priority_ids)} casos que deciden Pro vs Flash "
            "sin thinking. **Prioridad B:** "
            f"{len(disagreements) - len(priority_ids)} discrepancias exploratorias."
            if priority_pair is not None
            else ""
        ),
        "",
        "## Regla de equivalencia",
        "",
        "- Aceptar sinónimos, abreviaturas, variantes ortográficas y una formulación",
        "  más específica que conserve inequívocamente la enfermedad de referencia.",
        "- Rechazar diagnósticos solo relacionados por síntomas, localización,",
        "  mecanismo o tratamiento.",
        "- Rechazar otra causa, complicación, precursor, subtipo incompatible o",
        "  categoría amplia que cambie la entidad diagnóstica.",
        "- Si el diagnóstico de referencia es ambiguo, incorrecto o no es una",
        "  enfermedad, marcarlo explícitamente; no forzar una posición.",
        "",
        "## Entregable",
        "",
        "En cada caso:",
        "",
        "1. marcar si el diagnóstico de referencia es válido;",
        "2. escribir una sola posición `P1…Pn` o `0` si ninguna es equivalente;",
        "3. justificar la decisión en una o dos frases;",
        "4. marcar `consulta` si la regla no permite resolverlo.",
        "",
        "## Casos",
        "",
    ]

    priority_index = 0
    secondary_index = 0
    for case_id in disagreements:
        if case_id in priority_ids:
            priority_index += 1
            case_number = f"A{priority_index}"
        else:
            secondary_index += 1
            case_number = f"B{secondary_index}" if priority_pair else str(secondary_index)
        case = cases.get(case_id) or {}
        label = labels.get(case_id) or {}
        gold = diagnosis_names(label.get("gdx_details"))
        options = diagnosis_names(label.get("ddx_details"))
        lines.extend(
            [
                f"### {case_number}. {case_id}",
                "",
                f"**Complejidad:** {case.get('complexity', '—')}",
                "",
                "**Historia clínica**",
                "",
                f"> {str(case.get('case') or 'No disponible').replace(chr(10), ' ')}",
                "",
                f"**Diagnóstico de referencia:** {'; '.join(gold) or '—'}",
                "",
                "**Opciones diagnósticas**",
                "",
            ]
        )
        lines.extend(
            f"{option_index}. {option}"
            for option_index, option in enumerate(options, start=1)
        )
        if not blind:
            lines.extend(["", "**Decisiones automáticas**", ""])
            lines.extend(
                f"- {run_label}: `{decision_text(run[case_id])}`"
                for run_label, run in runs.items()
            )
        lines.extend(
            [
                "",
                "**Revisión clínica**",
                "",
                "- Diagnóstico de referencia: `[ ] válido` `[ ] ambiguo` `[ ] incorrecto`",
                "- Opción equivalente: `P__ / 0 / consulta`",
                "- Justificación:",
                "",
                "---",
                "",
            ]
        )

    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    dataset = json.loads(args.dataset.read_text(encoding="utf-8"))
    labeled = json.loads(args.labeled_input.read_text(encoding="utf-8"))
    runs = parse_runs(args.run)
    priority_pair = None
    if args.priority_pair:
        labels = tuple(part.strip() for part in args.priority_pair.split("|"))
        if len(labels) != 2 or any(label not in runs for label in labels):
            raise ValueError(
                "--priority-pair must contain two existing run labels separated by |"
            )
        priority_pair = (labels[0], labels[1])
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        render_review(
            dataset,
            labeled,
            runs,
            priority_pair,
            blind=args.blind,
            compact_answer_key=args.compact_answer_key,
        ),
        encoding="utf-8",
    )
    print(f"Review task written to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
