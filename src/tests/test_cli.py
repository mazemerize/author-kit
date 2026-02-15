"""CLI behavior tests for Author Kit installer workflows.

Author:
    Mazemerize contributors.
"""

import json
from pathlib import Path

import authorkit_cli as cli
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
    assert "authorkit-cli 0.1.0" in result.output


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


def test_book_stats_json_output_contains_totals():
    """Verify stats command emits JSON totals payload."""
    with runner.isolated_filesystem():
        book_dir = _seed_book_tree()
        result = runner.invoke(cli.app, ["book", "stats", "--book", book_dir.name, "--output", "json"])

        assert result.exit_code == 0, result.output
        payload = json.loads(result.output)
        assert payload["totals"]["chapters"] == 1
        assert payload["totals"]["words"] > 0


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
