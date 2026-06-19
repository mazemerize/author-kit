"""`authorkit autopilot` — the semi-autonomous authoring loop.

A deterministic harness that stitches clean LLM sessions of the existing
commands (write / review / research / discuss) over either chapter drafting
(`chapters`) or the plan layer (`plot`). Each tick a planning agent decides the
single next action (or to stop / escalate); this module observes, dispatches
that one action, checkpoints, and enforces the hard stops. It changes none of
the existing command behavior.

See docs/autopilot.md (design) and docs/autopilot-implementation.md (plan).

Author:
    mdemarne
"""

from __future__ import annotations

import re
import subprocess
from datetime import datetime
from pathlib import Path

import typer
from rich.console import Console

from .autopilot_core import (
    ESCALATION_TYPES,
    Directive,
    DirectiveError,
    all_chapters_approved,
    detect_no_progress,
    detect_oscillation,
    directive_to_obj,
    kill_switch_present,
    log_tick,
    preflight,
    write_escalation,
)
from .autopilot_runner import detect_flavor, get_runner
from .book_core import find_repo_root, resolve_book_dir, to_json
from .book_status import collect_status, status_report_to_obj

# Shared Rich console for AutoPilot output.
console = Console()
# Root Typer group registered as `authorkit autopilot`.
autopilot_app = typer.Typer(help="Autonomous authoring loop")

# Absolute backstop so a logic error can never loop forever (escalations,
# completion, --max-iters, and loop-health are the real stops; this is a net).
MAX_TICKS = 500

# Recommended resolution command per escalation type (the record names the door).
_RESOLVERS = {
    "quality-stall": "/authorkit.write <N> revise: <issue>",
    "grounding-gap": "/authorkit.research <topic>",
}


def _default_resolver(esc_type: str) -> str:
    """Recommended resolution command for an escalation type (discuss by default)."""
    return _RESOLVERS.get(esc_type, '/authorkit.discuss "resolve <ESC-ID>: <decision>"')


def _format_options(options: object) -> str:
    """Render planner-supplied options (list or string) into one line."""
    if isinstance(options, list):
        return "; ".join(str(item) for item in options if str(item).strip())
    return str(options).strip() if options else ""


def _parse_range(value: str) -> tuple[int, int]:
    """Parse a ``--range`` value (``A-B`` or a single ``A``) into (lo, hi)."""
    text = value.strip()
    match = re.match(r"^(\d+)\s*-\s*(\d+)$", text)
    if match:
        lo, hi = int(match.group(1)), int(match.group(2))
    elif re.match(r"^\d+$", text):
        lo = hi = int(text)
    else:
        raise typer.BadParameter("--range must be 'A-B' or a single chapter number, e.g. 1-8")
    if lo > hi:
        raise typer.BadParameter(f"--range start ({lo}) must be <= end ({hi}).")
    if lo < 1:
        raise typer.BadParameter("--range chapters must be >= 1.")
    return (lo, hi)


def _mode_brief(mode: str, chapter_range: tuple[int, int] | None, max_iters: int) -> str:
    """One-paragraph situational brief handed to the planner each tick."""
    if mode == "chapters" and chapter_range is not None:
        lo, hi = chapter_range
        return (
            f"chapters — draft and review chapters CH{lo:02d}-CH{hi:02d}. Choose the single next action "
            "(plan / draft / review / revise / research) for the lowest unfinished chapter in range, or "
            "escalate when a creative or structural decision is required. Never touch chapters outside the "
            "range or approved [X] chapters."
        )
    return (
        f"plot — develop the plan layer (outline, world, chapter plans, grounding) for up to {max_iters} ticks. "
        "Choose the single next action (typically a write-outline / write-plan / research / discuss-style command), "
        "return action 'done' when the plan is solid, or escalate when a story-direction decision is required."
    )


def _strip_frontmatter(text: str) -> str:
    """Drop a leading ``---`` YAML frontmatter block, returning the body."""
    text = text.lstrip("﻿")
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end >= 0:
            return text[end + 5 :]
    return text


def _load_planner_prompt(repo_root: Path) -> str:
    """Load the rendered planner prompt body for the installed flavor.

    Falls back to the canonical asset, then to an empty string (the FakeRunner
    ignores the prompt; real runners only see empty if assets are missing).
    """
    flavor = detect_flavor(repo_root)
    rendered = {
        "claude": repo_root / ".claude" / "commands" / "authorkit.autopilot-plan.md",
        "codex": repo_root / ".codex" / "prompts" / "authorkit.autopilot-plan.md",
        "copilot": repo_root / ".github" / "prompts" / "authorkit.autopilot-plan.prompt.md",
    }
    candidates = [rendered.get(flavor), repo_root / ".authorkit" / "prompts" / "authorkit.autopilot-plan.md"]
    for path in candidates:
        if path and path.is_file():
            try:
                return _strip_frontmatter(path.read_text(encoding="utf-8-sig"))
            except (OSError, UnicodeDecodeError):
                continue
    return ""


def _progress_key(mode: str, report) -> tuple:
    """A comparable snapshot of "progress" for loop-health checks.

    chapters mode keys on the chapter-status breakdown (any transition moves it);
    plot mode keys on the broader planning surface (outline presence, world
    growth, chapter list), since planning may not move chapter statuses.
    """
    counts = tuple(sorted(report.chapter_status_counts.items()))
    if mode == "chapters":
        return counts
    return (report.has_outline, report.world_entities, report.world_aliases, tuple(report.chapters_md_entries), counts)


def _completion_check(mode: str, book_dir: Path, chapter_range: tuple[int, int] | None) -> Directive | None:
    """Deterministic stop: chapters mode is done when the whole range is ``[X]``."""
    if mode == "chapters" and chapter_range is not None and all_chapters_approved(book_dir, chapter_range):
        lo, hi = chapter_range
        return Directive(action="done", reason=f"All chapters CH{lo:02d}-CH{hi:02d} are approved.")
    return None


def _plan_once(runner, prompt: str, report, brief: str) -> Directive:
    """Run the planner against the current status and return its directive."""
    status_json = to_json(status_report_to_obj(report))
    return runner.run_planner(prompt, status_json, brief)


def _today() -> str:
    """Today's date as ``YYYY-MM-DD`` for escalation filenames/records."""
    return datetime.now().strftime("%Y-%m-%d")


def _write_planner_escalation(book_dir: Path, directive: Directive) -> Path:
    """Write an escalation record from a planner ``escalate`` directive."""
    esc = directive.escalation or {}
    esc_type = str(esc.get("type", "story-fork"))
    if esc_type not in ESCALATION_TYPES:
        esc_type = "story-fork"
    return write_escalation(
        book_dir,
        esc_type=esc_type,
        trigger=str(esc.get("trigger", directive.reason or "")),
        decision_needed=str(esc.get("decision_needed", directive.reason or "")),
        today=_today(),
        context=str(esc.get("context", "")),
        options=_format_options(esc.get("options")),
        recommended_command=str(esc.get("recommended_command") or _default_resolver(esc_type)),
    )


def _write_health_escalation(book_dir: Path) -> Path:
    """Write a loop-health escalation (oscillation / no-progress trip)."""
    return write_escalation(
        book_dir,
        esc_type="loop-health",
        trigger="AutoPilot made no progress across recent ticks (oscillation or stalled status).",
        decision_needed=(
            "AutoPilot stalled — inspect book/runs/autopilot.jsonl and the latest review, then adjust "
            "the plan, the chapter, or the constitution before resuming."
        ),
        today=_today(),
        recommended_command='/authorkit.discuss "resolve <ESC-ID>: <decision>"',
        title="AutoPilot stalled (loop-health)",
        slug="autopilot-stalled",
    )


def _write_planner_failure_escalation(book_dir: Path, detail: str) -> Path:
    """Write a loop-health escalation when the planner won't return a valid directive."""
    return write_escalation(
        book_dir,
        esc_type="loop-health",
        trigger=f"Planner failed to return a valid directive twice: {detail}",
        decision_needed="The planning agent did not return a parseable directive — inspect the planner prompt / agent CLI.",
        today=_today(),
        recommended_command="",
        title="Planner returned no valid directive",
        slug="planner-failure",
    )


def _git_checkpoint(repo_root: Path, directive: Directive, tick: int) -> None:
    """Best-effort ``git add -A && git commit`` after an accepted tick (--commit)."""
    message = f"autopilot: {directive.action} {directive.command or ''} (tick {tick})".strip()
    try:
        subprocess.run(["git", "add", "-A"], cwd=str(repo_root), check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
        proc = subprocess.run(["git", "commit", "-m", message], cwd=str(repo_root), capture_output=True, text=True, encoding="utf-8", errors="replace")
        if proc.returncode != 0 and "nothing to commit" not in (proc.stdout + proc.stderr).lower():
            console.print(f"[yellow]Checkpoint commit skipped:[/yellow] {(proc.stderr or proc.stdout).strip()[:160]}")
    except (OSError, subprocess.SubprocessError) as exc:
        console.print(f"[yellow]Checkpoint commit failed:[/yellow] {exc}")


def _resolve_book_or_exit(repo_root: Path) -> Path:
    """Resolve the book/ workspace or exit with actionable guidance."""
    try:
        return resolve_book_dir(repo_root)
    except FileNotFoundError as exc:
        console.print(f"[red]No book workspace found:[/red] {exc}")
        console.print("[dim]Run /authorkit.discuss to create the book/ workspace.[/dim]")
        raise typer.Exit(code=1) from exc


def _run_autopilot(
    mode: str,
    *,
    range_: str | None,
    max_iters: int,
    dry_run: bool,
    step: bool,
    commit: bool,
    permission_mode: str | None = None,
) -> None:
    """Shared driver for both autopilot modes."""
    repo_root = find_repo_root()
    book_dir = _resolve_book_or_exit(repo_root)
    chapter_range = _parse_range(range_) if range_ else None

    pf = preflight(mode, book_dir, repo_root, chapter_range=chapter_range)
    if not pf.ok:
        console.print(f"[red]AutoPilot preflight failed ({mode} mode):[/red]")
        for err in pf.errors:
            console.print(f"  - {err}")
        console.print("[dim]Seed the book first, then re-run.[/dim]")
        raise typer.Exit(code=2)

    # Autonomy requires the worker to use tools without prompts: a headless agent
    # under default permissions cannot write files or run the setup/world-index
    # scripts, so the loop would make no progress. Default to skipping permission
    # checks (the only posture in which the loop actually works unattended) unless
    # the user restricts it with --permission-mode.
    skip_permissions = permission_mode is None
    if not dry_run:
        if skip_permissions:
            console.print(
                "[yellow]Heads-up:[/yellow] AutoPilot runs each worker with "
                "[bold]--dangerously-skip-permissions[/bold] (full tool access, no prompts) so it can "
                "write files and run scripts unattended. Pass [bold]--permission-mode <mode>[/bold] "
                "(e.g. acceptEdits, default) to restrict — note tighter modes may stall on scripts."
            )
        else:
            console.print(f"[dim]Workers run with --permission-mode {permission_mode}.[/dim]")

    runner = get_runner(repo_root, permission_mode=permission_mode, skip_permissions=skip_permissions)
    planner_prompt = _load_planner_prompt(repo_root)
    brief = _mode_brief(mode, chapter_range, max_iters)
    run_id = datetime.now().strftime("%Y%m%dT%H%M%S")

    # Dry-run: show the next directive (a preview), write nothing, dispatch nothing.
    if dry_run:
        report = collect_status(book_dir, repo_root)
        directive = _completion_check(mode, book_dir, chapter_range) or _plan_once(runner, planner_prompt, report, brief)
        console.print(
            to_json({"mode": mode, "tick": 1, "directive": directive_to_obj(directive)}),
            markup=False,
            highlight=False,
            soft_wrap=True,
        )
        return

    history: list[dict] = []
    tick = 0
    while True:
        tick += 1
        if tick > MAX_TICKS:
            console.print(f"[red]Halting:[/red] safety cap of {MAX_TICKS} ticks reached.")
            raise typer.Exit(code=1)

        report = collect_status(book_dir, repo_root)

        # Hard stops (safety, not budget).
        if report.open_escalations:
            ids = ", ".join(report.escalation_ids) if report.escalation_ids else f"{report.open_escalations}"
            console.print(
                f"[yellow]Halting:[/yellow] open escalation(s): {ids}. "
                "Resolve via /authorkit.discuss, then re-run."
            )
            raise typer.Exit(code=0)
        if kill_switch_present(book_dir):
            console.print("[yellow]Halting:[/yellow] kill switch present (book/runs/STOP).")
            raise typer.Exit(code=0)
        if detect_oscillation(history) or (mode == "chapters" and detect_no_progress(history)):
            path = _write_health_escalation(book_dir)
            console.print(
                f"[yellow]Halting:[/yellow] loop-health trip (no progress / oscillation). Wrote {path.name}."
            )
            raise typer.Exit(code=0)

        # Decide: deterministic completion first, else ask the planner (one retry).
        directive = _completion_check(mode, book_dir, chapter_range)
        if directive is None:
            try:
                directive = _plan_once(runner, planner_prompt, report, brief)
            except (DirectiveError, RuntimeError):
                try:
                    directive = _plan_once(runner, planner_prompt, report, brief)
                except (DirectiveError, RuntimeError) as exc:
                    path = _write_planner_failure_escalation(book_dir, str(exc))
                    console.print(
                        f"[red]Halting:[/red] planner did not return a valid directive ({exc}). Wrote {path.name}."
                    )
                    raise typer.Exit(code=1) from exc

        # Terminal directives.
        if directive.action == "done":
            console.print(f"[green]AutoPilot done[/green] ({mode}): {directive.reason or 'nothing left in scope.'}")
            raise typer.Exit(code=0)
        if directive.action == "escalate":
            path = _write_planner_escalation(book_dir, directive)
            console.print(
                f"[yellow]Escalation:[/yellow] wrote {path.name}. Resolve it (recommended command is in the "
                "record), then re-run."
            )
            raise typer.Exit(code=0)

        # Act: dispatch the one chosen command in a clean session.
        key_before = _progress_key(mode, report)
        console.print(f"[dim]tick {tick}[/dim] {directive.action}: {directive.command} [dim]({directive.reason})[/dim]")
        result = runner.run_command(directive.command)

        report_after = collect_status(book_dir, repo_root)
        status_changed = _progress_key(mode, report_after) != key_before

        entry: dict = {
            "tick": tick,
            "action": directive.action,
            "command": directive.command,
            "ok": result.ok,
            "status_changed": status_changed,
            "reason": directive.reason,
        }
        if not result.ok:
            entry["error"] = result.error[:500]
            console.print(f"[yellow]Command reported failure:[/yellow] {result.error[:200]}")
        history.append(entry)
        log_tick(book_dir, {"run": run_id, **entry})

        if commit:
            _git_checkpoint(repo_root, directive, tick)

        if step:
            console.print("[dim]--step: stopping after one tick.[/dim]")
            raise typer.Exit(code=0)
        if mode == "plot" and tick >= max_iters:
            console.print(f"[green]AutoPilot reached --max-iters={max_iters}[/green] (plot).")
            raise typer.Exit(code=0)


@autopilot_app.command("chapters")
def chapters_cmd(
    range_: str = typer.Option(..., "--range", help="Chapter range to draft, e.g. 1-8 (or a single number)."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show the planner's next directive; act on nothing."),
    step: bool = typer.Option(False, "--step", help="Run a single tick, then stop."),
    commit: bool = typer.Option(False, "--commit", help="git commit after each accepted tick."),
    permission_mode: str | None = typer.Option(None, "--permission-mode", help="Restrict worker tool access to this mode (e.g. acceptEdits, default). Default: full access via --dangerously-skip-permissions."),
) -> None:
    """Autonomously plan/draft/review chapters across a range, escalating on decisions."""
    _run_autopilot(
        "chapters",
        range_=range_,
        max_iters=MAX_TICKS,
        dry_run=dry_run,
        step=step,
        commit=commit,
        permission_mode=permission_mode,
    )


@autopilot_app.command("plot")
def plot_cmd(
    max_iters: int = typer.Option(10, "--max-iters", help="Maximum planning ticks before stopping (plot is open-ended)."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show the planner's next directive; act on nothing."),
    step: bool = typer.Option(False, "--step", help="Run a single tick, then stop."),
    commit: bool = typer.Option(False, "--commit", help="git commit after each accepted tick."),
    permission_mode: str | None = typer.Option(None, "--permission-mode", help="Restrict worker tool access to this mode (e.g. acceptEdits, default). Default: full access via --dangerously-skip-permissions."),
) -> None:
    """Autonomously develop the plan layer (outline, world, plans), escalating on direction."""
    if max_iters < 1:
        raise typer.BadParameter("--max-iters must be >= 1.")
    _run_autopilot(
        "plot",
        range_=None,
        max_iters=max_iters,
        dry_run=dry_run,
        step=step,
        commit=commit,
        permission_mode=permission_mode,
    )
