"""Safe predicate evaluation without arbitrary code execution."""

from typing import Any

from dystonia_icu_sim.models.patient import PatientState


def _get_path(state: PatientState, path: str) -> Any:
    parts = path.split(".")
    if not parts:
        return None
    root = parts[0]
    if root == "vitals":
        cur: Any = state.vitals
    elif root == "labs":
        cur = state.labs
    elif root == "flags":
        cur = state.flags
    elif root == "consults":
        cur = state.consults
    elif root == "elapsed_minutes":
        return state.elapsed_minutes
    else:
        return None
    for key in parts[1:]:
        if not isinstance(cur, dict) or key not in cur:
            return None
        cur = cur[key]
    return cur


def _compare(actual: Any, op: str, expected: Any) -> bool:
    if actual is None:
        return False
    if op == "eq":
        return actual == expected
    if op == "neq":
        return actual != expected
    if op == "gt":
        return actual > expected
    if op == "gte":
        return actual >= expected
    if op == "lt":
        return actual < expected
    if op == "lte":
        return actual <= expected
    if op == "in":
        return actual in expected
    if op == "contains":
        if isinstance(actual, str) and isinstance(expected, str):
            return expected in actual
        return False
    return False


def evaluate_condition(state: PatientState, condition: dict[str, Any]) -> bool:
    """Evaluate a single condition dict: {path, op, value} or {all: [...]} / {any: [...]}."""
    if "all" in condition:
        return all(evaluate_condition(state, c) for c in condition["all"])
    if "any" in condition:
        return any(evaluate_condition(state, c) for c in condition["any"])
    if "not" in condition:
        return not evaluate_condition(state, condition["not"])

    path = condition.get("path")
    op = condition.get("op", "eq")
    value = condition.get("value")
    if path is None:
        return False
    actual = _get_path(state, path)
    return _compare(actual, op, value)


def evaluate_when(state: PatientState, when: dict[str, Any]) -> bool:
    """Top-level transition predicate."""
    return evaluate_condition(state, when)
