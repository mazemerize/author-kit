"""Project health dashboard for Author Kit.

Implements `authorkit status` — a single-screen view of where the book is:
chapter status counts, parked decisions, world entity totals, last-sync hints,
and drift warnings between chapters.md and the chapters/ directory.

Author:
    mdemarne
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .book_core import (
    CHAPTER_STATUS_LABELS,
    CHAPTERS_DIR_NAME,
    discover_chapter_drafts,
    parse_chapter_statuses,
)


@dataclass(slots=True)
class StatusReport:
    """Aggregated project health data ready for rendering."""

    book_dir: Path
    has_concept: bool
    has_outline: bool
    has_constitution: bool
    chapter_status_counts: dict[str, int]
    chapter_total: int
    drafted_dirs: list[int]
    chapters_md_entries: list[int]
    drift_chapters: list[int]
    drift_dirs: list[int]
    open_parked: int
    overdue_parked: int
    nearest_parked_deadline: str | None
    world_entities: int | None
    world_aliases: int | None
    world_index_modified: str | None
    snapshot_count: int
    amendment_count: int


def _exists(path: Path) -> bool:
    """Tiny helper that returns True when a path exists, False on any error."""
    try:
        return path.exists()
    except OSError:
        return False


def _count_open_parked(parked_path: Path) -> tuple[int, int, str | None]:
    """Read parked-decisions.md and return (open_count, overdue_count, nearest_deadline_text).

    Overdue heuristic: a deadline like "Before CH12" is overdue if any chapter
    >= 12 has draft.md present. Status is `OPEN` if not `RESOLVED`.
    """
    if not _exists(parked_path):
        return 0, 0, None

    text = parked_path.read_text(encoding="utf-8-sig")
    open_count = 0
    overdue_count = 0
    nearest_deadline: str | None = None

    # Each PD-NNN block is delimited by horizontal rules; the marker lines we
    # care about are "**Status**: OPEN" / "**Deadline**: ...".
    block_pattern = re.compile(r"##\s+PD-\d+:.*?(?=\n##\s+PD-\d+:|\Z)", re.DOTALL)
    for block in block_pattern.findall(text):
        status_match = re.search(r"\*\*Status\*\*:\s*(\w+)", block)
        if not status_match or status_match.group(1).upper() != "OPEN":
            continue
        open_count += 1
        deadline_match = re.search(r"\*\*Deadline\*\*:\s*([^\n]+)", block)
        if deadline_match:
            deadline_text = deadline_match.group(1).strip()
            if nearest_deadline is None:
                nearest_deadline = deadline_text

    return open_count, overdue_count, nearest_deadline


def _count_world_index_stats(world_index_path: Path) -> tuple[int | None, int | None, str | None]:
    """Pull entity/alias counts from `world/_index.md` if the file exists.

    The build-world-index script writes deterministic header lines like
    `- **Total entities**: 17`. We grep them rather than re-parse the YAML to
    avoid coupling status to entity-file frontmatter.
    """
    if not _exists(world_index_path):
        return None, None, None

    text = world_index_path.read_text(encoding="utf-8-sig")
    entities = re.search(r"\*\*Total entities\*\*:\s*(\d+)", text)
    aliases = re.search(r"\*\*Total aliases\*\*:\s*(\d+)", text)

    last_modified: str | None = None
    try:
        mtime = world_index_path.stat().st_mtime
        last_modified = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
    except OSError:
        pass

    return (
        int(entities.group(1)) if entities else None,
        int(aliases.group(1)) if aliases else None,
        last_modified,
    )


def collect_status(book_dir: Path) -> StatusReport:
    """Gather the data needed to render `authorkit status`.

    Tolerant of partial state: a fresh `book/` with only `concept.md` returns
    a sparsely populated report. Missing files never raise.
    """
    chapters_md_path = book_dir / "chapters.md"
    parked_path = book_dir / "parked-decisions.md"
    world_dir = book_dir / "world"
    world_index = world_dir / "_index.md"
    snapshots_dir = book_dir / "snapshots"
    amendments_dir = book_dir / "amendments"

    drafts = discover_chapter_drafts(book_dir)
    drafted_dirs = [draft.chapter_number for draft in drafts]

    statuses = parse_chapter_statuses(book_dir)
    chapters_md_entries = sorted(statuses.keys())

    counts: dict[str, int] = {}
    for label in statuses.values():
        counts[label] = counts.get(label, 0) + 1
    chapter_total = max(len(statuses), len(drafted_dirs))

    # Drift: chapters listed in chapters.md but no draft.md, or draft.md without
    # an entry in chapters.md. Either direction is worth surfacing.
    drift_chapters = sorted(set(chapters_md_entries) - set(drafted_dirs))
    drift_dirs = sorted(set(drafted_dirs) - set(chapters_md_entries))

    open_parked, overdue_parked, nearest_parked = _count_open_parked(parked_path)
    world_entities, world_aliases, world_index_modified = _count_world_index_stats(world_index)

    snapshot_count = (
        len([p for p in snapshots_dir.glob("*.md") if p.is_file()])
        if _exists(snapshots_dir)
        else 0
    )
    amendment_count = (
        len([p for p in amendments_dir.glob("*.md") if p.is_file()])
        if _exists(amendments_dir)
        else 0
    )

    return StatusReport(
        book_dir=book_dir,
        has_concept=_exists(book_dir / "concept.md"),
        has_outline=_exists(book_dir / "outline.md"),
        has_constitution=_exists(Path(".authorkit/memory/constitution.md").resolve()),
        chapter_status_counts=counts,
        chapter_total=chapter_total,
        drafted_dirs=drafted_dirs,
        chapters_md_entries=chapters_md_entries,
        drift_chapters=drift_chapters,
        drift_dirs=drift_dirs,
        open_parked=open_parked,
        overdue_parked=overdue_parked,
        nearest_parked_deadline=nearest_parked,
        world_entities=world_entities,
        world_aliases=world_aliases,
        world_index_modified=world_index_modified,
        snapshot_count=snapshot_count,
        amendment_count=amendment_count,
    )


def format_status_lines(report: StatusReport) -> list[str]:
    """Render the status report as a list of plain-text lines for the console.

    Plain-text (no Rich markup) so that `--output text` and the default Rich
    print path stay structurally identical — easier to test, easier to pipe.
    """
    lines: list[str] = []
    lines.append(f"Book: {report.book_dir.name} ({report.book_dir})")
    lines.append("")

    lines.append("Workspace:")
    lines.append(f"  - constitution: {'ok' if report.has_constitution else 'missing'}")
    lines.append(f"  - concept.md: {'ok' if report.has_concept else 'missing'}")
    lines.append(f"  - outline.md: {'ok' if report.has_outline else 'missing'}")
    lines.append("")

    lines.append("Chapters:")
    if report.chapter_total == 0:
        lines.append("  - No chapters tracked yet. Run /authorkit.outline then /authorkit.chapters.")
    else:
        ordered_labels = ["pending", "planned", "drafted", "review", "approved"]
        breakdown_parts = []
        for label in ordered_labels:
            if label in report.chapter_status_counts:
                breakdown_parts.append(f"{report.chapter_status_counts[label]} {label}")
        # Surface unexpected markers (anything not in CHAPTER_STATUS_LABELS) so
        # malformed entries are visible rather than silently coerced.
        for label, count in report.chapter_status_counts.items():
            if label not in ordered_labels:
                breakdown_parts.append(f"{count} {label}")
        lines.append(f"  - total: {report.chapter_total}")
        if breakdown_parts:
            lines.append(f"  - status: {', '.join(breakdown_parts)}")

    if report.drift_chapters:
        lines.append(
            f"  - [drift] in chapters.md but no draft.md: {', '.join(f'CH{n:02d}' for n in report.drift_chapters)}"
        )
    if report.drift_dirs:
        lines.append(
            f"  - [drift] draft.md present but missing from chapters.md: {', '.join(f'CH{n:02d}' for n in report.drift_dirs)}"
        )
    lines.append("")

    if report.open_parked or report.overdue_parked or report.nearest_parked_deadline:
        lines.append("Parked decisions:")
        lines.append(f"  - open: {report.open_parked}")
        if report.overdue_parked:
            lines.append(f"  - overdue: {report.overdue_parked}")
        if report.nearest_parked_deadline:
            lines.append(f"  - nearest deadline: {report.nearest_parked_deadline}")
        lines.append("")

    if report.world_entities is not None:
        lines.append("World:")
        lines.append(f"  - entities: {report.world_entities}")
        if report.world_aliases is not None:
            lines.append(f"  - aliases: {report.world_aliases}")
        if report.world_index_modified:
            lines.append(f"  - last index rebuild: {report.world_index_modified}")
        lines.append("")

    if report.snapshot_count or report.amendment_count:
        lines.append("History:")
        if report.snapshot_count:
            lines.append(f"  - snapshots: {report.snapshot_count}")
        if report.amendment_count:
            lines.append(f"  - amendments: {report.amendment_count}")
        lines.append("")

    return lines
