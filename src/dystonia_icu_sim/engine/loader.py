import json
from pathlib import Path

import jsonschema
import yaml

from dystonia_icu_sim.models.rubric import Rubric, RubricDimension
from dystonia_icu_sim.models.scenario import (
    Choice,
    Endpoint,
    Node,
    Scenario,
    ScenarioMeta,
    StatePatch,
    Transition,
)
from dystonia_icu_sim.paths import RUBRICS_DIR, SCENARIOS_DIR, SCHEMA_PATH


def _load_schema() -> dict:
    with SCHEMA_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def validate_scenario_data(data: dict) -> list[str]:
    schema = _load_schema()
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
    return [e.message for e in errors]


def validate_scenario_file(path: Path) -> list[str]:
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        return [f"{path}: expected mapping at root"]
    return validate_scenario_data(data)


def _parse_state_patch(raw: dict | None) -> StatePatch:
    if not raw:
        return StatePatch()
    return StatePatch(**raw)


def _parse_scenario(data: dict) -> Scenario:
    meta_raw = data["meta"]
    meta = ScenarioMeta(**meta_raw)
    nodes: dict[str, Node] = {}
    for node_id, node_data in data["nodes"].items():
        choices = [
            Choice(
                id=c["id"],
                label=c["label"],
                effects=_parse_state_patch(c.get("effects")),
                time_cost=c.get("time_cost", 0),
                competency_tags=c.get("competency_tags", []),
                score_delta=c.get("score_delta", {}),
                hint=c.get("hint"),
                next_node=c.get("next_node"),
                nursing_action_id=c.get("nursing_action_id"),
                violates_critical_rule=c.get("violates_critical_rule"),
            )
            for c in node_data.get("choices", [])
        ]
        nodes[node_id] = Node(
            id=node_id,
            narrative=node_data["narrative"],
            choices=choices,
            is_terminal=node_data.get("is_terminal", False),
        )

    transitions = [Transition(**t) for t in data.get("transitions", [])]
    endpoints = {
        eid: Endpoint(**edata) for eid, edata in data.get("endpoints", {}).items()
    }

    return Scenario(
        meta=meta,
        initial_state=data["initial_state"],
        start_node=data["start_node"],
        nodes=nodes,
        transitions=transitions,
        endpoints=endpoints,
        critical_misses=data.get("critical_misses", []),
    )


def load_scenario(scenario_id: str) -> Scenario:
    scenario_dir = SCENARIOS_DIR / "dystonia_icu"
    path = scenario_dir / f"{scenario_id}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Scenario not found: {scenario_id} ({path})")
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    errors = validate_scenario_data(data)
    if errors:
        raise ValueError(f"Invalid scenario {scenario_id}: " + "; ".join(errors[:3]))
    return _parse_scenario(data)


def list_scenarios() -> list[dict[str, str]]:
    scenario_dir = SCENARIOS_DIR / "dystonia_icu"
    results = []
    for path in sorted(scenario_dir.glob("*.yaml")):
        with path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
        meta = data.get("meta", {})
        results.append(
            {
                "id": meta.get("id", path.stem),
                "title": meta.get("title", path.stem),
                "difficulty": meta.get("difficulty", "unknown"),
                "path": str(path),
            }
        )
    return results


def load_rubric(rubric_id: str) -> Rubric:
    path = RUBRICS_DIR / f"{rubric_id}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Rubric not found: {rubric_id}")
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    dimensions = [RubricDimension(**d) for d in data.get("dimensions", [])]
    return Rubric(
        id=data["id"],
        name=data["name"],
        dimensions=dimensions,
        pass_threshold=data.get("pass_threshold", 0.7),
        bands=data.get("bands", {}),
    )


def validate_directory(directory: Path | None = None) -> list[tuple[str, list[str]]]:
    base = directory or SCENARIOS_DIR
    results: list[tuple[str, list[str]]] = []
    for path in sorted(base.rglob("*.yaml")):
        if path.parent.name == "schema":
            continue
        results.append((str(path), validate_scenario_file(path)))
    return results
