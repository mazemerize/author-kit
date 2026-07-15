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
import os
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
# The *default* instance budget at which a tracked tic shape is "over budget" (Pass 2's
# Critical / gating threshold). Mirrors the review prompt's default; individual ledger
# entries may carry a stricter budget (0 = flag on sight) or a per-1,000-words one.
GATING_BUDGET = 3
# How many reviews a chapter may go WITHOUT its gating tic-set reaching a new minimum
# before the loop escalates a `quality-stall` (human override). This is the single
# reconciliation-progress knob: the sidecar tracks the smallest gating set ever reached
# (a ratchet — it only decreases), so genuine progress keeps resetting the counter and
# only true non-improvement accrues it. Because the signal is persisted, it bounds effort
# across restarts too, replacing the old separate cross-run cycle cap. A healthy
# reconciliation converges in 2-3; MAX_TICKS remains the unrelated per-process ceiling.
RECONCILE_STALL_LIMIT = 5


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


def _needs_leading_newline(log_path: Path) -> bool:
    """True when the log exists, is non-empty, and its last byte isn't ``\\n`` — a prior
    record left unterminated by a crash or an interleaved concurrent write. Prepending a
    newline then keeps every record on its own line for a naive line-by-line parser."""
    try:
        if log_path.stat().st_size == 0:
            return False
        with log_path.open("rb") as handle:
            handle.seek(-1, os.SEEK_END)
            return handle.read(1) != b"\n"
    except OSError:
        return False


def log_tick(book_dir: Path, record: dict) -> Path:
    """Append a per-tick (or terminal-outcome) record as one JSONL line to
    ``book/runs/autopilot.jsonl``, guaranteeing it starts on a fresh line."""
    runs_dir = book_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    log_path = runs_dir / "autopilot.jsonl"
    prefix = "\n" if _needs_leading_newline(log_path) else ""
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(prefix + json.dumps(record, ensure_ascii=False) + "\n")
    return log_path


def log_outcome(book_dir: Path, run_id: str, tick: int, outcome: str, **fields) -> Path:
    """Log a terminal run outcome (``done``/``escalate``/``loop-health``/``quality-stall``/…)
    to ``autopilot.jsonl`` so the log alone explains why a run ended — dispatched ticks alone
    never recorded the ending."""
    return log_tick(book_dir, {"run": run_id, "tick": tick, "outcome": outcome, **fields})


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
    """True when the last ``window`` dispatched ticks are a planner stuck in place:
    the exact same command every tick, or nothing but reviews cycling over at most
    two commands (the two-chapter ping-pong).

    Guideline campaigns need this: their progress key folds in a content
    fingerprint, and an LLM re-review virtually never rewrites review.md
    byte-identically, so the ``status_changed``-keyed detectors above can never
    fire. A healthy sweep advances to a different chapter — a different
    command — each tick, and a healthy review→revise reconciliation interleaves
    revise ticks (and is bounded by ``reconcile_stalled``), so an all-review
    window alternating between two commands is unproductive churn, however much
    the bytes move.
    """
    acts = [h for h in history if h.get("command")]
    if len(acts) < window:
        return False
    last = acts[-window:]
    distinct = {h["command"] for h in last}
    if len(distinct) == 1:
        return True
    return len(distinct) <= 2 and all(h.get("action") == "review" for h in last)


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
    # The Pass-2 carry-over set: () = an explicit "none" (gate clear); a tuple = the gating
    # shapes; None = the review emitted no ``**Gating Shapes**:`` line at all (contract not
    # followed — distinct from a cleared gate, so it is never mistaken for convergence).
    gating_shapes: tuple[str, ...] | None = None


def file_md5(path: Path) -> str | None:
    """Hex md5 of a file's bytes, or ``None`` if it can't be read (mirrors the loop's own
    content fingerprint). Content identity, unlike mtime, survives the per-tick git commit."""
    try:
        return hashlib.md5(path.read_bytes()).hexdigest()
    except OSError:
        return None


# Every location the review rules can live in this repo (the source prompt plus each
# flavor's rendered copy). campaign_sha folds ALL that exist into the campaign identity, so
# an authorkit upgrade (re-init rewrites the renders) or a hand-edit to any copy invalidates
# the stamps and a re-run of the same guideline text does a full re-sweep.
_REVIEW_PROMPT_CANDIDATES = (
    Path(".authorkit") / "prompts" / "authorkit.review.md",
    Path(".claude") / "commands" / "authorkit.review.md",
    Path(".github") / "prompts" / "authorkit.review.prompt.md",
    Path(".codex") / "prompts" / "authorkit.review.md",
)


def campaign_sha(guideline: str, repo_root: Path) -> str | None:
    """The identity of a guideline campaign: md5 of the guideline text **plus the review
    rules in force** (every existing review-prompt copy, in fixed order).

    This is what ``record_review`` stamps per chapter and what makes campaign progress
    deterministic across the loop's clean planner sessions: a chapter is campaign-processed
    iff its stamp equals the active campaign's sha. Hashing the prompts in means "reviewed
    under these rules", not "reviewed under this sentence" — re-running the same guideline
    text after an upgrade re-sweeps; re-running it unchanged resumes where it left off.
    ``None`` when no guideline is active (nothing gets stamped).
    """
    text = (guideline or "").strip()
    if not text:
        return None
    digest = hashlib.md5(text.encode("utf-8"))
    for rel in _REVIEW_PROMPT_CANDIDATES:
        path = repo_root / rel
        try:
            digest.update(path.read_bytes())
        except OSError:
            continue
    return digest.hexdigest()


# The authoritative verdict is the ``## Verdict`` **Status** line; the top
# **Overall Assessment** header is a fallback (they can disagree when a draft is
# half-filled from the template).
_STATUS_RE = re.compile(r"\*\*Status\*\*:\s*([^\n]+)", re.IGNORECASE)
_ASSESSMENT_RE = re.compile(r"\*\*Overall Assessment\*\*:\s*([^\n]+)", re.IGNORECASE)
_GATING_RE = re.compile(r"\*\*Gating Shapes\*\*:\s*([^\n]+)", re.IGNORECASE)
# A single chapter number, but NOT the first half of a range (``5-10`` / ``5 - 10``)
# — a range/manuscript review is not attributable to one chapter (see command_chapter).
# The ``(?!\d)`` keeps backtracking from splitting a multi-digit number: without it,
# ``15-20`` matches as ``1`` (``(\d+)`` gives back ``5``, and the range lookahead then
# sees ``5-20`` and passes).
_CMD_CHAPTER_RE = re.compile(r"/authorkit\.\w+\s+(\d+)(?!\d)(?!\s*-\s*\d)")
# A style-fidelity review (``/authorkit.review N style``) writes style-review.md, not
# review.md — so it must never stamp the craft-review sidecar (see record_review's caller).
_STYLE_REVIEW_RE = re.compile(r"/authorkit\.review\s+\d+\s+style\b", re.IGNORECASE)
_GATING_NONE = {"none", "n/a", "na", "-", "(none)", "0"}


def _classify_verdict(value: str) -> str | None:
    """Map one verdict-line value to PASS / NEEDS_REVISION / None.

    A value carrying BOTH markers is an unfilled template (``[PASS / NEEDS REVISION]``) —
    return None so the caller falls through rather than guessing.
    """
    upper = value.upper()
    has_needs = "NEEDS REVISION" in upper or "NEEDS_REVISION" in upper
    has_pass = "PASS" in upper
    if has_needs and has_pass:
        return None
    if has_needs:
        return "NEEDS_REVISION"
    if has_pass:
        return "PASS"
    return None


def parse_review_verdict(text: str) -> str | None:
    """Extract ``PASS`` / ``NEEDS_REVISION`` / ``None`` from a review.md body.

    Prefers the authoritative ``## Verdict`` ``**Status**`` line over the top
    ``**Overall Assessment**`` header, and skips any line still carrying the literal
    ``[PASS / NEEDS REVISION]`` template (both markers) — so a half-filled review whose
    header is untouched but whose Status is PASS is not misread as NEEDS_REVISION. When the
    prose heading is missing/templated, falls back to the machine-readable ``**Gating
    Shapes**:`` line (``none`` ⇒ PASS, else NEEDS_REVISION). The heading stays authoritative
    when present, because it reflects *all* gating passes (voice, logic, disclosure), not only
    the Pass-2 tic gate.
    """
    for regex in (_STATUS_RE, _ASSESSMENT_RE):
        for match in regex.finditer(text):
            verdict = _classify_verdict(match.group(1))
            if verdict is not None:
                return verdict
    gating = parse_gating_shapes(text)
    if gating is not None:
        return "PASS" if not gating else "NEEDS_REVISION"
    return None


def parse_gating_shapes(text: str) -> tuple[str, ...] | None:
    """Extract the review's machine-readable ``**Gating Shapes**:`` record — the Pass-2
    shapes that gated *this* review.

    Returns ``()`` for an explicit ``none`` (the tic gate is clear), a tuple of normalized
    shape ids otherwise, and ``None`` when the line is **absent or still an unfilled
    ``[…]`` template** — i.e. the review did not emit the convergence contract. ``None`` must
    never be treated as a cleared gate (that is the very bug that let the loop mistake a
    non-emitting review for convergence).
    """
    match = _GATING_RE.search(text)
    if not match:
        return None
    raw = match.group(1).strip()
    low = raw.lower()
    if raw.startswith("[") or "comma-separated" in low or "tic ids" in low:
        return None  # unfilled template placeholder — not a real record
    if not raw or low in _GATING_NONE:
        return ()
    parts = [p.strip().lower() for p in re.split(r"[;,]", raw)]
    return tuple(p for p in parts if p)


def command_chapter(command: str | None) -> int | None:
    """The single chapter a dispatched command targets, or ``None``.

    Returns ``None`` for a range (``/authorkit.review 5-10``) or manuscript
    (``/authorkit.review all``) review — those are not attributable to one chapter, so the
    no-op guard, the review-index sidecar, and the reconcile-stall history must skip them
    rather than misattribute the whole pass to its first chapter.
    """
    if not command:
        return None
    match = _CMD_CHAPTER_RE.search(command)
    return int(match.group(1)) if match else None


def is_style_review(command: str | None) -> bool:
    """True for a style-fidelity review dispatch (``/authorkit.review N style``).

    Style reviews write ``style-review.md`` and never touch ``review.md``, so recording one
    in the craft-review sidecar would stamp a stale craft verdict as current for the new
    draft hash (`ReviewState` is craft-only by contract).
    """
    return bool(command) and _STYLE_REVIEW_RE.search(command) is not None


def _review_index_path(book_dir: Path) -> Path:
    return book_dir / "runs" / REVIEW_INDEX_NAME


def read_review_index(book_dir: Path) -> dict:
    """Load the review-index sidecar (chapter key -> {draft_sha, verdict, and the
    reconciliation-progress signal: best_gate_size / reviews_since_improvement / last_gate});
    ``{}`` on any error."""
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


def _index_entry(index: dict, chapter: int) -> dict:
    """The sidecar entry dict for ``chapter`` (a fresh copy), tolerant of a missing/bad value."""
    entry = index.get(f"CH{chapter:02d}")
    return dict(entry) if isinstance(entry, dict) else {}


def _clear_reconcile_signal(entry: dict) -> None:
    """Reset the reconciliation-progress signal — a converged chapter starts fresh if it is
    later re-opened. Removes the fields rather than zeroing so a fresh entry has no residue."""
    entry.pop("best_gate_size", None)
    entry.pop("reviews_since_improvement", None)
    entry.pop("last_gate", None)


def record_review(
    book_dir: Path,
    chapter: int,
    *,
    draft_sha: str | None,
    verdict: str | None,
    gating_shapes: tuple[str, ...] | None = None,
    guideline_sha: str | None = None,
) -> None:
    """Record that ``chapter``'s review covered the draft hashed ``draft_sha`` (with ``verdict``).

    Called by the loop right after a ``review`` dispatch — ``review`` never edits the draft,
    so the current draft hash *is* the reviewed draft's hash.

    ``guideline_sha`` (the active ``campaign_sha``, when a guideline campaign is running)
    stamps the entry as reviewed-under-this-campaign — the planner reads it back as
    ``chapter_reviews[N].guideline_current`` so a fresh planner session can tell a standing
    PASS that *predates* the campaign from one the campaign itself produced (re-deriving
    that from file mtimes is what made re-review sweeps oscillate and stall). ``None``
    (no campaign) leaves any existing stamp untouched: a plain re-review under unchanged
    rules doesn't un-process a chapter.

    Also maintains the reconciliation-progress signal from this review's gating set: a
    ``best_gate_size`` ratchet (smallest gating set ever reached — only decreases) plus a
    ``reviews_since_improvement`` counter that resets whenever the gate reaches a new minimum
    and accrues otherwise. A converged review (PASS, or an explicit empty gate) clears the
    signal. A review that emitted no gating record (``gating_shapes is None``) leaves it
    untouched — we can't judge progress we didn't measure. This single persisted signal is
    what ``reconcile_stalled`` reads; being persisted, it bounds effort across restarts too.
    """
    index = read_review_index(book_dir)
    entry = _index_entry(index, chapter)
    entry["draft_sha"] = draft_sha
    entry["verdict"] = verdict
    if guideline_sha is not None:
        entry["guideline_sha"] = guideline_sha
    entry.pop("cycles", None)  # legacy field from the old cap — no longer used
    if verdict == "PASS" or gating_shapes == ():
        _clear_reconcile_signal(entry)
    elif gating_shapes is not None:
        size = len(gating_shapes)
        best = entry.get("best_gate_size")
        if not isinstance(best, int) or size < best:
            entry["best_gate_size"] = size
            entry["reviews_since_improvement"] = 0
        else:
            entry["reviews_since_improvement"] = int(entry.get("reviews_since_improvement") or 0) + 1
        entry["last_gate"] = list(gating_shapes)
    index[f"CH{chapter:02d}"] = entry
    write_review_index(book_dir, index)


def chapter_review_entry(book_dir: Path, chapter: int) -> dict:
    """The persisted sidecar entry for ``chapter`` (``{}`` if none) — carries the
    reconciliation-progress signal ``reconcile_stalled`` reads."""
    return _index_entry(read_review_index(book_dir), chapter)


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


def gating_findings(discovered: Mapping[str, int], *, budget: int = GATING_BUDGET) -> set[str]:
    """The Pass-2 tic shapes that gate a review: every discovered shape at/above ``budget``.

    This is the executable spec the review prompt mirrors and the reference the Bug-2 tests
    assert against. ``discovered`` maps shape -> instance count in the *current* draft (blind
    Step A + the ledger sweep). Shapes **below** budget are non-gating residual/seeds — that
    threshold, not an exclusion list, is what stops the blind pass from gating on "one more"
    low-density construction every cycle. The gate set is therefore exactly the carry-over
    (a prior ≥budget shape still ≥budget) plus any regression (a shape a revise pushed to
    ≥budget) — their union is just ``{shapes ≥ budget}``. For a fixed draft this set is stable;
    each effective revise reduces a shape below budget and drops it, shrinking the set toward
    the empty (converged-with-residual) fixed point. A revise that *worsens* a tolerated shape
    past budget re-gates it (soundness); one that merely re-shuffles low-density shapes changes
    nothing.
    """
    return {shape for shape, count in discovered.items() if count >= budget}


def gating_set_converging(prev: Iterable[str], curr: Iterable[str]) -> bool:
    """True when the current gating set introduces no shape absent from the previous one
    (``curr ⊆ prev``) — the Bug-2 convergence invariant for a fixed draft. ``False`` means the
    tic gate re-opened on a freshly-discovered shape (the moving-target regression)."""
    return set(curr) <= set(prev)


def reconcile_stalled(entry: dict, *, limit: int = RECONCILE_STALL_LIMIT) -> bool:
    """True when a chapter's tic reconciliation has stalled — its gating set is still
    non-empty and has failed to reach a *new* minimum size across the last ``limit`` reviews.

    Reads the single persisted progress signal ``record_review`` maintains (``last_gate`` +
    ``reviews_since_improvement``, backed by the ``best_gate_size`` ratchet). Because the
    ratchet only ever decreases, an oscillation that re-inflates the gate above its best (the
    moving-target signature the old window test could be fooled by) accrues
    ``reviews_since_improvement`` and trips here; genuine progress keeps resetting it. Being a
    pure function of persisted state, it holds identically within a run and across restarts —
    one signal, no separate cross-run cap. Escalate ``quality-stall`` when this is True; the
    loop otherwise churns to ``MAX_TICKS``.
    """
    gate_nonempty = bool(entry.get("last_gate"))
    reviews_since_improvement = int(entry.get("reviews_since_improvement") or 0)
    return gate_nonempty and reviews_since_improvement >= limit
