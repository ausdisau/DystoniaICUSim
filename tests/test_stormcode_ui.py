from dystonia_icu_sim.models.stormcode import StormCodeUiSpec
from dystonia_icu_sim.ui.loader import load_ui_spec, render_dashboard_text


def test_stormcode_spec_loads():
    spec = load_ui_spec("stormcode_noah_post_stage2_ui")
    assert spec.mode == "high_acuity_multimodal_simulation_dashboard"
    assert "icuRoom" in spec.assetMap
    assert spec.primaryClinicalState["patient"] == "Noah"


def test_critical_rule_validation():
    spec = load_ui_spec("STORMCODE_NOAH_POST_STAGE2_UI_V1")
    errors = spec.validate_choice(None, "do_not_remove_AAC")
    assert errors
    errors_ok = spec.validate_choice("NURSE_PROTECT_BODY", None)
    assert not errors_ok


def test_render_dashboard_contains_zones():
    spec = load_ui_spec("STORMCODE_NOAH_POST_STAGE2_UI_V1")
    text = render_dashboard_text(spec)
    assert "storm-header" in text or "UI zones" in text
    assert "do_not_remove_AAC" in text
