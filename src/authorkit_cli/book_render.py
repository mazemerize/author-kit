"""Document rendering pipeline for Author Kit."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .book_core import BookConfig, ChapterDraft

SUPPORTED_FORMATS = {"docx", "pdf", "epub"}


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
        "pdflatex": [
            "Windows: winget install --id MiKTeX.MiKTeX -e",
            "macOS: brew install --cask mactex-no-gui",
            "Ubuntu/Debian: sudo apt-get install texlive-latex-base",
        ],
    }
    lines = guidance.get(tool, [f"Install '{tool}' and ensure it is on PATH."])
    raise RuntimeError("Missing required system dependency: " + tool + "\n" + "\n".join(lines))


def build_manuscript_markdown(config: BookConfig, drafts: list[ChapterDraft]) -> str:
    """Assemble a full manuscript markdown document."""
    subtitle_line = f"subtitle: {config.subtitle}\n" if config.subtitle else ""
    frontmatter = (
        "---\n"
        f"title: {config.title}\n"
        f"author: {config.author}\n"
        f"lang: {config.language}\n"
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


def _find_repo_root(start: Path) -> Path:
    """Find repository root from a book path."""
    current = start.resolve()
    for parent in [current, *current.parents]:
        if (parent / ".authorkit").exists():
            return parent
    return current


def _resolve_asset_path(book_dir: Path, configured_path: str, default_rel: str) -> Path | None:
    """Resolve configured style path with repo defaults as fallback."""
    repo_root = _find_repo_root(book_dir)

    candidates: list[Path] = []
    if configured_path:
        cfg = Path(configured_path)
        candidates.extend(
            [
                cfg,
                book_dir / cfg,
                repo_root / cfg,
            ]
        )
    candidates.append(repo_root / default_rel)

    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.exists():
            return resolved
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
    if any(fmt.lower() == "pdf" for fmt in formats):
        ensure_system_tool("pdflatex")

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
            )
            if ref_path:
                cmd.extend([f"--reference-doc={ref_path}"])
        if format_name == "epub":
            cmd.extend(["--toc", "--toc-depth=1"])
            css_path = _resolve_asset_path(
                book_dir,
                config.epub_css,
                ".authorkit/templates/publishing/epub.css",
            )
            if css_path:
                cmd.extend([f"--css={css_path}"])

        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            detail = result.stderr.strip() or result.stdout.strip() or "unknown error"
            raise RuntimeError(f"Pandoc conversion failed for {format_name}: {detail}")

        produced.append(out_file)

    return produced
