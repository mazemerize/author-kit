# AutoPilot — Semi-Autonomous Authoring Loop (Design)

**Status:** Draft / Proposed
**Date:** 2026-06-18
**Owner:** @mdemarne

## Summary

AutoPilot is a semi-autonomous driver for Author Kit. It stitches together clean,
single-purpose LLM sessions of the **existing** four commands (`write`, `review`,
`research`, `discuss`) to iterate over either the **plot/plan** layer or **chapter
drafting**, pausing to **escalate** to the author whenever a creative, structural,
or quality decision is required.

It is an orchestration layer only. It adds no new prose-generation paths and does
not change how the existing commands behave — in particular, `review` keeps
flipping `[D]→[X]` / `[D]→[R]` exactly as it does today.

## Goals

- Iterate autonomously over (a) the plan/plot layer and (b) chapter drafting,
  **within a settled framing**.
- Reuse the existing commands as-is; the loop is orchestration, not new behavior.
- Stop and hand control to the author at every genuine decision point, with a
  clear, resumable escalation path.
- **Refuse to run without a proper seed.**
- Be fully resumable: kill at any point, restart from on-disk state.

## Non-goals

- No new prose generation or review logic — the workers are the existing commands.
- No change to current command behavior. `review` flips the status bit as today.
- **No out-of-process approval gate / anti-self-grading apparatus** (writer-can't-
  approve, hash-chained approval log, forced different-model reviewer, frozen
  golden set). Considered and rejected — see [Rejected alternatives](#rejected-alternatives).
- **No budget/cost knob.** Bounding is by `--range` (chapters) and `--max-iters` (plot).
- AutoPilot makes no creative decisions and never resolves its own escalations.

## Background

Author Kit already provides the substrate the loop needs:

- A chapter **state machine** in `chapters.md`: `[ ] → [P] → [D] → [R] → [X]`.
- Four self-dispatching commands that already reconcile state after writes and end
  with a suggested next command.
- `authorkit status`, a health view (chapters by status, draft/`chapters.md` drift,
  open/overdue parked decisions, world counts) that is straightforward to serialize.

AutoPilot is the missing piece: a deterministic driver plus a planning agent that
reads `status` and chooses the next single command to run.

## Architecture

Three layers; only the middle one is new code.

```
        ┌───────────────────────── authorkit autopilot (new code) ─────────────────────────┐
        │                                                                                   │
  OBSERVE  ──>  DECIDE  ──>  DISPATCH  ──>  (existing command runs)  ──>  CHECKPOINT ──> loop
  status        planning      one clean        write / review /             git commit
  --json        agent (LLM)   session          research / discuss           + tick log
                  │                                                              │
                  └── action = escalate / done ──> write record / stop ──────────┘
```

| Step | Owner | Why that owner |
|---|---|---|
| Observe | code — `authorkit status --json` | machine-readable, cheap, auditable; also feeds hard-stop checks |
| Decide next action | **planning agent** (LLM, fresh session each tick) | the author wants the overseer to judge "what's best next / when to stop" |
| Dispatch | code | clean sessions require new processes; the *stitching* is mechanical |
| Act | **existing command** (LLM, fresh session) | reuse; no new prose/review paths |
| Checkpoint | code — git commit/tag, tick log | crash-safe, reversible, attributable |
| Escalate / stop | code (on the planner's directive) | hand creative/structural forks to the author |

The mechanical loop is deterministic code; the **decision** of what to do next, and
whether to stop, is made by the planning agent. (This is the resolution of
"programmatically driven" + "an overseeing agent stitches clean sessions": code
stitches, the agent directs.)

### Tick loop (pseudo-code)

```
preflight(mode, range)            # refuse if the seed is missing for this mode
loop:
    status = run("authorkit status --json")
    if status.open_escalations:   halt("Resolve open escalation(s) first.")   # [red] + [dim] hint
    if loop_unhealthy(history):   write_escalation("loop-health"); halt
    directive = run_planner(status)        # one clean LLM session; emits ONE action
    log_tick(tick, status, directive)      # book/runs/<ts>.jsonl
    if dry_run:                   print(directive); break        # show, don't act
    match directive.action:
        "done":      report(); break
        "escalate":  write_escalation(directive.escalation); halt
        _:           checkpoint_pre(directive)
                     run(directive.command)         # one clean session, existing command
                     commit_checkpoint(directive)
    if mode == "plot" and tick >= max_iters:  report(); break
    tick += 1
```

### One action per tick

Each tick re-derives everything from `authorkit status`; the planner emits exactly
**one** directive; AutoPilot dispatches exactly **one** command (or escalates / stops).
A crash mid-tick is recovered by re-running the tick — idempotency rests on the
existing status markers and the `<!-- PARTIAL DRAFT: … -->` marker, so there is no
in-memory state to lose.

## Modes

```
authorkit autopilot chapters --range A-B [--dry-run]
authorkit autopilot plot      --max-iters N [--dry-run]
```

| Mode | Planner works on… | Stitches these commands | Bound | Terminates when… |
|---|---|---|---|---|
| `chapters` | per-chapter execution — owns `chapters/NN/` only, never scaffolding | status ladder for the lowest in-range chapter: `[ ]`→`write N plan`, `[P]`→`write N` (draft), `[D]`→`review N`, `[R]`→`write N revise`; occasional range `review A-B`; `research` for chapter grounding | `--range` (finite set) | every in-range chapter is `[X]`, or escalation, or a loop-health stop |
| `plot` | book-level scaffolding only (outline, `world/`, `research/`) — never touches `chapters/NN/` | `write outline`, `discuss` (fold research / build world), `research` | `--max-iters` (open-ended work) | planner judges outline + world solid, or `--max-iters` hit, or escalation, or a loop-health stop |

The two loops split by artifact: **plot** writes book-level scaffolding (`outline.md`,
the chapter list, `world/`, `research/`) and **chapters** owns everything under
`chapters/NN/`. Each is just today's manual rhythm automated — `write N plan` → `[P]`,
`write N` → `[D]`, `review N` → `[X]`/`[R]`, `write N revise` → `[D]` — and when one
layer surfaces a problem in the other (a draft contradicts canon, the outline is wrong),
the loop escalates rather than crossing the boundary.

Worker commands are dispatched **unattended** (`[AUTOPILOT-UNATTENDED]`), so a headless
`discuss` *proceeds* with grounded elaboration (build world, fold research) the
concept/outline/research already imply — inventing the specifics and writing them, all
git-committed and reviewable — rather than stalling on its interactive approval gate;
genuine forks still escalate.

The modes chain: run `plot` until the plan is solid → escalate for author sign-off →
run `chapters`. A combined "plot-then-chapters" default can be added later; `either/or`
is the primary surface.

## Planning agent

A single new prompt under `.authorkit/prompts/`, rendered per AI flavor like the others.

- **Reads:** `authorkit status --json`, including the per-chapter `chapter_statuses` map.
  In **plot** mode it additionally reads the small book-level files — `concept.md`,
  `outline.md`, `world/_index.md`, `research.md` — so it can judge what the story still
  needs (unused research, a thin world); **chapters** mode stays status-only. Never whole drafts.
- **Emits one directive:**

  ```json
  {
    "action": "plan | draft | review | revise | research | escalate | done",
    "chapter": 7,
    "command": "/authorkit.write 7",
    "reason": "CH7 is [P] with no draft; lowest unfinished chapter in range",
    "escalation": { "type": "...", "decision_needed": "...", "options": [], "recommendation": "..." }
  }
  ```

- **Never** edits prose, sets statuses, runs commands itself, or resolves an
  escalation. It only chooses; AutoPilot dispatches.

## Preflight (the seed gate)

`authorkit autopilot` refuses to start unless the seed exists for the chosen mode
(same spirit as `check-prerequisites`; errors follow the actionable `[red]` + `[dim]`
convention and point at `/authorkit.discuss`):

| Mode | Requires |
|---|---|
| `plot` | `concept.md` present, no blocking open clarifications |
| `chapters` | concept + a filled (non-template) constitution + `outline.md` + `chapters.md` covering `--range` |

You cannot autopilot drafting without a settled plan; you cannot autopilot planning
without a concept.

## Escalation & resolution

Escalation is a **first-class planner output** plus a set of code-level hard stops
the planner cannot override.

### Triggers

| Type | Detected by | Resolve with |
|---|---|---|
| Story-direction fork / outline exhausted | planner | `/authorkit.discuss` (Clarify / Conceive-extend) |
| Contradiction with `(CONCEPT)` / `(CHxx)` | reconcile or review output | `/authorkit.discuss` (Cross-cutting change) |
| Structural change needed (split / merge / reorder) | review output | `/authorkit.discuss` (Restructure) |
| Parked decision past its deadline | `status --json` | `/authorkit.discuss` (Park-resolve) |
| Quality stall — chapter fails review K× without converging | review verdict history | `/authorkit.write N revise:` / passage help — or `/authorkit.discuss` Constitution mode if the fix is a tic waiver / voice rule |
| Missing grounding the writer flagged | writer raise-hand | `/authorkit.research` |
| Loop-health (oscillation, no status change in K ticks, repeated tool errors) | AutoPilot | inspect; usually `/authorkit.discuss` |

### Record

AutoPilot writes `book/escalations/YYYY-MM-DD-ESC-NNN-<slug>.md`, reusing the
`parked-decisions.md` schema (an `OPEN`/`RESOLVED` status + a `## Resolution` block):

```markdown
# ESC-007: <short title>

**Status**: OPEN
**Raised**: 2026-06-18 by AutoPilot (chapters mode, tick 14)
**Type**: <story-fork | contradiction | outline-exhausted | quality-stall | structural | parked-overdue | grounding-gap | loop-health>
**Trigger**: <what tripped it, with citations>
**Context**: <relevant artifacts / chapters>
**Decision needed**: <the specific question for the author>
**Options**: <if applicable, with a recommendation>
**Recommended command**: /authorkit.discuss "resolve ESC-007: …"

## Resolution
**Resolved**: <date>
**Decision**: …
**Files changed**: …
**Amendment / Snapshot**: …
```

### Resolution flow

1. Loop hits a fork → AutoPilot writes the record `OPEN`, halts, surfaces it in
   `authorkit status`.
2. Author runs the recommended command — for most types `/authorkit.discuss "resolve
   ESC-007: <direction>"` (discuss lists open escalations the way it lists parked
   decisions and picks it up). Quality stalls route to `write`; grounding gaps to
   `research`.
3. `discuss` does its normal gated thing — talks it through, **proposes** the writes
   (outline / concept / world / plan / constitution / parked-decisions), the author
   approves, it writes, snapshots if cross-cutting — and as its last step marks the
   escalation `RESOLVED` with the Resolution block. Same close-out it already does
   for `resolve PD-NNN`.
4. Next `autopilot` run: no `OPEN` escalations → planner re-observes the updated
   artifacts → continues.

### The invariant

AutoPilot and the planner can **create** and **read** escalations but must **never
mark one resolved themselves** — otherwise the escalation is just the loop
rubber-stamping its own blocker. Resolution is always author-gated, which falls out
for free because `discuss` never writes without explicit approval.

**Self-correcting safety net:** if the author closes a record without actually fixing
the blocking condition, the planner re-detects it and re-escalates next tick — no
extra verification machinery needed.

**Manual fallback:** edit the record's `## Resolution`, set `RESOLVED`, make any
change by hand, re-run. `discuss` is the assisted path, not a required one.

## Loop health / hard stops

Independent of mode and not a budget — these are safety:

- **Oscillation** — the same directive repeats without a status change.
- **No progress** — no `chapters.md` status change across K ticks.
- **Repeated tool errors** — a worker command fails N times.
- **Kill switch** — a sentinel file or signal halts after the current tick.

Each writes a `loop-health` escalation and halts.

## New surface area

- **Commands:** `authorkit autopilot [plot|chapters] [--range A-B] [--max-iters N]
  [--dry-run]`; `authorkit status --json` (planner input + hard-stop signal; trivial
  since the status report already serializes).
- **Files / dirs:** `book/escalations/`, `book/runs/*.jsonl` (per-tick audit trail).
  No new config file — the flags are the whole knob set.
- **Prompts:** one new planning-agent prompt; a small extension to `discuss` so it
  treats escalations like parked decisions on the resolve path (recognize `ESC-NNN`,
  list open ones, close on resolution).
- **Unchanged:** `write`, `review`, `research`, and the rest of `discuss`. `review`
  still owns the `[X]`/`[R]` transition.

## Per-operation model/effort

AutoPilot makes three kinds of LLM calls per run: the **planner** (decides each
tick's next action), dispatched **review** commands (`/authorkit.review`), and
dispatched **writer** commands (`/authorkit.write`, `/authorkit.research`).
Each can be pointed at a different model/effort via an optional
`[autopilot.planner|review|writer]` section in `book.toml` — see the README's
`book.toml` docs for the user-facing usage. All fields are unset by default:
no built-in default, no CLI flag, so an untouched `book.toml` behaves exactly
as before this feature existed.

Flag syntax by flavor (only emitted when a value is actually set):

| Flavor | Model flag | Effort flag | Notes |
|---|---|---|---|
| Claude | `--model <alias\|id>` | `--effort <low\|medium\|high\|xhigh\|max>` | Both confirmed to work with headless `claude -p`. |
| Codex | `-m <id>` | `-c model_reasoning_effort="<level>"` (`minimal\|low\|medium\|high\|xhigh`) | No dedicated effort flag exists; several upstream Codex CLI issues report `model_reasoning_effort` occasionally being ignored — treat as best-effort. |
| Copilot | `--model=<id>` | `--effort=<level>` (`low\|medium\|high\|xhigh\|max`) | `--model` is confirmed to work with headless `-p`; `--effort` alongside `-p` is undocumented upstream and should be spot-checked before relying on it. |

Codex/Copilot's base invocation (not just these flags) is still marked "needs
live validation" below — see Open questions.

## Rollout

See [`autopilot-implementation.md`](autopilot-implementation.md) for the detailed, phased build plan.

1. **Read-only slice** — `status --json` + the planner prompt + `autopilot --dry-run`.
   Watch the planner choose one directive per tick against a real book before it
   writes anything.
2. **Supervised `chapters`** — one tick, then stop for confirmation. Proves
   dispatch + clean-session handoff end to end.
3. **Bounded unattended** — a full `chapters` run over one part, with escalation +
   a git checkpoint per tick.
4. **`plot` + long runs** — open-ended planning runs and unattended drafting, plus
   escalation notifications (push / PR comment).

## Locked decisions

- Strictly **one action per tick**; clean resume from `authorkit status`.
- **No budget knob** — `--range` bounds `chapters`, `--max-iters` bounds `plot`,
  `--dry-run` on both.
- **`review` keeps flipping the status bit** exactly as today; no approval gate.
- Escalations are **resolved through `discuss`** (with `write`/`research` for quality
  stalls and grounding gaps); the loop **never self-resolves**.

## Open questions

- **Escalation storage:** a separate `book/escalations/` directory (current plan) vs.
  folding loop-raised items into `parked-decisions.md` with a `blocks: autopilot`
  flag. Separate keeps blocking (hard) vs. soft semantics clean; folding reuses more.
- **Headless invocation per flavor:** AutoPilot needs a per-agent recipe to run a
  command in a fresh non-interactive session (e.g. `claude -p …`, `codex exec …`,
  Copilot equivalent). This is the main implementation detail to pin down for the
  multi-AI story — the base invocation (not just model/effort) is still unvalidated
  for Codex/Copilot.
- **Unattended notifications:** mechanism for surfacing an escalation when no one is
  watching (Phase 4).

## Rejected alternatives

- **Out-of-process approval gate / anti-self-grading apparatus** (writer can't set
  `[X]`, hash-chained approval log + audit, forced different-model reviewer, frozen
  golden reference set). Too heavy and it changes current command behavior; the
  author is comfortable with the existing `review` step flipping the bit. *(Rejected
  2026-06-18.)*
- **Git-hook enforcement** of the gate. *(Rejected earlier — too heavy.)*
- **Planner batches multiple actions per tick.** Hurts resumability and auditability;
  one-per-tick chosen instead.
- **Budget/cost knob.** Replaced by `--range` / `--max-iters` + loop-health stops.
- **Fully agent-driven orchestration** (an LLM running the mechanical loop). The loop
  is deterministic code; only the next-action decision is the agent's.
