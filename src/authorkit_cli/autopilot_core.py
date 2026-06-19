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

import json
import re
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
}
# Markers that mean the constitution is still the shipped template, not filled in.
CONSTITUTION_PLACEHOLDERS = ("[BOOK_TITLE]", "[PRINCIPLE_1_NAME]", "[PRINCIPLE_1_DESCRIPTION]")
# Sentinel filename under book/runs/ that halts the loop after the current tick.
KILL_SWITCH_NAME = "STOP"


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
