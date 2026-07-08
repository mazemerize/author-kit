"""Document rendering pipeline for Author Kit.

Assembles chapter drafts into a single manuscript and invokes pandoc to
produce the requested output formats (docx, epub).

Author:
    mdemarne
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from rich.console import Console

from .book_core import BookConfig, ChapterDraft, find_repo_root

# Shared Rich console for warnings emitted during render.
console = Console()

# Output formats supported by the pandoc build pipeline.
SUPPORTED_FORMATS = {"docx", "epub"}


def ensure_system_tool(tool: str) -> None:
    """Fail with actionable guidance when a system binary is missing."""
    if shutil.which(tool):
        return

    guidance = {
        "pandoc": [
            "Windows: winget install --id JohnMacFarlane.Pandoc -e",
            "macOS: brew install pandoc",
            "Ubuntu/Debian: sudo apt-get install pandoc",
        ],
        "ffmpeg": [
            "Windows: winget install --id Gyan.FFmpeg -e",
            "macOS: brew install ffmpeg",
            "Ubuntu/Debian: sudo apt-get install ffmpeg",
        ],
    }
    lines = guidance.get(tool, [f"Install '{tool}' and ensure it is on PATH."])
    lines.append("After installing, close and reopen your terminal so PATH updates are picked up.")
    raise RuntimeError("Missing required system dependency: " + tool + "\n" + "\n".join(lines))


def build_manuscript_markdown(config: BookConfig, drafts: list[ChapterDraft]) -> str:
    """Assemble a full manuscript markdown document."""
    # JSON string literals are valid YAML scalars and prevent punctuation parse errors.
    subtitle_line = f"subtitle: {json.dumps(config.subtitle, ensure_ascii=False)}\n" if config.subtitle else ""
    frontmatter = (
        "---\n"
        f"title: {json.dumps(config.title, ensure_ascii=False)}\n"
        f"author: {json.dumps(config.author, ensure_ascii=False)}\n"
        f"lang: {json.dumps(config.language, ensure_ascii=False)}\n"
        f"{subtitle_line}"
        "---\n\n"
    )

    parts: list[str] = [frontmatter]
    for draft in drafts:
        if parts[-1] and not parts[-1].endswith("\n\n"):
            parts.append("\n\n")
        parts.append(draft.text.strip())
        parts.append("\n\n")
    return "".join(parts).strip() + "\n"


def _resolve_asset_path(book_dir: Path, configured_path: str, default_rel: str, asset_label: str) -> Path | None:
    """Resolve configured style path with repo defaults as fallback.

    Returns the first existing candidate, or ``None`` if even the default is missing.
    Emits a warning when ``configured_path`` is set but resolves to nothing — this is
    the silent-degrade scenario where a typo in book.toml otherwise produces a
    default-styled output without telling the user.
    """
    repo_root = find_repo_root(book_dir)

    configured_candidates: list[Path] = []
    if configured_path:
        cfg = Path(configured_path)
        configured_candidates.extend([cfg, book_dir / cfg, repo_root / cfg])
    default_candidate = repo_root / default_rel

    seen: set[Path] = set()
    for candidate in configured_candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.exists():
            return resolved

    if configured_path:
        console.print(
            f"[yellow]Warning:[/yellow] {asset_label} configured as "
            f"'{configured_path}' but no file was found at that path. "
            f"Falling back to the bundled default."
        )

    default_resolved = default_candidate.resolve()
    if default_resolved.exists():
        return default_resolved
    return None


def render_formats(
    book_dir: Path,
    output_dir: Path,
    manuscript_path: Path,
    formats: list[str],
    config: BookConfig,
    force: bool,
) -> list[Path]:
    """Render manuscript markdown into requested output formats."""
    ensure_system_tool("pandoc")

    output_dir.mkdir(parents=True, exist_ok=True)
    produced: list[Path] = []

    for fmt in formats:
        format_name = fmt.lower()
        if format_name not in SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported format: {fmt}")

        out_file = output_dir / f"manuscript.{format_name}"
        if out_file.exists() and not force:
            raise FileExistsError(f"Output file already exists: {out_file}. Use --force to overwrite.")

        cmd = ["pandoc", str(manuscript_path), "-o", str(out_file)]

        if format_name == "docx":
            ref_path = _resolve_asset_path(
                book_dir,
                config.reference_docx,
                ".authorkit/templates/publishing/reference.docx",
                "DOCX reference document",
            )
            if ref_path:
                cmd.extend([f"--reference-doc={ref_path}"])
        if format_name == "epub":
            cmd.extend(["--toc", "--toc-depth=1"])
            css_path = _resolve_asset_path(
                book_dir,
                config.epub_css,
                ".authorkit/templates/publishing/epub.css",
                "EPUB stylesheet",
            )
            if css_path:
                cmd.extend([f"--css={css_path}"])

        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            detail = result.stderr.strip() or result.stdout.strip() or "unknown error"
            raise RuntimeError(f"Pandoc conversion failed for {format_name}: {detail}")

        produced.append(out_file)

    return produced
