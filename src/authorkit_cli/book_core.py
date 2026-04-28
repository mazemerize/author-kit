"""Core utilities for Author Kit book commands.

Provides shared data structures, path helpers, config parsing, and text
utilities consumed by the build, audio, and stats pipelines.

Author:
    mdemarne
"""

from __future__ import annotations

import json
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

# Canonical directory names relative to the project root.
BOOK_DIR_NAME = "book"
WORLD_DIR_NAME = "world"
CHAPTERS_DIR_NAME = "chapters"
DIST_DIR_NAME = "dist"

@dataclass(slots=True)
class ChapterDraft:
    """Represent one chapter draft file."""

    chapter_number: int
    draft_path: Path
    text: str


@dataclass(slots=True)
class BookConfig:
    """Resolved publishing metadata for a book."""

    title: str
    author: str
    language: str
    subtitle: str
    default_formats: list[str]
    reference_docx: str
    epub_css: str
    audio_provider: str
    audio_model: str
    audio_voice: str
    audio_instructions: str
    speaking_rate_wpm: int
    reading_wpm: int
    tts_cost_per_1m_chars: float | None


def normalize_name(value: str) -> str:
    """Normalize user-facing names for slug fallback."""
    return re.sub(r"\s+", " ", value.strip())


def safe_slug(value: str) -> str:
    """Create a filesystem-safe lowercase slug."""
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "book"


def find_repo_root(start: Path | None = None) -> Path:
    """Find repository root by searching for .git or .authorkit."""
    current = (start or Path.cwd()).resolve()
    for path in [current, *current.parents]:
        if (path / ".git").exists() or (path / ".authorkit").exists():
            return path
    return current


def resolve_book_dir(repo_root: Path) -> Path:
    """Resolve the canonical single-book directory."""
    book_dir = (repo_root / BOOK_DIR_NAME).resolve()
    if not book_dir.exists():
        raise FileNotFoundError(f"No book directory found at {book_dir}. Run /authorkit.conceive first.")
    return book_dir


class BookConfigError(Exception):
    """Raised when ``book.toml`` cannot be parsed or contains invalid types.

    Carries the offending file path and a remediation hint so callers can
    surface an actionable error to the user instead of a raw traceback.
    """

    def __init__(self, message: str, *, config_path: Path):
        super().__init__(message)
        self.config_path = config_path


def _coerce_int(value: object, default: int, *, field: str, config_path: Path) -> int:
    """Coerce a TOML value to ``int`` or raise BookConfigError with file context."""
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        # bool is a subclass of int in Python — explicitly reject it so that
        # `speaking_rate_wpm = true` doesn't silently parse as 1.
        raise BookConfigError(
            f"`{field}` in {config_path} must be a number, got boolean.",
            config_path=config_path,
        )
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise BookConfigError(
            f"`{field}` in {config_path} must be a number, got {value!r}.",
            config_path=config_path,
        ) from exc


def _coerce_optional_float(value: object, *, field: str, config_path: Path) -> float | None:
    """Coerce a TOML value to ``float``/None, rejecting strings/bools loudly.

    Returning None for absent keys keeps the "uncomment to enable" UX from the
    README — but a *present* value with the wrong type should error rather
    than silently disable the feature.
    """
    if value is None:
        return None
    if isinstance(value, bool):
        raise BookConfigError(
            f"`{field}` in {config_path} must be a number, got boolean.",
            config_path=config_path,
        )
    if isinstance(value, (int, float)):
        return float(value)
    raise BookConfigError(
        f"`{field}` in {config_path} must be a number, got {value!r}.",
        config_path=config_path,
    )


def parse_book_config(book_dir: Path) -> BookConfig:
    """Load book metadata from book.toml with safe defaults.

    Raises:
        BookConfigError: If the file is unreadable, malformed, or any required
            numeric field has the wrong type. CLI callers translate this to a
            ``typer.BadParameter`` with a hint pointing at ``authorkit init``.
    """
    config_path = book_dir / "book.toml"
    raw: dict = {}
    if config_path.exists():
        # Accept legacy BOM-prefixed files created by some shell encodings.
        try:
            raw = tomllib.loads(config_path.read_text(encoding="utf-8-sig"))
        except tomllib.TOMLDecodeError as exc:
            raise BookConfigError(
                f"Could not parse {config_path}: {exc}.",
                config_path=config_path,
            ) from exc
        except OSError as exc:
            raise BookConfigError(
                f"Could not read {config_path}: {exc}.",
                config_path=config_path,
            ) from exc

    book_section = raw.get("book", {})
    build_section = raw.get("build", {})
    audio_section = raw.get("audio", {})
    stats_section = raw.get("stats", {})

    title = normalize_name(str(book_section.get("title") or book_dir.name))
    author = normalize_name(str(book_section.get("author") or "Unknown Author"))
    language = str(book_section.get("language") or "en-US")
    subtitle = normalize_name(str(book_section.get("subtitle") or ""))

    default_formats_raw = build_section.get("default_formats") or ["docx"]
    default_formats = [str(item).lower() for item in default_formats_raw if str(item).strip()]
    if not default_formats:
        default_formats = ["docx"]

    return BookConfig(
        title=title,
        author=author,
        language=language,
        subtitle=subtitle,
        default_formats=default_formats,
        reference_docx=str(build_section.get("reference_docx") or "").strip(),
        epub_css=str(build_section.get("epub_css") or "").strip(),
        audio_provider=str(audio_section.get("provider") or "openai").strip().lower(),
        audio_model=str(audio_section.get("model") or "gpt-4o-mini-tts").strip(),
        audio_voice=str(audio_section.get("voice") or "marin").strip(),
        audio_instructions=str(audio_section.get("instructions") or "").strip(),
        speaking_rate_wpm=_coerce_int(
            audio_section.get("speaking_rate_wpm"), 170,
            field="audio.speaking_rate_wpm", config_path=config_path,
        ),
        reading_wpm=_coerce_int(
            stats_section.get("reading_wpm"), 200,
            field="stats.reading_wpm", config_path=config_path,
        ),
        tts_cost_per_1m_chars=_coerce_optional_float(
            stats_section.get("tts_cost_per_1m_chars"),
            field="stats.tts_cost_per_1m_chars", config_path=config_path,
        ),
    )


def discover_chapter_drafts(book_dir: Path, from_chapter: int | None = None, to_chapter: int | None = None) -> list[ChapterDraft]:
    """Load chapter draft files in numeric order."""
    chapters_root = book_dir / CHAPTERS_DIR_NAME
    if not chapters_root.exists():
        return []

    drafts: list[ChapterDraft] = []
    for entry in chapters_root.iterdir():
        if not entry.is_dir():
            continue
        # Only directories whose names are pure numeric (e.g. "01", "02") are real
        # chapter folders. This excludes backups like "01-old/" or "chapters/archived/"
        # which would otherwise silently be included in book build/stats output.
        match = re.match(r"^(\d+)$", entry.name)
        if not match:
            continue
        chapter_num = int(match.group(1))
        if from_chapter is not None and chapter_num < from_chapter:
            continue
        if to_chapter is not None and chapter_num > to_chapter:
            continue

        draft_path = entry / "draft.md"
        if draft_path.exists():
            drafts.append(ChapterDraft(chapter_number=chapter_num, draft_path=draft_path, text=draft_path.read_text(encoding="utf-8")))

    return sorted(drafts, key=lambda item: item.chapter_number)


def chapter_title(text: str, fallback: str) -> str:
    """Extract first H1 title from markdown text."""
    for line in text.splitlines():
        if line.startswith("# "):
            return normalize_name(line[2:])
    return fallback


# Status markers tracked in chapters.md: ` ` pending, P planned, D drafted,
# R needs revision, X approved. See README "Chapter-Level Iteration".
CHAPTER_STATUS_LABELS: dict[str, str] = {
    " ": "pending",
    "P": "planned",
    "D": "drafted",
    "R": "review",
    "X": "approved",
}


def parse_chapter_statuses(book_dir: Path) -> dict[int, str]:
    """Parse chapters.md and return a mapping of chapter number to status label.

    Returns an empty mapping if chapters.md does not exist or parses no entries.
    Tolerant by design: a missing or malformed chapters.md must not break stats.

    Format expected (per chapters-template.md):
        - [X] CH01 [Part 1] Title - Brief summary
        - [D] CH02 ...
    """
    chapters_path = book_dir / "chapters.md"
    if not chapters_path.exists():
        return {}

    statuses: dict[int, str] = {}
    pattern = re.compile(r"^\s*-\s*\[(.)\]\s*CH(\d+)\b", re.IGNORECASE)
    try:
        text = chapters_path.read_text(encoding="utf-8-sig")
    except OSError:
        return {}

    for line in text.splitlines():
        match = pattern.match(line)
        if not match:
            continue
        marker = match.group(1)
        try:
            chapter_num = int(match.group(2))
        except ValueError:
            continue
        # Normalize: lowercase letters or non-listed markers are reported as raw
        # so an unexpected marker doesn't get silently coerced to "pending".
        label = CHAPTER_STATUS_LABELS.get(marker.upper(), marker)
        statuses[chapter_num] = label

    return statuses


def markdown_to_plain_text(markdown: str) -> str:
    """Remove basic markdown formatting for metrics and TTS payloads."""
    text = re.sub(r"```.*?```", "", markdown, flags=re.DOTALL)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^[>-]\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"[*_~]", "", text)
    return text.strip()


def to_json(data: object) -> str:
    """Serialize JSON output with predictable formatting and human-readable Unicode."""
    return json.dumps(data, indent=2, ensure_ascii=False)
