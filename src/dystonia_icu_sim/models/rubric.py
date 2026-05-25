from pydantic import BaseModel, Field


class RubricDimension(BaseModel):
    id: str
    name: str
    weight: float = 1.0
    description: str = ""


class Rubric(BaseModel):
    id: str
    name: str
    dimensions: list[RubricDimension] = Field(default_factory=list)
    pass_threshold: float = 0.7
    bands: dict[str, float] = Field(
        default_factory=lambda: {
            "excellent": 0.9,
            "proficient": 0.7,
            "developing": 0.5,
        }
    )
