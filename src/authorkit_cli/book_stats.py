"""Statistics generation for Author Kit manuscripts.

Computes per-chapter and aggregate metrics (word counts, dialogue ratio,
estimated read/audio durations) and renders them as tables, JSON, or Markdown.

Author:
    mdemarne
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path

from mutagen import File

from .book_core import BookConfig, ChapterDraft, chapter_title, markdown_to_plain_text


@dataclass(slots=True)
class ChapterStats:
    """Metrics for one chapter draft."""

    chapter: int
    title: str
    words: int
    chars: int
    paragraphs: int
    headings: int
    dialogue_lines: int
    dialogue_ratio: float
    est_read_minutes: float
    est_audio_minutes: float


def _count_dialogue_lines(markdown: str) -> int:
    """Count non-empty lines that open with a quotation mark (dialogue heuristic).

    Args:
        markdown: Raw chapter markdown text.

    Returns:
        int: Number of lines identified as dialogue.
    """
    lines = [line.strip() for line in markdown.splitlines() if line.strip()]
    return sum(1 for line in lines if line.startswith('"') or line.startswith("'"))


def _mutagen_duration_seconds(path: Path) -> float:
    """Read the actual audio duration from an MP3 file via mutagen.

    Args:
        path: Path to the MP3 file.

    Returns:
        float: Duration in seconds, or 0.0 on any read failure.
    """
    try:
        audio_file = File(path)
        if audio_file and audio_file.info:
            return float(audio_file.info.length)
    except Exception:
        return 0.0
    return 0.0


def collect_stats(drafts: list[ChapterDraft], config: BookConfig, audio_dir: Path | None = None) -> dict[str, object]:
    """Build per-chapter and global manuscript statistics."""
    per_chapter: list[ChapterStats] = []

    for draft in drafts:
        plain = markdown_to_plain_text(draft.text)
        words = [token for token in re.split(r"\s+", plain) if token]
        word_count = len(words)
        paragraph_count = len([p for p in plain.split("\n\n") if p.strip()])
        heading_count = len([line for line in draft.text.splitlines() if line.startswith("#")])
        dialogue_lines = _count_dialogue_lines(draft.text)
        all_lines = len([line for line in draft.text.splitlines() if line.strip()])
        dialogue_ratio = (dialogue_lines / all_lines) if all_lines else 0.0
        est_read = word_count / max(config.reading_wpm, 1)
        est_audio = word_count / max(config.speaking_rate_wpm, 1)

        per_chapter.append(
            ChapterStats(
                chapter=draft.chapter_number,
                title=chapter_title(draft.text, f"CH{draft.chapter_number:02d}"),
                words=word_count,
                chars=len(plain),
                paragraphs=paragraph_count,
                headings=heading_count,
                dialogue_lines=dialogue_lines,
                dialogue_ratio=dialogue_ratio,
                est_read_minutes=est_read,
                est_audio_minutes=est_audio,
            )
        )

    total_words = sum(item.words for item in per_chapter)
    total_chars = sum(item.chars for item in per_chapter)
    est_audio_minutes = sum(item.est_audio_minutes for item in per_chapter)

    output: dict[str, object] = {
        "chapters": [asdict(item) for item in per_chapter],
        "totals": {
            "chapters": len(per_chapter),
            "words": total_words,
            "chars": total_chars,
            "est_read_minutes": sum(item.est_read_minutes for item in per_chapter),
            "est_audio_minutes": est_audio_minutes,
        },
        "cost_estimate": {
            "tts_cost_per_1m_chars": config.tts_cost_per_1m_chars,
            "estimated_tts_cost": (total_chars / 1_000_000.0) * config.tts_cost_per_1m_chars if config.tts_cost_per_1m_chars is not None else None,
        },
    }

    if audio_dir and audio_dir.exists():
        try:
            chapter_audio = sorted(path for path in audio_dir.glob("*.mp3") if path.is_file())
            output["audio"] = {
                "files": len(chapter_audio),
                "actual_minutes": sum(_mutagen_duration_seconds(path) for path in chapter_audio) / 60.0,
            }
        except Exception:
            output["audio"] = {
                "files": 0,
                "actual_minutes": 0.0,
            }

    return output


def render_stats_markdown(stats: dict[str, object]) -> str:
    """Render markdown report."""
    lines = ["# Book Statistics", "", "## Totals", ""]
    totals = stats["totals"]
    lines.append(f"- Chapters: {totals['chapters']}")
    lines.append(f"- Words: {totals['words']}")
    lines.append(f"- Characters: {totals['chars']}")
    lines.append(f"- Estimated read time (minutes): {totals['est_read_minutes']:.2f}")
    lines.append(f"- Estimated audio duration (minutes): {totals['est_audio_minutes']:.2f}")
    lines.append("")
    lines.append("## Per Chapter")
    lines.append("")
    lines.append("| Chapter | Title | Words | Chars | Dialogue Ratio | Est Audio Min |")
    lines.append("|---|---|---:|---:|---:|---:|")

    for chapter in stats["chapters"]:
        lines.append(
            f"| {chapter['chapter']} | {chapter['title']} | {chapter['words']} | {chapter['chars']} | {chapter['dialogue_ratio']:.2f} | {chapter['est_audio_minutes']:.2f} |"
        )
    return "\n".join(lines) + "\n"
