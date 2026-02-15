"""Typer subcommands for book build/audio/stats workflows."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from .book_audio import generate_audiobook
from .book_core import (
    discover_chapter_drafts,
    find_repo_root,
    parse_book_config,
    resolve_book_dir,
    to_json,
)
from .book_render import SUPPORTED_FORMATS, build_manuscript_markdown, render_formats
from .book_stats import collect_stats, render_stats_markdown

console = Console()
book_app = typer.Typer(help="Book publishing tools")


def _resolve_context(book: str | None) -> tuple[Path, Path]:
    repo_root = find_repo_root()
    book_dir = resolve_book_dir(repo_root, book)
    if not book_dir.exists():
        raise typer.BadParameter(f"Book directory not found: {book_dir}")
    return repo_root, book_dir


def _resolve_formats(formats: list[str] | None, default_formats: list[str]) -> list[str]:
    selected = [item.lower() for item in (formats or default_formats)]
    if not selected:
        selected = ["docx"]
    invalid = [fmt for fmt in selected if fmt not in SUPPORTED_FORMATS]
    if invalid:
        raise typer.BadParameter(f"Unsupported format(s): {', '.join(invalid)}")
    return selected


@book_app.command("build")
def build(
    book: str | None = typer.Option(None, "--book", help="Book directory name under books/"),
    format: list[str] | None = typer.Option(None, "--format", help="Repeat to select multiple formats: docx, pdf, epub"),
    output_dir: str | None = typer.Option(None, "--output-dir", help="Output directory (default books/<book>/dist)"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing output files"),
    quiet: bool = typer.Option(False, "--quiet", help="Reduce output"),
) -> None:
    """Build manuscript artifacts from chapter drafts."""
    _, book_dir = _resolve_context(book)
    config = parse_book_config(book_dir)
    formats = _resolve_formats(format, config.default_formats)

    drafts = discover_chapter_drafts(book_dir)
    if not drafts:
        raise typer.BadParameter(f"No draft chapters found in {book_dir / 'chapters'}")

    dist_dir = Path(output_dir).resolve() if output_dir else (book_dir / "dist")
    dist_dir.mkdir(parents=True, exist_ok=True)

    manuscript_markdown = build_manuscript_markdown(config, drafts)
    manuscript_path = dist_dir / "manuscript.md"
    manuscript_path.write_text(manuscript_markdown, encoding="utf-8")

    produced = render_formats(book_dir, dist_dir, manuscript_path, formats, config, force)

    if not quiet:
        console.print(f"Book: [bold]{book_dir.name}[/bold]")
        console.print(f"Manuscript source: {len(drafts)} chapter draft(s)")
        console.print(f"Assembled markdown: {manuscript_path}")
        for item in produced:
            console.print(f"Built: {item}")


@book_app.command("audio")
def audio(
    book: str | None = typer.Option(None, "--book", help="Book directory name under books/"),
    provider: str | None = typer.Option(None, "--provider", help="Audio provider (default from book.toml)"),
    voice: str | None = typer.Option(None, "--voice", help="Voice name override"),
    model: str | None = typer.Option(None, "--model", help="Model override"),
    output_dir: str | None = typer.Option(None, "--output-dir", help="Output directory (default books/<book>/dist/audio)"),
    merge: bool = typer.Option(False, "--merge", help="Also create merged audiobook"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing chapter audio without prompts"),
    yes: bool = typer.Option(False, "--yes", help="Non-interactive confirmation for overwrite prompts"),
    from_chapter: int | None = typer.Option(None, "--from-chapter", help="Minimum chapter number"),
    to_chapter: int | None = typer.Option(None, "--to-chapter", help="Maximum chapter number"),
) -> None:
    """Generate audiobook files from chapter drafts."""
    _, book_dir = _resolve_context(book)
    config = parse_book_config(book_dir)

    if provider:
        config.audio_provider = provider.lower()
    if voice:
        config.audio_voice = voice
    if model:
        config.audio_model = model

    drafts = discover_chapter_drafts(book_dir, from_chapter=from_chapter, to_chapter=to_chapter)
    if not drafts:
        raise typer.BadParameter("No matching draft chapters found for audio generation.")

    audio_dir = Path(output_dir).resolve() if output_dir else (book_dir / "dist" / "audio")

    result = generate_audiobook(
        drafts=drafts,
        config=config,
        audio_dir=audio_dir,
        merge_output=merge,
        force=force,
        yes=yes,
    )

    console.print(f"Audio directory: {audio_dir}")
    console.print(f"Generated: {result['generated']}")
    console.print(f"Skipped: {result['skipped']}")
    if result["merged_file"]:
        console.print(f"Merged file: {result['merged_file']}")


@book_app.command("stats")
def stats(
    book: str | None = typer.Option(None, "--book", help="Book directory name under books/"),
    output: str = typer.Option("table", "--output", help="Output format: table, json, markdown"),
    audio_dir: str | None = typer.Option(None, "--audio-dir", help="Audio directory for actual duration lookup"),
    wpm: int | None = typer.Option(None, "--wpm", help="Reading words-per-minute override"),
) -> None:
    """Show manuscript statistics from draft chapters."""
    _, book_dir = _resolve_context(book)
    config = parse_book_config(book_dir)
    if wpm is not None:
        config.reading_wpm = wpm

    drafts = discover_chapter_drafts(book_dir)
    if not drafts:
        raise typer.BadParameter("No draft chapters found for stats.")

    resolved_audio_dir = Path(audio_dir).resolve() if audio_dir else (book_dir / "dist" / "audio")
    stat_payload = collect_stats(drafts=drafts, config=config, audio_dir=resolved_audio_dir)

    rendered = output.lower().strip()
    if rendered == "json":
        console.print(to_json(stat_payload))
        return
    if rendered == "markdown":
        console.print(render_stats_markdown(stat_payload))
        return
    if rendered != "table":
        raise typer.BadParameter("Invalid --output. Use table, json, or markdown.")

    table = Table(title=f"Book Stats: {book_dir.name}")
    table.add_column("CH")
    table.add_column("Title")
    table.add_column("Words", justify="right")
    table.add_column("Chars", justify="right")
    table.add_column("Dialog %", justify="right")

    for chapter in stat_payload["chapters"]:
        table.add_row(
            str(chapter["chapter"]),
            chapter["title"],
            str(chapter["words"]),
            str(chapter["chars"]),
            f"{chapter['dialogue_ratio'] * 100:.1f}",
        )

    console.print(table)
    totals = stat_payload["totals"]
    console.print(
        "Totals: "
        f"chapters={totals['chapters']} "
        f"words={totals['words']} "
        f"chars={totals['chars']} "
        f"est_read_min={totals['est_read_minutes']:.2f} "
        f"est_audio_min={totals['est_audio_minutes']:.2f}"
    )
