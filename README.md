# DystoniaICUSim

A **disability specialist medical simulation framework** for acute dystonia and ICU neuro-respiratory crisis training. Scenarios are authored in YAML; a Python engine runs branching cases with competency rubrics, event logs, and debrief export.

**Educational use only — not medical advice.** All patients are synthetic; no PHI.

## Features

- Scenario engine with safe predicate-based auto-transitions
- Disability-specialist rubric (functional assessment, accommodations, coordination, communication, safety)
- CLI interactive runs with scoring and markdown debrief
- **StormCode** multimodal UI spec for high-acuity pediatric crisis (Noah post-stage-2)
- JSON Schema validation for scenario content

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

dystonia-sim list
dystonia-sim validate
dystonia-sim run status_dystonicus_01
dystonia-sim run noah_stormcode_post_stage2
dystonia-sim ui STORMCODE_NOAH_POST_STAGE2_UI_V1
pytest
```

## Scenarios

| ID | Description |
|----|-------------|
| `status_dystonicus_01` | Adult ICU status dystonicus with PM&R/AAC focus |
| `medication_trial_02` | Baclofen pump adjustment with disability supports |
| `noah_stormcode_post_stage2` | StormCode pediatric airway–neuro–respiratory crisis (links UI spec) |

## StormCode UI

The file [`ui_specs/stormcode_noah_post_stage2_ui.json`](ui_specs/stormcode_noah_post_stage2_ui.json) defines the **high-acuity multimodal dashboard**: ICU command board, timeline, airway/FONA, neuro-storm, cardiopulmonary, nursing continuity, AAC, and family-ethics panels. Critical rules (e.g. do not remove AAC, do not label as behavioural) are enforced in scenario choices.

## Project layout

- `src/dystonia_icu_sim/` — engine, scoring, debrief, CLI, UI loader
- `scenarios/dystonia_icu/` — scenario YAML
- `scenarios/schema/` — JSON Schema
- `rubrics/` — competency weights
- `ui_specs/` — StormCode and future dashboard specs
- `docs/` — author guide and competencies

## License

Mozilla Public License 2.0 — see [LICENSE](LICENSE).
