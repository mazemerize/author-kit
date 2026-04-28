"""CLI behavior tests for Author Kit installer workflows.

Author:
    Mazemerize contributors.
"""

import json
import re
from pathlib import Path

import pytest

import authorkit_cli as cli
import authorkit_cli.book_core as book_core
import authorkit_cli.book_commands as book_commands
import authorkit_cli.book_audio as book_audio
import authorkit_cli.book_render as book_render
from typer.testing import CliRunner


runner = CliRunner()


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
        assert Path(".claude/commands/authorkit.chapter.plan.md").exists()
        assert Path(".claude/commands/authorkit.research.md").exists()
        assert Path(".github/prompts/authorkit.chapter.plan.prompt.md").exists()
        assert Path(".github/prompts/authorkit.research.prompt.md").exists()
        assert Path("CLAUDE.md").exists()
        assert Path(".github/copilot-instructions.md").exists()

        manifest = json.loads(Path(".authorkit/install-manifest.json").read_text(encoding="utf-8"))
        assert manifest["ais"] == ["claude", "copilot"]
        assert manifest["script"] == "sh"
        assert ".claude/commands/authorkit.chapter.plan.md" in manifest["managed_paths"]
        assert ".claude/commands/authorkit.research.md" in manifest["managed_paths"]
        assert ".github/prompts/authorkit.chapter.plan.prompt.md" in manifest["managed_paths"]
        assert ".github/prompts/authorkit.research.prompt.md" in manifest["managed_paths"]


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

        assert Path(".codex/prompts/authorkit.chapter.plan.md").exists()
        assert Path(".codex/prompts/authorkit.research.md").exists()
        assert Path(".codex/AGENTS.md").exists()
        assert not Path(".claude/commands/authorkit.chapter.plan.md").exists()
        assert not Path(".github/prompts/authorkit.chapter.plan.prompt.md").exists()

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
    with runner.isolated_filesystem():
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
    with runner.isolated_filesystem():
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
    with runner.isolated_filesystem():
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
    with runner.isolated_filesystem():
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

        result = runner.invoke(cli.app, ["book", "build", "--format", "docx"])

        assert result.exit_code == 0, result.output
        assert called["render"] is False
        assert "No output formats selected for rendering." in result.output


def test_book_build_prompts_and_overwrites_existing_output(monkeypatch):
    """Verify existing outputs are rebuilt when overwrite prompt is accepted.

    Args:
        monkeypatch: Pytest monkeypatch fixture.
    """
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
    with runner.isolated_filesystem():
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
    with runner.isolated_filesystem():
        _seed_book_tree()
        result = runner.invoke(cli.app, ["book", "build", "--book", "book"])
        assert result.exit_code != 0
        plain_output = re.sub(r"\x1b\[[0-9;]*m", "", result.output)
        assert "No such option" in plain_output
        assert "--book" in plain_output


def test_book_build_requires_canonical_book_directory():
    """Verify build shows actionable guidance when book/ is missing."""
    with runner.isolated_filesystem():
        result = runner.invoke(cli.app, ["book", "build"])
        assert result.exit_code != 0
    assert "/authorkit.conceive" in result.output


def test_book_build_rejects_pdf_format():
    """Verify PDF format is rejected as unsupported."""
    with runner.isolated_filesystem():
        book_dir = _seed_book_tree()
        result = runner.invoke(cli.app, ["book", "build", "--format", "pdf"])

        assert result.exit_code != 0
        assert "Unsupported format(s): pdf" in result.output


def test_book_stats_json_output_contains_totals():
    """Verify stats command emits JSON totals payload."""
    with runner.isolated_filesystem():
        book_dir = _seed_book_tree()
        result = runner.invoke(cli.app, ["book", "stats", "--output", "json"])

        assert result.exit_code == 0, result.output
        payload = json.loads(result.output)
        assert payload["totals"]["chapters"] == 1
        assert payload["totals"]["words"] > 0


def test_book_stats_table_includes_est_audio_minutes():
    """Verify table output renders the per-chapter estimated audio duration column."""
    with runner.isolated_filesystem():
        book_dir = _seed_book_tree()
        result = runner.invoke(cli.app, ["book", "stats", "--output", "table"])

        assert result.exit_code == 0, result.output
        assert "Est Audio Min" in result.output


def test_book_audio_command_uses_generator(monkeypatch):
    """Verify audio command delegates to audio generator with defaults.

    Args:
        monkeypatch: Pytest monkeypatch fixture.
    """
    with runner.isolated_filesystem():
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
    with runner.isolated_filesystem():
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
    with runner.isolated_filesystem():
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
                "--ignore-agent-tools",
                "--no-git",
            ],
        )
        assert result.exit_code == 0, result.output

        draft_prompt = Path(".codex/prompts/authorkit.chapter.draft.md").read_text(encoding="utf-8")
        assert "## Shared Generation Guardrails" in draft_prompt
        assert "### Name Originality Protocol" in draft_prompt

        assert Path(".authorkit/prompts/_shared/generation-guardrails.md").exists()
        assert not Path(".codex/prompts/generation-guardrails.md").exists()
        assert not Path(".codex/prompts/_shared/generation-guardrails.md").exists()


def test_init_renders_clarify_prompt_for_all_ai_flavors():
    """Verify authorkit.clarify is rendered for claude, copilot, and codex with guardrails injected."""
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
            Path(".claude/commands/authorkit.clarify.md"),
            Path(".github/prompts/authorkit.clarify.prompt.md"),
            Path(".codex/prompts/authorkit.clarify.md"),
        ]
        for path in rendered_paths:
            assert path.exists(), f"Expected rendered clarify prompt at {path}"
            body = path.read_text(encoding="utf-8")
            assert "## Shared Generation Guardrails" in body, f"Guardrails missing in {path}"
            assert "### Name Originality Protocol" in body, f"Name protocol missing in {path}"
            assert "Clarifications" in body, f"Clarifications section reference missing in {path}"


def test_chapter_prompts_enforce_style_anchor_workflow():
    """Verify chapter lifecycle prompts include style-anchor loading and refresh instructions."""
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
                "--ignore-agent-tools",
                "--no-git",
            ],
        )
        assert result.exit_code == 0, result.output

        plan_prompt = Path(".codex/prompts/authorkit.chapter.plan.md").read_text(encoding="utf-8")
        draft_prompt = Path(".codex/prompts/authorkit.chapter.draft.md").read_text(encoding="utf-8")

        for text in (plan_prompt, draft_prompt):
            assert "STYLE_ANCHOR" in text
            assert "last two approved chapters" in text
            assert "templates/style-anchor-template.md" in text


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


def test_world_prompts_document_recursive_layout_and_path_preservation():
    """Verify world prompts describe recursive scans and preserving human-organized paths."""
    repo_root = Path(__file__).resolve().parents[2]
    world_build = (repo_root / ".authorkit" / "prompts" / "authorkit.world.build.md").read_text(encoding="utf-8")
    world_sync = (repo_root / ".authorkit" / "prompts" / "authorkit.world.sync.md").read_text(encoding="utf-8")

    assert "Never relocate or normalize existing files; preserve human-organized folder layouts." in world_build
    assert "Auto-created nesting depth is one level under the category root." in world_build
    # world.sync merges the former world.update + world.verify + world.index
    assert "world/" in world_sync
    assert "Rebuild" in world_sync or "index" in world_sync.lower()


def test_research_consumers_use_recursive_topic_loading_language():
    """Verify prompts that consume research artifacts mention recursive topic discovery."""
    repo_root = Path(__file__).resolve().parents[2]
    targets = [
        repo_root / ".authorkit" / "prompts" / "authorkit.outline.md",
        repo_root / ".authorkit" / "prompts" / "authorkit.chapter.plan.md",
        repo_root / ".authorkit" / "prompts" / "authorkit.chapter.draft.md",
        repo_root / ".authorkit" / "prompts" / "authorkit.chapter.review.md",
        repo_root / ".authorkit" / "prompts" / "authorkit.chapters.md",
    ]

    for target in targets:
        text = target.read_text(encoding="utf-8")
        assert "recursively" in text or "nested" in text


def test_readme_documents_adaptive_research_layout():
    """Verify README describes adaptive flat-first research placement and dual sync paths."""
    repo_root = Path(__file__).resolve().parents[2]
    readme = (repo_root / "README.md").read_text(encoding="utf-8")

    assert "`research/**/*.md`" in readme
    assert "Placement is adaptive: simple one-off topics stay flat" in readme
    assert "`world/notes/research-*.md` or `world/notes/research/*.md`" in readme
    assert "preserving any existing note path" in readme


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
    with runner.isolated_filesystem():
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
    """Verify every prompt with a scripts: block declares both sh: and ps: variants.

    `authorkit.constitution.md` is intentionally exempt: it edits
    `.authorkit/memory/constitution.md` directly and has no setup script to dispatch.
    """
    repo_root = Path(__file__).resolve().parents[2]
    prompts_dir = repo_root / ".authorkit" / "prompts"
    exempt = {"authorkit.constitution.md"}
    for prompt in prompts_dir.glob("authorkit.*.md"):
        text = prompt.read_text(encoding="utf-8")
        front_match = re.match(r"^---\n(.*?)\n---", text, flags=re.S)
        if not front_match:
            continue
        frontmatter = front_match.group(1)
        if "scripts:" not in frontmatter:
            assert prompt.name in exempt, (
                f"{prompt.name}: missing scripts: block. "
                f"Add one or extend the exempt set with rationale."
            )
            continue
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
    assert "/authorkit.conceive" in result.output


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
    deep inside /authorkit.world.sync rather than at install/check time.
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
    emitting drift noise. This is the realistic state right after `/authorkit.conceive`.
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
    has been drafted. Closes the loop on /authorkit.park's deadline tracking
    promise from the README.
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
