import json

import yaml

from dystonia_icu_sim.models.patient import PatientState
from dystonia_icu_sim.models.stormcode import (
    AssetMapEntry,
    NursingAction,
    StormCodeUiSpec,
    UiZone,
    VisualTone,
)
from dystonia_icu_sim.paths import REPO_ROOT

UI_SPECS_DIR = REPO_ROOT / "ui_specs"


def _parse_spec_data(data: dict) -> StormCodeUiSpec:
    parsed_assets = {
        name: AssetMapEntry(**entry) for name, entry in data.get("assetMap", {}).items()
    }
    zones = [UiZone(**z) for z in data.get("uiZones", [])]
    actions = [NursingAction(**a) for a in data.get("nursingActions", [])]
    vt = data.get("visualTone")
    return StormCodeUiSpec(
        stableId=data["stableId"],
        title=data["title"],
        mode=data["mode"],
        assetMap=parsed_assets,
        primaryClinicalState=data.get("primaryClinicalState", {}),
        uiZones=zones,
        criticalRules=data.get("criticalRules", []),
        nursingActions=actions,
        visualTone=VisualTone(**vt) if vt else None,
    )


def load_ui_spec(spec_id: str) -> StormCodeUiSpec:
    """Load UI spec by stableId or filename stem."""
    candidates = list(UI_SPECS_DIR.glob("*.json")) + list(UI_SPECS_DIR.glob("*.yaml"))
    for path in candidates:
        with path.open(encoding="utf-8") as f:
            if path.suffix == ".json":
                data = json.load(f)
            else:
                data = yaml.safe_load(f)
        if data.get("stableId") == spec_id or path.stem == spec_id:
            return _parse_spec_data(data)
    raise FileNotFoundError(f"UI spec not found: {spec_id}")


def render_dashboard_text(spec: StormCodeUiSpec, patient: PatientState | None = None) -> str:
    """Text rendering of StormCode dashboard for CLI / terminal clients."""
    state = spec.primaryClinicalState
    lines = [
        f"=== {spec.title} ===",
        f"Mode: {spec.mode}",
        f"Patient: {state.get('patient', 'unknown')} | Phase: {state.get('phase', '')}",
        f"StormCode: {'ACTIVE' if state.get('stormCodeActive') else 'inactive'}",
        "",
        "Working problems:",
    ]
    for p in state.get("workingProblems", []):
        lines.append(f"  - {p}")
    lines.extend(["", "UI zones:"])
    for zone in spec.uiZones:
        lines.append(f"  [{zone.id}] {', '.join(zone.components[:4])}...")
    if patient:
        lines.extend(
            [
                "",
                "Live vitals:",
                f"  {patient.vitals}",
                f"Elapsed: {patient.elapsed_minutes} min",
            ]
        )
    lines.extend(["", "Critical rules (do not):"])
    for rule in spec.criticalRules:
        lines.append(f"  ! {rule}")
    return "\n".join(lines)
