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
import authorkit_cli.book_render as book_render
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
        assert Path(".claude/commands/authorkit.research.md").exists()
        assert Path(".github/prompts/authorkit.chapter.prompt.md").exists()
        assert Path(".github/prompts/authorkit.research.prompt.md").exists()
        assert Path("CLAUDE.md").exists()
        assert Path(".github/copilot-instructions.md").exists()

        manifest = json.loads(Path(".authorkit/install-manifest.json").read_text(encoding="utf-8"))
        assert manifest["ais"] == ["claude", "copilot"]
        assert manifest["script"] == "sh"
        assert ".claude/commands/authorkit.chapter.md" in manifest["managed_paths"]
        assert ".claude/commands/authorkit.research.md" in manifest["managed_paths"]
        assert ".github/prompts/authorkit.chapter.prompt.md" in manifest["managed_paths"]
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

        assert Path(".codex/prompts/authorkit.chapter.md").exists()
        assert Path(".codex/prompts/authorkit.research.md").exists()
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
        audio_voice="onyx",
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
            audio_voice="onyx",
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
            assert "## Non-Negotiables (POV, Tense, Narrative Distance)" in text


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
    world_update = (repo_root / ".authorkit" / "prompts" / "authorkit.world.update.md").read_text(encoding="utf-8")
    world_verify = (repo_root / ".authorkit" / "prompts" / "authorkit.world.verify.md").read_text(encoding="utf-8")

    assert "Never relocate or normalize existing files; preserve human-organized folder layouts." in world_build
    assert "Auto-created nesting depth is one level under the category root." in world_build
    assert "search world/ files recursively under category folders." in world_update
    assert "Preserve file layout." in world_update
    assert "verify all files in that category recursively (including nested descendants)" in world_verify
    assert "Fall back to loading all world/ files within scope recursively." in world_verify


def test_research_consumers_use_recursive_topic_loading_language():
    """Verify prompts that consume research artifacts mention recursive topic discovery."""
    repo_root = Path(__file__).resolve().parents[2]
    targets = [
        repo_root / ".authorkit" / "prompts" / "authorkit.outline.md",
        repo_root / ".authorkit" / "prompts" / "authorkit.chapter.plan.md",
        repo_root / ".authorkit" / "prompts" / "authorkit.chapter.draft.md",
        repo_root / ".authorkit" / "prompts" / "authorkit.chapter.review.md",
        repo_root / ".authorkit" / "prompts" / "authorkit.chapters.md",
        repo_root / ".authorkit" / "prompts" / "authorkit.clarify.md",
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
    """Verify shared path scripts include STYLE_ANCHOR path metadata."""
    repo_root = Path(__file__).resolve().parents[2]
    ps_common = (repo_root / ".authorkit" / "scripts" / "powershell" / "common.ps1").read_text(encoding="utf-8")
    sh_common = (repo_root / ".authorkit" / "scripts" / "bash" / "common.sh").read_text(encoding="utf-8")
    prereq_ps = (repo_root / ".authorkit" / "scripts" / "powershell" / "check-prerequisites.ps1").read_text(
        encoding="utf-8"
    )

    assert "STYLE_ANCHOR" in ps_common
    assert "STYLE_ANCHOR" in sh_common
    assert "STYLE_ANCHOR" in prereq_ps


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
