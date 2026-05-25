import json
from pathlib import Path
from typing import Any

from dystonia_icu_sim.engine.engine import SimulationRun
from dystonia_icu_sim.paths import RUNS_DIR
from dystonia_icu_sim.scoring.service import ScoringResult


def save_run(run: SimulationRun, scoring: ScoringResult | None = None) -> Path:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {"run": run.to_dict()}
    if scoring:
        payload["scoring"] = {
            "rubric_id": scoring.rubric_id,
            "total_normalized": scoring.total_normalized,
            "band": scoring.band,
            "passed": scoring.passed,
            "outcome": scoring.outcome,
            "dimensions": [
                {
                    "dimension_id": d.dimension_id,
                    "name": d.name,
                    "raw_score": d.raw_score,
                    "normalized": d.normalized,
                }
                for d in scoring.dimensions
            ],
        }
    path = RUNS_DIR / f"{run.run_id}.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def load_run(run_id: str) -> dict[str, Any]:
    path = RUNS_DIR / f"{run_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Run not found: {run_id}")
    return json.loads(path.read_text(encoding="utf-8"))


def export_debrief_markdown(run: SimulationRun, scoring: ScoringResult) -> str:
    lines = [
        f"# Simulation Debrief: {run.scenario_id}",
        "",
        "**Educational simulation only — not medical advice.**",
        "",
        f"- Run ID: `{run.run_id}`",
        f"- Outcome: **{run.outcome or 'incomplete'}**",
        f"- Overall: **{scoring.band}** ({scoring.total_normalized:.0%}) — "
        f"{'PASS' if scoring.passed else 'REVIEW'}",
        "",
        "## Competency dimensions",
        "",
    ]
    for d in scoring.dimensions:
        lines.append(
            f"- **{d.name}**: {d.raw_score:.0f}/{d.max_score:.0f} "
            f"({d.normalized:.0%})"
        )
    if run.competency_hits:
        lines.extend(["", "## Competencies demonstrated", ""])
        for tag in sorted(run.competency_hits):
            lines.append(f"- {tag}")
    if run.flags_triggered:
        lines.extend(["", "## Critical gaps flagged", ""])
        for flag in sorted(run.flags_triggered):
            lines.append(f"- {flag}")
    lines.extend(["", "## Decision timeline", ""])
    for i, event in enumerate(run.events, 1):
        if event.event_type == "choice":
            label = event.details.get("label", event.choice_id)
            lines.append(f"{i}. Choice **{event.choice_id}**: {label}")
        elif event.event_type == "auto_transition":
            narrative = event.details.get("narrative", "")
            lines.append(f"{i}. Auto: {event.transition_id} — {narrative}")
        elif event.event_type == "critical_miss":
            lines.append(
                f"{i}. Critical miss: {event.details.get('description', '')}"
            )
    lines.extend(
        [
            "",
            "## Reflection prompts",
            "",
            "- What functional baseline was documented before disposition planning?",
            "- Which accommodations were planned for communication and positioning?",
            "- When should PM&R / disability specialist input occur in acute dystonia?",
            "",
        ]
    )
    return "\n".join(lines)


def export_debrief_json(run: SimulationRun, scoring: ScoringResult) -> dict[str, Any]:
    return {
        "run_id": run.run_id,
        "scenario_id": run.scenario_id,
        "outcome": run.outcome,
        "scoring": {
            "band": scoring.band,
            "total_normalized": scoring.total_normalized,
            "passed": scoring.passed,
            "dimensions": [
                {"id": d.dimension_id, "normalized": d.normalized}
                for d in scoring.dimensions
            ],
        },
        "events": [e.__dict__ for e in run.events],
    }
