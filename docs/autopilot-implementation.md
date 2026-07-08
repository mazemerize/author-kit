# AutoPilot — Implementation Plan

**Status:** Draft / Proposed
**Date:** 2026-06-18
**Owner:** @mdemarne
**Spec:** [`autopilot.md`](autopilot.md)

Turns the [AutoPilot design](autopilot.md) into a sequenced, testable build. Each
phase is a focused, independently shippable PR (per `CONTRIBUTING.md`), and every
phase ships with tests.

## Guiding principle

**All agent invocation goes through a single injectable seam.** The loop logic
(observe → decide → dispatch → checkpoint → escalate) must be testable without
spending tokens or needing a live agent. Define one interface — `AgentRunner` — with
a real implementation and a `FakeRunner` for tests. Get this seam right in Phase 1
and every later phase is unit-testable with scripted directives.

## Module layout

Mirrors the existing `book_*` modules + sub-typer pattern.

```
src/authorkit_cli/
  autopilot_runner.py    # AgentRunner protocol; ClaudeRunner (MVP); FakeRunner; flavor detection
  autopilot_core.py      # Directive, preflight, escalation records, tick log, loop-health, kill switch
  autopilot_commands.py  # autopilot_app: `chapters` + `plot`; registered on app like book_app
# edited:
  __init__.py            # add_typer(autopilot_app); status gains --json
  book_status.py         # serialize StatusReport; count OPEN escalations
.authorkit/
  prompts/authorkit.autopilot-plan.md   # planner prompt (canonical, rendered per flavor)
  prompts/authorkit.discuss.md          # + escalation-resolve handling
  templates/escalation-template.md      # ESC-NNN record schema (mirrors parked-decisions-template)
src/tests/test_cli.py                   # + autopilot tests
```

## Phase 0 — `status --json` + escalation count · size S

The smallest, fully independent slice; unblocks the planner's input.

- **Build:** in `book_status.py`, add `open_escalations` / `escalation_ids` to
  `StatusReport` (scan `book/escalations/*.md` for `**Status**: OPEN`, reusing the
  parked-decisions parse style); add a `status_report_to_obj(report)` that stringifies
  `Path`s. In the `status` command, add `--json`, emitting raw JSON via `to_json`
  (`book_core.py`) with `markup=False, highlight=False`. Surface an
  `Escalations: N open` line in `format_status_lines`.
- **Test:** JSON parses; has `chapters` / `world` / `parked` / `escalations` / `drift`
  keys; escalation count correct against a fixture dir.
- **Validate:** `uv run --with typer --with rich python -m authorkit_cli status --json`
- **DoD:** valid machine-readable status; escalations counted even with an empty dir.

## Phase 1 — Planner seam + preflight + `--dry-run` · size M

The read-only slice from the spec: watch the planner pick one directive per tick, no writes.

- **Build:**
  - `autopilot_runner.py`: `AgentRunner` protocol (`run_planner(status_json, mode) ->
    Directive`, `run_command(cmd) -> RunResult`); `ClaudeRunner` (MVP) that feeds
    *planner prompt + status JSON* to a headless session and parses a fenced JSON
    reply; `FakeRunner`; flavor detection from `install-manifest.json` (`ais` / `script`).
  - `autopilot_core.py`: `Directive` dataclass + strict validation (`action` enum;
    `command` required for act actions; `escalation` for escalate; invalid JSON →
    retry once → loop-health escalation); `preflight(mode, range)` — mode-aware seed
    gate (concept present; constitution not still template-stamped via `[PRINCIPLE_` /
    `[BOOK_TITLE]`; `outline.md` + `chapters.md` cover `--range`), refusing with
    `[red]` + `[dim]` hint to `/authorkit.discuss`.
  - `.authorkit/prompts/authorkit.autopilot-plan.md`: the planner prompt — reads
    status JSON, emits one directive (schema in the spec). **Not** in
    `GUARDRAIL_PROMPT_ALLOWLIST` (it decides, it doesn't write prose).
  - `autopilot_commands.py`: `autopilot chapters/plot ... --dry-run` → preflight +
    observe + `run_planner` once + print directive + exit.
- **Spike first (de-risks Phase 2+):** confirm the exact headless invocation +
  JSON-capture for the target agent (`claude -p … --output-format json` or
  fenced-JSON parse). This is the spec's main open question.
- **Test:** preflight refusals per mode (exit code + hint); directive validation
  (valid / invalid / garbage); `--dry-run` with `FakeRunner` prints the directive,
  writes nothing, exits 0.
- **Validate:** `… autopilot chapters --range 1-3 --dry-run` against a seeded fixture book.
- **DoD:** on a real seeded book, the planner returns a sane next action; bad seeds
  are refused.

## Phase 2 — Single-tick execution + escalation records + discuss resolve · size M

Supervised: do exactly one real tick, then stop. Proves dispatch + the escalation round-trip.

- **Build:**
  - `ClaudeRunner.run_command` — dispatch `directive.command` (e.g. `/authorkit.write
    7`) headless in a fresh session.
  - `autopilot_core`: escalation writer → `book/escalations/<date>-ESC-NNN-<slug>.md`
    from the new `escalation-template.md` (sequential `ESC-NNN`); kill-switch +
    tick-log scaffolding.
  - `autopilot_commands`: `--step` (one tick then stop); on `escalate` write record +
    halt; on `done` report.
  - **discuss extension** (edit `authorkit.discuss.md`): list open escalations
    alongside parked decisions; recognize `resolve ESC-NNN`; close the record
    (`RESOLVED` + Resolution block) on resolution — mirroring existing Park-resolve.
    Add the escalation template to its template list.
- **Test:** `--step` with `FakeRunner` → status transitions as expected; an `escalate`
  directive writes a well-formed `OPEN` record and halts; the loop refuses to start
  while an escalation is `OPEN`.
- **Validate:** `… autopilot chapters --range 1-1 --step` end-to-end on a fixture;
  then resolve a hand-made escalation via `/authorkit.discuss` and confirm the loop
  proceeds.
- **DoD:** one tick drafts/reviews a real chapter; escalation → record →
  discuss-resolve → resume works.

## Phase 3 — Bounded unattended loop (chapters) · size M/L

The full `chapters` loop over a range.

- **Build:** the loop in `autopilot_commands` (observe → plan → dispatch → checkpoint,
  repeat); hard stops in `autopilot_core` (oscillation = same directive w/o status
  change; no-progress across K ticks; repeated tool errors; `book/runs/STOP` kill
  switch) → each writes a `loop-health` escalation and halts; per-tick JSONL log to
  `book/runs/`. **Git checkpoint is opt-in** (`--commit`, default off): auto-committing
  on `main` is sensitive, so default to leaving writes in the working tree; when
  enabled, commit to a dedicated `autopilot/*` branch.
- **Test:** scripted `FakeRunner` sequences — act→act→done (range completes);
  oscillation → loop-health escalation; kill-switch halts after the current tick.
- **Validate:** a real bounded run over one part; inspect `book/runs/*.jsonl` +
  `chapters.md` transitions.
- **DoD:** a part drafts end-to-end unattended, halting cleanly on completion,
  escalation, or a health trip.

## Phase 4 — `plot` mode + multi-flavor + notifications · size L

- **Build:** planner behavior for the plan/plot layer + `--max-iters` termination;
  `CodexRunner` / `CopilotRunner` behind the same `AgentRunner` seam (additive — the
  abstraction is already there); escalation notifications for unattended runs
  (push / PR comment).
- **Test:** plot-mode dry-run + `--max-iters` stop; a runner-conformance test suite
  each backend must pass.
- **DoD:** `plot` runs to a solid plan or `--max-iters`; at least one second flavor
  passes conformance.

## Cross-cutting

- **Conventions:** brand (`Author Kit` / lowercase `authorkit`, never `AuthorKit`),
  `[green]/[yellow]/[red]/[dim]` + actionable errors, lowercase `book/...` dirs. All
  new prompts stay canonical in `.authorkit/prompts/`. README gets a user-facing
  AutoPilot section in the Phase 3 PR (first real CLI surface), per `CONTRIBUTING.md`.
- **Testing note:** when running the suite from a worktree, set `PYTHONPATH` to that
  worktree's `src` or pytest silently tests the main checkout. Suite:
  `uv run pytest src/tests/test_cli.py`.
- **Top risk:** the per-flavor headless invocation + reliable JSON capture from the
  planner. Mitigated by the Phase 1 spike and the `AgentRunner` seam (loop logic stays
  testable regardless).

## Recommended start

Phase 0 — small, independent, and it unblocks the planner's input.
