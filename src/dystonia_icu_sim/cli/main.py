from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from dystonia_icu_sim.debrief.export import (
    export_debrief_markdown,
    load_run,
    save_run,
)
from dystonia_icu_sim.engine.engine import SimulationEngine
from dystonia_icu_sim.engine.loader import (
    list_scenarios,
    load_scenario,
    validate_directory,
)
from dystonia_icu_sim.paths import SCENARIOS_DIR
from dystonia_icu_sim.scoring.service import ScoringService
from dystonia_icu_sim.ui.loader import load_ui_spec, render_dashboard_text

DISCLAIMER = (
    "[yellow]Educational simulation only — not medical advice. "
    "Synthetic patients; no PHI.[/yellow]"
)

app = typer.Typer(
    name="dystonia-sim",
    help="Disability specialist medical simulation for acute dystonia ICU training.",
    no_args_is_help=True,
)
console = Console()


@app.command("list")
def list_cmd() -> None:
    """List available scenarios."""
    scenarios = list_scenarios()
    table = Table(title="Scenarios")
    table.add_column("ID")
    table.add_column("Title")
    table.add_column("Difficulty")
    for s in scenarios:
        table.add_row(s["id"], s["title"], s["difficulty"])
    console.print(table)


@app.command("validate")
def validate_cmd(
    path: Optional[Path] = typer.Argument(
        None, help="Directory to validate (default: scenarios/)"
    ),
) -> None:
    """Validate scenario YAML files against JSON Schema."""
    directory = path or SCENARIOS_DIR
    results = validate_directory(directory)
    failed = 0
    for file_path, errors in results:
        if errors:
            failed += 1
            console.print(f"[red]FAIL[/red] {file_path}")
            for err in errors:
                console.print(f"  - {err}")
        else:
            console.print(f"[green]OK[/green] {file_path}")
    if failed:
        raise typer.Exit(code=1)
    console.print(f"\nValidated {len(results)} file(s), all passed.")


def _print_status(run) -> None:
    p = run.patient
    vitals = ", ".join(f"{k}={v}" for k, v in p.vitals.items())
    consults = ", ".join(f"{k}={v}" for k, v in p.consults.items()) or "none"
    console.print(
        Panel(
            f"Vitals: {vitals or 'n/a'}\n"
            f"Elapsed: {p.elapsed_minutes} min\n"
            f"Consults: {consults}",
            title="Status",
            border_style="dim",
        )
    )


def _interactive_loop(engine: SimulationEngine, run) -> None:
    while not run.terminal:
        node = engine.get_current_node(run)
        console.print(Panel(node.narrative, title=f"Node: {node.id}", border_style="blue"))
        _print_status(run)

        if not node.choices:
            break

        for i, choice in enumerate(node.choices, 1):
            console.print(f"  [bold]{i}[/bold]. {choice.label}")
        console.print("  [dim]hint <n> | status | quit[/dim]")

        raw = console.input("\nSelect option: ").strip().lower()
        if raw in ("quit", "q"):
            run.terminal = True
            run.outcome = "incomplete"
            break
        if raw == "status":
            continue
        if raw.startswith("hint"):
            parts = raw.split()
            idx = int(parts[1]) - 1 if len(parts) > 1 else 0
            if 0 <= idx < len(node.choices) and node.choices[idx].hint:
                console.print(f"[dim]Hint: {node.choices[idx].hint}[/dim]")
            else:
                console.print("[dim]No hint for that option.[/dim]")
            continue

        try:
            idx = int(raw) - 1
        except ValueError:
            console.print("[red]Enter a number, hint <n>, status, or quit.[/red]")
            continue
        if idx < 0 or idx >= len(node.choices):
            console.print("[red]Invalid option.[/red]")
            continue

        engine.apply_choice(run, node.choices[idx])

    if run.terminal and run.endpoint_id:
        endpoint = engine.scenario.endpoints.get(run.endpoint_id)
        if endpoint:
            console.print(
                Panel(endpoint.narrative, title=f"Outcome: {endpoint.outcome}", border_style="green")
            )


@app.command("run")
def run_cmd(
    scenario_id: str = typer.Argument(..., help="Scenario ID (e.g. status_dystonicus_01)"),
    seed: int = typer.Option(0, help="Random seed for reproducibility"),
    role: str = typer.Option("learner", help="Learner role label"),
) -> None:
    """Run an interactive simulation scenario."""
    console.print(DISCLAIMER)
    scenario = load_scenario(scenario_id)
    engine = SimulationEngine(scenario, seed=seed, role=role)
    run = engine.start()
    console.print(
        Panel(
            f"{scenario.meta.title}\n"
            f"Objectives: {', '.join(scenario.meta.learning_objectives)}",
            title="Scenario",
        )
    )
    if scenario.meta.ui_spec_id:
        try:
            ui_spec = load_ui_spec(scenario.meta.ui_spec_id)
            console.print(
                Panel(
                    render_dashboard_text(ui_spec, run.patient),
                    title="StormCode Dashboard",
                    border_style="red",
                )
            )
        except FileNotFoundError:
            console.print(f"[yellow]UI spec not found: {scenario.meta.ui_spec_id}[/yellow]")
    _interactive_loop(engine, run)
    scoring = ScoringService().score_run(run)
    path = save_run(run, scoring)
    md_path = path.with_suffix(".md")
    md_path.write_text(export_debrief_markdown(run, scoring), encoding="utf-8")
    console.print(f"\n[green]Run saved:[/green] {path}")
    console.print(f"[green]Debrief:[/green] {md_path}")
    console.print(
        f"Score: {scoring.total_normalized:.0%} ({scoring.band}) — "
        f"{'PASS' if scoring.passed else 'REVIEW'}"
    )


@app.command("debrief")
def debrief_cmd(run_id: str = typer.Argument(..., help="Run UUID from a prior session")) -> None:
    """Show debrief for a saved run."""
    data = load_run(run_id)
    run_data = data["run"]
    scoring_data = data.get("scoring", {})
    console.print(DISCLAIMER)
    console.print(f"Scenario: {run_data['scenario_id']}")
    console.print(f"Outcome: {run_data.get('outcome', 'unknown')}")
    if scoring_data:
        console.print(
            f"Score: {scoring_data.get('total_normalized', 0):.0%} "
            f"({scoring_data.get('band')})"
        )
    for event in run_data.get("events", []):
        if event["event_type"] == "choice":
            console.print(
                f"- {event['choice_id']}: {event['details'].get('label', '')}"
            )
    md_path = Path(str(run_id))
    stored = Path(".runs") / f"{run_id}.md"
    if stored.exists():
        console.print(Panel(stored.read_text(encoding="utf-8"), title="Debrief"))


@app.command("ui")
def ui_cmd(
    spec_id: str = typer.Argument(
        "STORMCODE_NOAH_POST_STAGE2_UI_V1",
        help="UI spec stableId or filename stem",
    ),
) -> None:
    """Display StormCode multimodal dashboard layout (text mode)."""
    console.print(DISCLAIMER)
    spec = load_ui_spec(spec_id)
    console.print(Panel(render_dashboard_text(spec), title=spec.title, border_style="cyan"))
    table = Table(title="Nursing actions")
    table.add_column("ID")
    table.add_column("Label")
    for action in spec.nursingActions:
        table.add_row(action.id, action.label)
    console.print(table)


if __name__ == "__main__":
    app()
