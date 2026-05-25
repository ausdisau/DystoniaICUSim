from typing import Any

from pydantic import BaseModel, Field


class PatientState(BaseModel):
    """Synthetic patient state tracked during simulation."""

    vitals: dict[str, Any] = Field(default_factory=dict)
    labs: dict[str, Any] = Field(default_factory=dict)
    flags: dict[str, bool] = Field(default_factory=dict)
    consults: dict[str, str] = Field(default_factory=dict)
    narrative_notes: list[str] = Field(default_factory=list)
    elapsed_minutes: int = 0

    def apply_patch(self, patch: dict[str, Any]) -> None:
        if "vitals" in patch:
            self.vitals.update(patch["vitals"])
        if "labs" in patch:
            self.labs.update(patch["labs"])
        if "flags" in patch:
            self.flags.update(patch["flags"])
        if "consults" in patch:
            self.consults.update(patch["consults"])
        if "note" in patch:
            self.narrative_notes.append(patch["note"])
        if "elapsed_minutes" in patch:
            self.elapsed_minutes += int(patch["elapsed_minutes"])

    def to_snapshot(self) -> dict[str, Any]:
        return {
            "vitals": dict(self.vitals),
            "labs": dict(self.labs),
            "flags": dict(self.flags),
            "consults": dict(self.consults),
            "narrative_notes": list(self.narrative_notes),
            "elapsed_minutes": self.elapsed_minutes,
        }
