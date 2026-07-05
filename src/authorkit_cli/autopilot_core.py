"""Core types and helpers for the AutoPilot autonomous authoring loop.

Pure logic only — the planner ``Directive`` and its parsing, the mode-aware
seed-gate ``preflight``, escalation records, the per-tick run log, and the
loop-health checks. No agent invocation (that lives in ``autopilot_runner``)
and no Typer wiring (that lives in ``autopilot_commands``), so everything here
is unit-testable without a live agent.

Author:
    mdemarne
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

from .book_core import parse_chapter_statuses

# Action verbs a planner directive may carry.
PLANNER_ACTIONS = {"plan", "draft", "review", "revise", "research", "escalate", "done"}
# Actions that dispatch an existing command (and therefore need a `command`).
ACT_ACTIONS = {"plan", "draft", "review", "revise", "research"}
# Escalation types recorded in the escalation file (informational).
ESCALATION_TYPES = {
    "story-fork",
    "contradiction",
    "outline-exhausted",
    "quality-stall",
    "structural",
    "parked-overdue",
    "grounding-gap",
    "loop-health",
    "numeric-contradiction",
    "disclosure-leak",
    "scaffolding-gap",
}
# Markers that mean the constitution is still the shipped template, not filled in.
CONSTITUTION_PLACEHOLDERS = ("[BOOK_TITLE]", "[PRINCIPLE_1_NAME]", "[PRINCIPLE_1_DESCRIPTION]")
# Sentinel filename under book/runs/ that halts the loop after the current tick.
KILL_SWITCH_NAME = "STOP"
# Harness-owned sidecar (sibling of autopilot.jsonl) mapping each reviewed chapter to
# the content hash of the draft that review covered, so the loop can tell a stale review
# (draft changed since — re-review) from a current one (re-review would be a pure no-op).
REVIEW_INDEX_NAME = "review-index.json"
# Instance count at which a tracked tic shape is "over budget" (Pass 2's Critical / gating
# threshold — a shape recurring this many times in a chapter). Mirrors the review prompt.
GATING_BUDGET = 3
# How many review/revise reconciliation round-trips a single chapter may burn before the
# loop escalates a `quality-stall` (human override) rather than churning to MAX_TICKS. A
# healthy reconciliation converges in 2-3; the pathological runs observed ran 8.
MAX_REVIEW_CYCLES_PER_CHAPTER = 6


class DirectiveError(ValueError):
    """Raised when a planner reply cannot be parsed into a valid Directive."""


@dataclass(slots=True)
class Directive:
    """One planner decision: the single next action for this tick."""

    action: str
    chapter: int | None = None
    command: str | None = None
    reason: str = ""
    escalation: dict | None = None

    @property
    def is_terminal(self) -> bool:
        """True for actions that stop the loop rather than dispatch a command."""
        return self.action in {"escalate", "done"}


def _coerce_directive_obj(payload: str | dict) -> dict:
    """Coerce a planner reply (dict or JSON-ish string) into a dict.

    A headless agent often wraps the JSON in a ```json fence or surrounds it
    with prose, so we extract the first fenced or brace-delimited object before
    parsing.
    """
    if isinstance(payload, dict):
        return payload
    if not isinstance(payload, str):
        raise DirectiveError(f"Cannot parse directive from {type(payload).__name__}")

    text = payload.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    else:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            text = text[start : end + 1]

    try:
        obj = json.loads(text)
    except json.JSONDecodeError as exc:
        raise DirectiveError(f"Planner reply is not valid JSON: {exc}") from exc
    if not isinstance(obj, dict):
        raise DirectiveError("Planner reply JSON must be an object")
    return obj


def parse_directive(payload: str | dict) -> Directive:
    """Parse and validate a planner reply into a Directive.

    Raises DirectiveError on anything malformed so the loop can retry once and
    then escalate, rather than dispatching a bogus command.
    """
    data = _coerce_directive_obj(payload)

    action = str(data.get("action", "")).strip().lower()
    if action not in PLANNER_ACTIONS:
        raise DirectiveError(f"Unknown or missing action: {data.get('action')!r}")

    chapter = data.get("chapter")
    if chapter is not None:
        try:
            chapter = int(chapter)
        except (TypeError, ValueError) as exc:
            raise DirectiveError(f"chapter must be an integer, got {chapter!r}") from exc

    command = data.get("command")
    command = str(command).strip() if command else None
    if action in ACT_ACTIONS and not command:
        raise DirectiveError(f"action {action!r} requires a 'command' to dispatch")

    escalation = data.get("escalation")
    if action == "escalate":
        if not isinstance(escalation, dict) or not str(escalation.get("decision_needed", "")).strip():
            raise DirectiveError("escalate requires an 'escalation' object with a 'decision_needed'")

    return Directive(
        action=action,
        chapter=chapter,
        command=command,
        reason=str(data.get("reason", "")).strip(),
        escalation=escalation if isinstance(escalation, dict) else None,
    )


def directive_to_obj(directive: Directive) -> dict:
    """JSON-ready dict for a Directive (used by --dry-run output)."""
    obj: dict = {"action": directive.action, "reason": directive.reason}
    if directive.chapter is not None:
        obj["chapter"] = directive.chapter
    if directive.command:
        obj["command"] = directive.command
    if directive.escalation:
        obj["escalation"] = directive.escalation
    return obj


@dataclass(slots=True)
class PreflightResult:
    """Outcome of the seed-gate preflight: ok plus any actionable errors."""

    ok: bool
    errors: list[str] = field(default_factory=list)


def _is_template_constitution(path: Path) -> bool:
    """True when the constitution still contains unfilled [PLACEHOLDER] tokens."""
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError):
        return False
    return any(token in text for token in CONSTITUTION_PLACEHOLDERS)


def _chapters_missing_from_list(book_dir: Path, chapter_range: tuple[int, int]) -> list[int]:
    """Chapter numbers in the range that have no entry in chapters.md."""
    statuses = parse_chapter_statuses(book_dir)
    lo, hi = chapter_range
    return [n for n in range(lo, hi + 1) if n not in statuses]


def preflight(
    mode: str,
    book_dir: Path,
    repo_root: Path,
    *,
    chapter_range: tuple[int, int] | None = None,
) -> PreflightResult:
    """Mode-aware seed gate.

    Returns ``ok=False`` with actionable errors when the book is not seeded
    enough for autonomous work in ``mode``:

    - ``plot`` needs ``concept.md``.
    - ``chapters`` additionally needs a filled (non-template) constitution,
      ``outline.md``, and a ``chapters.md`` that covers the requested range.
    """
    errors: list[str] = []

    if not (book_dir / "concept.md").is_file():
        errors.append("concept.md is missing — run /authorkit.discuss to conceive the book first.")

    if mode == "chapters":
        constitution = repo_root / ".authorkit" / "memory" / "constitution.md"
        if not constitution.is_file():
            errors.append(
                "constitution is missing — set voice/style via /authorkit.discuss (Constitution mode)."
            )
        elif _is_template_constitution(constitution):
            errors.append(
                "constitution still has unfilled [PLACEHOLDER]s — fill it via "
                "/authorkit.discuss (Constitution mode)."
            )
        if not (book_dir / "outline.md").is_file():
            errors.append("outline.md is missing — run /authorkit.write outline first.")
        chapters_md = book_dir / "chapters.md"
        if not chapters_md.is_file():
            errors.append("chapters.md is missing — run /authorkit.write to generate the chapter list.")
        elif chapter_range is not None:
            missing = _chapters_missing_from_list(book_dir, chapter_range)
            if missing:
                rng = f"{chapter_range[0]}-{chapter_range[1]}"
                joined = ", ".join(f"CH{n:02d}" for n in missing)
                errors.append(
                    f"chapters.md doesn't cover all of --range {rng} (missing: {joined}). "
                    "Extend the outline/list via /authorkit.write outline extend first."
                )

    return PreflightResult(ok=not errors, errors=errors)


def _slugify(value: str, maxlen: int = 40) -> str:
    """Filesystem-safe lowercase slug, trimmed at a word (hyphen) boundary."""
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", (value or "").strip().lower()).strip("-")
    if len(slug) > maxlen:
        slug = slug[:maxlen].rsplit("-", 1)[0].strip("-")
    return slug or "escalation"


def _short_title(text: str, limit: int = 56) -> str:
    """One-line title trimmed at a word boundary (adds an ellipsis when cut)."""
    text = " ".join((text or "").split())
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].rstrip(" ,.;:-—")
    return f"{cut}…" if cut else text[:limit]


def next_escalation_id(escalations_dir: Path) -> str:
    """Return the next sequential ``ESC-NNN`` id based on existing records."""
    max_n = 0
    if escalations_dir.is_dir():
        for path in escalations_dir.glob("*.md"):
            match = re.search(r"ESC-(\d+)", path.name, re.IGNORECASE)
            if not match:
                try:
                    match = re.search(r"ESC-(\d+)", path.read_text(encoding="utf-8-sig"), re.IGNORECASE)
                except (OSError, UnicodeDecodeError):
                    match = None
            if match:
                max_n = max(max_n, int(match.group(1)))
    return f"ESC-{max_n + 1:03d}"


def render_escalation(
    *,
    esc_id: str,
    esc_type: str,
    trigger: str,
    decision_needed: str,
    today: str,
    context: str = "",
    options: str = "",
    recommended_command: str = "",
    raised_by: str = "AutoPilot",
    title: str | None = None,
) -> str:
    """Render an OPEN escalation record (mirrors the parked-decisions schema)."""
    title = title or _short_title(decision_needed or esc_type)
    lines = [
        f"# {esc_id}: {title}",
        "",
        "**Status**: OPEN",
        f"**Raised**: {today} by {raised_by}",
        f"**Type**: {esc_type}",
        f"**Trigger**: {trigger}",
    ]
    if context:
        lines.append(f"**Context**: {context}")
    lines.append(f"**Decision needed**: {decision_needed}")
    if options:
        lines.append(f"**Options**: {options}")
    if recommended_command:
        lines.append(f"**Recommended command**: {recommended_command}")
    lines += [
        "",
        "## Resolution",
        "**Resolved**: ",
        "**Decision**: ",
        "**Files changed**: ",
        "**Amendment / Snapshot**: ",
        "",
    ]
    return "\n".join(lines)


def write_escalation(
    book_dir: Path,
    *,
    esc_type: str,
    trigger: str,
    decision_needed: str,
    today: str,
    context: str = "",
    options: str = "",
    recommended_command: str = "",
    raised_by: str = "AutoPilot",
    title: str | None = None,
    slug: str | None = None,
) -> Path:
    """Write an OPEN escalation record to ``book/escalations/`` and return its path.

    ``today`` (``YYYY-MM-DD``) is injected by the caller so this stays pure and
    testable. ``title``/``slug`` override the (word-boundary-trimmed) defaults
    derived from ``decision_needed`` — callers pass a concise pair for
    machine-raised escalations (loop-health, planner failure).
    """
    escalations_dir = book_dir / "escalations"
    escalations_dir.mkdir(parents=True, exist_ok=True)
    esc_id = next_escalation_id(escalations_dir)
    title = title or _short_title(decision_needed or esc_type)
    slug = slug or _slugify(title)
    path = escalations_dir / f"{today}-{esc_id}-{slug}.md"
    path.write_text(
        render_escalation(
            esc_id=esc_id,
            esc_type=esc_type,
            trigger=trigger,
            decision_needed=decision_needed,
            today=today,
            context=context,
            options=options,
            recommended_command=recommended_command,
            raised_by=raised_by,
            title=title,
        ),
        encoding="utf-8",
    )
    return path


def log_tick(book_dir: Path, record: dict) -> Path:
    """Append a per-tick record (JSONL) to ``book/runs/autopilot.jsonl``."""
    runs_dir = book_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    log_path = runs_dir / "autopilot.jsonl"
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return log_path


def kill_switch_present(book_dir: Path) -> bool:
    """True when ``book/runs/STOP`` exists (operator kill switch)."""
    return (book_dir / "runs" / KILL_SWITCH_NAME).exists()


def detect_oscillation(history: list[dict], window: int = 3) -> bool:
    """True when the last ``window`` dispatched ticks repeated the same command
    with no chapters.md status change between them."""
    acts = [h for h in history if h.get("command")]
    if len(acts) < window:
        return False
    last = acts[-window:]
    same_command = len({h["command"] for h in last}) == 1
    no_change = all(h.get("status_changed") is False for h in last)
    return same_command and no_change


def detect_command_churn(history: list[dict], window: int = 4) -> bool:
    """True when the last ``window`` dispatched ticks repeated the exact same
    command, regardless of status or content change.

    Guideline campaigns need this: their progress key folds in a content
    fingerprint, and an LLM re-review virtually never rewrites review.md
    byte-identically, so the ``status_changed``-keyed detectors above can never
    fire. A healthy sweep advances to a different chapter — a different
    command — each tick; the same command ``window`` times in a row is a
    planner stuck in place, however much the bytes churn.
    """
    acts = [h for h in history if h.get("command")]
    if len(acts) < window:
        return False
    return len({h["command"] for h in acts[-window:]}) == 1


def detect_no_progress(history: list[dict], k: int = 4) -> bool:
    """True when the last ``k`` dispatched ticks produced no status change."""
    acts = [h for h in history if h.get("command")]
    if len(acts) < k:
        return False
    return all(h.get("status_changed") is False for h in acts[-k:])


def all_chapters_approved(book_dir: Path, chapter_range: tuple[int, int]) -> bool:
    """True when every chapter in the range is approved (``[X]``) in chapters.md."""
    statuses = parse_chapter_statuses(book_dir)
    lo, hi = chapter_range
    return all(statuses.get(n) == "approved" for n in range(lo, hi + 1))


# --- Review currency & tic-gate convergence -----------------------------------
#
# Two failure modes made the chapters loop churn instead of converging:
#   (1) the planner re-dispatched `review` on an unchanged, already-reviewed draft
#       (a pure no-op that only tripped a loop-health guard after several wasted ticks);
#   (2) Pass 2's blind tic discovery re-opened the gating set every cycle, so findings
#       never monotonically shrank and a reviser could be kept busy forever.
# The helpers below give the loop a deterministic, git-immune notion of "is this review
# current for this draft" (via a content-hash sidecar, NOT mtimes — the loop git-commits
# every tick), the verdict/gating record parsed from review.md, the convergence invariant
# for the tic gate, and a per-chapter reconcile-stall detector that bounds a non-converging
# chapter to a `quality-stall` escalation instead of MAX_TICKS of subprocesses.


@dataclass(slots=True)
class ReviewState:
    """What the standing ``chapters/NN/review.md`` says about the current draft.

    ``current`` is True only when the review on disk was produced against *this* draft's
    bytes (per the review-index sidecar) — so a re-review would be a no-op. ``verdict`` and
    ``gating_shapes`` are parsed from review.md (the full craft review, never style-review.md).
    """

    exists: bool = False
    current: bool = False
    verdict: str | None = None
    gating_shapes: tuple[str, ...] = ()


def file_md5(path: Path) -> str | None:
    """Hex md5 of a file's bytes, or ``None`` if it can't be read (mirrors the loop's own
    content fingerprint). Content identity, unlike mtime, survives the per-tick git commit."""
    try:
        return hashlib.md5(path.read_bytes()).hexdigest()
    except OSError:
        return None


_VERDICT_RE = re.compile(r"\*\*(?:Overall Assessment|Status)\*\*:\s*([^\n]+)", re.IGNORECASE)
_GATING_RE = re.compile(r"\*\*Gating Shapes\*\*:\s*([^\n]+)", re.IGNORECASE)
_CMD_CHAPTER_RE = re.compile(r"/authorkit\.\w+\s+(\d+)")
_GATING_NONE = {"none", "n/a", "na", "-", "(none)", "0"}


def parse_review_verdict(text: str) -> str | None:
    """Extract ``PASS`` / ``NEEDS_REVISION`` / ``None`` from a review.md body.

    Reads the ``**Overall Assessment**`` header or the ``## Verdict`` ``**Status**`` line;
    an ambiguous/templated value that mentions both resolves to the safe ``NEEDS_REVISION``.
    """
    for match in _VERDICT_RE.finditer(text):
        value = match.group(1).upper()
        if "NEEDS REVISION" in value or "NEEDS_REVISION" in value:
            return "NEEDS_REVISION"
        if "PASS" in value:
            return "PASS"
    return None


def parse_gating_shapes(text: str) -> tuple[str, ...]:
    """Extract the review's machine-readable ``**Gating Shapes**:`` record — the Pass-2
    shapes that gated *this* review — as a normalized tuple. Absent or ``none`` → empty."""
    match = _GATING_RE.search(text)
    if not match:
        return ()
    raw = match.group(1).strip()
    if not raw or raw.strip().lower() in _GATING_NONE:
        return ()
    parts = [p.strip().lower() for p in re.split(r"[;,]", raw)]
    return tuple(p for p in parts if p)


def command_chapter(command: str | None) -> int | None:
    """Best-effort chapter number from a dispatched command (``/authorkit.write 7 revise``)."""
    if not command:
        return None
    match = _CMD_CHAPTER_RE.search(command)
    return int(match.group(1)) if match else None


def _review_index_path(book_dir: Path) -> Path:
    return book_dir / "runs" / REVIEW_INDEX_NAME


def read_review_index(book_dir: Path) -> dict:
    """Load the review-index sidecar (chapter key -> {draft_sha, verdict}); ``{}`` on any error."""
    try:
        data = json.loads(_review_index_path(book_dir).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def write_review_index(book_dir: Path, index: dict) -> Path:
    """Persist the review-index sidecar under ``book/runs/`` and return its path."""
    runs_dir = book_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    path = runs_dir / REVIEW_INDEX_NAME
    path.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def record_review(book_dir: Path, chapter: int, *, draft_sha: str | None, verdict: str | None) -> None:
    """Record that ``chapter``'s review covered the draft hashed ``draft_sha`` (with ``verdict``).

    Called by the loop right after a ``review`` dispatch — ``review`` never edits the draft,
    so the current draft hash *is* the reviewed draft's hash.
    """
    index = read_review_index(book_dir)
    index[f"CH{chapter:02d}"] = {"draft_sha": draft_sha, "verdict": verdict}
    write_review_index(book_dir, index)


def review_state(book_dir: Path, chapter: int) -> ReviewState:
    """Resolve the standing review's currency + verdict for ``chapter``.

    ``current`` requires the review-index sidecar's recorded draft hash to equal the current
    ``draft.md`` hash — deterministic and git-commit-immune. A missing sidecar entry (e.g. a
    review run by hand outside AutoPilot, or an old book) degrades safely to ``current=False``
    (worst case: one extra real review that then populates the sidecar).
    """
    chap = book_dir / "chapters" / f"{chapter:02d}"
    review_md = chap / "review.md"
    draft_md = chap / "draft.md"
    if not review_md.is_file():
        return ReviewState(exists=False)
    try:
        text = review_md.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError):
        return ReviewState(exists=True)
    verdict = parse_review_verdict(text)
    gating = parse_gating_shapes(text)
    recorded = read_review_index(book_dir).get(f"CH{chapter:02d}")
    recorded_sha = recorded.get("draft_sha") if isinstance(recorded, dict) else None
    current = (
        recorded_sha is not None
        and draft_md.is_file()
        and recorded_sha == file_md5(draft_md)
    )
    return ReviewState(exists=True, current=current, verdict=verdict, gating_shapes=gating)


def gating_findings(
    carried_over: Iterable[str],
    discovered: Mapping[str, int],
    *,
    prior: Iterable[str] = (),
    budget: int = GATING_BUDGET,
) -> set[str]:
    """The Pass-2 tic shapes that gate a review under the carry-over convergence rule.

    This is the executable spec the review prompt mirrors; it is also the reference the
    Bug-2 tests assert against. Inputs:

    - ``carried_over``: shapes that gated the *prior* review of this chapter (the set that
      must shrink). A carry-over shape keeps gating only while it is still over ``budget``.
    - ``discovered``: shape -> instance count in the *current* draft (blind Step A + ledger).
    - ``prior``: shapes present in the prior review of this chapter — used to tell a genuine
      regression (a rampant shape the last revise *introduced*) from ordinary blind discovery.

    A freshly-discovered shape gates only if it is over budget AND was absent last review
    (a regression); otherwise it is non-gating residual/seed. For a fixed draft this makes the
    gating set stable and non-growing; each revise that clears a carry-over shape strictly
    shrinks it toward the empty (converged-with-residual) fixed point.
    """
    carried = set(carried_over)
    prior_set = set(prior)
    gating = {shape for shape in carried if discovered.get(shape, 0) >= budget}
    for shape, count in discovered.items():
        if count >= budget and shape not in prior_set and shape not in carried:
            gating.add(shape)  # regression introduced since the last review — still gates
    return gating


def gating_set_converging(prev: Iterable[str], curr: Iterable[str]) -> bool:
    """True when the current gating set introduces no shape absent from the previous one
    (``curr ⊆ prev``) — the Bug-2 convergence invariant for a fixed draft. ``False`` means the
    tic gate re-opened on a freshly-discovered shape (the moving-target regression)."""
    return set(curr) <= set(prev)


def _chapter_dispatches(history: list[dict], chapter: int) -> list[dict]:
    """Dispatched ticks (with a command) attributed to one chapter, in order."""
    return [h for h in history if h.get("command") and h.get("chapter") == chapter]


def detect_reconcile_stall(
    history: list[dict],
    chapter: int,
    *,
    cap: int = MAX_REVIEW_CYCLES_PER_CHAPTER,
    window: int = 3,
) -> bool:
    """True when ``chapter``'s review/revise reconciliation is not converging.

    Two arms, either of which trips (the loop then escalates ``quality-stall`` instead of
    churning to ``MAX_TICKS``):

    - **Cap**: the chapter has been revised ``>= cap`` times without reaching ``[X]`` (the
      loop only reaches this check while the chapter is still un-approved).
    - **Diminishing returns**: across the last ``window`` reviews the parsed gating-shape set
      never strictly shrank (stuck at the same size, or growing) while still non-empty — the
      moving-target signature Bug 2 is meant to end.
    """
    ticks = _chapter_dispatches(history, chapter)
    revises = [h for h in ticks if h.get("action") == "revise"]
    if len(revises) >= cap:
        return True
    reviews = [h for h in ticks if h.get("action") == "review"]
    recent = reviews[-window:]
    if len(recent) >= window:
        sizes = [len(h.get("gating_shapes") or ()) for h in recent]
        if sizes[-1] > 0 and all(sizes[i] <= sizes[i + 1] for i in range(len(sizes) - 1)):
            return True
    return False
