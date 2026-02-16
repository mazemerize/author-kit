"""CLI behavior tests for Author Kit installer workflows.

Author:
    Mazemerize contributors.
"""

import json
import re
from pathlib import Path

import authorkit_cli as cli
import authorkit_cli.book_core as book_core
import authorkit_cli.book_commands as book_commands
import authorkit_cli.book_audio as book_audio
from typer.testing import CliRunner


runner = CliRunner()


def test_init_installs_multiple_ai_flavors_side_by_side():
    """Verify multi-AI installation writes side-by-side outputs.

    Returns:
        None
    """
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli.app,
            [
                "init",
                ".",
                "--ai",
                "claude",
                "--ai",
                "copilot",
                "--script",
                "sh",
                "--here",
                "--force",
                "--ignore-agent-tools",
                "--no-git",
            ],
        )

        assert result.exit_code == 0, result.output
        assert Path(".claude/commands/authorkit.chapter.md").exists()
        assert Path(".github/prompts/authorkit.chapter.prompt.md").exists()
        assert Path("CLAUDE.md").exists()
        assert Path(".github/copilot-instructions.md").exists()

        manifest = json.loads(Path(".authorkit/install-manifest.json").read_text(encoding="utf-8"))
        assert manifest["ais"] == ["claude", "copilot"]
        assert manifest["script"] == "sh"
        assert ".claude/commands/authorkit.chapter.md" in manifest["managed_paths"]
        assert ".github/prompts/authorkit.chapter.prompt.md" in manifest["managed_paths"]


def test_init_rerun_replaces_unselected_ai_outputs():
    """Verify rerun removes stale outputs for unselected AI flavors.

    Returns:
        None
    """
    with runner.isolated_filesystem():
        first = runner.invoke(
            cli.app,
            [
                "init",
                ".",
                "--ai",
                "claude,copilot",
                "--script",
                "sh",
                "--here",
                "--force",
                "--ignore-agent-tools",
                "--no-git",
            ],
        )
        assert first.exit_code == 0, first.output

        second = runner.invoke(
            cli.app,
            [
                "init",
                ".",
                "--ai",
                "codex",
                "--script",
                "sh",
                "--here",
                "--force",
                "--ignore-agent-tools",
                "--no-git",
            ],
        )
        assert second.exit_code == 0, second.output

        assert Path(".codex/prompts/authorkit.chapter.md").exists()
        assert Path(".codex/AGENTS.md").exists()
        assert not Path(".claude/commands/authorkit.chapter.md").exists()
        assert not Path(".github/prompts/authorkit.chapter.prompt.md").exists()

        manifest = json.loads(Path(".authorkit/install-manifest.json").read_text(encoding="utf-8"))
        assert manifest["ais"] == ["codex"]


def test_init_errors_when_required_tool_missing(monkeypatch):
    """Verify required agent tool checks fail when tool is missing.

    Args:
        monkeypatch: Pytest monkeypatch fixture.

    Returns:
        None
    """
    monkeypatch.setattr(cli, "tool_exists", lambda tool: False if tool == "codex" else True)

    with runner.isolated_filesystem():
        result = runner.invoke(
            cli.app,
            [
                "init",
                ".",
                "--ai",
                "codex",
                "--script",
                "sh",
                "--here",
                "--force",
            ],
        )

        assert result.exit_code != 0
        assert "Required tool(s) not found in PATH: codex" in result.output


def test_version_command_outputs_version():
    """Verify version output contains the CLI version string.

    Returns:
        None
    """
    result = runner.invoke(cli.app, ["version"])
    assert result.exit_code == 0
    assert f"authorkit-cli {cli.get_cli_version()}" in result.output


def _seed_book_tree(book_name: str = "001-test-book") -> Path:
    root = Path("books") / book_name / "chapters" / "01"
    root.mkdir(parents=True, exist_ok=True)
    (root / "draft.md").write_text("# Chapter One\n\nThis is a test draft.\n", encoding="utf-8")
    return root.parents[1]


def test_book_build_command_writes_manuscript_and_formats(monkeypatch):
    """Verify book build assembles manuscript and calls format renderer."""
    with runner.isolated_filesystem():
        book_dir = _seed_book_tree()
        outputs = [book_dir / "dist" / "manuscript.docx"]

        monkeypatch.setattr(book_commands, "render_formats", lambda *args, **kwargs: outputs)

        result = runner.invoke(cli.app, ["book", "build", "--book", book_dir.name])

        assert result.exit_code == 0, result.output
        assert (book_dir / "dist" / "manuscript.md").exists()
        assert "Built:" in result.output


def test_book_build_prompts_and_skips_existing_output(monkeypatch):
    """Verify existing outputs are skipped when overwrite prompt is declined."""
    with runner.isolated_filesystem():
        book_dir = _seed_book_tree()
        dist_dir = book_dir / "dist"
        dist_dir.mkdir(parents=True, exist_ok=True)
        (dist_dir / "manuscript.docx").write_text("existing", encoding="utf-8")
        called = {"render": False}

        def fake_render(*args, **kwargs):
            called["render"] = True
            return []

        monkeypatch.setattr(book_commands, "render_formats", fake_render)
        monkeypatch.setattr(book_commands.typer, "confirm", lambda *args, **kwargs: False)

        result = runner.invoke(cli.app, ["book", "build", "--book", book_dir.name, "--format", "docx"])

        assert result.exit_code == 0, result.output
        assert called["render"] is False
        assert "No output formats selected for rendering." in result.output


def test_book_build_prompts_and_overwrites_existing_output(monkeypatch):
    """Verify existing outputs are rebuilt when overwrite prompt is accepted."""
    with runner.isolated_filesystem():
        book_dir = _seed_book_tree()
        dist_dir = book_dir / "dist"
        dist_dir.mkdir(parents=True, exist_ok=True)
        (dist_dir / "manuscript.docx").write_text("existing", encoding="utf-8")
        captured = {}
        outputs = [dist_dir / "manuscript.docx"]

        def fake_render(*args, **kwargs):
            captured["formats"] = args[3]
            captured["force"] = kwargs["force"]
            return outputs

        monkeypatch.setattr(book_commands, "render_formats", fake_render)
        monkeypatch.setattr(book_commands.typer, "confirm", lambda *args, **kwargs: True)

        result = runner.invoke(cli.app, ["book", "build", "--book", book_dir.name, "--format", "docx"])

        assert result.exit_code == 0, result.output
        assert captured["formats"] == ["docx"]
        assert captured["force"] is True
        assert "Built:" in result.output


def test_book_build_command_reports_render_failures(monkeypatch):
    """Verify build command prints a concise error when rendering fails."""
    with runner.isolated_filesystem():
        book_dir = _seed_book_tree()

        def fail_render(*args, **kwargs):
            raise RuntimeError("Pandoc conversion failed for pdf: pdflatex not found")

        monkeypatch.setattr(book_commands, "render_formats", fail_render)
        result = runner.invoke(cli.app, ["book", "build", "--book", book_dir.name, "--format", "pdf"])

        assert result.exit_code == 1
        assert "Build failed:" in result.output
        assert "pdflatex not found" in result.output


def test_book_stats_json_output_contains_totals():
    """Verify stats command emits JSON totals payload."""
    with runner.isolated_filesystem():
        book_dir = _seed_book_tree()
        result = runner.invoke(cli.app, ["book", "stats", "--book", book_dir.name, "--output", "json"])

        assert result.exit_code == 0, result.output
        payload = json.loads(result.output)
        assert payload["totals"]["chapters"] == 1
        assert payload["totals"]["words"] > 0


def test_book_stats_table_includes_est_audio_minutes():
    """Verify table output renders the per-chapter estimated audio duration column."""
    with runner.isolated_filesystem():
        book_dir = _seed_book_tree()
        result = runner.invoke(cli.app, ["book", "stats", "--book", book_dir.name, "--output", "table"])

        assert result.exit_code == 0, result.output
        assert "Est Audio Min" in result.output


def test_book_audio_command_uses_generator(monkeypatch):
    """Verify audio command delegates to audio generator with defaults."""
    with runner.isolated_filesystem():
        book_dir = _seed_book_tree()
        called = {}

        def fake_generate_audiobook(**kwargs):
            called["audio_dir"] = kwargs["audio_dir"]
            return {"generated": 1, "skipped": 0, "chapter_files": [], "merged_file": None}

        monkeypatch.setattr(book_commands, "generate_audiobook", fake_generate_audiobook)

        result = runner.invoke(cli.app, ["book", "audio", "--book", book_dir.name, "--yes"])

        assert result.exit_code == 0, result.output
        assert called["audio_dir"] == (book_dir / "dist" / "audio").resolve()
        assert "Generated: 1" in result.output


def test_check_command_reports_pdflatex_status():
    """Verify environment check output includes pdflatex status."""
    result = runner.invoke(cli.app, ["check"])
    assert result.exit_code == 0
    assert "pdflatex (book pdf build):" in result.output


def test_generate_audiobook_skipped_existing_file_still_writes_metadata(monkeypatch):
    """Verify skipped existing chapter audio gets metadata backfilled."""
    with runner.isolated_filesystem():
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        chapter_dir = Path("books/001-test-book/chapters/01")
        chapter_dir.mkdir(parents=True, exist_ok=True)
        draft_path = chapter_dir / "draft.md"
        draft_path.write_text("# Chapter One\n\nAlready generated.\n", encoding="utf-8")

        audio_dir = Path("books/001-test-book/dist/audio")
        audio_dir.mkdir(parents=True, exist_ok=True)
        existing = audio_dir / "01-chapter-one.mp3"
        existing.write_bytes(b"ID3")

        drafts = [
            book_core.ChapterDraft(
                chapter_number=1,
                draft_path=draft_path,
                text=draft_path.read_text(encoding="utf-8"),
            )
        ]
        config = book_core.BookConfig(
            title="Test Book",
            author="Test Author",
            language="en-US",
            subtitle="",
            default_formats=["docx"],
            reference_docx="",
            epub_css="",
            audio_provider="openai",
            audio_model="gpt-4o-mini-tts",
            audio_voice="onyx",
            speaking_rate_wpm=170,
            reading_wpm=200,
            tts_cost_per_1m_chars=0.0,
        )

        metadata_calls: list[Path] = []

        class DummyOpenAI:
            def __init__(self, api_key: str):
                self.api_key = api_key

        monkeypatch.setattr(book_audio, "OpenAI", DummyOpenAI)
        monkeypatch.setattr(book_audio.typer, "confirm", lambda *args, **kwargs: False)
        monkeypatch.setattr(
            book_audio,
            "_write_mp3_metadata",
            lambda **kwargs: metadata_calls.append(kwargs["path"]),
        )

        result = book_audio.generate_audiobook(
            drafts=drafts,
            config=config,
            audio_dir=audio_dir,
            merge_output=False,
            force=False,
            yes=False,
            dotenv_search_roots=[],
        )

        assert result["generated"] == 0
        assert result["skipped"] == 1
        assert metadata_calls == [existing]


def test_audio_enhancer_adds_dialog_and_pause_markers():
    """Verify speech enhancer inserts dialog and pause markers."""
    markdown = """# Chapter One

> _An opening epigraph line_
> — Someone

"I know this is a trap," she said.
"""
    enhanced = book_audio._enhance_text_for_speech(markdown)

    assert book_audio.PAUSE_MARKER in enhanced
    assert book_audio.DIALOG_MARKER in enhanced


def test_audio_instruction_mentions_markers():
    """Verify marker-aware instruction text is generated."""
    chunk = f"{book_audio.PAUSE_MARKER} {book_audio.DIALOG_MARKER} Hello."
    instructions = book_audio._speech_instructions(chunk)
    assert "do not say the marker" in instructions
    assert book_audio.PAUSE_MARKER in instructions
    assert book_audio.DIALOG_MARKER in instructions


def test_docs_and_prompts_use_lowercase_world_paths():
    """Verify canonical lowercase world path casing in docs/prompts/templates."""
    repo_root = Path(__file__).resolve().parents[2]
    targets: list[Path] = []
    targets.extend((repo_root / ".authorkit" / "prompts").glob("*.md"))
    targets.extend((repo_root / ".authorkit" / "instructions").glob("*.md.tmpl"))
    targets.append(repo_root / ".authorkit" / "templates" / "world-entity-frontmatter.md")
    targets.append(repo_root / "README.md")

    disallowed = [
        r"\bWorld/",
        r"\bworld/Characters/",
        r"\bworld/Places/",
        r"\bworld/Organizations/",
        r"\bworld/History/",
        r"\bworld/Systems/",
        r"\bworld/Notes/",
    ]

    for path in targets:
        text = path.read_text(encoding="utf-8")
        for pattern in disallowed:
            assert re.search(pattern, text) is None, f"Found disallowed path casing '{pattern}' in {path}"


def test_world_index_scripts_assume_lowercase_world_layout():
    """Verify world index scripts are configured for lowercase world directories."""
    repo_root = Path(__file__).resolve().parents[2]
    ps_script = (repo_root / ".authorkit" / "scripts" / "powershell" / "build-world-index.ps1").read_text(encoding="utf-8")
    sh_script = (repo_root / ".authorkit" / "scripts" / "bash" / "build-world-index.sh").read_text(encoding="utf-8")

    assert "Join-Path $bookDir 'world'" in ps_script
    assert "WORLD_DIR=\"$BOOK_DIR/world\"" in sh_script

    for token in ["characters", "places", "organizations", "history", "systems", "notes"]:
        assert token in ps_script
        assert token in sh_script
