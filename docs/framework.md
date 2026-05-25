# Framework author guide

## Scenario file structure

Each scenario under `scenarios/dystonia_icu/<id>.yaml` includes:

- **meta** — `id`, `title`, `learning_objectives`, optional `ui_spec_id` for StormCode dashboards
- **initial_state** — `vitals`, `labs`, `flags`, `consults`, `narrative_notes`, `elapsed_minutes`
- **nodes** — narrative and **choices** with `effects`, `score_delta`, `competency_tags`
- **transitions** — automatic branches when `when` predicates match
- **endpoints** — terminal outcomes (`success`, `partial`, `failure`)
- **critical_misses** — penalties when conditions fire without learner action

## Predicates

Use only structured conditions (no `eval`):

```yaml
when:
  path: flags.storm_code_active
  op: eq
  value: true
```

Operators: `eq`, `neq`, `gt`, `gte`, `lt`, `lte`, `in`, `contains`. Combine with `all`, `any`, `not`.

Paths: `vitals.*`, `labs.*`, `flags.*`, `consults.*`, `elapsed_minutes`.

## Disability-specialist tags

Tag choices with competencies such as `DS-01` (functional baseline), `DS-02` (accommodations). Map to rubric dimensions via `score_delta` keys:

- `functional_assessment`
- `accommodation_planning`
- `interprofessional_coordination`
- `patient_centered_communication`
- `safety_escalation`

## StormCode integration

1. Add UI JSON under `ui_specs/` with `stableId`, `uiZones`, `criticalRules`, `nursingActions`.
2. Set `meta.ui_spec_id` on the scenario to that `stableId`.
3. Reference `nursing_action_id` on choices and `violates_critical_rule` for rule-breaking options.

## Validation

```bash
dystonia-sim validate scenarios/
```

## Adding a scenario

1. Copy an existing YAML and change `meta.id`.
2. Run validate.
3. Add a row to README scenario table.
4. Add a test path in `tests/test_scenario_validation.py` if needed.
