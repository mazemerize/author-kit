"""Core utilities for Author Kit book commands."""

from __future__ import annotations

import json
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

BOOK_DIR_NAME = "book"
WORLD_DIR_NAME = "world"
CHAPTERS_DIR_NAME = "chapters"
CHECKLISTS_DIR_NAME = "checklists"
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


def parse_book_config(book_dir: Path) -> BookConfig:
    """Load book metadata from book.toml with safe defaults."""
    config_path = book_dir / "book.toml"
    raw: dict = {}
    if config_path.exists():
        # Accept legacy BOM-prefixed files created by some shell encodings.
        raw = tomllib.loads(config_path.read_text(encoding="utf-8-sig"))

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

    tts_cost = stats_section.get("tts_cost_per_1m_chars")
    parsed_tts_cost = float(tts_cost) if isinstance(tts_cost, (int, float)) else None

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
        audio_voice=str(audio_section.get("voice") or "onyx").strip(),
        speaking_rate_wpm=int(audio_section.get("speaking_rate_wpm") or 170),
        reading_wpm=int(stats_section.get("reading_wpm") or 200),
        tts_cost_per_1m_chars=parsed_tts_cost,
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
        match = re.match(r"^(\d+)", entry.name)
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
    """Serialize JSON output with predictable formatting."""
    return json.dumps(data, indent=2, ensure_ascii=True)
