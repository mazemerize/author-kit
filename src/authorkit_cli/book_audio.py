"""Audio generation pipeline for Author Kit.

Converts chapter drafts to MP3 files via the OpenAI TTS API, handles
chunking, concatenation with ffmpeg, and ID3 metadata tagging.

Author:
    mdemarne
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import typer
from dotenv import load_dotenv
from mutagen.id3 import COMM, TALB, TLAN, TIT2, TPE1, TRCK, ID3, ID3NoHeaderError
from openai import OpenAI
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn, TimeElapsedColumn

from .book_core import BookConfig, ChapterDraft, chapter_title, find_repo_root, markdown_to_plain_text
from .book_render import ensure_system_tool

# Maximum characters per TTS API request; avoids payload size rejections.
MAX_CHARS_PER_REQUEST = 3500
# Default location of the narration instructions template inside the repo.
DEFAULT_INSTRUCTIONS_REL = ".authorkit/templates/publishing/audio-instructions.txt"
# Shared Rich console for progress output.
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


def resolve_audio_instructions(book_dir: Path, config: BookConfig) -> str:
    """Resolve and read the narration instructions template.

    Resolution order mirrors the asset path logic used for epub/docx templates:
    configured path (absolute → relative to book dir → relative to repo root),
    then the shipped default.
    """
    repo_root = find_repo_root(book_dir)
    candidates: list[Path] = []
    if config.audio_instructions:
        cfg = Path(config.audio_instructions)
        candidates.extend([cfg, book_dir / cfg, repo_root / cfg])
    candidates.append(repo_root / DEFAULT_INSTRUCTIONS_REL)

    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.exists():
            return resolved.read_text(encoding="utf-8").strip()

    # Inline fallback when no template file is found anywhere.
    return "You are the narrator for an audiobook. Speak clearly with steady pacing and natural expression."


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


def _synthesize_openai_chunk(client: object, model: str, voice: str, chunk: str, out_file: Path, instructions: str) -> None:
    """Generate one chunk of speech audio to a file."""
    response = client.audio.speech.create(
        model=model,
        voice=voice,
        input=chunk,
        instructions=instructions,
    )
    response.stream_to_file(str(out_file))


def _generate_silence(duration_s: float, out_file: Path) -> None:
    """Generate a silent MP3 of the given duration using ffmpeg."""
    ensure_system_tool("ffmpeg")
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"anullsrc=r=24000:cl=mono",
        "-t", str(duration_s),
        "-c:a", "libmp3lame", "-b:a", "64k",
        str(out_file),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "unknown error"
        raise RuntimeError(f"FFmpeg silence generation failed: {detail}")


def _concat_mp3_files(
    input_files: list[Path],
    output_file: Path,
    gap_seconds: float = 0.0,
) -> None:
    """Concatenate mp3 files with ffmpeg concat demuxer.

    When *gap_seconds* is positive a short silence is inserted between
    every pair of input files so that chapter segments don't run together.
    """
    if not input_files:
        return

    ensure_system_tool("ffmpeg")

    silence_file: Path | None = None
    if gap_seconds > 0:
        silence_file = output_file.parent / "_silence_gap.mp3"
        _generate_silence(gap_seconds, silence_file)

    temp_list = output_file.parent / "_concat_list.txt"
    lines: list[str] = []
    for i, f in enumerate(input_files):
        lines.append(f"file '{f.resolve().as_posix()}'")
        if silence_file and i < len(input_files) - 1:
            lines.append(f"file '{silence_file.resolve().as_posix()}'")
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
        if silence_file:
            silence_file.unlink(missing_ok=True)


def _chapter_output_path(audio_dir: Path, draft: ChapterDraft) -> Path:
    """Build the output MP3 path for a chapter draft.

    Args:
        audio_dir: Target audio output directory.
        draft: Chapter draft providing chapter number and title text.

    Returns:
        Path: Filesystem-safe MP3 path inside audio_dir.
    """
    title = chapter_title(draft.text, f"CH{draft.chapter_number:02d}")
    filename = f"{draft.chapter_number:02d}-{title.lower().replace(' ', '-')}.mp3"
    filename = "".join(ch for ch in filename if ch.isalnum() or ch in "-._")
    return audio_dir / filename


def _write_mp3_metadata(
    *,
    path: Path,
    title: str,
    album: str,
    artist: str,
    language: str,
    track_number: int | None = None,
    track_total: int | None = None,
    comment: str = "Generated by Author Kit",
) -> None:
    """Write ID3 metadata tags to an MP3 file; warn and continue on failures."""
    try:
        try:
            tags = ID3(path)
        except ID3NoHeaderError:
            tags = ID3()

        tags.delall("TIT2")
        tags.delall("TALB")
        tags.delall("TPE1")
        tags.delall("TLAN")
        tags.delall("TRCK")
        tags.delall("COMM")

        tags.add(TIT2(encoding=3, text=[title]))
        tags.add(TALB(encoding=3, text=[album]))
        tags.add(TPE1(encoding=3, text=[artist]))
        tags.add(TLAN(encoding=3, text=[language]))
        if track_number is not None and track_total is not None:
            tags.add(TRCK(encoding=3, text=[f"{track_number}/{track_total}"]))
        tags.add(COMM(encoding=3, lang="eng", desc="authorkit", text=[comment]))
        tags.save(path)
    except Exception as exc:
        console.print(f"[yellow]Warning:[/yellow] Failed to write metadata for {path.name}: {exc}")


def generate_audiobook(
    drafts: list[ChapterDraft],
    config: BookConfig,
    audio_dir: Path,
    merge_output: bool,
    force: bool,
    yes: bool,
    dotenv_search_roots: list[Path] | None = None,
    book_dir: Path | None = None,
) -> dict[str, object]:
    """Generate chapter audio files and optional merged audiobook file."""
    if config.audio_provider != "openai":
        raise ValueError(f"Unsupported audio provider: {config.audio_provider}")

    setup_progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=console,
        transient=False,
    )
    with setup_progress:
        setup_task = setup_progress.add_task("Loading environment configuration...", total=None)

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

        setup_progress.update(setup_task, description="Audio runtime ready.")

    audio_dir.mkdir(parents=True, exist_ok=True)
    client = OpenAI(api_key=api_key)
    instructions = resolve_audio_instructions(book_dir or audio_dir.parent.parent, config)
    chapter_total = len(drafts)

    chapter_jobs: list[tuple[int, ChapterDraft, Path, bool]] = []
    for chapter_index, draft in enumerate(drafts, start=1):
        chapter_out = _chapter_output_path(audio_dir, draft)
        should_generate = True
        if chapter_out.exists() and not force:
            should_generate = yes or typer.confirm(f"Audio already exists for CH{draft.chapter_number:02d}: overwrite?", default=False)
        chapter_jobs.append((chapter_index, draft, chapter_out, should_generate))

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
        chapter_task = progress.add_task("Generating chapter audio...", total=chapter_total)
        for chapter_index, draft, chapter_out, should_generate in chapter_jobs:
            clean_title = chapter_title(draft.text, f"Chapter {draft.chapter_number:02d}")
            metadata_title = chapter_title(draft.text, f"CH{draft.chapter_number:02d}")

            if not should_generate:
                skipped += 1
                chapter_outputs.append(chapter_out)
                _write_mp3_metadata(
                    path=chapter_out,
                    title=metadata_title,
                    album=config.title,
                    artist=config.author,
                    language=config.language,
                    track_number=chapter_index,
                    track_total=chapter_total,
                    comment=f"Author Kit chapter audio CH{draft.chapter_number:02d}",
                )
                progress.advance(chapter_task)
                continue

            speech_text = markdown_to_plain_text(draft.text)
            if not speech_text:
                skipped += 1
                progress.advance(chapter_task)
                continue

            # The title text survives markdown_to_plain_text (only the
            # "#" marker is stripped), so remove it to avoid reading the
            # title twice — we prepend clean_title ourselves with a
            # better pause.
            speech_lines = speech_text.split("\n", 1)
            if speech_lines and speech_lines[0].strip().lower() == clean_title.strip().lower():
                speech_text = speech_lines[1].strip() if len(speech_lines) > 1 else ""

            speech_input = f"{clean_title}\n\n{speech_text}"
            chunks = _chunk_text(speech_input)
            temp_files: list[Path] = []
            prev_chunk: str | None = None
            for idx, chunk in enumerate(chunks, start=1):
                progress.update(
                    chapter_task,
                    description=f"CH{draft.chapter_number:02d}: synthesizing chunk {idx}/{len(chunks)}",
                )
                temp_chunk = audio_dir / f".tmp-ch{draft.chapter_number:02d}-{idx:03d}.mp3"

                # Give the TTS model trailing context from the previous
                # chunk so it can maintain consistent tone and pacing
                # across segment boundaries.
                chunk_instructions = instructions
                if prev_chunk is not None:
                    tail = prev_chunk.strip().rsplit("\n\n", 1)[-1][-300:]
                    chunk_instructions = (
                        f"{instructions}\n\n"
                        "Continue seamlessly from the previous passage. "
                        "Match the tone, pace, and energy of the preceding text "
                        f"which ended with:\n\"{tail}\""
                    )

                _synthesize_openai_chunk(client, config.audio_model, config.audio_voice, chunk, temp_chunk, chunk_instructions)
                prev_chunk = chunk
                temp_files.append(temp_chunk)

            progress.update(chapter_task, description=f"CH{draft.chapter_number:02d}: combining chunks")
            _concat_mp3_files(temp_files, chapter_out, gap_seconds=0.8)
            for temp in temp_files:
                temp.unlink(missing_ok=True)
            _write_mp3_metadata(
                path=chapter_out,
                title=metadata_title,
                album=config.title,
                artist=config.author,
                language=config.language,
                track_number=chapter_index,
                track_total=chapter_total,
                comment=f"Author Kit chapter audio CH{draft.chapter_number:02d}",
            )

            generated += 1
            chapter_outputs.append(chapter_out)
            progress.advance(chapter_task)

    merged_path: Path | None = None
    if merge_output and chapter_outputs:
        console.print("Merging chapter audio files into full audiobook...")
        merged_path = audio_dir / "audiobook-full.mp3"
        if merged_path.exists():
            overwrite_merged = force or yes or typer.confirm("Merged audiobook exists: overwrite?", default=False)
            if overwrite_merged:
                merged_path.unlink(missing_ok=True)
        if not merged_path.exists():
            _concat_mp3_files(chapter_outputs, merged_path, gap_seconds=1.5)
        _write_mp3_metadata(
            path=merged_path,
            title=f"{config.title} (Audiobook)",
            album=config.title,
            artist=config.author,
            language=config.language,
            comment="Author Kit merged audiobook",
        )

    return {
        "generated": generated,
        "skipped": skipped,
        "chapter_files": [str(path) for path in chapter_outputs],
        "merged_file": str(merged_path) if merged_path else None,
    }
