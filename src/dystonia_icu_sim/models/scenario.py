from typing import Any

from pydantic import BaseModel, Field

from dystonia_icu_sim.models.patient import PatientState


class ScenarioMeta(BaseModel):
    id: str
    title: str
    version: str = "1.0"
    difficulty: str = "intermediate"
    estimated_minutes: int = 20
    learning_objectives: list[str] = Field(default_factory=list)
    roles: list[str] = Field(default_factory=list)
    ui_spec_id: str | None = None
    mode: str | None = None


class StatePatch(BaseModel):
    vitals: dict[str, Any] | None = None
    labs: dict[str, Any] | None = None
    flags: dict[str, bool] | None = None
    consults: dict[str, str] | None = None
    note: str | None = None
    elapsed_minutes: int | None = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        if self.vitals is not None:
            out["vitals"] = self.vitals
        if self.labs is not None:
            out["labs"] = self.labs
        if self.flags is not None:
            out["flags"] = self.flags
        if self.consults is not None:
            out["consults"] = self.consults
        if self.note is not None:
            out["note"] = self.note
        if self.elapsed_minutes is not None:
            out["elapsed_minutes"] = self.elapsed_minutes
        return out


class Choice(BaseModel):
    id: str
    label: str
    effects: StatePatch = Field(default_factory=StatePatch)
    time_cost: int = 0
    competency_tags: list[str] = Field(default_factory=list)
    score_delta: dict[str, int] = Field(default_factory=dict)
    hint: str | None = None
    next_node: str | None = None
    nursing_action_id: str | None = None
    violates_critical_rule: str | None = None


class Transition(BaseModel):
    id: str
    when: dict[str, Any]
    next_node: str
    narrative: str | None = None


class Node(BaseModel):
    id: str
    narrative: str
    choices: list[Choice] = Field(default_factory=list)
    is_terminal: bool = False


class Endpoint(BaseModel):
    id: str
    outcome: str
    narrative: str
    competency_tags: list[str] = Field(default_factory=list)
    score_delta: dict[str, int] = Field(default_factory=dict)


class Scenario(BaseModel):
    meta: ScenarioMeta
    initial_state: dict[str, Any]
    start_node: str
    nodes: dict[str, Node]
    transitions: list[Transition] = Field(default_factory=list)
    endpoints: dict[str, Endpoint] = Field(default_factory=dict)
    critical_misses: list[dict[str, Any]] = Field(default_factory=list)

    def build_initial_patient(self) -> PatientState:
        data = self.initial_state
        return PatientState(
            vitals=data.get("vitals", {}),
            labs=data.get("labs", {}),
            flags=data.get("flags", {}),
            consults=data.get("consults", {}),
            narrative_notes=data.get("narrative_notes", []),
            elapsed_minutes=data.get("elapsed_minutes", 0),
        )
