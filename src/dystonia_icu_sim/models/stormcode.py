from typing import Any

from pydantic import BaseModel, Field


class AssetMapEntry(BaseModel):
    role: str
    visualTone: str
    useCases: list[str] = Field(default_factory=list)


class UiZone(BaseModel):
    id: str
    components: list[str] = Field(default_factory=list)


class NursingAction(BaseModel):
    id: str
    label: str
    requiredTeams: list[str] = Field(default_factory=list)
    mode: str | None = None
    sequenceFields: list[str] = Field(default_factory=list)
    status: str | None = None


class VisualTone(BaseModel):
    style: str
    accent: str = ""
    layout: str = ""
    avoid: list[str] = Field(default_factory=list)


class StormCodeUiSpec(BaseModel):
    stableId: str
    title: str
    mode: str
    assetMap: dict[str, AssetMapEntry] = Field(default_factory=dict)
    primaryClinicalState: dict[str, Any] = Field(default_factory=dict)
    uiZones: list[UiZone] = Field(default_factory=list)
    criticalRules: list[str] = Field(default_factory=list)
    nursingActions: list[NursingAction] = Field(default_factory=list)
    visualTone: VisualTone | None = None

    def nursing_action_ids(self) -> set[str]:
        return {a.id for a in self.nursingActions}

    def validate_choice(self, nursing_action_id: str | None, violates_rule: str | None) -> list[str]:
        errors: list[str] = []
        if violates_rule and violates_rule in self.criticalRules:
            errors.append(f"Violates critical rule: {violates_rule}")
        if nursing_action_id and nursing_action_id not in self.nursing_action_ids():
            errors.append(f"Unknown nursing action: {nursing_action_id}")
        return errors
