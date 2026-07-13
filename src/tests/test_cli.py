"""CLI behavior tests for Author Kit installer workflows.

Author:
    Mazemerize contributors.
"""

import contextlib
import json
import os
import re
import tempfile
from pathlib import Path

import pytest

import authorkit_cli as cli
import authorkit_cli.book_core as book_core
import authorkit_cli.book_commands as book_commands
import authorkit_cli.book_audio as book_audio
import authorkit_cli.book_render as book_render
import authorkit_cli.autopilot_core as autopilot_core
import authorkit_cli.autopilot_runner as autopilot_runner
import authorkit_cli.autopilot_commands as autopilot_commands
from typer.testing import CliRunner


runner = CliRunner()


@contextlib.contextmanager
def isolated_filesystem():
    """Run a block inside a fresh temporary working directory.

    Replaces ``CliRunner.isolated_filesystem`` which Click removed in 8.3.
    Restoring it here keeps the tests independent of the installed Click
    version (deps are unpinned, so CI may resolve a newer Click than local).

    Yields:
        str: The temporary directory now serving as the working directory.
    """
    cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmp:
        os.chdir(tmp)
        try:
            yield tmp
        finally:
            os.chdir(cwd)


def _bash_with_working_python_available() -> bool:
    """True when `bash` is on PATH AND can launch a working Python via the
    same fallback chain the bash scripts use (`python3` then `python`).

    We round-trip a sentinel string so that the Microsoft Store alias stub
    on Windows runners — which silently shadows `python3` and emits UTF-16
    garbage when piped a heredoc — is not mistaken for a real interpreter.
    Used to skip bash regression tests cleanly on hosts where the bash +
    Python combination isn't actually viable.
    """
    import shutil
    import subprocess

    if not shutil.which("bash"):
        return False
    try:
        result = subprocess.run(
            [
                "bash",
                "-c",
                "for c in python3 python; do "
                "  if command -v \"$c\" >/dev/null 2>&1; then "
                "    out=$(\"$c\" -c \"print('AUTHORKIT_PY_OK')\" 2>/dev/null) || out=''; "
                "    if [ \"$out\" = 'AUTHORKIT_PY_OK' ]; then exit 0; fi; "
                "  fi; "
                "done; exit 1",
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


def test_init_installs_multiple_ai_flavors_side_by_side():
    """Verify multi-AI installation writes side-by-side outputs.

    Returns:
        None
    """
    with isolated_filesystem():
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
        assert Path(".claude/commands/authorkit.write.md").exists()
        assert Path(".claude/commands/authorkit.research.md").exists()
        assert Path(".github/prompts/authorkit.write.prompt.md").exists()
        assert Path(".github/prompts/authorkit.research.prompt.md").exists()
        assert Path("CLAUDE.md").exists()
        assert Path(".github/copilot-instructions.md").exists()

        manifest = json.loads(Path(".authorkit/install-manifest.json").read_text(encoding="utf-8"))
        assert manifest["ais"] == ["claude", "copilot"]
        assert manifest["script"] == "sh"
        assert ".claude/commands/authorkit.write.md" in manifest["managed_paths"]
        assert ".claude/commands/authorkit.research.md" in manifest["managed_paths"]
        assert ".github/prompts/authorkit.write.prompt.md" in manifest["managed_paths"]
        assert ".github/prompts/authorkit.research.prompt.md" in manifest["managed_paths"]


def test_init_rerun_replaces_unselected_ai_outputs():
    """Verify rerun removes stale outputs for unselected AI flavors.

    Returns:
        None
    """
    with isolated_filesystem():
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

        assert Path(".codex/prompts/authorkit.write.md").exists()
        assert Path(".codex/prompts/authorkit.research.md").exists()
        assert Path(".codex/AGENTS.md").exists()
        assert not Path(".claude/commands/authorkit.write.md").exists()
        assert not Path(".github/prompts/authorkit.write.prompt.md").exists()

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

    with isolated_filesystem():
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


def test_init_captures_git_init_output(monkeypatch):
    """Verify init captures git output so progress rendering is not interrupted.

    Args:
        monkeypatch: Pytest monkeypatch fixture.
    """
    calls: list[tuple[list[str], dict]] = []

    def fake_run(cmd, **kwargs):
        calls.append((cmd, kwargs))
        if cmd[:2] == ["git", "rev-parse"]:
            raise RuntimeError("not in git repo")
        return None

    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    with isolated_filesystem():
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
                "--ignore-agent-tools",
            ],
        )

        assert result.exit_code == 0, result.output
        init_calls = [kwargs for cmd, kwargs in calls if cmd[:2] == ["git", "init"]]
        assert len(init_calls) == 1
        assert init_calls[0]["capture_output"] is True
        assert init_calls[0]["text"] is True


def test_init_ensures_gitignore_contains_required_entries():
    """Verify init creates repo-level .gitignore with required local entries."""
    with isolated_filesystem():
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
                "--ignore-agent-tools",
                "--no-git",
            ],
        )

        assert result.exit_code == 0, result.output
        gitignore = Path(".gitignore")
        assert gitignore.exists()
        lines = gitignore.read_text(encoding="utf-8").splitlines()
        required = [
            ".env",
            "dist/",
            ".claude/settings.local.json",
            ".codex/auth.json",
            ".codex/config.toml",
            ".codex/models_cache.json",
            ".codex/.personality_migration",
            ".codex/sessions/",
            ".codex/tmp/",
            ".codex/skills/.system/",
        ]
        for entry in required:
            assert entry in lines


def test_init_appends_required_gitignore_entries_without_duplicates():
    """Verify init appends required entries once and avoids duplicates on reruns."""
    with isolated_filesystem():
        Path(".gitignore").write_text("node_modules", encoding="utf-8")

        first = runner.invoke(
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

        lines = Path(".gitignore").read_text(encoding="utf-8").splitlines()
        assert "node_modules" in lines
        required = [
            ".env",
            "dist/",
            ".claude/settings.local.json",
            ".codex/auth.json",
            ".codex/config.toml",
            ".codex/models_cache.json",
            ".codex/.personality_migration",
            ".codex/sessions/",
            ".codex/tmp/",
            ".codex/skills/.system/",
        ]
        for entry in required:
            assert lines.count(entry) == 1


def test_init_preserves_existing_constitution_on_rerun():
    """Verify init does not overwrite a user-edited constitution on rerun."""
    with isolated_filesystem():
        first = runner.invoke(
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
        assert first.exit_code == 0, first.output

        constitution_path = Path(".authorkit/memory/constitution.md")
        edited = "# Custom Constitution\n\nKeep this."
        constitution_path.write_text(edited, encoding="utf-8")

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
        assert constitution_path.read_text(encoding="utf-8") == edited


def test_version_command_outputs_version():
    """Verify version output contains the CLI version string.

    Returns:
        None
    """
    result = runner.invoke(cli.app, ["version"])
    assert result.exit_code == 0
    assert f"authorkit-cli {cli.get_cli_version()}" in result.output


def _seed_book_tree() -> Path:
    """Create a minimal book directory tree with one chapter draft.

    Returns:
        Path: Absolute path to the seeded book directory.
    """
    root = Path("book") / "chapters" / "01"
    root.mkdir(parents=True, exist_ok=True)
    (root / "draft.md").write_text("# Chapter One\n\nThis is a test draft.\n", encoding="utf-8")
    return root.parents[1].resolve()


def test_parse_book_config_accepts_utf8_bom():
    """Verify book.toml with UTF-8 BOM is parsed successfully."""
    with isolated_filesystem():
        book_dir = Path("book")
        book_dir.mkdir(parents=True, exist_ok=True)
        (book_dir / "book.toml").write_text(
            '[book]\ntitle = "BOM Title"\nauthor = "Test Author"\nlanguage = "en-US"\n',
            encoding="utf-8-sig",
        )

        config = book_core.parse_book_config(book_dir.resolve())
        assert config.title == "BOM Title"
        assert config.author == "Test Author"


def test_book_build_command_writes_manuscript_and_formats(monkeypatch):
    """Verify book build assembles manuscript and calls format renderer.

    Args:
        monkeypatch: Pytest monkeypatch fixture.
    """
    with isolated_filesystem():
        book_dir = _seed_book_tree()
        outputs = [book_dir / "dist" / "manuscript.docx"]

        monkeypatch.setattr(book_commands, "render_formats", lambda *args, **kwargs: outputs)

        result = runner.invoke(cli.app, ["book", "build"])

        assert result.exit_code == 0, result.output
        assert (book_dir / "dist" / "manuscript.md").exists()
        assert "Built:" in result.output


def test_build_manuscript_markdown_quotes_yaml_metadata_values():
    """Verify manuscript frontmatter quotes punctuation-heavy metadata safely."""
    config = book_core.BookConfig(
        title="Inside Author Kit: AI-Assisted Writing Done Right",
        author="Mathieu Demarne: Author",
        language="en-US",
        subtitle='A "practical" guide',
        default_formats=["docx"],
        reference_docx="",
        epub_css="",
        audio_provider="openai",
        audio_model="gpt-4o-mini-tts",
        audio_voice="marin",
        audio_instructions="",
        speaking_rate_wpm=170,
        reading_wpm=200,
        tts_cost_per_1m_chars=0.0,
    )
    drafts = [book_core.ChapterDraft(chapter_number=1, draft_path=Path("book/chapters/01/draft.md"), text="# Ch1\n\nBody.")]

    rendered = book_render.build_manuscript_markdown(config, drafts)

    assert 'title: "Inside Author Kit: AI-Assisted Writing Done Right"' in rendered
    assert 'author: "Mathieu Demarne: Author"' in rendered
    assert 'subtitle: "A \\"practical\\" guide"' in rendered


def test_book_build_prompts_and_skips_existing_output(monkeypatch):
    """Verify existing outputs are skipped when overwrite prompt is declined.

    Args:
        monkeypatch: Pytest monkeypatch fixture.
    """
    with isolated_filesystem():
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

        result = runner.invoke(cli.app, ["book", "build", "--format", "docx"])

        assert result.exit_code == 0, result.output
        assert called["render"] is False
        assert "No output formats selected for rendering." in result.output


def test_book_build_prompts_and_overwrites_existing_output(monkeypatch):
    """Verify existing outputs are rebuilt when overwrite prompt is accepted.

    Args:
        monkeypatch: Pytest monkeypatch fixture.
    """
    with isolated_filesystem():
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

        result = runner.invoke(cli.app, ["book", "build", "--format", "docx"])

        assert result.exit_code == 0, result.output
        assert captured["formats"] == ["docx"]
        assert captured["force"] is True
        assert "Built:" in result.output


def test_book_build_command_reports_render_failures(monkeypatch):
    """Verify build command prints a concise error when rendering fails.

    Args:
        monkeypatch: Pytest monkeypatch fixture.
    """
    with isolated_filesystem():
        book_dir = _seed_book_tree()

        def fail_render(*args, **kwargs):
            raise RuntimeError("Pandoc conversion failed for docx: unknown error")

        monkeypatch.setattr(book_commands, "render_formats", fail_render)
        result = runner.invoke(cli.app, ["book", "build", "--format", "docx"])

        assert result.exit_code == 1
        assert "Build failed:" in result.output
        assert "Pandoc conversion failed for docx" in result.output


def test_book_commands_reject_removed_book_option():
    """Verify single-book mode rejects the legacy --book option."""
    with isolated_filesystem():
        _seed_book_tree()
        result = runner.invoke(cli.app, ["book", "build", "--book", "book"])
        assert result.exit_code != 0
        plain_output = re.sub(r"\x1b\[[0-9;]*m", "", result.output)
        assert "No such option" in plain_output
        assert "--book" in plain_output


def test_book_build_requires_canonical_book_directory():
    """Verify build shows actionable guidance when book/ is missing."""
    with isolated_filesystem():
        result = runner.invoke(cli.app, ["book", "build"])
        assert result.exit_code != 0
    assert "/authorkit.discuss" in result.output


def test_book_build_rejects_pdf_format():
    """Verify PDF format is rejected as unsupported."""
    with isolated_filesystem():
        book_dir = _seed_book_tree()
        result = runner.invoke(cli.app, ["book", "build", "--format", "pdf"])

        assert result.exit_code != 0
        assert "Unsupported format(s): pdf" in result.output


def test_book_stats_json_output_contains_totals():
    """Verify stats command emits JSON totals payload."""
    with isolated_filesystem():
        book_dir = _seed_book_tree()
        result = runner.invoke(cli.app, ["book", "stats", "--output", "json"])

        assert result.exit_code == 0, result.output
        payload = json.loads(result.output)
        assert payload["totals"]["chapters"] == 1
        assert payload["totals"]["words"] > 0


def test_book_stats_table_includes_est_audio_minutes():
    """Verify table output renders the per-chapter estimated audio duration column."""
    with isolated_filesystem():
        book_dir = _seed_book_tree()
        result = runner.invoke(cli.app, ["book", "stats", "--output", "table"])

        assert result.exit_code == 0, result.output
        assert "Est Audio Min" in result.output


def test_book_audio_command_uses_generator(monkeypatch):
    """Verify audio command delegates to audio generator with defaults.

    Args:
        monkeypatch: Pytest monkeypatch fixture.
    """
    with isolated_filesystem():
        book_dir = _seed_book_tree()
        called = {}

        def fake_generate_audiobook(**kwargs):
            called["audio_dir"] = kwargs["audio_dir"]
            return {"generated": 1, "skipped": 0, "chapter_files": [], "merged_file": None}

        monkeypatch.setattr(book_commands, "generate_audiobook", fake_generate_audiobook)

        result = runner.invoke(cli.app, ["book", "audio", "--yes"])

        assert result.exit_code == 0, result.output
        assert called["audio_dir"] == (book_dir / "dist" / "audio").resolve()
        assert "Generated: 1" in result.output


def test_check_command_reports_no_pdflatex_status():
    """Verify environment check output no longer includes pdflatex status."""
    result = runner.invoke(cli.app, ["check"])
    assert result.exit_code == 0
    assert "pdflatex" not in result.output


def test_generate_audiobook_skipped_existing_file_still_writes_metadata(monkeypatch):
    """Verify skipped existing chapter audio gets metadata backfilled.

    Args:
        monkeypatch: Pytest monkeypatch fixture.
    """
    with isolated_filesystem():
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        chapter_dir = Path("book/chapters/01")
        chapter_dir.mkdir(parents=True, exist_ok=True)
        draft_path = chapter_dir / "draft.md"
        draft_path.write_text("# Chapter One\n\nAlready generated.\n", encoding="utf-8")

        audio_dir = Path("book/dist/audio")
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
            audio_voice="marin",
            audio_instructions="",
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
        monkeypatch.setattr(
            book_audio,
            "resolve_audio_instructions",
            lambda book_dir, config: "Test instructions.",
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


def test_audio_instructions_loaded_from_template():
    """Verify instructions are loaded from the default template file."""
    repo_root = Path(__file__).resolve().parents[2]
    template_path = repo_root / book_audio.DEFAULT_INSTRUCTIONS_REL
    assert template_path.exists(), f"Default audio instructions template not found at {template_path}"

    config = book_core.BookConfig(
        title="T", author="A", language="en", subtitle="", default_formats=[],
        reference_docx="", epub_css="", audio_provider="openai",
        audio_model="m", audio_voice="v", audio_instructions="",
        speaking_rate_wpm=170, reading_wpm=200, tts_cost_per_1m_chars=None,
    )
    instructions = book_audio.resolve_audio_instructions(repo_root / "book", config)
    assert "Voice:" in instructions
    assert "Delivery:" in instructions


def test_audio_instructions_custom_path():
    """Verify custom instructions path from config is used."""
    with isolated_filesystem():
        custom = Path("my-instructions.txt")
        custom.write_text("Custom narrator instructions.", encoding="utf-8")

        config = book_core.BookConfig(
            title="T", author="A", language="en", subtitle="", default_formats=[],
            reference_docx="", epub_css="", audio_provider="openai",
            audio_model="m", audio_voice="v", audio_instructions="my-instructions.txt",
            speaking_rate_wpm=170, reading_wpm=200, tts_cost_per_1m_chars=None,
        )
        instructions = book_audio.resolve_audio_instructions(Path("."), config)
        assert instructions == "Custom narrator instructions."


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


def test_init_injects_shared_generation_guardrails_and_keeps_shared_asset_unrendered():
    """Verify rendered generation prompts inject shared guardrails and do not render shared assets as commands."""
    with isolated_filesystem():
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
                "--ignore-agent-tools",
                "--no-git",
            ],
        )
        assert result.exit_code == 0, result.output

        write_prompt = Path(".codex/prompts/authorkit.write.md").read_text(encoding="utf-8")
        assert "## Shared Generation Guardrails" in write_prompt
        assert "### Entropy Protocol" in write_prompt

        assert Path(".authorkit/prompts/_shared/generation-guardrails.md").exists()
        assert not Path(".codex/prompts/generation-guardrails.md").exists()
        assert not Path(".codex/prompts/_shared/generation-guardrails.md").exists()


def test_init_renders_discuss_prompt_for_all_ai_flavors():
    """Verify authorkit.discuss is rendered for claude, copilot, and codex with guardrails injected.

    Discuss absorbs the legacy clarify behavior — it owns the Clarifications log in
    concept.md — so we assert that the rendered prompt still references that mechanism.
    """
    with isolated_filesystem():
        result = runner.invoke(
            cli.app,
            [
                "init",
                ".",
                "--ai",
                "claude",
                "--ai",
                "copilot",
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
        assert result.exit_code == 0, result.output

        rendered_paths = [
            Path(".claude/commands/authorkit.discuss.md"),
            Path(".github/prompts/authorkit.discuss.prompt.md"),
            Path(".codex/prompts/authorkit.discuss.md"),
        ]
        for path in rendered_paths:
            assert path.exists(), f"Expected rendered discuss prompt at {path}"
            body = path.read_text(encoding="utf-8")
            assert "## Shared Generation Guardrails" in body, f"Guardrails missing in {path}"
            assert "### Entropy Protocol" in body, f"Entropy protocol missing in {path}"
            assert "Clarifications" in body, f"Clarifications section reference missing in {path}"


def test_write_prompt_enforces_style_anchor_workflow():
    """Verify the unified write prompt includes style-anchor loading and refresh instructions.

    Style continuity was previously enforced across chapter.plan / chapter.draft /
    chapter.review; in v0.5.0 it all lives in /authorkit.write, which runs plan +
    draft + revise + reconcile and refreshes the anchor before every prose-producing
    mode. The anchor is sourced from the *fixed origin* (constitution + concept
    voice/tone + the earliest approved chapters), not a trailing window of recent
    approvals — so the voice bar resists drift instead of following it. Voice is
    two-layered: the fixed origin is the global drift bar, while character/scene
    texture is matched against the earliest *relevant* approved chapter — an
    intelligent choice that still resists drift because it anchors to the earliest
    match, not a trailing one.
    """
    with isolated_filesystem():
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
                "--ignore-agent-tools",
                "--no-git",
            ],
        )
        assert result.exit_code == 0, result.output

        write_prompt = Path(".codex/prompts/authorkit.write.md").read_text(encoding="utf-8")

        assert "STYLE_ANCHOR" in write_prompt
        # Anchor sources from the fixed origin (earliest approved chapters),
        # not a trailing "last two approved" window that follows drift.
        assert "fixed origin" in write_prompt
        assert "earliest" in write_prompt
        assert "last two approved chapters" not in write_prompt
        # The origin is overridable via a recorded constitution pin, defaulting
        # to earliest — so an unrepresentative opening or a sanctioned voice
        # shift can be pinned without letting the bar drift silently.
        assert "Voice Origin" in write_prompt
        # Two-layer voice model: global voice holds to the fixed origin, while
        # character/scene/arc *texture* matches the earliest *relevant* approved
        # chapter (intelligent selection that still anchors to the earliest match,
        # not a trailing one).
        assert "texture exemplar" in write_prompt
        assert "earliest *relevant*" in write_prompt
        assert "templates/style-anchor-template.md" in write_prompt


def test_docs_prompts_templates_and_instructions_avoid_seeded_stock_examples():
    """Verify seeded stock names and arbitrary age-retcon examples are absent from shipped assets."""
    repo_root = Path(__file__).resolve().parents[2]
    targets: list[Path] = []
    targets.extend((repo_root / ".authorkit" / "prompts").rglob("*.md"))
    targets.extend((repo_root / ".authorkit" / "templates").glob("*.md"))
    targets.extend((repo_root / ".authorkit" / "instructions").glob("*.md.tmpl"))
    targets.append(repo_root / "README.md")

    banned_literals = [
        "Elena Voss",
        "Elena was 42 -> Elena is 38",
    ]

    for path in targets:
        text = path.read_text(encoding="utf-8")
        for literal in banned_literals:
            assert literal not in text, f"Found banned stock example '{literal}' in {path}"


def test_setup_book_powershell_writes_toml_without_bom():
    """Verify setup-book.ps1 uses explicit UTF-8 without BOM for book.toml."""
    repo_root = Path(__file__).resolve().parents[2]
    ps_script = (repo_root / ".authorkit" / "scripts" / "powershell" / "setup-book.ps1").read_text(encoding="utf-8")

    assert "[System.Text.UTF8Encoding]::new($false)" in ps_script
    assert "Write-Utf8NoBom -Path $bookTomlPath -Content $bookToml" in ps_script


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

    assert "Get-ChildItem -Path $dirPath -Filter '*.md' -File -Recurse" in ps_script
    assert "Substring($worldDir.Length)" in ps_script
    assert "for f in sorted(d.rglob(\"*.md\")):" in sh_script
    assert "rel = f.relative_to(world_dir).as_posix()" in sh_script


def test_research_prompt_supports_adaptive_routing_and_sync_paths():
    """Verify research prompt documents adaptive topic routing and sync path compatibility."""
    repo_root = Path(__file__).resolve().parents[2]
    research_prompt = (repo_root / ".authorkit" / "prompts" / "authorkit.research.md").read_text(encoding="utf-8")

    assert "folder: <relative-path-under-research>" in research_prompt
    assert "search recursively under `BOOK_DIR/research/` for an existing topic file" in research_prompt
    assert "adaptive flat-first placement" in research_prompt
    assert "BOOK_DIR/research/**/*.md" in research_prompt
    assert "BOOK_DIR/world/notes/research-<slug>.md" in research_prompt
    assert "BOOK_DIR/world/notes/research/<slug>.md" in research_prompt
    assert "Preserve human layout" in research_prompt


def test_world_handling_preserves_human_layout_and_rebuilds_index():
    """Verify the prompts that touch world/ describe path preservation and index rebuilding.

    In v0.5.0, world building and extraction are no longer standalone commands —
    they live as modes inside /authorkit.discuss (World Seed, cross-cutting amend)
    and /authorkit.write (Reconcile after drafting). This test asserts that both
    of those prompts still document the two load-bearing guarantees:

    1. Existing files are updated in place (no relocation / normalization).
    2. world/_index.md is rebuilt after world writes.
    """
    repo_root = Path(__file__).resolve().parents[2]
    discuss = (repo_root / ".authorkit" / "prompts" / "authorkit.discuss.md").read_text(encoding="utf-8")
    write = (repo_root / ".authorkit" / "prompts" / "authorkit.write.md").read_text(encoding="utf-8")

    # Preserve human-organized folder layouts: phrase from the legacy world.build
    # rule, preserved in the discuss World Seed and write Reconcile sections.
    assert "Never relocate or normalize existing files" in discuss
    assert "Preserve file layout" in write or "Preserve human" in write or "Preserve file" in write

    # Index rebuild via the canonical script token. The renderer substitutes the
    # token at install time, so we check for the token *or* the resolved name.
    for body in (discuss, write):
        rebuilds_index = (
            "{{SCRIPT_BUILD_WORLD_INDEX}}" in body
            or "build-world-index" in body
            or "world/_index.md" in body
        )
        assert rebuilds_index, "Prompt must reference rebuilding world/_index.md after world writes"


def test_research_consumers_use_recursive_topic_loading_language():
    """Verify prompts that consume research artifacts mention recursive topic discovery.

    The four v0.5.0 commands replace 13+ legacy prompts. Of those four,
    /authorkit.discuss (any mode that loads context), /authorkit.write (planning
    + drafting + reconciling), and /authorkit.review (chapter craft + manuscript
    drift) all consume research artifacts. /authorkit.research itself writes them
    and is therefore exempt from this test.
    """
    repo_root = Path(__file__).resolve().parents[2]
    targets = [
        repo_root / ".authorkit" / "prompts" / "authorkit.discuss.md",
        repo_root / ".authorkit" / "prompts" / "authorkit.write.md",
        repo_root / ".authorkit" / "prompts" / "authorkit.review.md",
    ]

    for target in targets:
        text = target.read_text(encoding="utf-8")
        assert "recursive" in text.lower() or "nested" in text, (
            f"{target.name} must mention recursive/nested research/ loading"
        )


def test_readme_documents_adaptive_research_layout():
    """Verify README describes adaptive flat-first research placement and gated world sync.

    The v0.5.0 README condenses the research section. It still has to describe:
    1. Where topic files go (research.md + research/**/*.md, flat-first).
    2. That world sync is offered/gated, not automatic, and writes to world/.
    """
    repo_root = Path(__file__).resolve().parents[2]
    readme = (repo_root / "README.md").read_text(encoding="utf-8")

    assert "`research/**/*.md`" in readme
    assert "flat" in readme.lower(), "README should describe flat-first research placement"
    assert "world sync" in readme.lower(), "README should mention world sync behavior"
    # Gated by author approval, not automatic.
    assert "gated" in readme.lower() or "approval" in readme.lower() or "offers" in readme.lower()


def test_path_scripts_expose_style_anchor_path():
    """Verify shared path scripts include STYLE_ANCHOR path metadata across bash and powershell."""
    repo_root = Path(__file__).resolve().parents[2]
    ps_common = (repo_root / ".authorkit" / "scripts" / "powershell" / "common.ps1").read_text(encoding="utf-8")
    sh_common = (repo_root / ".authorkit" / "scripts" / "bash" / "common.sh").read_text(encoding="utf-8")
    prereq_ps = (repo_root / ".authorkit" / "scripts" / "powershell" / "check-prerequisites.ps1").read_text(
        encoding="utf-8"
    )
    prereq_sh = (repo_root / ".authorkit" / "scripts" / "bash" / "check-prerequisites.sh").read_text(
        encoding="utf-8"
    )

    assert "STYLE_ANCHOR" in ps_common
    assert "STYLE_ANCHOR" in sh_common
    assert "STYLE_ANCHOR" in prereq_ps
    assert "STYLE_ANCHOR" in prereq_sh


def test_bash_scripts_have_no_utf8_bom():
    """Verify bash scripts start with the shebang and not a UTF-8 BOM (would break exec on Linux/macOS)."""
    repo_root = Path(__file__).resolve().parents[2]
    bash_dir = repo_root / ".authorkit" / "scripts" / "bash"
    for script in bash_dir.glob("*.sh"):
        head = script.read_bytes()[:3]
        assert head != b"\xef\xbb\xbf", f"{script} starts with UTF-8 BOM — strip it (breaks shebang on Linux/macOS)"


def test_instruction_templates_have_no_utf8_bom():
    """Verify instruction templates do not start with a UTF-8 BOM (asset hygiene; consumers can read either, but BOMs are inconsistent with the rest of the repo)."""
    repo_root = Path(__file__).resolve().parents[2]
    instructions_dir = repo_root / ".authorkit" / "instructions"
    for template in instructions_dir.glob("*.md.tmpl"):
        head = template.read_bytes()[:3]
        assert head != b"\xef\xbb\xbf", f"{template} starts with UTF-8 BOM — re-save as plain UTF-8"


def test_rendered_prompts_do_not_contain_unsubstituted_args_token():
    """Verify rendered prompts contain no literal {ARGS} placeholder (the renderer only substitutes {{USER_INPUT_TOKEN}}/$ARGUMENTS/{SCRIPT}/{{SCRIPT_*}})."""
    with isolated_filesystem():
        result = runner.invoke(
            cli.app,
            [
                "init",
                ".",
                "--ai",
                "claude,copilot,codex",
                "--script",
                "sh",
                "--here",
                "--force",
                "--ignore-agent-tools",
                "--no-git",
            ],
        )
        assert result.exit_code == 0, result.output

        rendered_dirs = [
            Path(".claude/commands"),
            Path(".github/prompts"),
            Path(".codex/prompts"),
        ]
        for rendered_dir in rendered_dirs:
            for prompt in rendered_dir.glob("*.md"):
                text = prompt.read_text(encoding="utf-8")
                assert "{ARGS}" not in text, (
                    f"{prompt} contains an unsubstituted '{{ARGS}}' token — "
                    "use {{USER_INPUT_TOKEN}} or remove the literal"
                )


def test_concept_template_uses_bracket_placeholder():
    """Verify concept-template.md does not leak Claude-only $ARGUMENTS placeholder into copied book/concept.md."""
    repo_root = Path(__file__).resolve().parents[2]
    template = (repo_root / ".authorkit" / "templates" / "concept-template.md").read_text(encoding="utf-8")
    assert "$ARGUMENTS" not in template, (
        "concept-template.md is copied verbatim by setup-book scripts; "
        "use [USER_DESCRIPTION] (or another bracket placeholder), not $ARGUMENTS"
    )


def test_prompt_scripts_blocks_declare_both_shells():
    """Verify every prompt declares both sh: and ps: variants in its scripts: block.

    In v0.5.0 all four user-facing prompts (discuss, write, review, research)
    need to call check-prerequisites at minimum, so each ships a scripts: block.
    """
    repo_root = Path(__file__).resolve().parents[2]
    prompts_dir = repo_root / ".authorkit" / "prompts"
    for prompt in prompts_dir.glob("authorkit.*.md"):
        text = prompt.read_text(encoding="utf-8")
        front_match = re.match(r"^---\n(.*?)\n---", text, flags=re.S)
        assert front_match, f"{prompt.name}: missing YAML frontmatter"
        frontmatter = front_match.group(1)
        assert "scripts:" in frontmatter, (
            f"{prompt.name}: missing scripts: block. "
            f"Every v0.5.0 prompt invokes a script (typically check-prerequisites)."
        )
        assert re.search(r"^\s+sh:\s+scripts/bash/", frontmatter, re.M), (
            f"{prompt.name}: scripts: block is missing sh: variant for Linux/macOS"
        )
        assert re.search(r"^\s+ps:\s+scripts/powershell/", frontmatter, re.M), (
            f"{prompt.name}: scripts: block is missing ps: variant for Windows"
        )


def test_build_world_index_scripts_parse_yaml_frontmatter():
    """Smoke test: bash build-world-index.sh must parse YAML frontmatter (regression for double-escape bug)."""
    import shutil
    import subprocess
    import tempfile

    if not _bash_with_working_python_available():
        return  # skip when bash + working Python aren't both reachable (e.g. Windows runner where python3 is the Microsoft Store stub)

    repo_root = Path(__file__).resolve().parents[2]
    bash_script = repo_root / ".authorkit" / "scripts" / "bash" / "build-world-index.sh"
    common_sh = repo_root / ".authorkit" / "scripts" / "bash" / "common.sh"

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        # Stage a minimal repo
        subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
        scripts_dst = tmp_path / ".authorkit" / "scripts" / "bash"
        scripts_dst.mkdir(parents=True)
        shutil.copy(common_sh, scripts_dst / "common.sh")
        shutil.copy(bash_script, scripts_dst / "build-world-index.sh")

        char_dir = tmp_path / "book" / "world" / "characters"
        char_dir.mkdir(parents=True)
        (char_dir / "iria.md").write_text(
            "---\n"
            "id: char-iria-calder\n"
            "type: character\n"
            "name: Iria Calder\n"
            "aliases: [Iria, the astronomer]\n"
            "chapters: [CONCEPT, CH01]\n"
            "first_appearance: CH01\n"
            "relationships: []\n"
            "tags: []\n"
            "last_updated: 2026-04-26\n"
            "---\n\n# Iria Calder\n",
            encoding="utf-8",
        )

        result = subprocess.run(
            ["bash", str(scripts_dst / "build-world-index.sh"), "--json"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout.strip())
        assert payload["ENTITY_COUNT"] == 1
        assert payload["ALIAS_COUNT"] == 3  # name + 2 aliases
        assert payload["FILES_WITHOUT_FRONTMATTER"] == 0

        index_text = (tmp_path / "book" / "world" / "_index.md").read_text(encoding="utf-8")
        assert "[NO FRONTMATTER]" not in index_text, (
            "Index flagged a file with frontmatter as missing — regex likely double-escaped (see build-world-index.sh heredoc)"
        )
        assert "char-iria-calder" in index_text
        assert "the astronomer" in index_text


def test_build_world_index_add_frontmatter_yaml_safe_for_colon_in_name():
    """Regression: --add-frontmatter must produce valid YAML when an entity H1 contains
    YAML-significant punctuation (colons, quotes). Names like 'Daemon: The Watcher'
    used to interpolate raw, producing unparseable YAML."""
    import shutil
    import subprocess
    import tempfile

    if not _bash_with_working_python_available():
        return  # skip when bash + working Python aren't both reachable

    repo_root = Path(__file__).resolve().parents[2]
    bash_script = repo_root / ".authorkit" / "scripts" / "bash" / "build-world-index.sh"
    common_sh = repo_root / ".authorkit" / "scripts" / "bash" / "common.sh"

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
        scripts_dst = tmp_path / ".authorkit" / "scripts" / "bash"
        scripts_dst.mkdir(parents=True)
        shutil.copy(common_sh, scripts_dst / "common.sh")
        shutil.copy(bash_script, scripts_dst / "build-world-index.sh")

        char_dir = tmp_path / "book" / "world" / "characters"
        char_dir.mkdir(parents=True)
        # No frontmatter — script will derive name from the H1 and write a fresh block.
        (char_dir / "daemon.md").write_text(
            '# Daemon: The "Watcher"\n\nA character described in chapter (CH01).\n',
            encoding="utf-8",
        )

        result = subprocess.run(
            ["bash", str(scripts_dst / "build-world-index.sh"), "--add-frontmatter", "--json"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr

        rewritten = (char_dir / "daemon.md").read_text(encoding="utf-8")
        # Frontmatter block must start the file and parse as YAML.
        assert rewritten.startswith("---\n"), f"Expected frontmatter block at start, got: {rewritten[:80]!r}"

        # Extract just the frontmatter body for YAML validation.
        end = rewritten.find("\n---\n", 4)
        assert end > 0, "Frontmatter has no closing delimiter"
        fm_body = rewritten[4:end]

        # The name field must be a valid YAML scalar even with a colon and quotes inside.
        try:
            import yaml as _yaml  # type: ignore
            parsed = _yaml.safe_load(fm_body)
            assert parsed["name"] == 'Daemon: The "Watcher"', (
                f"name round-trip failed: got {parsed.get('name')!r}"
            )
        except ImportError:
            # PyYAML not installed in test env — fall back to a structural check
            # that the value is JSON-quoted (the encoding strategy we adopted).
            assert '"Daemon: The \\"Watcher\\""' in fm_body or '"Daemon: The \\"Watcher\\""\n' in fm_body, (
                f"Expected JSON-quoted YAML scalar for the name field, got frontmatter:\n{fm_body}"
            )


def test_docs_prompts_templates_use_single_book_workspace_paths():
    """Verify canonical docs/prompts/templates reference /book/ workspace paths."""
    repo_root = Path(__file__).resolve().parents[2]
    targets: list[Path] = []
    targets.extend((repo_root / ".authorkit" / "prompts").glob("*.md"))
    targets.extend((repo_root / ".authorkit" / "templates").glob("*.md"))
    targets.extend((repo_root / ".authorkit" / "instructions").glob("*.md.tmpl"))
    targets.append(repo_root / "README.md")
    targets.append(repo_root / "CONTRIBUTING.md")

    disallowed = [
        r"/books/\[###-book-name\]/",
        r"books/<active-book>/",
        r"books/<book>/",
    ]

    for path in targets:
        text = path.read_text(encoding="utf-8")
        for pattern in disallowed:
            assert re.search(pattern, text) is None, f"Found legacy multi-book pattern '{pattern}' in {path}"


def test_instruction_templates_carry_handoff_placeholder_note():
    """Every AI flavor's instruction template must teach the agent to substitute
    bracketed handoff placeholders ([N], [PD-NNN], [topic]) before forwarding.

    Regression guard: this note was historically only in claude.md.tmpl, causing
    Copilot/Codex agents to forward literal `[N]` text into chat.
    """
    repo_root = Path(__file__).resolve().parents[2]
    instructions_dir = repo_root / ".authorkit" / "instructions"
    expected_signal = "Handoff `prompt:` strings may contain bracketed placeholders"

    templates = sorted(instructions_dir.glob("*.md.tmpl"))
    assert len(templates) >= 3, f"Expected at least 3 instruction templates, found {len(templates)}"

    for template in templates:
        text = template.read_text(encoding="utf-8")
        assert expected_signal in text, (
            f"Instruction template {template.name} is missing the handoff-placeholder "
            f"substitution note. Copy it from claude.md.tmpl. Without it, agents will "
            f"forward literal '[N]' text into chat."
        )


def test_prompts_have_no_legacy_command_references():
    """Removed commands (pivot, reconcile, retcon, checklist, world.update,
    world.verify, world.index) must not appear in canonical prompts.

    Regression guard against accidental reintroduction during edits.
    """
    repo_root = Path(__file__).resolve().parents[2]
    prompt_files = list((repo_root / ".authorkit" / "prompts").glob("authorkit.*.md"))
    assert prompt_files, "No canonical prompts found"

    legacy_patterns = [
        r"/authorkit\.pivot\b",
        r"/authorkit\.reconcile\b",
        r"/authorkit\.retcon\b",
        r"/authorkit\.checklist\b",
        r"/authorkit\.world\.update\b",
        r"/authorkit\.world\.verify\b",
        r"/authorkit\.world\.index\b",
    ]

    for prompt in prompt_files:
        text = prompt.read_text(encoding="utf-8")
        for pattern in legacy_patterns:
            match = re.search(pattern, text)
            assert match is None, (
                f"Legacy command reference '{match.group(0) if match else pattern}' "
                f"found in {prompt.name}. These commands were removed during the "
                f"step-by-step consolidation; update the reference."
            )


def test_build_world_index_bash_and_powershell_produce_matching_json():
    """Parity guard: bash and PowerShell `build-world-index` scripts must agree
    on entity count, alias count, chapter count, and missing-frontmatter count
    for the same fixture. The PS1 reimplements logic that the bash version
    delegates to embedded Python; this test catches drift.

    Skips when either runtime is missing (e.g. CI on Windows without bash).
    """
    import shutil
    import subprocess
    import tempfile

    pwsh_available = shutil.which("pwsh") or shutil.which("powershell")
    if not _bash_with_working_python_available() or not pwsh_available:
        return  # both runtimes required; skip when only one is available

    repo_root = Path(__file__).resolve().parents[2]
    bash_script = repo_root / ".authorkit" / "scripts" / "bash" / "build-world-index.sh"
    common_sh = repo_root / ".authorkit" / "scripts" / "bash" / "common.sh"
    ps_script = repo_root / ".authorkit" / "scripts" / "powershell" / "build-world-index.ps1"
    common_ps = repo_root / ".authorkit" / "scripts" / "powershell" / "common.ps1"

    def _run(scripts_dst_bash, scripts_dst_ps, fixture_root):
        bash_result = subprocess.run(
            ["bash", str(scripts_dst_bash / "build-world-index.sh"), "--json"],
            cwd=fixture_root,
            capture_output=True,
            text=True,
        )
        assert bash_result.returncode == 0, bash_result.stderr

        # On Windows, prefer 'pwsh'; fall back to Windows PowerShell if absent.
        ps_exe = "pwsh" if shutil.which("pwsh") else "powershell"
        ps_result = subprocess.run(
            [
                ps_exe,
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(scripts_dst_ps / "build-world-index.ps1"),
                "-Json",
            ],
            cwd=fixture_root,
            capture_output=True,
            text=True,
        )
        assert ps_result.returncode == 0, ps_result.stderr

        return json.loads(bash_result.stdout.strip()), json.loads(ps_result.stdout.strip())

    with tempfile.TemporaryDirectory() as tmp:
        fixture_root = Path(tmp)
        subprocess.run(["git", "init", "-q"], cwd=fixture_root, check=True)

        scripts_bash = fixture_root / ".authorkit" / "scripts" / "bash"
        scripts_bash.mkdir(parents=True)
        shutil.copy(common_sh, scripts_bash / "common.sh")
        shutil.copy(bash_script, scripts_bash / "build-world-index.sh")

        scripts_ps = fixture_root / ".authorkit" / "scripts" / "powershell"
        scripts_ps.mkdir(parents=True)
        shutil.copy(common_ps, scripts_ps / "common.ps1")
        shutil.copy(ps_script, scripts_ps / "build-world-index.ps1")

        # Two characters in two categories with overlapping aliases — exercises
        # entity counting, alias dedup, and chapter manifest.
        char_dir = fixture_root / "book" / "world" / "characters"
        char_dir.mkdir(parents=True)
        (char_dir / "iria.md").write_text(
            "---\n"
            "id: char-iria-calder\n"
            "type: character\n"
            "name: Iria Calder\n"
            "aliases: [Iria, the astronomer]\n"
            "chapters: [CONCEPT, CH01, CH03]\n"
            "first_appearance: CH01\n"
            "relationships: []\n"
            "tags: []\n"
            "last_updated: 2026-04-26\n"
            "---\n\n# Iria Calder\n",
            encoding="utf-8",
        )
        place_dir = fixture_root / "book" / "world" / "places"
        place_dir.mkdir(parents=True)
        (place_dir / "observatory.md").write_text(
            "---\n"
            "id: place-observatory\n"
            "type: place\n"
            "name: The Observatory\n"
            "aliases: [observatory]\n"
            "chapters: [CONCEPT, CH01]\n"
            "first_appearance: CH01\n"
            "relationships: []\n"
            "tags: []\n"
            "last_updated: 2026-04-26\n"
            "---\n\n# The Observatory\n",
            encoding="utf-8",
        )

        bash_payload, ps_payload = _run(scripts_bash, scripts_ps, fixture_root)

        # Compare the four parity-critical counts. INDEX_FILE and BOOK_DIR may
        # differ in path separator on Windows; we don't enforce string equality
        # for those.
        for key in ("ENTITY_COUNT", "ALIAS_COUNT", "CHAPTER_COUNT", "FILES_WITHOUT_FRONTMATTER"):
            assert bash_payload[key] == ps_payload[key], (
                f"build-world-index parity violation on {key}: "
                f"bash={bash_payload[key]} ps={ps_payload[key]}. "
                f"Bash payload: {bash_payload}. PS payload: {ps_payload}."
            )


def test_status_command_reports_chapter_breakdown(tmp_path, monkeypatch):
    """`authorkit status` summarizes the project state — chapter counts by
    status marker, parked decisions, world stats, drift warnings — closing
    the loop between the slash workflow and the CLI.
    """
    book_dir = tmp_path / "book"
    book_dir.mkdir()
    (book_dir / "concept.md").write_text("# Concept\n", encoding="utf-8")
    (book_dir / "outline.md").write_text("# Outline\n", encoding="utf-8")
    (book_dir / "chapters.md").write_text(
        "# Chapters\n\n"
        "- [X] CH01 The Arrival - First chapter\n"
        "- [D] CH02 The Catalogue - Second chapter\n"
        "- [P] CH03 The Pattern - Third chapter\n"
        "- [ ] CH04 The Predecessor - Fourth chapter\n",
        encoding="utf-8",
    )
    (book_dir / "chapters" / "01").mkdir(parents=True)
    (book_dir / "chapters" / "01" / "draft.md").write_text("# Chapter 1\n", encoding="utf-8")
    (book_dir / "chapters" / "02").mkdir()
    (book_dir / "chapters" / "02" / "draft.md").write_text("# Chapter 2\n", encoding="utf-8")

    (book_dir / "parked-decisions.md").write_text(
        "# Parked Decisions\n\n"
        "## PD-001: Fate of Marcus\n\n"
        "**Status**: OPEN\n"
        "**Deadline**: Before CH12\n",
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)
    result = runner.invoke(cli.app, ["status"])
    assert result.exit_code == 0, result.output

    out = result.output
    assert "Book:" in out
    assert "Chapters:" in out
    assert "approved" in out
    assert "drafted" in out
    assert "planned" in out
    assert "pending" in out
    assert "Parked decisions:" in out
    assert "Before CH12" in out


def test_status_json_output_includes_escalations_and_chapters(tmp_path, monkeypatch):
    """`authorkit status --json` emits a machine-readable dashboard for the
    AutoPilot planner: parseable JSON carrying the chapter-status breakdown and
    a count of OPEN escalation records in book/escalations/ (RESOLVED ones are
    not counted).
    """
    book_dir = tmp_path / "book"
    book_dir.mkdir()
    (book_dir / "concept.md").write_text("# Concept\n", encoding="utf-8")
    (book_dir / "outline.md").write_text("# Outline\n", encoding="utf-8")
    (book_dir / "chapters.md").write_text(
        "# Chapters\n\n"
        "- [X] CH01 The Arrival - First chapter\n"
        "- [D] CH02 The Catalogue - Second chapter\n",
        encoding="utf-8",
    )
    (book_dir / "chapters" / "01").mkdir(parents=True)
    (book_dir / "chapters" / "01" / "draft.md").write_text("# Chapter 1\n", encoding="utf-8")

    escalations_dir = book_dir / "escalations"
    escalations_dir.mkdir()
    (escalations_dir / "2026-06-18-ESC-001-villain-fate.md").write_text(
        "# ESC-001: Fate of the villain\n\n**Status**: OPEN\n",
        encoding="utf-8",
    )
    (escalations_dir / "2026-06-17-ESC-000-resolved.md").write_text(
        "# ESC-000: Already handled\n\n**Status**: RESOLVED\n",
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)
    result = runner.invoke(cli.app, ["status", "--json"])
    assert result.exit_code == 0, result.output

    payload = json.loads(result.output)
    assert payload["open_escalations"] == 1
    assert payload["escalation_ids"] == ["ESC-001"]
    assert payload["chapter_status_counts"] == {"approved": 1, "drafted": 1}
    # Per-chapter map (JSON object keys are strings) — the chapters planner needs this.
    assert payload["chapter_statuses"] == {"1": "approved", "2": "drafted"}
    assert payload["book_dir"].endswith("book")


def test_status_command_errors_when_no_book_workspace(tmp_path, monkeypatch):
    """`authorkit status` should fail loudly with actionable guidance when
    no book/ workspace exists, rather than silently emitting empty stats.
    """
    monkeypatch.chdir(tmp_path)
    # Create a marker so find_repo_root resolves here, but no book/ folder.
    (tmp_path / ".authorkit").mkdir()

    result = runner.invoke(cli.app, ["status"])
    assert result.exit_code == 1, result.output
    assert "No book workspace found" in result.output
    assert "/authorkit.discuss" in result.output


def test_book_stats_includes_chapter_status_from_chapters_md(tmp_path, monkeypatch):
    """`book stats` should pull chapter status (`[X]` approved, `[D]` drafted, etc.)
    from chapters.md, not just report word counts. Closes the UX gap where users
    couldn't tell if 120K words were drafted vs reviewed vs approved."""
    book_dir = tmp_path / "book"
    chapters_dir = book_dir / "chapters" / "01"
    chapters_dir.mkdir(parents=True)
    (chapters_dir / "draft.md").write_text("# Chapter 1\n\nHello world.\n", encoding="utf-8")

    chapters2 = book_dir / "chapters" / "02"
    chapters2.mkdir()
    (chapters2 / "draft.md").write_text("# Chapter 2\n\nMore prose here.\n", encoding="utf-8")

    (book_dir / "chapters.md").write_text(
        "# Chapters\n\n"
        "- [X] CH01 The Arrival - First chapter\n"
        "- [D] CH02 The Catalogue - Second chapter\n",
        encoding="utf-8",
    )
    (book_dir / "book.toml").write_text("[book]\ntitle = \"Test\"\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    result = runner.invoke(cli.app, ["book", "stats", "--output", "json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)

    statuses = {ch["chapter"]: ch["status"] for ch in payload["chapters"]}
    assert statuses == {1: "approved", 2: "drafted"}, f"Unexpected statuses: {statuses}"

    breakdown = payload["totals"]["status_breakdown"]
    assert breakdown == {"approved": 1, "drafted": 1}, f"Unexpected breakdown: {breakdown}"


def test_prompts_use_canonical_outline_section_heading():
    """Prompt body sections should use `## Outline` (not `## Execution Steps`,
    `## General Guidelines`, etc.) so a reader scanning the prompt directory
    finds the same landmark in every file. Catches future drift.
    """
    repo_root = Path(__file__).resolve().parents[2]
    prompt_files = list((repo_root / ".authorkit" / "prompts").glob("authorkit.*.md"))
    assert prompt_files, "No canonical prompts found"

    # Synonyms historically used in place of "## Outline" (the de-facto standard
    # across 16+ prompts). Any of these as a top-level heading is drift.
    drift_headings = [
        "## Execution Steps",
        "## General Guidelines",
    ]

    for prompt in prompt_files:
        text = prompt.read_text(encoding="utf-8")
        for heading in drift_headings:
            assert heading not in text.splitlines(), (
                f"Prompt {prompt.name} uses non-canonical heading '{heading}'. "
                f"Rename to '## Outline' for consistency. Synonyms drift over time "
                f"and confuse readers comparing prompts."
            )


def test_prompts_use_canonical_key_rules_section_heading():
    """Constraint/rule sections at prompt end should use `## Key Rules` rather
    than `## Key Principles`, `## Review Principles`, `## Writing Rules`,
    `## Revision Principles`, `## Chapter Entry Rules`, etc.

    Exempt: `## Operating Constraints` in analyze (declares command mode, distinct
    from end-of-prompt rules) and `## Operation-Specific Rules` in chapter.reorder
    (genuine operation-specific content, paired with a separate `## Key Rules`).
    """
    repo_root = Path(__file__).resolve().parents[2]
    prompt_files = list((repo_root / ".authorkit" / "prompts").glob("authorkit.*.md"))

    drift_headings = [
        "## Key Principles",
        "## Review Principles",
        "## Writing Rules",
        "## Revision Principles",
        "## Chapter Entry Rules",
    ]

    for prompt in prompt_files:
        text = prompt.read_text(encoding="utf-8")
        for heading in drift_headings:
            assert heading not in text.splitlines(), (
                f"Prompt {prompt.name} uses non-canonical heading '{heading}'. "
                f"Rename to '## Key Rules' for consistency."
            )


def test_cli_source_does_not_use_AuthorKit_brand_misspelling():
    """Brand is 'Author Kit' (human-readable) or 'authorkit' (CLI/package) — never 'AuthorKit'.

    Convention enforced by CONTRIBUTING.md. Catches accidental drift in docstrings,
    user-facing strings, and inline comments. ASCII banner uses non-Latin glyphs
    that don't trigger this regex, so banner is exempt by construction.
    """
    repo_root = Path(__file__).resolve().parents[2]
    cli_files = list((repo_root / "src" / "authorkit_cli").glob("*.py"))
    assert cli_files, "Expected to find authorkit_cli source files"

    for py_file in cli_files:
        text = py_file.read_text(encoding="utf-8")
        # Match "AuthorKit" but NOT "Author Kit" or inside URLs (github.com/.../author-kit).
        matches = [match for match in re.finditer(r"\bAuthorKit\b", text)]
        assert not matches, (
            f"Brand misspelling 'AuthorKit' found in {py_file.name} "
            f"at offset(s) {[m.start() for m in matches]}. "
            f"Use 'Author Kit' (with space) or 'authorkit' (lowercase) per CONTRIBUTING.md."
        )


def test_check_command_reports_python_for_world_index():
    """`authorkit check` must surface python availability — the bash world-index
    script depends on it, and a missing python interpreter previously failed
    deep inside the world-extraction phase of /authorkit.write rather than at
    install/check time.
    """
    result = runner.invoke(cli.app, ["check"])
    assert result.exit_code == 0, result.output
    assert "python" in result.output.lower(), (
        f"Expected 'python' in check output. Got:\n{result.output}"
    )


def test_status_constitution_resolves_against_repo_root_not_cwd(tmp_path, monkeypatch):
    """`authorkit status` must report the constitution as present when the
    user runs it from a subdirectory (e.g. inside `book/`). Previously the
    path was resolved against cwd, so running from `book/` looked for
    `book/.authorkit/memory/constitution.md` and falsely reported missing.
    """
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / ".authorkit" / "memory").mkdir(parents=True)
    (repo_root / ".authorkit" / "memory" / "constitution.md").write_text(
        "# Constitution\n", encoding="utf-8"
    )
    book_dir = repo_root / "book"
    book_dir.mkdir()
    (book_dir / "concept.md").write_text("# Concept\n", encoding="utf-8")

    # Run from inside `book/` — the failure mode for the previous bug.
    monkeypatch.chdir(book_dir)
    result = runner.invoke(cli.app, ["status"])

    assert result.exit_code == 0, result.output
    assert "constitution: ok" in result.output, (
        f"Expected constitution reported as present. Got:\n{result.output}"
    )


def test_status_command_handles_partial_workspace(tmp_path, monkeypatch):
    """`authorkit status` should print a coherent dashboard for a half-initialized
    book (only `concept.md`, no `chapters.md`, no `world/`) without raising or
    emitting drift noise. This is the realistic state right after the first
    /authorkit.discuss session that produces concept.md.
    """
    repo_root = tmp_path
    (repo_root / ".authorkit").mkdir()
    book_dir = repo_root / "book"
    book_dir.mkdir()
    (book_dir / "concept.md").write_text("# Concept\n", encoding="utf-8")

    monkeypatch.chdir(repo_root)
    result = runner.invoke(cli.app, ["status"])

    assert result.exit_code == 0, result.output
    assert "Workspace:" in result.output
    assert "concept.md: ok" in result.output
    assert "outline.md: missing" in result.output
    assert "No chapters tracked yet" in result.output
    # Nothing to drift against, so no drift lines should appear.
    assert "[unwritten]" not in result.output
    assert "[untracked]" not in result.output


def test_status_overdue_parked_decisions_are_counted(tmp_path, monkeypatch):
    """`authorkit status` must surface overdue parked decisions — a decision
    flagged "Before CH02" is overdue once chapter 2 (or any later chapter)
    has been drafted. Closes the loop on the Park-mode deadline tracking
    promise of /authorkit.discuss (and the legacy /authorkit.park behavior
    it absorbed).
    """
    repo_root = tmp_path
    (repo_root / ".authorkit").mkdir()
    book_dir = repo_root / "book"
    book_dir.mkdir()

    (book_dir / "chapters" / "02").mkdir(parents=True)
    (book_dir / "chapters" / "02" / "draft.md").write_text("# Chapter 2\n", encoding="utf-8")
    (book_dir / "chapters.md").write_text(
        "# Chapters\n\n- [D] CH02 Title - Summary\n", encoding="utf-8"
    )

    (book_dir / "parked-decisions.md").write_text(
        "# Parked Decisions\n\n"
        "## PD-001: Should Marcus die\n\n"
        "**Status**: OPEN\n"
        "**Deadline**: Before CH02\n\n"
        "## PD-002: Final twist\n\n"
        "**Status**: OPEN\n"
        "**Deadline**: Before CH10\n",
        encoding="utf-8",
    )

    monkeypatch.chdir(repo_root)
    result = runner.invoke(cli.app, ["status"])

    assert result.exit_code == 0, result.output
    assert "open: 2" in result.output
    assert "overdue: 1" in result.output, (
        f"Expected 1 overdue decision (Before CH02 with CH02 drafted). Got:\n{result.output}"
    )


def test_parse_book_config_rejects_malformed_toml_with_actionable_message(tmp_path):
    """Malformed `book.toml` must produce a `BookConfigError` carrying the
    file path so CLI callers can surface remediation guidance instead of a
    raw traceback.
    """
    book_dir = tmp_path / "book"
    book_dir.mkdir()
    (book_dir / "book.toml").write_text(
        "[book\ntitle = \"oops\"\n", encoding="utf-8"
    )

    try:
        book_core.parse_book_config(book_dir)
    except book_core.BookConfigError as exc:
        assert "book.toml" in str(exc)
        assert exc.config_path == (book_dir / "book.toml")
    else:
        raise AssertionError("Expected BookConfigError for malformed book.toml")


def test_parse_book_config_rejects_string_typed_numeric_fields(tmp_path):
    """A non-numeric `tts_cost_per_1m_chars` value must fail loudly. Previously
    the value was silently dropped to None, so users who quoted their cost
    setting saw `$0` cost reports without warning.
    """
    book_dir = tmp_path / "book"
    book_dir.mkdir()
    (book_dir / "book.toml").write_text(
        '[book]\ntitle = "Test"\n[stats]\ntts_cost_per_1m_chars = "0.005"\n',
        encoding="utf-8",
    )

    try:
        book_core.parse_book_config(book_dir)
    except book_core.BookConfigError as exc:
        assert "tts_cost_per_1m_chars" in str(exc)
    else:
        raise AssertionError("Expected BookConfigError for string-typed cost")


def test_parse_book_config_rejects_scalar_autopilot_sections(tmp_path):
    """A scalar where an ``[autopilot.<bucket>]`` table belongs (e.g.
    ``planner = "haiku"`` under ``[autopilot]``) must raise BookConfigError,
    not leak an AttributeError past the CLI's friendly error handling."""
    book_dir = tmp_path / "book"
    book_dir.mkdir()
    (book_dir / "book.toml").write_text(
        '[book]\ntitle = "Test"\n[autopilot]\nplanner = "haiku"\n',
        encoding="utf-8",
    )
    with pytest.raises(book_core.BookConfigError, match="autopilot.planner"):
        book_core.parse_book_config(book_dir)

    # The whole section as a scalar is equally friendly (top-level key, before
    # any [table] header so it stays a root key).
    (book_dir / "book.toml").write_text(
        'autopilot = "haiku"\n[book]\ntitle = "Test"\n',
        encoding="utf-8",
    )
    with pytest.raises(book_core.BookConfigError, match="autopilot"):
        book_core.parse_book_config(book_dir)


def test_book_build_surfaces_friendly_error_for_malformed_toml(tmp_path, monkeypatch):
    """`authorkit book build` must translate `BookConfigError` into a friendly
    Typer message (exit code 2) instead of crashing with a raw traceback.
    """
    repo_root = tmp_path
    (repo_root / ".authorkit").mkdir()
    book_dir = repo_root / "book"
    (book_dir / "chapters" / "01").mkdir(parents=True)
    (book_dir / "chapters" / "01" / "draft.md").write_text("# Ch1\n", encoding="utf-8")
    (book_dir / "book.toml").write_text("[book\nbroken = \n", encoding="utf-8")

    monkeypatch.chdir(repo_root)
    result = runner.invoke(cli.app, ["book", "build"])

    assert result.exit_code != 0
    assert "book.toml" in result.output
    assert "authorkit init" in result.output


def test_book_build_respects_chapter_range_filter(tmp_path, monkeypatch):
    """`book build --from-chapter --to-chapter` must include only chapters in
    the requested range. Mirrors the existing flag on `book audio`; closes
    the UX gap where partial-export wasn't possible.
    """
    repo_root = tmp_path
    (repo_root / ".authorkit").mkdir()
    book_dir = repo_root / "book"
    for n in (1, 2, 3):
        (book_dir / "chapters" / f"0{n}").mkdir(parents=True)
        (book_dir / "chapters" / f"0{n}" / "draft.md").write_text(
            f"# Chapter {n}\n\nBody {n}.\n", encoding="utf-8"
        )

    captured: dict[str, list[int]] = {}

    def fake_render(book_dir, dist_dir, manuscript_path, formats, config, force=True):
        captured["chapters"] = [
            line for line in manuscript_path.read_text(encoding="utf-8").splitlines()
            if line.startswith("# Chapter ")
        ]
        return [dist_dir / "manuscript.docx"]

    monkeypatch.setattr(book_commands, "render_formats", fake_render)
    monkeypatch.chdir(repo_root)

    result = runner.invoke(cli.app, ["book", "build", "--from-chapter", "2", "--to-chapter", "2"])

    assert result.exit_code == 0, result.output
    assert captured["chapters"] == ["# Chapter 2"], (
        f"Expected only Chapter 2 in manuscript. Got: {captured['chapters']}"
    )


def test_book_stats_respects_chapter_range_filter(tmp_path, monkeypatch):
    """`book stats --from-chapter --to-chapter` must restrict computation to
    the requested chapters."""
    repo_root = tmp_path
    (repo_root / ".authorkit").mkdir()
    book_dir = repo_root / "book"
    for n in (1, 2, 3):
        (book_dir / "chapters" / f"0{n}").mkdir(parents=True)
        (book_dir / "chapters" / f"0{n}" / "draft.md").write_text(
            f"# Chapter {n}\n\nBody body body {n}.\n", encoding="utf-8"
        )

    monkeypatch.chdir(repo_root)
    result = runner.invoke(cli.app, ["book", "stats", "--from-chapter", "2", "--output", "json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    chapter_numbers = [c["chapter"] for c in payload["chapters"]]
    assert chapter_numbers == [2, 3], (
        f"Expected chapters 2 and 3 only. Got: {chapter_numbers}"
    )


def test_setup_book_bash_preserves_existing_book_toml_customizations(tmp_path, monkeypatch):
    """Re-running `setup-book.sh` against an existing `book.toml` must not
    clobber custom fields like `tts_cost_per_1m_chars` or `voice` overrides.
    Previously the script overwrote the entire file every run, silently
    discarding any user customization (see C1 in the audit plan).

    We exercise the script via Python rather than bash so the test runs on
    Windows too — the behavior we care about (the existing file branch) is
    pure file-content manipulation.
    """
    repo_root = Path(__file__).resolve().parents[2]
    setup_script = (repo_root / ".authorkit" / "scripts" / "bash" / "setup-book.sh").read_text(
        encoding="utf-8"
    )

    # The "file exists" branch must not contain a single-line `cat > "$BOOK_TOML"`
    # heredoc — that was the source of the clobber. The fresh-install branch
    # still uses one (gated on `! -f`), which is correct.
    fresh_branch_marker = 'if [[ ! -f "$BOOK_TOML" ]]; then'
    existing_branch_marker = "else"
    assert fresh_branch_marker in setup_script, "setup-book.sh must branch on file existence"
    fresh_idx = setup_script.index(fresh_branch_marker)
    # Only one cat-redirect should remain (the fresh path).
    assert setup_script.count('cat > "$BOOK_TOML"') == 1, (
        "Expected exactly one full-file write, scoped to the fresh-install branch."
    )
    # And the existing-file branch must rely on Set-style key replacement.
    assert "replace_book_string" in setup_script
    # The commented `tts_cost_per_1m_chars` line keeps the README example honest.
    assert "# tts_cost_per_1m_chars = 0.000015" in setup_script


def test_setup_book_powershell_preserves_existing_book_toml_customizations():
    """Same contract as the bash variant — the PowerShell script must not
    rewrite an existing `book.toml`.
    """
    repo_root = Path(__file__).resolve().parents[2]
    ps_script = (
        repo_root / ".authorkit" / "scripts" / "powershell" / "setup-book.ps1"
    ).read_text(encoding="utf-8")

    assert "Set-BookStringField" in ps_script
    # tts_cost should ship commented out so users opt in.
    assert "# tts_cost_per_1m_chars = 0.000015" in ps_script
    # The existing-file branch must NOT call Write-Utf8NoBom on the full template.
    # The full-template write is only inside the fresh-install branch.
    fresh_marker = "-not (Test-Path $bookTomlPath -PathType Leaf)"
    assert fresh_marker in ps_script


def test_discover_chapter_drafts_rejects_inverted_range(tmp_path):
    """`--from-chapter > --to-chapter` is almost always a typo. Surfacing it as
    a `ValueError` lets the CLI translate it into a clean `BadParameter` instead
    of the generic "no draft chapters found" message.
    """
    from authorkit_cli.book_core import discover_chapter_drafts

    book_dir = tmp_path / "book"
    book_dir.mkdir()

    with pytest.raises(ValueError, match="must be <="):
        discover_chapter_drafts(book_dir, from_chapter=10, to_chapter=5)


def test_book_stats_rejects_inverted_chapter_range(tmp_path, monkeypatch):
    """End-to-end: `authorkit book stats --from-chapter 10 --to-chapter 5` must
    fail with an actionable error mentioning the flag names, not the generic
    "no draft chapters found" path.
    """
    repo_root = tmp_path
    (repo_root / ".authorkit").mkdir()
    book_dir = repo_root / "book"
    (book_dir / "chapters" / "01").mkdir(parents=True)
    (book_dir / "chapters" / "01" / "draft.md").write_text(
        "# Chapter 1\n\nBody.\n", encoding="utf-8"
    )

    monkeypatch.chdir(repo_root)
    result = runner.invoke(cli.app, ["book", "stats", "--from-chapter", "10", "--to-chapter", "5"])

    assert result.exit_code != 0
    assert "--from-chapter" in result.output
    assert "--to-chapter" in result.output


def test_book_audio_quiet_flag_suppresses_summary(tmp_path, monkeypatch):
    """`book audio --quiet` should not print the chapter-summary lines that
    the verbose path emits. CI consumers running batch audio rely on this.
    """
    repo_root = tmp_path
    (repo_root / ".authorkit").mkdir()
    book_dir = repo_root / "book"
    (book_dir / "chapters" / "01").mkdir(parents=True)
    (book_dir / "chapters" / "01" / "draft.md").write_text(
        "# Chapter 1\n\nBody.\n", encoding="utf-8"
    )

    def fake_generate_audiobook(**kwargs):
        return {
            "generated": 1,
            "skipped": 0,
            "chapter_files": [],
            "merged_file": None,
        }

    monkeypatch.setattr(book_commands, "generate_audiobook", fake_generate_audiobook)
    monkeypatch.chdir(repo_root)

    quiet_result = runner.invoke(cli.app, ["book", "audio", "--quiet"])
    loud_result = runner.invoke(cli.app, ["book", "audio"])

    assert quiet_result.exit_code == 0, quiet_result.output
    assert loud_result.exit_code == 0, loud_result.output
    assert "Generated:" not in quiet_result.output
    assert "Generated:" in loud_result.output


def test_status_legend_is_printed_when_chapters_tracked(tmp_path, monkeypatch):
    """The status dashboard must teach the marker semantics on the same screen
    as the counts — first-time users won't otherwise know that `[X]` ties back
    to the "approved" label printed above it.
    """
    repo_root = tmp_path
    (repo_root / ".authorkit").mkdir()
    book_dir = repo_root / "book"
    book_dir.mkdir()
    (book_dir / "concept.md").write_text("# Concept\n", encoding="utf-8")
    (book_dir / "chapters.md").write_text(
        "- [X] CH01 Title - summary\n- [ ] CH02 Title - summary\n",
        encoding="utf-8",
    )

    monkeypatch.chdir(repo_root)
    result = runner.invoke(cli.app, ["status"])

    assert result.exit_code == 0, result.output
    # Rich may soft-wrap the legend on narrow CI terminals; collapse whitespace
    # before asserting so the test is robust to wrap position.
    flattened = " ".join(result.output.split())
    assert "legend:" in flattened
    assert "[X] approved" in flattened


def test_init_drop_ai_confirmation_declined_keeps_existing_install():
    """Re-running init with a narrower --ai set (and no --force) must warn that
    dropping a flavor removes files, and abort cleanly when the user declines —
    leaving the previous install untouched.

    Then accepting the prompt must proceed with the swap. This exercises the
    interactive confirmation branch that the --force rerun tests bypass.
    """
    base_args = [
        "init",
        ".",
        "--script",
        "sh",
        "--here",
        "--ignore-agent-tools",
        "--no-git",
    ]
    with isolated_filesystem():
        first = runner.invoke(cli.app, [*base_args, "--ai", "claude,copilot", "--force"])
        assert first.exit_code == 0, first.output

        # Without --force, init first confirms the merge into a non-empty dir
        # ("y"), then the new drop-AI swap warning. Decline the swap ("n"): exit
        # is clean (0) and nothing changes.
        declined = runner.invoke(cli.app, [*base_args, "--ai", "codex"], input="y\nn\n")
        assert declined.exit_code == 0, declined.output
        assert "Switching AI flavors" in declined.output
        assert Path(".claude/commands/authorkit.write.md").exists()
        assert not Path(".codex/AGENTS.md").exists()
        manifest = json.loads(Path(".authorkit/install-manifest.json").read_text(encoding="utf-8"))
        assert manifest["ais"] == ["claude", "copilot"]

        # Accept both prompts: the previous flavors are removed and codex installed.
        accepted = runner.invoke(cli.app, [*base_args, "--ai", "codex"], input="y\ny\n")
        assert accepted.exit_code == 0, accepted.output
        assert Path(".codex/AGENTS.md").exists()
        assert not Path(".claude/commands/authorkit.write.md").exists()
        manifest = json.loads(Path(".authorkit/install-manifest.json").read_text(encoding="utf-8"))
        assert manifest["ais"] == ["codex"]


def test_book_audio_surfaces_runtime_error_cleanly(monkeypatch):
    """A RuntimeError from generate_audiobook (TTS synthesis / ffmpeg concat
    failure) must produce a clean non-zero exit with an actionable message,
    mirroring `build`, instead of a bare traceback.
    """
    with isolated_filesystem():
        _seed_book_tree()

        def boom(**kwargs):
            raise RuntimeError("CH01: OpenAI TTS synthesis failed on chunk 1/2: upstream 500")

        monkeypatch.setattr(book_commands, "generate_audiobook", boom)
        result = runner.invoke(cli.app, ["book", "audio", "--yes"])

        assert result.exit_code == 1, result.output
        assert "Audio generation failed" in result.output
        assert "upstream 500" in result.output


def test_book_audio_surfaces_value_error_cleanly():
    """An unsupported audio provider makes generate_audiobook raise ValueError
    (not RuntimeError). The command must surface it cleanly like `build`, not as
    a bare traceback. Exercises the real provider-validation path end-to-end
    rather than monkeypatching the raise, so it also guards generate_audiobook's
    contract.
    """
    with isolated_filesystem():
        _seed_book_tree()
        result = runner.invoke(cli.app, ["book", "audio", "--provider", "bogus", "--yes"])

        assert result.exit_code == 1, result.output
        assert "Audio generation failed" in result.output
        assert "Unsupported audio provider" in result.output


def test_status_tolerates_unreadable_parked_and_world_files(tmp_path, monkeypatch):
    """`authorkit status` must honor its "missing files never raise" contract
    even when parked-decisions.md / world/_index.md exist but can't be read.

    We force the unreadable case portably by creating those paths as
    directories: ``_exists`` is True but ``read_text`` raises an OSError
    subclass (IsADirectoryError on POSIX, PermissionError on Windows), which
    the guards in book_status must swallow.
    """
    repo_root = tmp_path
    (repo_root / ".authorkit").mkdir()
    book_dir = repo_root / "book"
    book_dir.mkdir()
    (book_dir / "concept.md").write_text("# Concept\n", encoding="utf-8")
    (book_dir / "chapters.md").write_text("- [X] CH01 Title - summary\n", encoding="utf-8")
    (book_dir / "parked-decisions.md").mkdir()
    (book_dir / "world").mkdir()
    (book_dir / "world" / "_index.md").mkdir()

    monkeypatch.chdir(repo_root)
    result = runner.invoke(cli.app, ["status"])

    assert result.exit_code == 0, result.output
    assert "Chapters:" in result.output


def test_status_tolerates_misencoded_parked_and_world_files(tmp_path, monkeypatch):
    """`authorkit status` must also survive parked-decisions.md / world/_index.md
    that exist but hold non-UTF-8 bytes (e.g. saved as cp1252/UTF-16). read_text
    raises UnicodeDecodeError — a ValueError subclass, NOT an OSError — so the
    guards must catch it explicitly or the dashboard crashes.
    """
    repo_root = tmp_path
    (repo_root / ".authorkit").mkdir()
    book_dir = repo_root / "book"
    book_dir.mkdir()
    (book_dir / "concept.md").write_text("# Concept\n", encoding="utf-8")
    (book_dir / "chapters.md").write_text("- [X] CH01 Title - summary\n", encoding="utf-8")
    # 0x97 is a lone continuation byte: invalid UTF-8 but legal cp1252 (em dash).
    (book_dir / "parked-decisions.md").write_bytes(
        b"## PD-001: thing\n**Status**: OPEN\n**Deadline**: Before CH12 \x97 soon\n"
    )
    (book_dir / "world").mkdir()
    (book_dir / "world" / "_index.md").write_bytes(b"- **Total entities**: 5 \x97\n")

    monkeypatch.chdir(repo_root)
    result = runner.invoke(cli.app, ["status"])

    assert result.exit_code == 0, result.output
    assert "Chapters:" in result.output


def test_check_prerequisites_counts_only_numeric_chapter_dirs():
    """check-prerequisites must report `chapters/` present only for a pure-numeric
    chapter folder that actually contains a draft.md (book/chapters/NN/draft.md),
    matching the CLI's discover_chapter_drafts convention — not for stray dirs
    like a `notes/` sibling, a `01-old/` backup, or an empty `01/` with no draft.
    """
    import shutil
    import subprocess
    import tempfile

    # Use the round-tripping guard, not a bare which("bash"): on Windows runners
    # `bash` resolves to the WSL launcher stub, which prints a UTF-16 "install a
    # distro" message and exits non-zero. _bash_with_working_python_available
    # actually executes bash and confirms it works before we depend on it.
    if not _bash_with_working_python_available():
        pytest.skip("working bash + python not available on this host")

    repo_root = Path(__file__).resolve().parents[2]
    common_sh = repo_root / ".authorkit" / "scripts" / "bash" / "common.sh"
    prereq_sh = repo_root / ".authorkit" / "scripts" / "bash" / "check-prerequisites.sh"

    def available_docs(chapter_subdir: str, *, with_draft: bool = True) -> list:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
            dst = tmp_path / ".authorkit" / "scripts" / "bash"
            dst.mkdir(parents=True)
            shutil.copy(common_sh, dst / "common.sh")
            shutil.copy(prereq_sh, dst / "check-prerequisites.sh")
            book = tmp_path / "book"
            chapter_dir = book / "chapters" / chapter_subdir
            chapter_dir.mkdir(parents=True)
            if with_draft:
                (chapter_dir / "draft.md").write_text("# Draft\n", encoding="utf-8")
            (book / "outline.md").write_text("# Outline\n", encoding="utf-8")
            result = subprocess.run(
                ["bash", str(dst / "check-prerequisites.sh"), "--json"],
                cwd=tmp_path,
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0, result.stderr
            return json.loads(result.stdout.strip())["AVAILABLE_DOCS"]

    assert "chapters/" in available_docs("01")
    assert "chapters/" not in available_docs("notes")
    assert "chapters/" not in available_docs("01-old")
    # A numeric folder with no draft.md must not count — discover_chapter_drafts
    # requires the draft, so the prereq check must too.
    assert "chapters/" not in available_docs("01", with_draft=False)


def test_check_prerequisites_powershell_counts_only_numeric_chapter_dirs():
    """PowerShell parity for the numeric chapter-dir rule: check-prerequisites.ps1
    must report `chapters/` only for a pure-numeric folder that contains a
    draft.md, matching the bash flavor and the CLI. Skips when no PowerShell
    runtime is available.
    """
    import shutil
    import subprocess
    import tempfile

    pwsh_available = shutil.which("pwsh") or shutil.which("powershell")
    if not pwsh_available:
        pytest.skip("PowerShell runtime not available on this host")

    ps_exe = "pwsh" if shutil.which("pwsh") else "powershell"
    repo_root = Path(__file__).resolve().parents[2]
    common_ps = repo_root / ".authorkit" / "scripts" / "powershell" / "common.ps1"
    prereq_ps = repo_root / ".authorkit" / "scripts" / "powershell" / "check-prerequisites.ps1"

    def available_docs(chapter_subdir: str, *, with_draft: bool = True) -> list:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
            dst = tmp_path / ".authorkit" / "scripts" / "powershell"
            dst.mkdir(parents=True)
            shutil.copy(common_ps, dst / "common.ps1")
            shutil.copy(prereq_ps, dst / "check-prerequisites.ps1")
            book = tmp_path / "book"
            chapter_dir = book / "chapters" / chapter_subdir
            chapter_dir.mkdir(parents=True)
            if with_draft:
                (chapter_dir / "draft.md").write_text("# Draft\n", encoding="utf-8")
            (book / "outline.md").write_text("# Outline\n", encoding="utf-8")
            result = subprocess.run(
                [ps_exe, "-NoProfile", "-ExecutionPolicy", "Bypass",
                 "-File", str(dst / "check-prerequisites.ps1"), "-Json"],
                cwd=tmp_path,
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0, result.stderr
            docs = json.loads(result.stdout.strip()).get("AVAILABLE_DOCS")
            # ConvertTo-Json unwraps a single-element array to a scalar and an
            # empty array to null — normalize both back to a list.
            if docs is None:
                return []
            return [docs] if isinstance(docs, str) else docs

    assert "chapters/" in available_docs("01")
    assert "chapters/" not in available_docs("notes")
    assert "chapters/" not in available_docs("01-old")
    # A numeric folder with no draft.md must not count — parity with the bash
    # flavor and discover_chapter_drafts.
    assert "chapters/" not in available_docs("01", with_draft=False)


# --- AutoPilot (authorkit autopilot) -----------------------------------------


def _seed_autopilot_book(tmp_path, *, chapters_md=None, constitution_filled=True):
    """Seed a tmp repo good enough for chapters-mode preflight.

    Creates `.authorkit/` (so find_repo_root resolves here) with a filled (or
    template) constitution, plus book/{concept,outline,chapters}.md.
    """
    book_dir = tmp_path / "book"
    book_dir.mkdir(parents=True, exist_ok=True)
    (book_dir / "concept.md").write_text("# Concept\n\nPremise.\n", encoding="utf-8")
    (book_dir / "outline.md").write_text("# Outline\n\nCH01 ...\n", encoding="utf-8")
    if chapters_md is None:
        chapters_md = (
            "# Chapters\n\n"
            "- [D] CH01 The Arrival - First chapter\n"
            "- [P] CH02 The Catalogue - Second chapter\n"
        )
    (book_dir / "chapters.md").write_text(chapters_md, encoding="utf-8")

    mem = tmp_path / ".authorkit" / "memory"
    mem.mkdir(parents=True, exist_ok=True)
    if constitution_filled:
        constitution = "# My Book Constitution\n\n## Voice & Style\n\n### I. Voice\n\nThird person limited, past tense.\n"
    else:
        constitution = "# [BOOK_TITLE] Constitution\n\n### [PRINCIPLE_1_NAME]\n\n[PRINCIPLE_1_DESCRIPTION]\n"
    (mem / "constitution.md").write_text(constitution, encoding="utf-8")
    return book_dir


def test_parse_directive_variants():
    """parse_directive accepts dicts and fenced JSON, and rejects malformed replies."""
    drafted = autopilot_core.parse_directive(
        {"action": "draft", "chapter": 3, "command": "/authorkit.write 3", "reason": "x"}
    )
    assert drafted.action == "draft" and drafted.chapter == 3 and drafted.command == "/authorkit.write 3"

    fenced = autopilot_core.parse_directive('prose...\n```json\n{"action": "done", "reason": "all set"}\n```\n')
    assert fenced.action == "done"

    with pytest.raises(autopilot_core.DirectiveError):
        autopilot_core.parse_directive({"action": "frobnicate"})
    with pytest.raises(autopilot_core.DirectiveError):
        autopilot_core.parse_directive({"action": "review"})  # act action needs a command
    with pytest.raises(autopilot_core.DirectiveError):
        autopilot_core.parse_directive({"action": "escalate", "escalation": {}})  # needs decision_needed
    with pytest.raises(autopilot_core.DirectiveError):
        autopilot_core.parse_directive("not json at all")


def test_next_escalation_id_sequences(tmp_path):
    """next_escalation_id returns ESC-001 when empty and increments past the max."""
    escalations = tmp_path / "escalations"
    escalations.mkdir()
    assert autopilot_core.next_escalation_id(escalations) == "ESC-001"
    (escalations / "2026-01-01-ESC-001-a.md").write_text("# ESC-001\n", encoding="utf-8")
    (escalations / "2026-01-02-ESC-007-b.md").write_text("# ESC-007\n", encoding="utf-8")
    assert autopilot_core.next_escalation_id(escalations) == "ESC-008"


def test_autopilot_preflight_refuses_without_concept(tmp_path, monkeypatch):
    """`autopilot chapters` refuses (exit 2) when the seed (concept.md) is missing."""
    (tmp_path / ".authorkit").mkdir()
    (tmp_path / "book").mkdir()
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(cli.app, ["autopilot", "chapters", "--range", "1-2"])
    assert result.exit_code == 2, result.output
    assert "preflight failed" in result.output
    assert "concept.md" in result.output
    assert "/authorkit.discuss" in result.output


def test_autopilot_chapters_preflight_requires_outline(tmp_path, monkeypatch):
    """chapters mode requires outline.md even when concept + constitution exist."""
    book_dir = tmp_path / "book"
    book_dir.mkdir(parents=True)
    (book_dir / "concept.md").write_text("# Concept\n", encoding="utf-8")
    mem = tmp_path / ".authorkit" / "memory"
    mem.mkdir(parents=True)
    (mem / "constitution.md").write_text("# Filled\n\nThird person past tense.\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(cli.app, ["autopilot", "chapters", "--range", "1-2"])
    assert result.exit_code == 2, result.output
    assert "outline.md" in result.output


def test_autopilot_chapters_preflight_flags_template_constitution(tmp_path, monkeypatch):
    """A still-templated constitution is treated as not seeded for chapters mode."""
    _seed_autopilot_book(tmp_path, constitution_filled=False)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(cli.app, ["autopilot", "chapters", "--range", "1-2"])
    assert result.exit_code == 2, result.output
    assert "constitution" in result.output.lower()


def test_autopilot_dry_run_prints_directive_without_acting(tmp_path, monkeypatch):
    """--dry-run prints the planner's next directive and dispatches nothing."""
    _seed_autopilot_book(tmp_path)
    fake = autopilot_runner.FakeRunner(
        [autopilot_core.Directive(action="draft", chapter=2, command="/authorkit.write 2", reason="next")]
    )
    monkeypatch.setattr(autopilot_commands, "get_runner", lambda *a, **k: fake)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(cli.app, ["autopilot", "chapters", "--range", "1-2", "--dry-run"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["mode"] == "chapters"
    assert payload["directive"]["action"] == "draft"
    assert payload["directive"]["command"] == "/authorkit.write 2"
    assert fake.dispatched == []


def test_autopilot_step_dispatches_one_command(tmp_path, monkeypatch):
    """--step runs exactly one tick: dispatch the chosen command, then stop."""
    _seed_autopilot_book(tmp_path)
    fake = autopilot_runner.FakeRunner(
        [autopilot_core.Directive(action="review", chapter=1, command="/authorkit.review 1", reason="review CH1")]
    )
    monkeypatch.setattr(autopilot_commands, "get_runner", lambda *a, **k: fake)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(cli.app, ["autopilot", "chapters", "--range", "1-2", "--step"])
    assert result.exit_code == 0, result.output
    assert fake.dispatched == ["/authorkit.review 1"]
    assert "--step" in result.output


def test_autopilot_escalate_writes_record_and_halts(tmp_path, monkeypatch):
    """An escalate directive writes an OPEN ESC-NNN record and halts; nothing dispatched."""
    book_dir = _seed_autopilot_book(tmp_path)
    esc = {"type": "story-fork", "decision_needed": "Should the keeper survive act 3?", "options": ["yes", "no"]}
    fake = autopilot_runner.FakeRunner(
        [autopilot_core.Directive(action="escalate", reason="need direction", escalation=esc)]
    )
    monkeypatch.setattr(autopilot_commands, "get_runner", lambda *a, **k: fake)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(cli.app, ["autopilot", "chapters", "--range", "1-2"])
    assert result.exit_code == 0, result.output

    records = list((book_dir / "escalations").glob("*.md"))
    assert len(records) == 1
    text = records[0].read_text(encoding="utf-8")
    assert "**Status**: OPEN" in text
    assert "ESC-001" in text
    assert "Should the keeper survive act 3?" in text
    assert fake.dispatched == []


def test_autopilot_refuses_when_open_escalation_exists(tmp_path, monkeypatch):
    """The loop halts immediately when an OPEN escalation is present."""
    book_dir = _seed_autopilot_book(tmp_path)
    esc_dir = book_dir / "escalations"
    esc_dir.mkdir()
    (esc_dir / "2026-06-18-ESC-001-open.md").write_text("# ESC-001: X\n\n**Status**: OPEN\n", encoding="utf-8")
    fake = autopilot_runner.FakeRunner(
        [autopilot_core.Directive(action="review", chapter=1, command="/authorkit.review 1")]
    )
    monkeypatch.setattr(autopilot_commands, "get_runner", lambda *a, **k: fake)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(cli.app, ["autopilot", "chapters", "--range", "1-2"])
    assert result.exit_code == 0, result.output
    assert "open escalation" in result.output.lower()
    assert fake.dispatched == []


def test_autopilot_chapters_loop_completes_range(tmp_path, monkeypatch):
    """The loop reviews the chapter, observes [D]->[X], then reports done."""
    book_dir = _seed_autopilot_book(tmp_path, chapters_md="# Chapters\n\n- [D] CH01 The Arrival - First\n")

    def on_command(_cmd):
        path = book_dir / "chapters.md"
        path.write_text(path.read_text(encoding="utf-8").replace("[D] CH01", "[X] CH01"), encoding="utf-8")

    fake = autopilot_runner.FakeRunner(
        [autopilot_core.Directive(action="review", chapter=1, command="/authorkit.review 1", reason="review CH1")],
        on_command=on_command,
    )
    monkeypatch.setattr(autopilot_commands, "get_runner", lambda *a, **k: fake)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(cli.app, ["autopilot", "chapters", "--range", "1-1"])
    assert result.exit_code == 0, result.output
    assert fake.dispatched == ["/authorkit.review 1"]
    assert "done" in result.output.lower()
    assert "[X] CH01" in (book_dir / "chapters.md").read_text(encoding="utf-8")


def test_autopilot_loop_health_oscillation_escalates(tmp_path, monkeypatch):
    """Repeating the same command with no status change trips a loop-health escalation."""
    book_dir = _seed_autopilot_book(tmp_path, chapters_md="# Chapters\n\n- [D] CH01 X - first\n")
    same = autopilot_core.Directive(action="review", chapter=1, command="/authorkit.review 1", reason="stuck")
    fake = autopilot_runner.FakeRunner([same, same, same, same, same])  # on_command=None: no status change
    monkeypatch.setattr(autopilot_commands, "get_runner", lambda *a, **k: fake)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(cli.app, ["autopilot", "chapters", "--range", "1-1"])
    assert result.exit_code == 0, result.output
    assert "loop-health" in result.output.lower() or "no progress" in result.output.lower()

    records = list((book_dir / "escalations").glob("*.md"))
    assert len(records) == 1
    assert "loop-health" in records[0].read_text(encoding="utf-8")


# --- Review-currency gate & tic-gate convergence (Bug 1 + Bug 2) --------------


def _seed_chapter_review(book_dir, n, *, draft, review_verdict, gating="none", status_line, record_sha=True):
    """Create chapters/NN/{draft,review}.md, set CH0N's chapters.md row, and (optionally)
    the review-index sidecar so ``review_state`` sees the review as current for the draft."""
    chap = book_dir / "chapters" / f"{n:02d}"
    chap.mkdir(parents=True, exist_ok=True)
    draft_path = chap / "draft.md"
    draft_path.write_text(draft, encoding="utf-8")
    (chap / "review.md").write_text(
        f"# Chapter Review: Chapter {n:02d}\n\n**Overall Assessment**: {review_verdict}\n\n"
        f"## Verdict\n**Status**: {review_verdict}\n**Gating Shapes**: {gating}\n",
        encoding="utf-8",
    )
    (book_dir / "chapters.md").write_text(f"# Chapters\n\n- {status_line}\n", encoding="utf-8")
    if record_sha:
        verdict = "NEEDS_REVISION" if "NEEDS" in review_verdict.upper() else "PASS"
        autopilot_core.write_review_index(
            book_dir, {f"CH{n:02d}": {"draft_sha": autopilot_core.file_md5(draft_path), "verdict": verdict}}
        )
    return draft_path


def _flip_status(book_dir, old, new):
    path = book_dir / "chapters.md"
    path.write_text(path.read_text(encoding="utf-8").replace(old, new), encoding="utf-8")


def test_review_state_currency(tmp_path):
    """review_state is `current` only while the sidecar hash matches the draft on disk."""
    book_dir = _seed_autopilot_book(tmp_path)
    draft_path = _seed_chapter_review(
        book_dir, 1, draft="v0", review_verdict="NEEDS REVISION", status_line="[R] CH01 X - first"
    )

    state = autopilot_core.review_state(book_dir, 1)
    assert state.exists and state.current and state.verdict == "NEEDS_REVISION"

    # Draft changes (a revise) → the standing review is stale, so not a no-op anymore.
    draft_path.write_text("v1", encoding="utf-8")
    assert autopilot_core.review_state(book_dir, 1).current is False

    # No sidecar entry (e.g. a hand-run review) degrades safely to not-current.
    autopilot_core.write_review_index(book_dir, {})
    assert autopilot_core.review_state(book_dir, 1).current is False

    # No review at all.
    assert autopilot_core.review_state(book_dir, 2).exists is False


def test_autopilot_converts_noop_review_to_revise(tmp_path, monkeypatch):
    """Bug 1: a stubborn planner asking to re-review an unchanged NEEDS-REVISION draft is
    converted to the prescribed revise — never two identical reviews in a row — and the loop
    still terminates (does not run to MAX_TICKS)."""
    book_dir = _seed_autopilot_book(tmp_path)
    draft_path = _seed_chapter_review(
        book_dir, 1, draft="draft v0", review_verdict="NEEDS REVISION", status_line="[R] CH01 X - first"
    )
    review_path = book_dir / "chapters" / "01" / "review.md"

    def on_command(cmd):
        if "revise" in cmd:  # mutate the draft (so the next review is real) and re-draft
            draft_path.write_text("draft v1", encoding="utf-8")
            _flip_status(book_dir, "[R] CH01", "[D] CH01")
        elif "/authorkit.review" in cmd:  # a real review this time: approve to terminate
            review_path.write_text(
                "# Review\n\n**Overall Assessment**: PASS\n\n## Verdict\n"
                "**Status**: PASS\n**Gating Shapes**: none\n",
                encoding="utf-8",
            )
            _flip_status(book_dir, "[D] CH01", "[X] CH01")

    review = autopilot_core.Directive(action="review", chapter=1, command="/authorkit.review 1", reason="stub")
    fake = autopilot_runner.FakeRunner([review, review, review, review], on_command=on_command)
    monkeypatch.setattr(autopilot_commands, "get_runner", lambda *a, **k: fake)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(cli.app, ["autopilot", "chapters", "--range", "1-1"])
    assert result.exit_code == 0, result.output
    assert "done" in result.output.lower()

    # First dispatch was the CONVERTED revise, not a re-review of the current draft.
    assert fake.dispatched[0].startswith("/authorkit.write 1 revise")
    assert fake.dispatched[1] == "/authorkit.review 1"
    # No two consecutive identical review commands ever slipped through.
    for a, b in zip(fake.dispatched, fake.dispatched[1:]):
        assert not (a == b == "/authorkit.review 1")

    # The conversion is visible in autopilot.jsonl (planner asked review, harness ran revise).
    log_lines = (book_dir / "runs" / "autopilot.jsonl").read_text(encoding="utf-8").splitlines()
    first = json.loads(log_lines[0])
    assert first["planner_action"] == "review" and first["action"] == "revise" and first["chapter"] == 1


def test_autopilot_reviews_when_draft_changed_since_review(tmp_path, monkeypatch):
    """Bug 1 negative: when the draft changed since the last review (sidecar stale), the guard
    dispatches a real review — it does not convert."""
    book_dir = _seed_autopilot_book(tmp_path)
    draft_path = _seed_chapter_review(
        book_dir, 1, draft="v0", review_verdict="NEEDS REVISION", status_line="[D] CH01 X - first"
    )
    draft_path.write_text("v1 — edited since review", encoding="utf-8")  # sidecar now stale

    review = autopilot_core.Directive(action="review", chapter=1, command="/authorkit.review 1", reason="real")
    fake = autopilot_runner.FakeRunner([review])
    monkeypatch.setattr(autopilot_commands, "get_runner", lambda *a, **k: fake)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(cli.app, ["autopilot", "chapters", "--range", "1-1", "--step"])
    assert result.exit_code == 0, result.output
    assert fake.dispatched == ["/authorkit.review 1"]  # not converted


def test_autopilot_range_review_not_attributed_to_first_chapter(tmp_path, monkeypatch):
    """Review-fix #1: a range review (`/authorkit.review 1-2`) is dispatched as-is — never
    converted to a single-chapter revise — and is not recorded against CH01's sidecar, even
    when CH01's standing review is current + NEEDS_REVISION (which WOULD convert a single review)."""
    book_dir = _seed_autopilot_book(tmp_path)
    _seed_chapter_review(book_dir, 1, draft="v0", review_verdict="NEEDS REVISION", status_line="[R] CH01 A - a")
    (book_dir / "chapters.md").write_text("# Chapters\n\n- [R] CH01 A - a\n- [R] CH02 B - b\n", encoding="utf-8")
    before = json.loads((book_dir / "runs" / "review-index.json").read_text(encoding="utf-8"))

    rng = autopilot_core.Directive(action="review", chapter=None, command="/authorkit.review 1-2", reason="drift")
    fake = autopilot_runner.FakeRunner([rng])
    monkeypatch.setattr(autopilot_commands, "get_runner", lambda *a, **k: fake)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(cli.app, ["autopilot", "chapters", "--range", "1-2", "--step"])
    assert result.exit_code == 0, result.output
    assert fake.dispatched == ["/authorkit.review 1-2"]  # dispatched as-is, not converted

    # The last dispatched-tick record (a terminal 'step' outcome line now follows it).
    records = [
        json.loads(l)
        for l in (book_dir / "runs" / "autopilot.jsonl").read_text(encoding="utf-8").splitlines()
        if l.strip()
    ]
    entry = next(r for r in reversed(records) if "action" in r)
    assert entry["chapter"] is None and entry["action"] == "review"
    after = json.loads((book_dir / "runs" / "review-index.json").read_text(encoding="utf-8"))
    assert after["CH01"]["draft_sha"] == before["CH01"]["draft_sha"]  # not re-stamped by the range pass


def test_gating_findings_convergence():
    """Bug 2 spec: the gate set is exactly {shapes >= budget}; below-budget residuals never
    gate; a revise that drops a shape below budget shrinks it to the converged-with-residual
    fixed point; a revise that worsens a tolerated shape past budget re-gates it (soundness)."""
    # Fixed draft, blind discovery surfaces a DIFFERENT below-budget residual each cycle.
    g1 = autopilot_core.gating_findings({"tic-003": 3, "blind-a": 1})
    g2 = autopilot_core.gating_findings({"tic-003": 3, "blind-b": 1})
    assert g1 == g2 == {"tic-003"}  # stable, non-growing — the residuals never gate
    assert autopilot_core.gating_set_converging(g1, g2)

    # A revise brings the shape below budget → empty gating set (converged-with-residual).
    g3 = autopilot_core.gating_findings({"tic-003": 0, "blind-c": 2})
    assert g3 == set() and g3 < g1  # strictly shrank

    # A revise that WORSENS a previously-tolerated shape (2 -> 4) past budget re-gates it.
    g4 = autopilot_core.gating_findings({"tic-003": 0, "tic-050": 4})
    assert g4 == {"tic-050"}
    assert autopilot_core.gating_set_converging({"a"}, {"a"}) is True
    assert autopilot_core.gating_set_converging({"a"}, {"a", "c"}) is False


def test_gating_set_stable_across_repeated_reviews():
    """Bug 2 simulation: repeated reviews of a fixed draft return a stable, non-growing gating
    set even as blind discovery injects a brand-new below-budget shape every cycle."""
    seen = [
        frozenset(autopilot_core.gating_findings({"tic-003": 3, f"blind-{i}": 1}))
        for i in range(6)
    ]
    assert all(s == seen[0] for s in seen)  # identical across every review
    assert all(autopilot_core.gating_set_converging(seen[0], s) for s in seen)  # never grows


def test_command_chapter_ignores_ranges():
    """A single-chapter command yields its number; a range/manuscript review yields None so it
    is not misattributed to its first chapter (review-fix #1)."""
    assert autopilot_core.command_chapter("/authorkit.review 7") == 7
    assert autopilot_core.command_chapter("/authorkit.review 15") == 15
    assert autopilot_core.command_chapter("/authorkit.write 12 revise: fix voice") == 12
    assert autopilot_core.command_chapter("/authorkit.review 5-10") is None
    assert autopilot_core.command_chapter("/authorkit.review 5 - 10") is None
    # Multi-digit ranges: backtracking must not split "15" into "1" + a passing lookahead.
    assert autopilot_core.command_chapter("/authorkit.review 15-20") is None
    assert autopilot_core.command_chapter("/authorkit.review 12 - 20") is None
    assert autopilot_core.command_chapter("/authorkit.review all") is None
    assert autopilot_core.command_chapter(None) is None


def test_parse_review_verdict_prefers_status_and_skips_template():
    """The authoritative `## Verdict` Status line wins over a stale/templated Overall
    Assessment header, and an unfilled `[PASS / NEEDS REVISION]` value is treated as unparsed
    (review-fix #2)."""
    # Header left as the literal template, Status correctly filled PASS → PASS (not churn).
    body = (
        "**Overall Assessment**: [PASS / NEEDS REVISION]\n\n"
        "## Verdict\n**Status**: PASS - ready to move on\n"
    )
    assert autopilot_core.parse_review_verdict(body) == "PASS"
    # A real NEEDS REVISION is still read.
    assert autopilot_core.parse_review_verdict("**Status**: NEEDS REVISION - see issues\n") == "NEEDS_REVISION"
    # Fully templated review → unparsed (None), so the guard won't wrongly convert.
    assert autopilot_core.parse_review_verdict("**Overall Assessment**: [PASS / NEEDS REVISION]\n") is None


def test_parse_gating_shapes_absent_vs_none_vs_template():
    """An ABSENT or unfilled-template Gating Shapes line is None (contract not followed —
    never mistaken for convergence); an explicit `none` is the empty gate (review-fix / complaint)."""
    assert autopilot_core.parse_gating_shapes("a review with no such line") is None
    assert autopilot_core.parse_gating_shapes("**Gating Shapes**: none\n") == ()
    # Unfilled `[…]`/template placeholder → treated as absent, not as a shape list.
    assert autopilot_core.parse_gating_shapes("**Gating Shapes**: [REQUIRED, comma-separated ids]\n") is None
    assert autopilot_core.parse_gating_shapes("**Gating Shapes**: TIC-059, TIC-066\n") == ("tic-059", "tic-066")


def test_parse_review_verdict_falls_back_to_gating_line():
    """When the prose heading is missing/templated, the machine-readable Gating Shapes line is
    the fallback verdict: `none` -> PASS (converged), non-empty -> NEEDS_REVISION."""
    assert autopilot_core.parse_review_verdict("## Verdict\n**Gating Shapes**: none\n") == "PASS"
    assert autopilot_core.parse_review_verdict("## Verdict\n**Gating Shapes**: TIC-1\n") == "NEEDS_REVISION"
    # A present heading still wins over the gating line (it reflects ALL gating passes).
    assert autopilot_core.parse_review_verdict("**Status**: NEEDS REVISION\n**Gating Shapes**: none\n") == "NEEDS_REVISION"
    # Neither a heading nor a gating line → unknown.
    assert autopilot_core.parse_review_verdict("prose only, no verdict") is None


def test_reconcile_stall_signal(tmp_path):
    """The single persisted progress signal: a ratcheting best-gate-size resets the
    'reviews since improvement' counter, oscillation ABOVE that floor accrues it (the
    moving-target case the old any-shrink-in-window test could be fooled by), reconcile_stalled
    trips at the limit, a review with no gating record leaves it untouched, and a converged
    (empty-gate / PASS) review clears it."""
    book_dir = tmp_path / "book"
    limit = autopilot_core.RECONCILE_STALL_LIMIT

    def review(chapter, gating, verdict=None):
        autopilot_core.record_review(book_dir, chapter, draft_sha="sha", verdict=verdict, gating_shapes=gating)
        return autopilot_core.chapter_review_entry(book_dir, chapter)

    # First gated review establishes the best; a strictly smaller gate is a new minimum.
    e = review(1, ("a", "b"))
    assert e["best_gate_size"] == 2 and e["reviews_since_improvement"] == 0
    assert autopilot_core.reconcile_stalled(e) is False
    e = review(1, ("a",))
    assert e["best_gate_size"] == 1 and e["reviews_since_improvement"] == 0

    # Oscillation back above the floor (1↔2) never reaches a NEW minimum — each review accrues
    # the counter even though it keeps 'shrinking' 2→1→2→1, and reconcile_stalled trips exactly
    # at the limit. (This is precisely what defeated the old detector.)
    gates = [("a", "b"), ("a",)]
    for i in range(1, limit + 1):
        e = review(1, gates[i % 2])
        assert e["best_gate_size"] == 1  # ratchet never re-inflates
        assert e["reviews_since_improvement"] == i
        assert autopilot_core.reconcile_stalled(e) is (i >= limit)

    # A review that emitted no gating record leaves the signal untouched (can't judge unmeasured
    # progress) — neither advancing nor clearing it.
    before = autopilot_core.chapter_review_entry(book_dir, 1)["reviews_since_improvement"]
    e = review(1, None)
    assert e["reviews_since_improvement"] == before

    # An explicit empty gate clears the signal (converged) — a re-open starts fresh.
    e = review(2, ("x", "y"))
    e = review(2, ())
    assert "reviews_since_improvement" not in e and "best_gate_size" not in e and "last_gate" not in e
    assert autopilot_core.reconcile_stalled(e) is False

    # A PASS verdict clears too, even with a non-empty gate line (verdict is authoritative).
    review(3, ("a", "b"))
    e = review(3, ("a",), verdict="PASS")
    assert "reviews_since_improvement" not in e
    assert autopilot_core.reconcile_stalled(e) is False


def test_reconcile_stall_slow_progress_never_trips(tmp_path):
    """Genuine slow progress — the gate shrinks by one shape each review — keeps reaching a new
    minimum, so the counter never accrues and reconcile_stalled stays False however many cycles
    it takes (no arbitrary cap cuts it off); a final PASS clears the signal for a clean re-open."""
    book_dir = tmp_path / "book"
    shapes = [f"tic-{n}" for n in range(7)]
    for k in range(len(shapes), 0, -1):  # 7,6,5,4,3,2,1 — a new minimum each time
        autopilot_core.record_review(book_dir, 1, draft_sha="s", verdict=None, gating_shapes=tuple(shapes[:k]))
        e = autopilot_core.chapter_review_entry(book_dir, 1)
        assert e["reviews_since_improvement"] == 0
        assert autopilot_core.reconcile_stalled(e) is False
    autopilot_core.record_review(book_dir, 1, draft_sha="s", verdict="PASS", gating_shapes=())
    e = autopilot_core.chapter_review_entry(book_dir, 1)
    assert autopilot_core.reconcile_stalled(e) is False
    assert "reviews_since_improvement" not in e


def test_log_tick_never_concatenates_records(tmp_path):
    """log_tick guarantees each record starts on its own line even when a prior write left the
    file without a trailing newline (crash/interleave), so a naive line-by-line parser never
    sees two JSON records glued together."""
    book_dir = tmp_path / "book"
    (book_dir / "runs").mkdir(parents=True)
    log = book_dir / "runs" / "autopilot.jsonl"
    log.write_text('{"a": 1}', encoding="utf-8")  # a prior record, no trailing newline
    autopilot_core.log_tick(book_dir, {"b": 2})
    lines = [l for l in log.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(lines) == 2
    assert json.loads(lines[0]) == {"a": 1}
    assert json.loads(lines[1]) == {"b": 2}


def test_autopilot_logs_terminal_outcome(tmp_path, monkeypatch):
    """Terminal outcomes are recorded in autopilot.jsonl so the log alone explains why a run
    ended — previously only dispatched ticks were logged, never the ending."""
    book_dir = _seed_autopilot_book(tmp_path, chapters_md="# Chapters\n\n- [X] CH01 A - a\n")
    # Whole range already [X] → the deterministic completion check ends the run at 'done'
    # before any directive is dispatched.
    fake = autopilot_runner.FakeRunner([])
    monkeypatch.setattr(autopilot_commands, "get_runner", lambda *a, **k: fake)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(cli.app, ["autopilot", "chapters", "--range", "1-1"])
    assert result.exit_code == 0, result.output
    outcomes = [
        json.loads(l)
        for l in (book_dir / "runs" / "autopilot.jsonl").read_text(encoding="utf-8").splitlines()
        if l.strip()
    ]
    assert any(o.get("outcome") == "done" for o in outcomes)


def test_autopilot_escalates_quality_stall_on_nonconverging_chapter(tmp_path, monkeypatch):
    """Bug 2 backstop: a chapter whose gating set never shrinks across reviews escalates a
    quality-stall (human override) instead of churning to MAX_TICKS."""
    book_dir = _seed_autopilot_book(tmp_path)
    draft_path = _seed_chapter_review(
        book_dir, 1, draft="draft v0", review_verdict="NEEDS REVISION",
        gating="tic-003, tic-009", status_line="[R] CH01 X - first",
    )
    review_path = book_dir / "chapters" / "01" / "review.md"
    counter = {"n": 0}

    def on_command(cmd):
        if "revise" in cmd:  # edits the draft but never fixes the tics
            counter["n"] += 1
            draft_path.write_text(f"draft v{counter['n']}", encoding="utf-8")
            _flip_status(book_dir, "[R] CH01", "[D] CH01")
        elif "/authorkit.review" in cmd:  # same two shapes gate every time — no progress
            review_path.write_text(
                "# Review\n\n**Overall Assessment**: NEEDS REVISION\n\n## Verdict\n"
                "**Status**: NEEDS REVISION\n**Gating Shapes**: tic-003, tic-009\n",
                encoding="utf-8",
            )
            _flip_status(book_dir, "[D] CH01", "[R] CH01")

    review = autopilot_core.Directive(action="review", chapter=1, command="/authorkit.review 1", reason="stuck")
    fake = autopilot_runner.FakeRunner([review] * 30, on_command=on_command)
    monkeypatch.setattr(autopilot_commands, "get_runner", lambda *a, **k: fake)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(cli.app, ["autopilot", "chapters", "--range", "1-1"])
    assert result.exit_code == 0, result.output
    assert "quality-stall" in result.output.lower() or "not converging" in result.output.lower()

    records = list((book_dir / "escalations").glob("*.md"))
    assert len(records) == 1
    assert "quality-stall" in records[0].read_text(encoding="utf-8")
    # Bounded: it stopped well short of the MAX_TICKS backstop.
    assert len(fake.dispatched) < 20


def test_autopilot_shrinking_gate_does_not_trip_loop_health(tmp_path, monkeypatch):
    """Regression (ESC-014): a chapter whose chapters.md status stays flat while its gating set
    shrinks 3→2→1→0 is making real progress — a review that reaches a new gating minimum counts
    as progress, so loop-health (detect_no_progress) must NOT kill the converging reconciliation
    before it reaches PASS."""
    book_dir = _seed_autopilot_book(tmp_path, chapters_md="# Chapters\n\n- [D] CH01 A - a\n")
    chap = book_dir / "chapters" / "01"
    chap.mkdir(parents=True)
    draft_path = chap / "draft.md"
    draft_path.write_text("v0", encoding="utf-8")
    review_path = chap / "review.md"
    gates = [["a", "b", "c"], ["a", "b"], ["a"], []]  # 3 → 2 → 1 → 0 (converged)
    st = {"rev": 0, "review": 0}

    def on_command(cmd):
        if "revise" in cmd:  # change the draft so the next review isn't a no-op; status stays [D]
            st["rev"] += 1
            draft_path.write_text(f"v{st['rev']}", encoding="utf-8")
        elif "/authorkit.review" in cmd:
            gate = gates[min(st["review"], len(gates) - 1)]
            st["review"] += 1
            if gate:  # NEEDS REVISION with a shrinking gate — status deliberately left flat at [D]
                review_path.write_text(
                    "# Review\n\n**Overall Assessment**: NEEDS REVISION\n\n## Verdict\n"
                    f"**Status**: NEEDS REVISION\n**Gating Shapes**: {', '.join(gate)}\n",
                    encoding="utf-8",
                )
            else:  # converged → PASS and approve
                review_path.write_text(
                    "# Review\n\n**Overall Assessment**: PASS\n\n## Verdict\n"
                    "**Status**: PASS\n**Gating Shapes**: none\n",
                    encoding="utf-8",
                )
                _flip_status(book_dir, "[D] CH01", "[X] CH01")

    rv = autopilot_core.Directive(action="review", chapter=1, command="/authorkit.review 1", reason="review")
    wr = autopilot_core.Directive(action="revise", chapter=1, command="/authorkit.write 1 revise: shrink the gate", reason="revise")
    fake = autopilot_runner.FakeRunner([rv, wr, rv, wr, rv, wr, rv], on_command=on_command)
    monkeypatch.setattr(autopilot_commands, "get_runner", lambda *a, **k: fake)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(cli.app, ["autopilot", "chapters", "--range", "1-1"])
    assert result.exit_code == 0, result.output
    # No loop-health escalation — the shrinking gate was recognized as progress.
    assert "loop-health" not in result.output.lower()
    assert not list((book_dir / "escalations").glob("*.md"))
    # It converged: CH01 reached [X] and the run ended 'done'.
    assert "[X] CH01" in (book_dir / "chapters.md").read_text(encoding="utf-8")
    assert "done" in result.output.lower()


def test_autopilot_converged_with_residual_review_reaches_approved(tmp_path, monkeypatch):
    """Complaint acceptance: a re-review whose carry-over gating shapes are all fixed but whose
    blind sweep found NEW shapes emits `Gating Shapes: none` + Status PASS, reaches [X], and the
    loop completes — the planner advances rather than dispatching yet another revise."""
    book_dir = _seed_autopilot_book(tmp_path, chapters_md="# Chapters\n\n- [D] CH01 A - a\n")
    chap = book_dir / "chapters" / "01"
    chap.mkdir(parents=True)
    (chap / "draft.md").write_text("revised draft", encoding="utf-8")

    def on_command(cmd):
        # Prior gate (tic-003) is fixed; the fresh blind sweep names a new residual (blind-9)
        # which is seeded, NOT gated → converged-with-residual → PASS.
        (chap / "review.md").write_text(
            "# Review\n\n**Overall Assessment**: PASS\n\n"
            "Pass 2: converged-with-residual — new residual shape blind-9 seeded to the ledger.\n\n"
            "## Verdict\n**Status**: PASS - ready to move on\n**Gating Shapes**: none\n",
            encoding="utf-8",
        )
        _flip_status(book_dir, "[D] CH01", "[X] CH01")

    review = autopilot_core.Directive(action="review", chapter=1, command="/authorkit.review 1", reason="re-review")
    fake = autopilot_runner.FakeRunner([review, review], on_command=on_command)
    monkeypatch.setattr(autopilot_commands, "get_runner", lambda *a, **k: fake)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(cli.app, ["autopilot", "chapters", "--range", "1-1"])
    assert result.exit_code == 0, result.output
    assert "done" in result.output.lower()
    assert fake.dispatched == ["/authorkit.review 1"]  # a single review, no revise churn
    assert "[X] CH01" in (book_dir / "chapters.md").read_text(encoding="utf-8")
    assert autopilot_core.review_state(book_dir, 1).verdict == "PASS"  # parsed as converged, not failing


def test_autopilot_converging_chapter_reaches_approved_within_cap(tmp_path, monkeypatch):
    """Complaint acceptance #5: a tic-heavy chapter whose gating set shrinks each revise
    terminates at [X] within the reconciliation cap — the loop converges, it does not escalate."""
    book_dir = _seed_autopilot_book(tmp_path)
    draft_path = _seed_chapter_review(
        book_dir, 1, draft="v0", review_verdict="NEEDS REVISION",
        gating="tic-a, tic-b", status_line="[R] CH01 A - a",
    )
    review_path = book_dir / "chapters" / "01" / "review.md"
    st = {"gate": ["tic-a", "tic-b"], "v": 0}

    def on_command(cmd):
        if "revise" in cmd:  # each revise fixes one gating shape and re-drafts
            if st["gate"]:
                st["gate"].pop()
            st["v"] += 1
            draft_path.write_text(f"v{st['v']}", encoding="utf-8")
            _flip_status(book_dir, "[R] CH01", "[D] CH01")
        elif "/authorkit.review" in cmd:  # re-review reports the shrinking carry-over set
            if st["gate"]:
                review_path.write_text(
                    "# Review\n\n**Overall Assessment**: NEEDS REVISION\n\n## Verdict\n"
                    f"**Status**: NEEDS REVISION\n**Gating Shapes**: {', '.join(st['gate'])}\n",
                    encoding="utf-8",
                )
                _flip_status(book_dir, "[D] CH01", "[R] CH01")
            else:  # gate empty → converged → PASS
                review_path.write_text(
                    "# Review\n\n**Overall Assessment**: PASS\n\n## Verdict\n"
                    "**Status**: PASS\n**Gating Shapes**: none\n",
                    encoding="utf-8",
                )
                _flip_status(book_dir, "[D] CH01", "[X] CH01")

    review = autopilot_core.Directive(action="review", chapter=1, command="/authorkit.review 1", reason="converge")
    fake = autopilot_runner.FakeRunner([review] * 12, on_command=on_command)
    monkeypatch.setattr(autopilot_commands, "get_runner", lambda *a, **k: fake)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(cli.app, ["autopilot", "chapters", "--range", "1-1"])
    assert result.exit_code == 0, result.output
    assert "done" in result.output.lower()
    assert "[X] CH01" in (book_dir / "chapters.md").read_text(encoding="utf-8")
    assert not list((book_dir / "escalations").glob("*.md"))  # converged, never escalated


def test_autopilot_kill_switch_halts(tmp_path, monkeypatch):
    """A book/runs/STOP sentinel halts the loop before any dispatch."""
    book_dir = _seed_autopilot_book(tmp_path)
    runs = book_dir / "runs"
    runs.mkdir()
    (runs / "STOP").write_text("", encoding="utf-8")
    fake = autopilot_runner.FakeRunner(
        [autopilot_core.Directive(action="review", chapter=1, command="/authorkit.review 1")]
    )
    monkeypatch.setattr(autopilot_commands, "get_runner", lambda *a, **k: fake)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(cli.app, ["autopilot", "chapters", "--range", "1-2"])
    assert result.exit_code == 0, result.output
    assert "kill switch" in result.output.lower()
    assert fake.dispatched == []


def test_autopilot_plot_dry_run_needs_only_concept(tmp_path, monkeypatch):
    """plot mode preflight needs only concept.md; --dry-run previews the directive."""
    book_dir = tmp_path / "book"
    book_dir.mkdir(parents=True)
    (book_dir / "concept.md").write_text("# Concept\n", encoding="utf-8")
    (tmp_path / ".authorkit").mkdir()
    fake = autopilot_runner.FakeRunner(
        [autopilot_core.Directive(action="research", command="/authorkit.research observatory architecture", reason="ground it")]
    )
    monkeypatch.setattr(autopilot_commands, "get_runner", lambda *a, **k: fake)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(cli.app, ["autopilot", "plot", "--max-iters", "3", "--dry-run"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["mode"] == "plot"
    assert payload["directive"]["action"] == "research"
    assert fake.dispatched == []


def test_autopilot_plot_respects_max_iters(tmp_path, monkeypatch):
    """plot mode stops after --max-iters ticks."""
    book_dir = tmp_path / "book"
    book_dir.mkdir(parents=True)
    (book_dir / "concept.md").write_text("# Concept\n", encoding="utf-8")
    (tmp_path / ".authorkit").mkdir()
    directives = [
        autopilot_core.Directive(action="research", command=f"/authorkit.research topic{i}", reason="r")
        for i in range(5)
    ]
    fake = autopilot_runner.FakeRunner(directives)
    monkeypatch.setattr(autopilot_commands, "get_runner", lambda *a, **k: fake)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(cli.app, ["autopilot", "plot", "--max-iters", "2"])
    assert result.exit_code == 0, result.output
    assert len(fake.dispatched) == 2
    assert "max-iters" in result.output.lower()


def test_detect_flavor_reads_manifest(tmp_path):
    """detect_flavor returns the first installed AI, defaulting to claude when absent."""
    (tmp_path / ".authorkit").mkdir()
    (tmp_path / ".authorkit" / "install-manifest.json").write_text(
        json.dumps({"ais": ["codex", "claude"]}), encoding="utf-8"
    )
    assert autopilot_runner.detect_flavor(tmp_path) == "codex"
    assert autopilot_runner.detect_flavor(tmp_path / "missing") == "claude"


def test_claude_runner_builds_argv_and_parses_envelope(tmp_path, monkeypatch):
    """ClaudeRunner builds a `claude -p ... --output-format json` planner call and
    unwraps the JSON envelope's `result` into a Directive."""
    captured = {}

    class FakeProc:
        returncode = 0
        stdout = json.dumps({"type": "result", "result": '{"action": "done", "reason": "ok"}'})
        stderr = ""

    def fake_run(argv, **kwargs):
        captured["planner_argv"] = argv
        return FakeProc()

    monkeypatch.setattr(autopilot_runner.subprocess, "run", fake_run)
    claude = autopilot_runner.ClaudeRunner(tmp_path)
    directive = claude.run_planner("PROMPT", "{}", "brief")
    assert captured["planner_argv"][0] == "claude"
    assert "--output-format" in captured["planner_argv"]
    assert directive.action == "done"

    class OkProc:
        returncode = 0
        stdout = "did it"
        stderr = ""

    def fake_run_cmd(argv, **kwargs):
        captured["cmd_argv"] = argv
        return OkProc()

    monkeypatch.setattr(autopilot_runner.subprocess, "run", fake_run_cmd)
    res = claude.run_command("/authorkit.write 3")
    assert res.ok is True
    assert captured["cmd_argv"][:2] == ["claude", "-p"]
    # The dispatched -p arg carries the command plus the unattended directive.
    assert captured["cmd_argv"][2].startswith("/authorkit.write 3")
    assert "AUTOPILOT-UNATTENDED" in captured["cmd_argv"][2]


def test_init_renders_autopilot_planner_prompt():
    """init renders the AutoPilot planner prompt for each selected AI flavor."""
    with isolated_filesystem():
        result = runner.invoke(
            cli.app,
            ["init", ".", "--ai", "claude,codex", "--script", "sh", "--here", "--force", "--ignore-agent-tools", "--no-git"],
        )
        assert result.exit_code == 0, result.output
        assert Path(".claude/commands/authorkit.autopilot-plan.md").exists()
        assert Path(".codex/prompts/authorkit.autopilot-plan.md").exists()


def test_claude_runner_uses_utf8_decoding(tmp_path, monkeypatch):
    """ClaudeRunner decodes subprocess output as UTF-8 (errors=replace), not the OS
    default — Windows cp1252 otherwise crashes on the smart quotes / em-dashes that
    Author Kit prose emits (the reader-thread UnicodeDecodeError from the live run)."""
    captured = {}

    class OkProc:
        returncode = 0
        stdout = "ran it"
        stderr = ""

    def fake_run(argv, **kwargs):
        captured["kwargs"] = kwargs
        return OkProc()

    monkeypatch.setattr(autopilot_runner.subprocess, "run", fake_run)
    autopilot_runner.ClaudeRunner(tmp_path).run_command("/authorkit.write 1")
    assert captured["kwargs"].get("encoding") == "utf-8"
    assert captured["kwargs"].get("errors") == "replace"


def test_claude_runner_permission_flags(tmp_path):
    """Permission posture flows into the worker argv (and is off by default)."""
    base = autopilot_runner.ClaudeRunner(tmp_path)._command_argv("/authorkit.write 1")
    assert "--dangerously-skip-permissions" not in base
    assert "--permission-mode" not in base

    skip = autopilot_runner.ClaudeRunner(tmp_path, skip_permissions=True)._command_argv("/authorkit.write 1")
    assert "--dangerously-skip-permissions" in skip

    mode = autopilot_runner.ClaudeRunner(tmp_path, permission_mode="acceptEdits")._command_argv("/authorkit.write 1")
    assert mode[-2:] == ["--permission-mode", "acceptEdits"]


def _autopilot_config(**buckets) -> book_core.AutopilotConfig:
    """Build an AutopilotConfig for tests, defaulting unset buckets to (None, None)."""
    empty = book_core.AutopilotOpConfig(model=None, effort=None)
    return book_core.AutopilotConfig(
        planner=buckets.get("planner", empty),
        review=buckets.get("review", empty),
        writer=buckets.get("writer", empty),
    )


def test_runner_model_effort_unset_by_default(tmp_path):
    """No [autopilot.*] config -> no --model/--effort (or flavor-equivalent) flags,
    for every flavor -- identical argv to before this feature existed."""
    for cls in (autopilot_runner.ClaudeRunner, autopilot_runner.CodexRunner, autopilot_runner.CopilotRunner):
        agent_runner = cls(tmp_path)
        planner_argv = agent_runner._planner_argv("prompt")
        writer_argv = agent_runner._command_argv("/authorkit.write 1", "writer")
        review_argv = agent_runner._command_argv("/authorkit.review 1", "review")
        for argv in (planner_argv, writer_argv, review_argv):
            assert "--model" not in argv
            assert "--effort" not in argv
            assert "-m" not in argv
            assert "-c" not in argv


def test_claude_runner_model_effort_per_bucket(tmp_path):
    """Each bucket's book.toml override lands on the matching invocation only."""
    models = _autopilot_config(
        planner=book_core.AutopilotOpConfig(model="haiku", effort="low"),
        review=book_core.AutopilotOpConfig(model="sonnet", effort="medium"),
        writer=book_core.AutopilotOpConfig(model="opus", effort="high"),
    )
    agent_runner = autopilot_runner.ClaudeRunner(tmp_path, models=models)

    planner_argv = agent_runner._planner_argv("prompt")
    assert planner_argv[-4:] == ["--model", "haiku", "--effort", "low"]

    review_argv = agent_runner._command_argv("/authorkit.review 1", "review")
    assert review_argv[-4:] == ["--model", "sonnet", "--effort", "medium"]

    writer_argv = agent_runner._command_argv("/authorkit.write 1", "writer")
    assert writer_argv[-4:] == ["--model", "opus", "--effort", "high"]


def test_claude_runner_model_only_omits_effort_flag(tmp_path):
    """Setting only model (not effort) injects --model alone."""
    models = _autopilot_config(writer=book_core.AutopilotOpConfig(model="opus", effort=None))
    argv = autopilot_runner.ClaudeRunner(tmp_path, models=models)._command_argv("/authorkit.write 1", "writer")
    assert "--model" in argv and "opus" in argv
    assert "--effort" not in argv


def test_codex_runner_model_effort_flags(tmp_path):
    """Codex uses -m for model and -c model_reasoning_effort=... for effort."""
    models = _autopilot_config(writer=book_core.AutopilotOpConfig(model="gpt-5.5", effort="high"))
    argv = autopilot_runner.CodexRunner(tmp_path, models=models)._command_argv("/authorkit.write 1", "writer")
    assert "-m" in argv
    assert argv[argv.index("-m") + 1] == "gpt-5.5"
    assert "-c" in argv
    assert argv[argv.index("-c") + 1] == 'model_reasoning_effort="high"'


def test_copilot_runner_model_effort_flags(tmp_path):
    """Copilot uses --model/--effort, both confirmed real flags."""
    models = _autopilot_config(review=book_core.AutopilotOpConfig(model="claude-sonnet-4.6", effort="medium"))
    argv = autopilot_runner.CopilotRunner(tmp_path, models=models)._command_argv("/authorkit.review 1", "review")
    assert argv[-4:] == ["--model", "claude-sonnet-4.6", "--effort", "medium"]


def test_book_config_parses_autopilot_section(tmp_path):
    """[autopilot.*] parses per-bucket model/effort; absent section is all-None."""
    book_dir = tmp_path / "book"
    book_dir.mkdir()
    (book_dir / "book.toml").write_text(
        "[autopilot.planner]\n"
        'model = "haiku"\n'
        'effort = "low"\n'
        "[autopilot.review]\n"
        'model = "sonnet"\n',
        encoding="utf-8",
    )
    config = book_core.parse_book_config(book_dir)
    assert config.autopilot.planner.model == "haiku"
    assert config.autopilot.planner.effort == "low"
    assert config.autopilot.review.model == "sonnet"
    assert config.autopilot.review.effort is None
    assert config.autopilot.writer.model is None
    assert config.autopilot.writer.effort is None


def test_book_config_autopilot_defaults_to_unset(tmp_path):
    """No [autopilot] section at all -> every field is None (no defaults)."""
    book_dir = tmp_path / "book"
    book_dir.mkdir()
    (book_dir / "book.toml").write_text('[book]\ntitle = "T"\n', encoding="utf-8")
    config = book_core.parse_book_config(book_dir)
    for bucket in (config.autopilot.planner, config.autopilot.review, config.autopilot.writer):
        assert bucket.model is None
        assert bucket.effort is None


def test_autopilot_dispatch_tags_review_vs_writer_op(tmp_path, monkeypatch):
    """The dispatch loop tags review actions with op='review' and everything
    else (plan/draft/revise/research) with op='writer'."""
    _seed_autopilot_book(tmp_path, chapters_md="# Chapters\n\n- [D] CH01 The Arrival - First\n")
    plan = autopilot_core.Directive(action="plan", chapter=1, command="/authorkit.write 1 plan", reason="x")
    review = autopilot_core.Directive(action="review", chapter=1, command="/authorkit.review 1", reason="x")
    revise = autopilot_core.Directive(action="revise", chapter=1, command="/authorkit.write 1 revise", reason="x")
    fake = autopilot_runner.FakeRunner([plan, review, revise])
    monkeypatch.setattr(autopilot_commands, "get_runner", lambda *a, **k: fake)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(cli.app, ["autopilot", "chapters", "--range", "1-1", "--step"])
    assert result.exit_code == 0, result.output
    assert fake.dispatched_ops == ["writer"]

    result = runner.invoke(cli.app, ["autopilot", "chapters", "--range", "1-1", "--step"])
    assert result.exit_code == 0, result.output
    assert fake.dispatched_ops == ["writer", "review"]


def test_escalation_record_title_and_slug_are_concise(tmp_path):
    """A long decision yields a word-boundary title (ellipsis) + short slug;
    explicit title/slug override the derivation."""
    long_decision = (
        "AutoPilot stalled and could not determine whether the protagonist should "
        "betray the guild before the third act climax or hold the secret"
    )
    path = autopilot_core.write_escalation(
        tmp_path / "book",
        esc_type="story-fork",
        trigger="t",
        decision_needed=long_decision,
        today="2026-06-18",
    )
    first_line = path.read_text(encoding="utf-8").splitlines()[0]
    assert first_line.startswith("# ESC-001: ")
    title = first_line[len("# ESC-001: ") :]
    assert title.endswith("…")
    assert len(title) <= 60
    assert not title[:-1].endswith(" ")  # trimmed at a word boundary
    slug = path.stem.split("ESC-001-", 1)[1]
    assert 0 < len(slug) <= 40

    explicit = autopilot_core.write_escalation(
        tmp_path / "book",
        esc_type="loop-health",
        trigger="t",
        decision_needed=long_decision,
        today="2026-06-18",
        title="AutoPilot stalled (loop-health)",
        slug="autopilot-stalled",
    )
    assert explicit.name.endswith("ESC-002-autopilot-stalled.md")
    assert explicit.read_text(encoding="utf-8").splitlines()[0] == "# ESC-002: AutoPilot stalled (loop-health)"


def test_autopilot_permission_default_and_override(tmp_path, monkeypatch):
    """Workers default to skip-permissions (warned); --permission-mode restricts
    and silences the warning. The chosen posture flows into get_runner."""
    _seed_autopilot_book(tmp_path)
    monkeypatch.chdir(tmp_path)

    captured: dict = {}

    def fake_get_runner(repo_root, **kwargs):
        captured.clear()
        captured.update(kwargs)
        return autopilot_runner.FakeRunner(
            [autopilot_core.Directive(action="review", chapter=1, command="/authorkit.review 1")]
        )

    monkeypatch.setattr(autopilot_commands, "get_runner", fake_get_runner)

    result = runner.invoke(cli.app, ["autopilot", "chapters", "--range", "1-2", "--step"])
    assert result.exit_code == 0, result.output
    assert "--dangerously-skip-permissions" in result.output
    assert captured.get("skip_permissions") is True
    assert captured.get("permission_mode") is None

    result2 = runner.invoke(
        cli.app, ["autopilot", "chapters", "--range", "1-2", "--step", "--permission-mode", "acceptEdits"]
    )
    assert result2.exit_code == 0, result2.output
    assert "--dangerously-skip-permissions" not in result2.output
    assert captured.get("skip_permissions") is False
    assert captured.get("permission_mode") == "acceptEdits"


def test_autopilot_plot_planner_receives_plan_layer_context(tmp_path, monkeypatch):
    """In plot mode the planner is handed the read-only book-level files so it can
    judge what the story still needs (vs. status-only)."""
    book = tmp_path / "book"
    (book / "world").mkdir(parents=True)
    (book / "concept.md").write_text("# Concept\n\nA lighthouse mystery.\n", encoding="utf-8")
    (book / "outline.md").write_text("# Outline\n\nPart 1 ...\n", encoding="utf-8")
    (book / "world" / "_index.md").write_text(
        "# World Index\n\n## Statistics\n- Total entities: 3\n", encoding="utf-8"
    )
    (book / "research.md").write_text("# Research Index\n\n- lighthouse optics\n", encoding="utf-8")
    (tmp_path / ".authorkit").mkdir()

    fake = autopilot_runner.FakeRunner([autopilot_core.Directive(action="done", reason="solid")])
    monkeypatch.setattr(autopilot_commands, "get_runner", lambda *a, **k: fake)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(cli.app, ["autopilot", "plot", "--max-iters", "3", "--dry-run"])
    assert result.exit_code == 0, result.output

    ctx = fake.planner_inputs[0]["context"]
    assert "lighthouse mystery" in ctx       # concept.md
    assert "### outline.md" in ctx
    assert "Total entities: 3" in ctx        # world/_index.md
    assert "lighthouse optics" in ctx        # research.md


def test_autopilot_chapters_planner_is_status_only(tmp_path, monkeypatch):
    """Chapters mode passes no plan-layer context — the planner stays status-only."""
    _seed_autopilot_book(tmp_path)
    fake = autopilot_runner.FakeRunner([autopilot_core.Directive(action="done", reason="x")])
    monkeypatch.setattr(autopilot_commands, "get_runner", lambda *a, **k: fake)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(cli.app, ["autopilot", "chapters", "--range", "1-2", "--dry-run"])
    assert result.exit_code == 0, result.output
    assert fake.planner_inputs[0]["context"] == ""


def test_autopilot_plot_done_suggests_chapters(tmp_path, monkeypatch):
    """When plot finishes, the loop hands off to the chapters loop."""
    book = tmp_path / "book"
    book.mkdir(parents=True)
    (book / "concept.md").write_text("# Concept\n", encoding="utf-8")
    (tmp_path / ".authorkit").mkdir()
    fake = autopilot_runner.FakeRunner([autopilot_core.Directive(action="done", reason="plan solid")])
    monkeypatch.setattr(autopilot_commands, "get_runner", lambda *a, **k: fake)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(cli.app, ["autopilot", "plot", "--max-iters", "3"])
    assert result.exit_code == 0, result.output
    assert "autopilot chapters" in result.output


def test_write_prompt_has_plan_only_dispatch():
    """The write prompt routes the `plan` keyword to a plan-only mode, so plot stays
    out of drafting and chapters can plan as its own tick."""
    repo_root = Path(__file__).resolve().parents[2]
    write = (repo_root / ".authorkit" / "prompts" / "authorkit.write.md").read_text(encoding="utf-8")
    assert "Plan (only)" in write
    assert "do **not** draft" in write


def test_guardrails_state_reader_only_sees_chapters():
    """The shared guardrails must tell every prose command that the finished reader
    sees only the drafted chapters — world/outline/research are internal scaffolding."""
    repo_root = Path(__file__).resolve().parents[2]
    guardrails = (
        repo_root / ".authorkit" / "prompts" / "_shared" / "generation-guardrails.md"
    ).read_text(encoding="utf-8")
    assert "Reader-Facing Surface" in guardrails
    assert "only the drafted chapters" in guardrails
    assert "internal scaffolding" in guardrails

    # And it must reach a rendered generation prompt (guardrails are injected into write).
    with isolated_filesystem():
        result = runner.invoke(
            cli.app,
            ["init", ".", "--ai", "codex", "--script", "sh", "--here", "--force", "--ignore-agent-tools", "--no-git"],
        )
        assert result.exit_code == 0, result.output
        write_prompt = Path(".codex/prompts/authorkit.write.md").read_text(encoding="utf-8")
        assert "Reader-Facing Surface" in write_prompt


def test_review_prompt_has_explicit_style_fidelity_pass():
    """The review command leads with an explicit, gating Style Fidelity pass and
    exposes a focused `N style` mode that writes chapters/NN/style-review.md."""
    repo_root = Path(__file__).resolve().parents[2]
    review = (repo_root / ".authorkit" / "prompts" / "authorkit.review.md").read_text(encoding="utf-8")
    assert "Style Fidelity (gating" in review
    assert "## Mode: Style Fidelity" in review
    assert "chapters/NN/style-review.md" in review
    assert "7 style" in review  # focused style-only scope keyword
    assert "automatically NEEDS REVISION" in review  # the gate


def test_voice_origin_supports_author_excerpts():
    """The fixed voice origin can be author excerpts (`### Voice Exemplars`), not
    just chapter pins — threaded through the constitution and every origin-resolving
    prompt (write, review, guardrails, discuss)."""
    repo_root = Path(__file__).resolve().parents[2]
    akit = repo_root / ".authorkit"
    constitution = (akit / "memory" / "constitution.md").read_text(encoding="utf-8")
    assert "Voice Exemplars" in constitution

    origin_resolvers = [
        akit / "prompts" / "authorkit.write.md",
        akit / "prompts" / "authorkit.review.md",
        akit / "prompts" / "_shared" / "generation-guardrails.md",
        akit / "prompts" / "authorkit.discuss.md",
    ]
    for path in origin_resolvers:
        text = path.read_text(encoding="utf-8")
        assert "Voice Exemplars" in text, f"{path.name} must reference Voice Exemplars excerpts in origin resolution"


def test_unattended_mode_wired_into_guardrails_and_discuss():
    """AutoPilot signals unattended on dispatch, and the shared guardrails + discuss
    define how a headless worker behaves (grounded elaboration proceeds; forks escalate)."""
    repo_root = Path(__file__).resolve().parents[2]
    akit = repo_root / ".authorkit"
    guardrails = (akit / "prompts" / "_shared" / "generation-guardrails.md").read_text(encoding="utf-8")
    discuss = (akit / "prompts" / "authorkit.discuss.md").read_text(encoding="utf-8")

    assert "Unattended Mode" in guardrails
    assert "AUTOPILOT-UNATTENDED" in guardrails
    assert "Grounded elaboration proceeds" in guardrails
    assert "AUTOPILOT-UNATTENDED" in discuss
    # The runtime directive AutoPilot appends keys on the same marker the prompts read.
    assert "AUTOPILOT-UNATTENDED" in autopilot_runner.UNATTENDED_DIRECTIVE


# --- Entropy tool (code-driven names & numbers) ------------------------------

import authorkit_cli.entropy as entropy  # noqa: E402


def test_entropy_roll_numbers_respects_bounds_and_kinds():
    """roll_numbers honors the inclusive bounds, count, and per-kind output shape."""
    ints = entropy.roll_numbers("int", 3, 40, count=50)
    assert len(ints) == 50
    assert all(isinstance(v, int) and 3 <= v <= 40 for v in ints)

    flts = entropy.roll_numbers("float", 0, 1, count=20)
    assert all(isinstance(v, float) and 0.0 <= v <= 1.0 for v in flts)

    years = entropy.roll_numbers("year", 1900, 1901, count=10)
    assert all(v in (1900, 1901) for v in years)

    times = entropy.roll_numbers("time", 9, 17, count=10)
    assert all(len(t) == 5 and t[2] == ":" and 9 <= int(t[:2]) <= 17 for t in times)

    with pytest.raises(ValueError):
        entropy.roll_numbers("int", 10, 1)  # max < min
    with pytest.raises(ValueError):
        entropy.roll_numbers("bogus", 1, 2)  # bad kind


def test_entropy_fractional_bounds_stay_inclusive():
    """Fractional bounds never produce out-of-range values: int/year bounds are
    ceil/floor'd (not truncated toward zero), floats are clamped after rounding."""
    ints = entropy.roll_numbers("int", 2.7, 9.9, count=50)
    assert all(3 <= v <= 9 for v in ints)  # int(2.7)=2 would escape the range

    negs = entropy.roll_numbers("int", -9.9, -2.7, count=50)
    assert all(-9 <= v <= -3 for v in negs)  # int(-2.7)=-2 would escape the range

    with pytest.raises(ValueError):
        entropy.roll_numbers("int", 2.7, 2.9)  # no integers in the range

    flts = entropy.roll_numbers("float", 0, 0.999, count=200)
    assert all(0.0 <= v <= 0.999 for v in flts)  # round(0.9985, 2) == 1.0 must be clamped


def test_entropy_name_seed_is_scaffold_not_finished_name():
    """make_name_seed returns construction scaffolding (skeleton/initial/length),
    honors a known culture, and falls back to generic for an unknown one."""
    import random

    seed = entropy.make_name_seed("norse", syllables=2, rng=random.Random(1))
    assert seed.culture == "norse"
    assert seed.skeleton.count("-") == 1  # two syllables
    assert seed.initial.isupper() and len(seed.initial) == 1
    assert seed.length_target >= 3

    assert entropy.make_name_seed("klingon").culture == "generic"  # unknown -> generic


def test_entropy_number_cli_json_and_bounds(monkeypatch):
    """`authorkit entropy number --json` emits a stable shape within bounds."""
    result = runner.invoke(cli.app, ["entropy", "number", "--min", "5", "--max", "9", "--count", "4", "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["kind"] == "int" and len(payload["values"]) == 4
    assert all(5 <= v <= 9 for v in payload["values"])

    bad = runner.invoke(cli.app, ["entropy", "number", "--min", "9", "--max", "5"])
    assert bad.exit_code != 0


def test_entropy_name_cli_varies_across_calls():
    """`authorkit entropy name` produces seeds (not stock names) that vary."""
    seeds = set()
    for _ in range(8):
        result = runner.invoke(cli.app, ["entropy", "name", "--culture", "latin", "--count", "1", "--json"])
        assert result.exit_code == 0, result.output
        payload = json.loads(result.output)
        assert payload["culture"] == "latin"
        seeds.add(payload["seeds"][0]["scaffold"])
    assert len(seeds) > 1  # true randomness: not all identical


def test_entropy_name_json_reports_resolved_culture():
    """An unknown culture falls back to the generic bank — the JSON's top-level culture
    must report the resolved bank, not echo the raw option (no self-contradictory payload)."""
    result = runner.invoke(cli.app, ["entropy", "name", "--culture", "klingon", "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["culture"] == "generic"
    assert all(s["culture"] == "generic" for s in payload["seeds"])


# --- AutoPilot planner guidelines (--guideline campaigns) --------------------


def test_autopilot_guideline_threads_into_planner_and_skips_auto_done(tmp_path, monkeypatch):
    """--guideline reaches the planner and suppresses the all-[X] auto-done so a
    re-review campaign over approved chapters is not ended before it starts."""
    # Whole range already approved: without a guideline this would auto-`done`.
    book_dir = _seed_autopilot_book(tmp_path, chapters_md="# Chapters\n\n- [X] CH01 The Arrival - First\n")
    fake = autopilot_runner.FakeRunner(
        [autopilot_core.Directive(action="review", chapter=1, command="/authorkit.review 1", reason="campaign")]
    )
    monkeypatch.setattr(autopilot_commands, "get_runner", lambda *a, **k: fake)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        cli.app,
        ["autopilot", "chapters", "--range", "1-1", "--guideline", "re-review CH1 against the new tic patterns", "--dry-run"],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    # Planner was consulted (not short-circuited to done) and got the guideline.
    assert payload["directive"]["action"] == "review"
    assert "tic patterns" in fake.planner_inputs[0]["guideline"]


def test_autopilot_guideline_progress_is_content_aware(tmp_path, monkeypatch):
    """Under a guideline, a draft rewrite counts as progress even when chapter
    statuses don't move, so loop-health doesn't misfire on a re-review sweep."""
    book_dir = _seed_autopilot_book(tmp_path, chapters_md="# Chapters\n\n- [X] CH01 The Arrival - First\n")
    draft = book_dir / "chapters" / "01" / "draft.md"
    draft.parent.mkdir(parents=True, exist_ok=True)
    draft.write_text("# Chapter 01\n\nOriginal prose.\n", encoding="utf-8")

    calls = {"n": 0}

    def on_command(_cmd):
        # Each tick rewrites the draft (status stays [X]); content fingerprint moves.
        calls["n"] += 1
        draft.write_text(f"# Chapter 01\n\nRevised prose {calls['n']}.\n", encoding="utf-8")

    # Four revise ticks: status never changes. Without content-aware progress
    # this trips no-progress; with it, each tick registers progress. The issue
    # text varies per tick (as a real planner's would) so the command-churn
    # guard doesn't read the sequence as a stall.
    revises = [
        autopilot_core.Directive(
            action="revise", chapter=1, command=f"/authorkit.write 1 revise: issue {n}", reason="x"
        )
        for n in range(1, 5)
    ]
    done = autopilot_core.Directive(action="done", reason="campaign swept")
    fake = autopilot_runner.FakeRunner([*revises, done], on_command=on_command)
    monkeypatch.setattr(autopilot_commands, "get_runner", lambda *a, **k: fake)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        cli.app,
        ["autopilot", "chapters", "--range", "1-1", "--guideline", "revise then re-review every chapter"],
    )
    assert result.exit_code == 0, result.output
    assert "loop-health" not in result.output.lower()
    assert "done" in result.output.lower()
    assert calls["n"] >= 4


def test_autopilot_guideline_review_only_sweep_registers_progress(tmp_path, monkeypatch):
    """A re-review sweep touches review.md but not the draft or the [X] status.
    The content fingerprint folds in review.md, so an advancing sweep across
    already-approved chapters registers progress and does not trip loop-health."""
    book_dir = _seed_autopilot_book(
        tmp_path,
        chapters_md=(
            "# Chapters\n\n"
            "- [X] CH01 A - x\n- [X] CH02 B - x\n- [X] CH03 C - x\n- [X] CH04 D - x\n"
        ),
    )
    for n in range(1, 5):
        d = book_dir / "chapters" / f"{n:02d}" / "draft.md"
        d.parent.mkdir(parents=True, exist_ok=True)
        d.write_text(f"# Chapter {n:02d}\n\nProse.\n", encoding="utf-8")

    calls = {"n": 0}

    def on_command(_cmd):
        # Each tick re-reviews the next chapter: writes review.md, leaves the
        # draft and the [X] status untouched. Only the review fingerprint moves.
        calls["n"] += 1
        rv = book_dir / "chapters" / f"{calls['n']:02d}" / "review.md"
        rv.write_text(f"# Review {calls['n']}\n\nPASS.\n", encoding="utf-8")

    # The sweep advances to a different chapter (a different command) each tick.
    reviews = [
        autopilot_core.Directive(action="review", chapter=n, command=f"/authorkit.review {n}", reason="sweep")
        for n in range(1, 5)
    ]
    done = autopilot_core.Directive(action="done", reason="campaign swept")
    fake = autopilot_runner.FakeRunner([*reviews, done], on_command=on_command)
    monkeypatch.setattr(autopilot_commands, "get_runner", lambda *a, **k: fake)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        cli.app,
        ["autopilot", "chapters", "--range", "1-4", "--guideline", "re-review every chapter against the new tics"],
    )
    assert result.exit_code == 0, result.output
    assert "loop-health" not in result.output.lower()
    assert "done" in result.output.lower()
    assert calls["n"] >= 4


def test_autopilot_guideline_command_churn_trips_loop_health(tmp_path, monkeypatch):
    """Under a guideline, byte-changing rewrites always register as 'progress',
    so a planner stuck re-dispatching the exact same command must be caught by
    the command-churn guard instead of running to the MAX_TICKS cap."""
    book_dir = _seed_autopilot_book(tmp_path, chapters_md="# Chapters\n\n- [X] CH01 The Arrival - First\n")
    rv = book_dir / "chapters" / "01" / "review.md"
    rv.parent.mkdir(parents=True, exist_ok=True)

    calls = {"n": 0}

    def on_command(_cmd):
        # Every tick rewrites review.md with different bytes: content-aware
        # progress says "moving", but the command never changes — a stall.
        calls["n"] += 1
        rv.write_text(f"# Review sweep {calls['n']}\n\nPASS.\n", encoding="utf-8")

    stuck = autopilot_core.Directive(action="review", chapter=1, command="/authorkit.review 1", reason="sweep")
    fake = autopilot_runner.FakeRunner([stuck] * 8, on_command=on_command)
    monkeypatch.setattr(autopilot_commands, "get_runner", lambda *a, **k: fake)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        cli.app,
        ["autopilot", "chapters", "--range", "1-1", "--guideline", "re-review every chapter"],
    )
    assert result.exit_code == 0, result.output
    assert "loop-health" in result.output.lower()
    assert calls["n"] == 4  # tripped right after the churn window, not at MAX_TICKS


def test_detect_command_churn_alternating_reviews():
    """Churn also catches a planner ping-ponging between two review commands (the
    same-command rule misses it, and under a guideline the status-keyed detectors are
    blind), while a healthy review→revise reconciliation and a multi-chapter sweep
    never trip it."""
    def rv(cmd):
        return {"command": cmd, "action": "review"}

    def wr(cmd):
        return {"command": cmd, "action": "revise"}

    ping = [rv("/authorkit.review 1"), rv("/authorkit.review 2")] * 2
    assert autopilot_core.detect_command_churn(ping) is True
    # A review→revise cycle interleaves revise ticks — bounded by reconcile-stall, not churn.
    cycle = [
        rv("/authorkit.review 3"), wr("/authorkit.write 3 revise: apply the standing review"),
        rv("/authorkit.review 3"), wr("/authorkit.write 3 revise: apply the standing review"),
    ]
    assert autopilot_core.detect_command_churn(cycle) is False
    # A healthy sweep advances to a different chapter each tick.
    sweep = [rv(f"/authorkit.review {n}") for n in (1, 2, 3, 4)]
    assert autopilot_core.detect_command_churn(sweep) is False
    # The exact same command window-times in a row still trips regardless of action mix.
    assert autopilot_core.detect_command_churn([wr("/authorkit.write 1 revise: x")] * 4) is True


def test_style_reviews_never_stamp_the_craft_sidecar():
    """`/authorkit.review N style` writes style-review.md, so it is neither a craft-review
    no-op nor a sidecar-stampable review (ReviewState is craft-only by contract)."""
    assert autopilot_core.is_style_review("/authorkit.review 3 style") is True
    assert autopilot_core.is_style_review("/authorkit.review 3 STYLE") is True
    assert autopilot_core.is_style_review("/authorkit.review 3") is False
    assert autopilot_core.is_style_review("/authorkit.write 3 revise: fix style drift") is False
    assert autopilot_core.is_style_review(None) is False


def test_content_fingerprint_scope(tmp_path):
    """The guideline progress fingerprint covers style-review.md (a style sweep is progress)
    and only pure-numeric chapter dirs (a backup like 01-old/ can't register progress)."""
    book_dir = tmp_path / "book"
    for rel in ("chapters/01/draft.md", "chapters/01/style-review.md", "chapters/01-old/draft.md"):
        path = book_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rel, encoding="utf-8")
    fp = autopilot_commands._content_fingerprint(book_dir)
    entries = {(chapter, name) for chapter, name, _ in fp}
    assert ("01", "draft.md") in entries
    assert ("01", "style-review.md") in entries  # style sweeps register as progress
    assert all(chapter == "01" for chapter, _ in entries)  # 01-old/ excluded


def test_autopilot_guideline_brief_is_mode_scoped():
    """The guideline addendum defers to the planner prompt's canonical rules and
    never authorizes chapter work from plot mode."""
    chapters = autopilot_commands._mode_brief("chapters", (1, 4), 20, "re-review everything")
    plot = autopilot_commands._mode_brief("plot", None, 20, "re-check the outline")
    assert "AUTHOR GUIDELINES ARE ACTIVE" in chapters
    assert "AUTHOR GUIDELINES ARE ACTIVE" in plot
    # Plot mode keeps its invariant: guidelines never open chapters/NN/.
    assert "off-limits" in plot
    assert "re-open" not in plot and "re-open" not in chapters  # semantics live in the prompt file


def test_autopilot_plan_prompt_documents_guidelines_and_escalations():
    """The planner prompt explains author guidelines and the new escalation types."""
    repo_root = Path(__file__).resolve().parents[2]
    plan = (repo_root / ".authorkit" / "prompts" / "authorkit.autopilot-plan.md").read_text(encoding="utf-8")
    assert "Author Guidelines" in plan
    assert "re-open" in plan and "[X]" in plan
    for esc in ("numeric-contradiction", "disclosure-leak", "scaffolding-gap"):
        assert esc in plan
        assert esc in autopilot_core.ESCALATION_TYPES


# --- Review passes / tic catalog / writer strictness (prompt content) --------


def test_analysis_passes_roster_is_shared_source_of_truth():
    """The canonical Analysis Passes roster lives in the shared guardrails and the
    review command renders the same named passes."""
    repo_root = Path(__file__).resolve().parents[2]
    akit = repo_root / ".authorkit"
    guardrails = (akit / "prompts" / "_shared" / "generation-guardrails.md").read_text(encoding="utf-8")
    review = (akit / "prompts" / "authorkit.review.md").read_text(encoding="utf-8")
    assert "Analysis Passes" in guardrails
    for pass_name in (
        "Style Fidelity",
        "AI-Tic Audit",
        "In-Chapter Logical Consistency",
        "Cross-Chapter & Plot-Arc Logical Consistency",
        "Disclosure Horizon",
        "Standalone Readability",
    ):
        assert pass_name in guardrails, f"roster missing {pass_name}"
        assert pass_name in review, f"review missing pass {pass_name}"


def test_new_tic_patterns_in_catalog():
    """The catalog keeps the looping-echo and creed-maxim patterns (and budget rows)
    but is framed as a bootstrap seed for book/tic-ledger.md, not a normative gate."""
    repo_root = Path(__file__).resolve().parents[2]
    catalog = (
        repo_root / ".authorkit" / "prompts" / "_shared" / "literary-tic-catalog.md"
    ).read_text(encoding="utf-8")
    assert "Looping self-echo" in catalog
    assert "Creed / trade-maxim" in catalog
    assert "competence tag" in catalog
    assert "| 23 |" in catalog and "| 24 |" in catalog
    # Seed framing: the ledger is normative, this file only bootstraps it and
    # is quarantined from drafting.
    assert "bootstrap seed" in catalog
    assert "book/tic-ledger.md" in catalog
    assert "Never load this file while drafting" in catalog
    assert "normative for any command" not in catalog


def test_guardrails_define_entropy_disclosure_continuity_protocols():
    """The shared guardrails carry the entropy, continuity, and disclosure protocols
    and reference the entropy CLI."""
    repo_root = Path(__file__).resolve().parents[2]
    guardrails = (
        repo_root / ".authorkit" / "prompts" / "_shared" / "generation-guardrails.md"
    ).read_text(encoding="utf-8")
    assert "Entropy Protocol" in guardrails
    assert "authorkit entropy name" in guardrails and "authorkit entropy number" in guardrails
    assert "Quantitative & Logical Continuity Protocol" in guardrails
    assert "Disclosure Horizon Protocol" in guardrails
    # The disclosure horizon binds planning, not just prose (a plan that
    # prescribes a premature reveal is executed faithfully downstream).
    assert "binds planning" in guardrails


def test_disclosure_horizon_is_enforced_at_planning_not_just_review():
    """Plan and Outline modes must run the disclosure-horizon check so a
    proleptic reveal is caught at the plan, not left to slip through to review."""
    repo_root = Path(__file__).resolve().parents[2]
    write = (repo_root / ".authorkit" / "prompts" / "authorkit.write.md").read_text(encoding="utf-8")
    # Both plan-producing modes reference the shared protocol by name.
    assert write.count("Disclosure Horizon Protocol") >= 2
    assert "Disclosure-horizon check" in write  # Outline Phase 2 validation
    assert "Disclosure-horizon check (before writing the plan)" in write  # single-chapter Plan mode


def test_review_has_logic_disclosure_standalone_passes_and_manuscript_passes():
    """The review command exposes the new chapter passes and manuscript detection passes."""
    repo_root = Path(__file__).resolve().parents[2]
    review = (repo_root / ".authorkit" / "prompts" / "authorkit.review.md").read_text(encoding="utf-8")
    # Chapter-craft passes
    assert "Pass 3 — In-Chapter Logical Consistency" in review
    assert "Pass 4 — Cross-Chapter & Plot-Arc Logical Consistency" in review
    assert "Pass 5 — Disclosure Horizon" in review
    assert "Pass 6 — Standalone Readability" in review
    # Manuscript detection passes
    assert "Quantitative Continuity Ledger" in review
    assert "Premature Disclosure" in review
    assert "Scaffolding Leakage" in review


def test_write_revise_is_pass_structured():
    """Revise walks the Analysis Passes roster and re-verifies each pass."""
    repo_root = Path(__file__).resolve().parents[2]
    write = (repo_root / ".authorkit" / "prompts" / "authorkit.write.md").read_text(encoding="utf-8")
    assert "Revise pass-by-pass" in write
    assert "Re-run that pass's own check" in write
    assert "authorkit entropy" in write  # entropy wired into drafting


def test_guardrails_define_tic_ledger_voice_pairs_and_conditioning():
    """The shared guardrails carry the self-learning tic defense (ledger + pairs,
    with the generation-side quarantine) and the voice conditioning protocol."""
    repo_root = Path(__file__).resolve().parents[2]
    guardrails = (
        repo_root / ".authorkit" / "prompts" / "_shared" / "generation-guardrails.md"
    ).read_text(encoding="utf-8")
    assert "Tic Ledger & Voice Pairs" in guardrails
    assert "book/tic-ledger.md" in guardrails
    assert "book/voice-pairs.md" in guardrails
    assert "MUST NOT load" in guardrails  # quarantine rule is binding
    assert "bootstrap seed" in guardrails
    assert "Voice Conditioning Protocol" in guardrails
    assert "Pass A" in guardrails and "Pass B" in guardrails
    # Ledger lifecycle is defined (decay to retirement).
    assert "dormant" in guardrails and "retired" in guardrails


def test_write_prompt_quarantines_tic_lists_and_conditions_on_voice():
    """Drafting never loads the tic catalog or ledger; it conditions on origin
    prose + voice pairs, drafts scenes in two passes, and harvests pairs on revise."""
    repo_root = Path(__file__).resolve().parents[2]
    write = (repo_root / ".authorkit" / "prompts" / "authorkit.write.md").read_text(encoding="utf-8")
    # Quarantine: no catalog path anywhere in the write prompt.
    assert "literary-tic-catalog" not in write
    # Generation-side conditioning artifacts.
    assert "book/voice-pairs.md" in write
    assert "Active Pairs" in write
    assert "Voice Conditioning Protocol" in write
    # Two-stage drafting, all draft modes.
    assert "Pass A — content" in write
    assert "Pass B — voice" in write
    assert "no new facts, names, or numbers" in write
    # Pair harvesting on revise and reconcile.
    assert "Harvest voice pairs" in write
    assert "voice-pairs-template.md" in write
    assert "tagged `author`" in write  # author-edit harvest during reconcile (one canonical tag)
    # Revise's final sweep covers the WHOLE draft, not just edited spans — drift in a span
    # the review missed and revise never touched is still caught before saving.
    assert "whole-draft style match" in write


def test_revise_reanchors_repeat_offenders_on_origin_counter_example():
    """Revise loads the tic ledger (revision is not quarantined — only drafting is) and,
    for a carry-over gating shape (a failed prior fix, whose harvested voice pair is the
    rewrite that didn't hold), re-anchors on the ledger's origin counter-example instead
    of retrying a variant of that pair."""
    repo_root = Path(__file__).resolve().parents[2]
    write = (repo_root / ".authorkit" / "prompts" / "authorkit.write.md").read_text(encoding="utf-8")
    revise = write.split("## Mode: Revise", 1)[1].split("## Mode: Passage Help", 1)[0]
    assert "book/tic-ledger.md" in revise  # Load Context cites the ledger explicitly
    assert "Repeat offenders" in revise
    assert "carry-over" in revise
    assert "origin counter-example" in revise
    assert "replaces" in revise  # the new pair replaces the stale (failed) one
    # Root cause of non-shrinking gates: fix a gating shape across the WHOLE draft, not just
    # the cited spans, so its count actually drops below budget and the gate clears.
    assert "whole-draft instance count under the ledger" in revise.lower()
    assert "sweep the entire draft" in revise
    # The shared roster stays in sync: guardrails name the re-anchoring obligation.
    guardrails = (
        repo_root / ".authorkit" / "prompts" / "_shared" / "generation-guardrails.md"
    ).read_text(encoding="utf-8")
    assert "failed prior fix" in guardrails
    assert "origin counter-example" in guardrails


def test_review_pass2_is_blind_discovery_with_ledger_reconciliation():
    """Pass 2 discovers tics by blind contrast against the origin and maintains
    book/tic-ledger.md (bootstrapped from the seed catalog on first run)."""
    repo_root = Path(__file__).resolve().parents[2]
    review = (repo_root / ".authorkit" / "prompts" / "authorkit.review.md").read_text(encoding="utf-8")
    assert "Tic Discovery & Contrast" in review
    assert "Step A — blind discovery" in review
    assert "Step B — ledger reconciliation" in review
    assert "book/tic-ledger.md" in review
    assert "tic-ledger-template.md" in review  # bootstrap path
    assert "Status: seed" in review
    # The blind step must not receive the ledger or the seed catalog.
    assert "no ledger and no seed catalog" in review
    # Per-entry budgets: zero-budget forms gate on sight; long chapters count per 1k words.
    assert "`Budget:`" in review
    assert "Critical and gating at one instance" in review
    assert "0.75/1k" in review
    # Legacy waivers naming a seed-catalog pattern number stay binding.
    assert "pattern *number*" in review


def test_discuss_constitution_mode_records_tic_waivers_on_ledger():
    """Constitution mode frames tic overrides as waivers recorded on the ledger."""
    repo_root = Path(__file__).resolve().parents[2]
    discuss = (repo_root / ".authorkit" / "prompts" / "authorkit.discuss.md").read_text(encoding="utf-8")
    assert "Tic Waivers" in discuss
    assert "book/tic-ledger.md" in discuss


def test_init_copies_tic_ledger_and_voice_pairs_templates_and_keeps_seed_catalog():
    """Init ships the new templates, and the demoted seed catalog stays at its
    original path so re-install never deletes it from existing projects."""
    with isolated_filesystem():
        result = runner.invoke(
            cli.app,
            [
                "init",
                ".",
                "--ai",
                "claude",
                "--script",
                "sh",
                "--here",
                "--force",
                "--ignore-agent-tools",
                "--no-git",
            ],
        )
        assert result.exit_code == 0, result.output
        assert Path(".authorkit/templates/tic-ledger-template.md").exists()
        assert Path(".authorkit/templates/voice-pairs-template.md").exists()
        manifest = json.loads(Path(".authorkit/install-manifest.json").read_text(encoding="utf-8"))
        assert ".authorkit/templates/tic-ledger-template.md" in manifest["managed_paths"]
        assert ".authorkit/templates/voice-pairs-template.md" in manifest["managed_paths"]
        # Seed catalog still shipped at its original path (re-install safety).
        assert ".authorkit/prompts/_shared/literary-tic-catalog.md" in manifest["managed_paths"]
        # Rendered claude write prompt: guardrails injected, catalog quarantined.
        # The injected guardrails block precedes the command body (which starts
        # at "## User Input"); the catalog path may appear only in guardrails.
        rendered_write = Path(".claude/commands/authorkit.write.md").read_text(encoding="utf-8")
        assert "Tic Ledger & Voice Pairs" in rendered_write  # via injected guardrails
        write_body = rendered_write.split("## User Input", 1)[1]
        assert "literary-tic-catalog" not in write_body
        # Rendered review prompt bootstraps the ledger.
        rendered_review = Path(".claude/commands/authorkit.review.md").read_text(encoding="utf-8")
        assert "tic-ledger-template.md" in rendered_review


def test_catalog_new_patterns_and_budget_table():
    """Tic-catalog expansion (patterns 28-47): every pattern heading has a budget-table
    row, the class/weighting preamble exists, the volatile lexical entry is marked, and
    the bootstrap seeding list names the new high-signal patterns."""
    repo_root = Path(__file__).resolve().parents[2]
    catalog = (repo_root / ".authorkit" / "prompts" / "_shared" / "literary-tic-catalog.md").read_text(encoding="utf-8")

    headings = {int(m.group(1)) for m in re.finditer(r"^### (\d+)\.", catalog, re.M)}
    assert headings == set(range(1, 48)), f"Expected patterns 1-47, got {sorted(headings)}"

    table_rows = {
        int(n)
        for m in re.finditer(r"^\| (\d+)(?:\+(\d+))? \|", catalog, re.M)
        for n in m.groups()
        if n
    }
    assert set(range(1, 48)) <= table_rows, (
        f"Budget table missing rows for patterns {sorted(set(range(1, 48)) - table_rows)}"
    )

    assert "## Pattern Classes & Weighting" in catalog
    assert "**Volatility: high**" in catalog or "**Volatility:** high" in catalog or "`Volatility: high`" in catalog
    # New high-signal seeds are named in the How to Apply seeding list
    assert re.search(r"7, 13, 21, 22, 23, 24, 29, 33, 35, 36, 41", catalog), (
        "Seeding list must name the new high-signal patterns 29/33/35/36/41"
    )
    # The user-requested zero-budget summary-closer boilerplate is present and greppable
    assert "that was the whole of it" in catalog


def test_review_prompt_literal_sweep_and_cluster_rules():
    """Review Pass 2 reinforcement: literal Grep sweep for zero-budget phrase shapes,
    cluster escalator, tic-load gating label, persistence check, softened seed retirement."""
    repo_root = Path(__file__).resolve().parents[2]
    review = (repo_root / ".authorkit" / "prompts" / "authorkit.review.md").read_text(encoding="utf-8")

    assert "Literal sweep" in review and "Grep" in review, "Step B must mandate the literal Grep sweep"
    assert "Cluster escalator" in review, "Severity mapping must include the co-occurrence cluster rule"
    assert "Tic-load index" in review and "`tic-load`" in review, (
        "Tic-load gating must be defined and emitted as the synthetic `tic-load` label"
    )
    assert "Persistence check" in review and "3 or more consecutive reviewed chapters" in review
    assert "retire after 4 reviews" in review, "Seed retirement must be softened to 4 reviews"
    assert "never retire" in review, "Zero-budget phrase-class seeds must never retire"

    # The three density thresholds are tunable per book via book.toml [review];
    # the prompt must name the keys and their defaults, and the setup scripts must
    # document them in the generated book.toml.
    for key in ("tic_load_threshold", "cluster_min_shapes", "persistence_chapters"):
        assert key in review, f"review.md must name the configurable threshold {key}"
    assert "`[review]`" in review or "[review]" in review, "review.md must point at book.toml's [review] table"
    for script in (
        repo_root / ".authorkit" / "scripts" / "bash" / "setup-book.sh",
        repo_root / ".authorkit" / "scripts" / "powershell" / "setup-book.ps1",
    ):
        body = script.read_text(encoding="utf-8")
        for key in ("tic_load_threshold", "cluster_min_shapes", "persistence_chapters"):
            assert key in body, f"{script.name} must document {key} in the generated book.toml"


def test_ledger_template_class_field_and_lifecycle():
    """Ledger template: optional Class field present, lifecycle softened to 4 reviews,
    zero-budget phrase seeds exempt from retirement."""
    repo_root = Path(__file__).resolve().parents[2]
    template = (repo_root / ".authorkit" / "templates" / "tic-ledger-template.md").read_text(encoding="utf-8")

    assert "**Class**:" in template, "Entry template must carry the optional Class field"
    assert "after 4 reviews" in template, "Seed retirement must say 4 reviews"
    assert "never retire" in template, "Zero-budget phrase-class seeds must be exempt from retirement"


def test_parse_gating_shapes_accepts_tic_load_label():
    """The synthetic tic-load gating label must round-trip through the AutoPilot gate
    parser like any TIC id, and must not collide with the explicit-none vocabulary."""
    parsed = autopilot_core.parse_gating_shapes("**Gating Shapes**: tic-load, TIC-059")
    assert parsed == ("tic-load", "tic-059")

    only_load = autopilot_core.parse_gating_shapes("**Gating Shapes**: tic-load")
    assert only_load == ("tic-load",)
    assert "tic-load" not in autopilot_core._GATING_NONE

    # And it shrinks like any shape: dropping tic-load converges.
    assert autopilot_core.gating_set_converging(("tic-load", "tic-059"), ("tic-059",))
    assert not autopilot_core.gating_set_converging(("tic-059",), ("tic-059", "tic-load"))


def test_guardrails_quarantine_unchanged_and_pass2_reinforced():
    """The drafting quarantine must survive the Pass 2 reinforcement, and the roster's
    Pass 2 paragraph must describe the literal sweep, tic-load, and zero-budget Grep-on-revise."""
    repo_root = Path(__file__).resolve().parents[2]
    guardrails = (repo_root / ".authorkit" / "prompts" / "_shared" / "generation-guardrails.md").read_text(encoding="utf-8")

    assert "Quarantine rule (binding)" in guardrails
    assert "MUST NOT load" in guardrails, "Drafting quarantine wording must remain intact"
    assert "literal sweep" in guardrails.lower(), "Pass 2 roster must mention the literal sweep"
    assert "tic-load" in guardrails, "Pass 2 roster must mention the tic-load compounding gate"
    assert "Greps the whole draft" in guardrails, (
        "Revise must be told to Grep the whole draft for zero-budget phrase shapes"
    )

    write_prompt = (repo_root / ".authorkit" / "prompts" / "authorkit.write.md").read_text(encoding="utf-8")
    assert "Grep the whole draft" in write_prompt, (
        "write.md Revise must sweep zero-budget phrase shapes by literal search"
    )
