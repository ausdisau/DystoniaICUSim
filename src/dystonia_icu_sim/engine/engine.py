import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from dystonia_icu_sim.engine.predicates import evaluate_when
from dystonia_icu_sim.models.patient import PatientState
from dystonia_icu_sim.models.scenario import Choice, Scenario


@dataclass
class EventRecord:
    timestamp: str
    event_type: str
    node_id: str | None = None
    choice_id: str | None = None
    transition_id: str | None = None
    endpoint_id: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class SimulationRun:
    run_id: str
    scenario_id: str
    seed: int
    role: str
    patient: PatientState
    current_node_id: str
    events: list[EventRecord] = field(default_factory=list)
    scores: dict[str, float] = field(default_factory=dict)
    competency_hits: set[str] = field(default_factory=set)
    flags_triggered: set[str] = field(default_factory=set)
    terminal: bool = False
    endpoint_id: str | None = None
    outcome: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "scenario_id": self.scenario_id,
            "seed": self.seed,
            "role": self.role,
            "patient": self.patient.to_snapshot(),
            "current_node_id": self.current_node_id,
            "events": [
                {
                    "timestamp": e.timestamp,
                    "event_type": e.event_type,
                    "node_id": e.node_id,
                    "choice_id": e.choice_id,
                    "transition_id": e.transition_id,
                    "endpoint_id": e.endpoint_id,
                    "details": e.details,
                }
                for e in self.events
            ],
            "scores": self.scores,
            "competency_hits": sorted(self.competency_hits),
            "flags_triggered": sorted(self.flags_triggered),
            "terminal": self.terminal,
            "endpoint_id": self.endpoint_id,
            "outcome": self.outcome,
        }


class SimulationEngine:
    def __init__(self, scenario: Scenario, seed: int = 0, role: str = "learner"):
        self.scenario = scenario
        self.seed = seed
        self.role = role

    def start(self) -> SimulationRun:
        run = SimulationRun(
            run_id=str(uuid.uuid4()),
            scenario_id=self.scenario.meta.id,
            seed=self.seed,
            role=self.role,
            patient=self.scenario.build_initial_patient(),
            current_node_id=self.scenario.start_node,
        )
        self._log(run, "start", node_id=run.current_node_id)
        self._apply_auto_transitions(run)
        return run

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _log(
        self,
        run: SimulationRun,
        event_type: str,
        *,
        node_id: str | None = None,
        choice_id: str | None = None,
        transition_id: str | None = None,
        endpoint_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        run.events.append(
            EventRecord(
                timestamp=self._now(),
                event_type=event_type,
                node_id=node_id,
                choice_id=choice_id,
                transition_id=transition_id,
                endpoint_id=endpoint_id,
                details=details or {},
            )
        )

    def _apply_score_delta(self, run: SimulationRun, delta: dict[str, int]) -> None:
        for dim, points in delta.items():
            run.scores[dim] = run.scores.get(dim, 0.0) + float(points)

    def _check_critical_misses(self, run: SimulationRun) -> None:
        for miss in self.scenario.critical_misses:
            miss_id = miss.get("id", "unknown")
            if miss_id in run.flags_triggered:
                continue
            when = miss.get("when", {})
            if evaluate_when(run.patient, when):
                run.flags_triggered.add(miss_id)
                penalty = miss.get("penalty", {})
                self._apply_score_delta(run, penalty)
                self._log(
                    run,
                    "critical_miss",
                    details={"miss_id": miss_id, "description": miss.get("description")},
                )

    def _apply_auto_transitions(self, run: SimulationRun) -> None:
        changed = True
        while changed and not run.terminal:
            changed = False
            for transition in self.scenario.transitions:
                if evaluate_when(run.patient, transition.when):
                    run.current_node_id = transition.next_node
                    self._log(
                        run,
                        "auto_transition",
                        transition_id=transition.id,
                        node_id=run.current_node_id,
                        details={"narrative": transition.narrative},
                    )
                    if transition.narrative:
                        run.patient.narrative_notes.append(transition.narrative)
                    changed = True
                    break
            self._check_critical_misses(run)
            node = self.scenario.nodes.get(run.current_node_id)
            if node and node.is_terminal:
                self._resolve_terminal_node(run, node.id)

    def _resolve_terminal_node(self, run: SimulationRun, node_id: str) -> None:
        endpoint = self.scenario.endpoints.get(node_id)
        if endpoint:
            run.terminal = True
            run.endpoint_id = endpoint.id
            run.outcome = endpoint.outcome
            run.competency_hits.update(endpoint.competency_tags)
            self._apply_score_delta(run, endpoint.score_delta)
            self._log(run, "endpoint", endpoint_id=endpoint.id, node_id=node_id)

    def get_current_node(self, run: SimulationRun):
        return self.scenario.nodes[run.current_node_id]

    def apply_choice(self, run: SimulationRun, choice: Choice) -> None:
        if run.terminal:
            raise RuntimeError("Simulation already finished")

        if choice.violates_critical_rule:
            run.flags_triggered.add(choice.violates_critical_rule)
            self._log(
                run,
                "critical_rule_violation",
                node_id=run.current_node_id,
                choice_id=choice.id,
                details={"rule": choice.violates_critical_rule, "label": choice.label},
            )
            penalty = {dim: -3 for dim in ("functional_assessment", "safety_escalation")}
            self._apply_score_delta(run, penalty)

        run.patient.apply_patch(choice.effects.to_dict())
        if choice.time_cost:
            run.patient.elapsed_minutes += choice.time_cost

        run.competency_hits.update(choice.competency_tags)
        self._apply_score_delta(run, choice.score_delta)
        self._log(
            run,
            "choice",
            node_id=run.current_node_id,
            choice_id=choice.id,
            details={"label": choice.label},
        )

        next_node = choice.next_node
        if next_node:
            run.current_node_id = next_node

        self._apply_auto_transitions(run)

        if not run.terminal:
            node = self.scenario.nodes.get(run.current_node_id)
            if node and node.is_terminal:
                self._resolve_terminal_node(run, node.id)
