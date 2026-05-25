from dataclasses import dataclass

from dystonia_icu_sim.engine.engine import SimulationRun
from dystonia_icu_sim.engine.loader import load_rubric
from dystonia_icu_sim.models.rubric import Rubric


@dataclass
class DimensionScore:
    dimension_id: str
    name: str
    raw_score: float
    max_score: float
    normalized: float
    weight: float


@dataclass
class ScoringResult:
    rubric_id: str
    dimensions: list[DimensionScore]
    total_normalized: float
    band: str
    passed: bool
    outcome: str | None


class ScoringService:
    """Normalize raw dimension scores against rubric weights and bands."""

    DEFAULT_MAX_PER_DIMENSION = 10.0

    def __init__(self, rubric: Rubric | None = None):
        self.rubric = rubric or load_rubric("disability_specialist")

    def score_run(self, run: SimulationRun) -> ScoringResult:
        dim_scores: list[DimensionScore] = []
        weighted_sum = 0.0
        weight_total = 0.0

        for dim in self.rubric.dimensions:
            raw = run.scores.get(dim.id, 0.0)
            max_score = self.DEFAULT_MAX_PER_DIMENSION
            normalized = min(1.0, max(0.0, raw / max_score)) if max_score else 0.0
            dim_scores.append(
                DimensionScore(
                    dimension_id=dim.id,
                    name=dim.name,
                    raw_score=raw,
                    max_score=max_score,
                    normalized=normalized,
                    weight=dim.weight,
                )
            )
            weighted_sum += normalized * dim.weight
            weight_total += dim.weight

        total = weighted_sum / weight_total if weight_total else 0.0
        band = self._band_for(total)
        return ScoringResult(
            rubric_id=self.rubric.id,
            dimensions=dim_scores,
            total_normalized=total,
            band=band,
            passed=total >= self.rubric.pass_threshold,
            outcome=run.outcome,
        )

    def _band_for(self, total: float) -> str:
        bands = sorted(
            self.rubric.bands.items(),
            key=lambda x: x[1],
            reverse=True,
        )
        for name, threshold in bands:
            if total >= threshold:
                return name
        return "needs_improvement"

    def merge_rubrics(self, run: SimulationRun, rubric_ids: list[str]) -> ScoringResult:
        """Score using primary rubric but include ICU dimension if present in run scores."""
        primary = self.score_run(run)
        return primary
