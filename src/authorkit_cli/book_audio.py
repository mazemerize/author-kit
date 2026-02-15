"""Audio generation pipeline for Author Kit."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn, TimeElapsedColumn

from .book_core import BookConfig, ChapterDraft, chapter_title, ensure_python_package, markdown_to_plain_text
from .book_render import ensure_system_tool

MAX_CHARS_PER_REQUEST = 3500
PAUSE_MARKER = "[PAUSE]"
DIALOG_MARKER = "[DIALOG]"
console = Console()


def _extract_key_from_dotenv(dotenv_path: Path) -> str | None:
    """Extract OPENAI_API_KEY from dotenv file with encoding fallbacks."""
    if not dotenv_path.exists() or not dotenv_path.is_file():
        return None

    contents: str | None = None
    for encoding in ("utf-8", "utf-8-sig", "utf-16"):
        try:
            contents = dotenv_path.read_text(encoding=encoding)
            break
        except Exception:
            continue

    if not contents:
        return None

    for line in contents.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        if key.strip() == "OPENAI_API_KEY":
            return value.strip().strip('"').strip("'")
    return None


def _strip_inline_markdown(text: str) -> str:
    """Strip common inline markdown syntax while preserving prose."""
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"[*_~]", "", text)
    return text.strip()


def _enhance_text_for_speech(markdown: str) -> str:
    """Enhance markdown prose with speech markers for better narration."""
    lines = markdown.splitlines()
    enhanced_lines: list[str] = []
    in_epigraph = False

    for raw_line in lines:
        stripped = raw_line.strip()
        if not stripped:
            enhanced_lines.append("")
            continue

        if stripped.startswith("# "):
            # Chapter title is handled separately in the audio intro.
            continue

        is_blockquote = stripped.startswith(">")
        working = stripped[1:].strip() if is_blockquote else stripped
        clean_line = _strip_inline_markdown(working)
        if not clean_line:
            continue

        if is_blockquote and (working.startswith("_") or working.startswith("*")) and not in_epigraph:
            in_epigraph = True
            enhanced_lines.append(clean_line)
            continue

        if in_epigraph and (clean_line.startswith("—") or clean_line.startswith("--")):
            enhanced_lines.append(clean_line)
            enhanced_lines.append(PAUSE_MARKER)
            in_epigraph = False
            continue

        if in_epigraph and is_blockquote:
            enhanced_lines.append(clean_line)
            continue

        quote_count = clean_line.count('"')
        if quote_count >= 2:
            enhanced_lines.append(f"{DIALOG_MARKER} {clean_line}")
        else:
            enhanced_lines.append(clean_line)

    compact = "\n".join(enhanced_lines)
    compact = re.sub(r"\n{3,}", "\n\n", compact)
    return compact.strip()


def _speech_instructions(chunk: str) -> str:
    """Build TTS instructions for a chunk based on included markers."""
    instructions = [
        "You are the narrator for an audiobook.",
        "Speak clearly with steady pacing and natural expression.",
        "Do not read markdown syntax.",
    ]
    if PAUSE_MARKER in chunk:
        instructions.append(f"When you encounter {PAUSE_MARKER}, take a deliberate 2-3 second pause and do not say the marker.")
    if DIALOG_MARKER in chunk:
        instructions.append(f"When you encounter {DIALOG_MARKER}, shift to a conversational tone and do not say the marker.")
    return " ".join(instructions)


def _chunk_text(text: str, max_chars: int = MAX_CHARS_PER_REQUEST) -> list[str]:
    """Split text into chunks below API request size limits."""
    chunks: list[str] = []
    current = ""
    for paragraph in text.split("\n\n"):
        candidate = (current + "\n\n" + paragraph).strip() if current else paragraph
        if len(candidate) > max_chars and current:
            chunks.append(current)
            current = paragraph
        else:
            current = candidate
    if current.strip():
        chunks.append(current)
    return chunks


def _synthesize_openai_chunk(client: object, model: str, voice: str, chunk: str, out_file: Path) -> None:
    """Generate one chunk of speech audio to a file."""
    response = client.audio.speech.create(
        model=model,
        voice=voice,
        input=chunk,
        instructions=_speech_instructions(chunk),
    )
    response.stream_to_file(str(out_file))


def _concat_mp3_files(input_files: list[Path], output_file: Path) -> None:
    """Concatenate mp3 files losslessly with ffmpeg concat demuxer."""
    if not input_files:
        return

    ensure_system_tool("ffmpeg")
    temp_list = output_file.parent / "_concat_list.txt"
    lines = [f"file '{f.resolve().as_posix()}'" for f in input_files]
    temp_list.write_text("\n".join(lines), encoding="utf-8")

    try:
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(temp_list),
            "-c",
            "copy",
            str(output_file),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            detail = result.stderr.strip() or result.stdout.strip() or "unknown error"
            raise RuntimeError(f"FFmpeg concat failed: {detail}")
    finally:
        temp_list.unlink(missing_ok=True)


def generate_audiobook(
    drafts: list[ChapterDraft],
    config: BookConfig,
    audio_dir: Path,
    merge_output: bool,
    force: bool,
    yes: bool,
    dotenv_search_roots: list[Path] | None = None,
) -> dict[str, object]:
    """Generate chapter audio files and optional merged audiobook file."""
    if config.audio_provider != "openai":
        raise ValueError(f"Unsupported audio provider: {config.audio_provider}")

    ensure_python_package("dotenv", "python-dotenv")
    ensure_python_package("openai")

    from dotenv import load_dotenv
    from openai import OpenAI

    dotenv_candidates: list[Path] = [Path.cwd() / ".env"]
    for root in dotenv_search_roots or []:
        dotenv_candidates.append(root / ".env")

    seen: set[Path] = set()
    for candidate in dotenv_candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.exists():
            load_dotenv(dotenv_path=resolved, override=False)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        for candidate in dotenv_candidates:
            key = _extract_key_from_dotenv(candidate)
            if key:
                os.environ["OPENAI_API_KEY"] = key
                api_key = key
                break
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set. Set it in your environment or .env file before running audio generation.")

    audio_dir.mkdir(parents=True, exist_ok=True)
    client = OpenAI(api_key=api_key)

    chapter_outputs: list[Path] = []
    generated = 0
    skipped = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
        transient=False,
    ) as progress:
        chapter_task = progress.add_task("Generating chapter audio...", total=len(drafts))
        for draft in drafts:
            title = chapter_title(draft.text, f"CH{draft.chapter_number:02d}")
            filename = f"{draft.chapter_number:02d}-{title.lower().replace(' ', '-')}.mp3"
            filename = "".join(ch for ch in filename if ch.isalnum() or ch in "-._")
            chapter_out = audio_dir / filename

            if chapter_out.exists() and not force:
                overwrite = yes or typer.confirm(f"Audio already exists for CH{draft.chapter_number:02d}: overwrite?", default=False)
                if not overwrite:
                    skipped += 1
                    chapter_outputs.append(chapter_out)
                    progress.advance(chapter_task)
                    continue

            clean_title = chapter_title(draft.text, f"Chapter {draft.chapter_number:02d}")
            enhanced_text = _enhance_text_for_speech(draft.text)
            if not enhanced_text:
                skipped += 1
                progress.advance(chapter_task)
                continue

            # Add a short title prelude and pause to improve chapter transitions.
            title_prefix = f"{PAUSE_MARKER}\n{clean_title}\n{PAUSE_MARKER}\n\n"
            speech_input = title_prefix + enhanced_text
            speech_input = markdown_to_plain_text(speech_input)
            chunks = _chunk_text(speech_input)
            temp_files: list[Path] = []
            for idx, chunk in enumerate(chunks, start=1):
                progress.update(
                    chapter_task,
                    description=f"CH{draft.chapter_number:02d}: synthesizing chunk {idx}/{len(chunks)}",
                )
                temp_chunk = audio_dir / f".tmp-ch{draft.chapter_number:02d}-{idx:03d}.mp3"
                _synthesize_openai_chunk(client, config.audio_model, config.audio_voice, chunk, temp_chunk)
                temp_files.append(temp_chunk)

            progress.update(chapter_task, description=f"CH{draft.chapter_number:02d}: combining chunks")
            _concat_mp3_files(temp_files, chapter_out)
            for temp in temp_files:
                temp.unlink(missing_ok=True)

            generated += 1
            chapter_outputs.append(chapter_out)
            progress.advance(chapter_task)

    merged_path: Path | None = None
    if merge_output and chapter_outputs:
        console.print("Merging chapter audio files into full audiobook...")
        merged_path = audio_dir / "audiobook-full.mp3"
        if merged_path.exists() and (force or yes or typer.confirm("Merged audiobook exists: overwrite?", default=False)):
            merged_path.unlink(missing_ok=True)
        if not merged_path.exists():
            _concat_mp3_files(chapter_outputs, merged_path)

    return {
        "generated": generated,
        "skipped": skipped,
        "chapter_files": [str(path) for path in chapter_outputs],
        "merged_file": str(merged_path) if merged_path else None,
    }
