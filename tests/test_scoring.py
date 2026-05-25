from dystonia_icu_sim.engine.engine import SimulationEngine
from dystonia_icu_sim.engine.loader import load_rubric, load_scenario
from dystonia_icu_sim.scoring.service import ScoringService


def test_scoring_pass_threshold():
    rubric = load_rubric("disability_specialist")
    scenario = load_scenario("medication_trial_02")
    engine = SimulationEngine(scenario)
    run = engine.start()
    node = engine.get_current_node(run)
    engine.apply_choice(run, next(c for c in node.choices if c.id == "coordinated_titration"))
    node = engine.get_current_node(run)
    engine.apply_choice(run, next(c for c in node.choices if c.id == "adjust_with_aac_plan"))
    scoring = ScoringService(rubric).score_run(run)
    assert scoring.total_normalized > 0
    assert scoring.rubric_id == "disability_specialist"
    assert len(scoring.dimensions) == 5


def test_scoring_band_assignment():
    rubric = load_rubric("disability_specialist")
    service = ScoringService(rubric)
    from dystonia_icu_sim.engine.engine import SimulationRun
    from dystonia_icu_sim.models.patient import PatientState

    run = SimulationRun(
        run_id="test",
        scenario_id="x",
        seed=0,
        role="learner",
        patient=PatientState(),
        current_node_id="n",
        scores={
            "functional_assessment": 9,
            "accommodation_planning": 9,
            "interprofessional_coordination": 8,
            "patient_centered_communication": 8,
            "safety_escalation": 9,
        },
    )
    result = service.score_run(run)
    assert result.band in ("excellent", "proficient", "developing", "needs_improvement")
