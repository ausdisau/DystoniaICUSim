from pathlib import Path

import pytest

from dystonia_icu_sim.engine.loader import (
    list_scenarios,
    load_scenario,
    validate_directory,
    validate_scenario_file,
)
from dystonia_icu_sim.paths import SCENARIOS_DIR
from dystonia_icu_sim.ui.loader import load_ui_spec


def test_all_scenarios_validate():
    results = validate_directory(SCENARIOS_DIR)
    failures = [(p, e) for p, e in results if e]
    assert not failures, failures


def test_list_scenarios_includes_three_cases():
    ids = {s["id"] for s in list_scenarios()}
    assert "status_dystonicus_01" in ids
    assert "medication_trial_02" in ids
    assert "noah_stormcode_post_stage2" in ids


def test_load_noah_stormcode_ui_spec():
    scenario = load_scenario("noah_stormcode_post_stage2")
    assert scenario.meta.ui_spec_id == "STORMCODE_NOAH_POST_STAGE2_UI_V1"
    spec = load_ui_spec(scenario.meta.ui_spec_id)
    assert spec.stableId == "STORMCODE_NOAH_POST_STAGE2_UI_V1"
    assert len(spec.criticalRules) >= 5
    assert "NURSE_CALL_AIRWAY_EMERGENCY" in spec.nursing_action_ids()


def test_invalid_yaml_fails_validation(tmp_path: Path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("meta:\n  title: x\n", encoding="utf-8")
    errors = validate_scenario_file(bad)
    assert errors
