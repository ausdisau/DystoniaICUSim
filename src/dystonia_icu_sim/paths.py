"""Repository path helpers."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCENARIOS_DIR = REPO_ROOT / "scenarios"
RUBRICS_DIR = REPO_ROOT / "rubrics"
RUNS_DIR = REPO_ROOT / ".runs"
SCHEMA_PATH = SCENARIOS_DIR / "schema" / "scenario.schema.json"
