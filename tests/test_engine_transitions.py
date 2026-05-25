from dystonia_icu_sim.engine.engine import SimulationEngine
from dystonia_icu_sim.engine.loader import load_scenario
from dystonia_icu_sim.models.scenario import Choice, StatePatch


def test_status_dystonicus_success_path():
    scenario = load_scenario("status_dystonicus_01")
    engine = SimulationEngine(scenario)
    run = engine.start()
    node = engine.get_current_node(run)
    choice = next(c for c in node.choices if c.id == "escalate_neuro_icu")
    engine.apply_choice(run, choice)
    node = engine.get_current_node(run)
    choice = next(c for c in node.choices if c.id == "pmr_consult")
    engine.apply_choice(run, choice)
    node = engine.get_current_node(run)
    choice = next(c for c in node.choices if c.id == "aac_plan")
    engine.apply_choice(run, choice)
    node = engine.get_current_node(run)
    choice = next(c for c in node.choices if c.id == "complete_handover")
    engine.apply_choice(run, choice)
    assert run.terminal
    assert run.outcome == "success"


def test_critical_rule_violation_flags():
    scenario = load_scenario("status_dystonicus_01")
    engine = SimulationEngine(scenario)
    run = engine.start()
    node = engine.get_current_node(run)
    bad = next(c for c in node.choices if c.violates_critical_rule)
    engine.apply_choice(run, bad)
    assert bad.violates_critical_rule in run.flags_triggered


def test_auto_transition_on_delay():
    scenario = load_scenario("status_dystonicus_01")
    engine = SimulationEngine(scenario)
    run = engine.start()
    node = engine.get_current_node(run)
    delay = next(c for c in node.choices if c.id == "delay_for_imaging")
    engine.apply_choice(run, delay)
    assert run.patient.flags.get("treatment_delayed")
    transition_events = [e for e in run.events if e.event_type == "auto_transition"]
    assert any(e.transition_id == "auto_worsen_delayed" for e in transition_events) or (
        run.current_node_id == "worsening"
    )


def test_predicate_operators():
    from dystonia_icu_sim.engine.predicates import evaluate_when
    from dystonia_icu_sim.models.patient import PatientState

    state = PatientState(vitals={"temp_c": 39}, flags={"x": True}, elapsed_minutes=70)
    assert evaluate_when(state, {"path": "vitals.temp_c", "op": "gte", "value": 38.5})
    assert evaluate_when(
        state,
        {"all": [{"path": "flags.x", "op": "eq", "value": True}]},
    )
