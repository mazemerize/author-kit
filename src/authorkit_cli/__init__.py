"""Author Kit CLI installer and updater.

Handles project initialisation, prompt rendering for all AI agent flavours,
asset management, and environment validation.

Author:
    mdemarne
"""

from __future__ import annotations

import json
import os
import platform
import re
import shutil
import subprocess
from importlib import metadata
from datetime import datetime, timezone
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import BarColumn, Progress, TextColumn, TimeElapsedColumn

from .book_commands import book_app
from .book_core import find_repo_root, resolve_book_dir
from .book_status import collect_status, format_status_lines

# Shared Rich console for terminal output.
console = Console()
app = typer.Typer(add_completion=False, help="Author Kit project installer")
app.add_typer(book_app, name="book")

# CLI banner (ASCII only).
BANNER = r"""
    /  \  _   _| |_| |__   ___  _ __  | ' / _| |_
   / /\ \| | | | __| '_ \ / _ \| '__| |  < | | __|
  / ____ \ |_| | |_| | | | (_) | |    | . \| | |_
 /_/    \_\__,_|\__|_| |_|\___/|_|    |_|\_\_|\__|
"""

# One-line tagline displayed beneath the ASCII banner.
TAGLINE = "Write books with structured AI assistance."

# Supported AI targets and CLI requirements.
AGENT_CONFIG = {
    "claude": {"name": "Claude Code", "folder": ".claude", "requires_cli": True, "tool": "claude"},
    "copilot": {"name": "GitHub Copilot", "folder": ".github", "requires_cli": False, "tool": None},
    "codex": {"name": "Codex CLI", "folder": ".codex", "requires_cli": True, "tool": "codex"},
}

# Maps --script flag values to human-readable names used in prompts.
SCRIPT_CHOICES = {"sh": "POSIX Shell", "ps": "PowerShell"}
# Managed paths that are never removed during re-init (user-edited files).
PROTECTED_MANAGED_PATHS = {".authorkit/memory/constitution.md"}
# Canonical path to the shared generation guardrail source asset.
SHARED_GUARDRAILS_PATH = Path(".authorkit/prompts/_shared/generation-guardrails.md")
# Prompts that receive the shared generation guardrail block when rendered.
# Excluded by design: workflow tools that don't generate user-facing prose
# (park, snapshot, whatif, chapter.reorder) — they orchestrate state, files,
# and git, so the prose-generation guardrails don't apply.
GUARDRAIL_PROMPT_ALLOWLIST = {
    "authorkit.amend.md",
    "authorkit.analyze.md",
    "authorkit.chapter.draft.md",
    "authorkit.chapter.help.md",
    "authorkit.chapter.plan.md",
    "authorkit.chapter.review.md",
    "authorkit.chapters.md",
    "authorkit.clarify.md",
    "authorkit.conceive.md",
    "authorkit.constitution.md",
    "authorkit.discuss.md",
    "authorkit.outline.md",
    "authorkit.research.md",
    "authorkit.revise.md",
    "authorkit.world.build.md",
    "authorkit.world.sync.md",
}


def show_banner() -> None:
    """Render Author Kit ASCII banner."""
    console.print(BANNER)
    console.print(TAGLINE)
    console.print()


def package_root() -> Path:
    """Return the package module directory.

    Returns:
        Path: Directory containing this module.
    """
    return Path(__file__).resolve().parent


def asset_root() -> Path:
    """Resolve toolkit asset root.

    Prefers packaged wheel assets and falls back to repository root assets
    when running from source.

    Returns:
        Path: Root path that contains `.authorkit` assets.
    """
    packaged = package_root() / "assets"
    if (packaged / ".authorkit").exists():
        return packaged

    for parent in package_root().parents:
        candidate = parent / ".authorkit"
        if candidate.exists():
            return parent

    return packaged


def read_text(path: Path) -> str:
    """Read UTF-8 text file.

    Args:
        path: File path to read.

    Returns:
        str: File contents.
    """
    return path.read_text(encoding="utf-8-sig")


def record_managed(path: Path, root: Path, managed: set[str]) -> None:
    """Record a managed path relative to the project root.

    Args:
        path: Absolute path of a managed file.
        root: Project root used for relative path conversion.
        managed: Mutable set of managed relative paths.
    """
    managed.add(str(path.relative_to(root).as_posix()))


def write_text(path: Path, content: str, root: Path, managed: set[str]) -> None:
    """Write file content and track it as managed.

    Args:
        path: Destination file path.
        content: UTF-8 content to write.
        root: Project root.
        managed: Mutable set of managed paths.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    record_managed(path, root, managed)


def copy_tree(
    src: Path,
    dst: Path,
    root: Path,
    managed: set[str],
    skip_overwrite_paths: set[str] | None = None,
) -> None:
    """Copy directory tree and track copied files as managed.

    Args:
        src: Source directory.
        dst: Destination directory.
        root: Project root.
        managed: Mutable set of managed paths.
        skip_overwrite_paths: Paths (repo-relative) that should not be overwritten when present.
    """
    if not src.exists():
        return

    for p in src.rglob("*"):
        rel = p.relative_to(src)
        target = dst / rel
        if p.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        relative = str(target.relative_to(root).as_posix())
        if target.exists() and skip_overwrite_paths and relative in skip_overwrite_paths:
            record_managed(target, root, managed)
            continue
        # Running init in the source repository can make source and target identical.
        # Treat this as already managed instead of attempting a self-copy.
        if p.resolve() == target.resolve():
            record_managed(target, root, managed)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, target)
        record_managed(target, root, managed)


def parse_frontmatter(text: str) -> tuple[list[str], str]:
    """Split markdown frontmatter from body.

    Args:
        text: Full markdown prompt content.

    Returns:
        tuple[list[str], str]: Frontmatter lines and body markdown.
    """
    text = text.lstrip("\ufeff")  # Strip UTF-8 BOM; its presence silently breaks startswith("---\n").
    if not text.startswith("---\n"):
        return [], text
    end = text.find("\n---\n", 4)
    if end < 0:
        return [], text
    fm = text[4:end].splitlines()
    body = text[end + 5 :]
    return fm, body


def remove_block(lines: list[str], key: str) -> list[str]:
    """Remove a YAML-style key block and its indented children.

    Args:
        lines: Frontmatter lines.
        key: Key name to remove.

    Returns:
        list[str]: Filtered lines.
    """
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip() == f"{key}:":
            i += 1
            while i < len(lines) and re.match(r"^\s{2,}", lines[i]):
                i += 1
            continue
        out.append(line)
        i += 1
    return out


def extract_script_path(frontmatter_lines: list[str]) -> str | None:
    """Extract script command from prompt frontmatter.

    Args:
        frontmatter_lines: Frontmatter line list.

    Returns:
        str | None: Script command string, if present.
    """
    for i, line in enumerate(frontmatter_lines):
        if line.strip() == "scripts:" and i + 1 < len(frontmatter_lines):
            j = i + 1
            while j < len(frontmatter_lines) and re.match(r"^\s{2,}", frontmatter_lines[j]):
                match = re.match(r"^\s{2,}(?:ps|sh):\s*(.+)$", frontmatter_lines[j])
                if match:
                    return match.group(1).strip()
                j += 1
    return None


def resolve_script(path_from_frontmatter: str | None, script_type: str) -> str:
    """Map frontmatter script path to selected script flavor path.

    Args:
        path_from_frontmatter: Script command extracted from frontmatter.
        script_type: Selected script flavor (`sh` or `ps`).

    Returns:
        str: Script path used in rendered prompts.
    """
    if not path_from_frontmatter:
        return ""
    script_name = Path(path_from_frontmatter).name
    if script_type == "sh":
        script_name = script_name.replace(".ps1", ".sh")
        return f".authorkit/scripts/bash/{script_name}"
    return f".authorkit/scripts/powershell/{script_name}"


def resolve_token_script(token: str, script_type: str) -> str:
    """Resolve canonical script token to flavored script path.

    Args:
        token: Canonical prompt token.
        script_type: Selected script flavor (`sh` or `ps`).

    Returns:
        str: Script path replacement string.
    """
    token_map = {
        "{{SCRIPT_CHECK_PREREQ}}": "check-prerequisites",
        "{{SCRIPT_SETUP_BOOK}}": "setup-book",
        "{{SCRIPT_SETUP_OUTLINE}}": "setup-outline",
        "{{SCRIPT_BUILD_WORLD_INDEX}}": "build-world-index",
    }
    stem = token_map.get(token)
    if not stem:
        return ""
    if script_type == "sh":
        return f".authorkit/scripts/bash/{stem}.sh"
    return f".authorkit/scripts/powershell/{stem}.ps1"


def load_generation_guardrails() -> str:
    """Load shared generation guardrails text from assets.

    Returns:
        str: Guardrail content.

    Raises:
        typer.BadParameter: If the shared guardrail file is missing.
    """
    path = asset_root() / SHARED_GUARDRAILS_PATH
    if not path.is_file():
        raise typer.BadParameter(
            f"Missing required shared guardrail file: {path}. "
            "Restore .authorkit/prompts/_shared/generation-guardrails.md and rerun init."
        )
    return read_text(path).strip()


def inject_generation_guardrails(body: str, prompt_name: str, guardrails: str) -> str:
    """Inject shared guardrails into selected generation prompts.

    Args:
        body: Prompt body markdown.
        prompt_name: Canonical prompt filename.
        guardrails: Shared guardrail markdown.

    Returns:
        str: Prompt body with guardrails injected when applicable.
    """
    if prompt_name not in GUARDRAIL_PROMPT_ALLOWLIST:
        return body
    injected = (
        "## Shared Generation Guardrails\n\n"
        "Apply this central policy for this command.\n\n"
        f"{guardrails}\n"
    )
    return f"{injected}\n{body.lstrip()}"


def render_prompt(raw: str, ai: str, script_type: str, prompt_name: str, guardrails: str) -> str:
    """Render canonical prompt for a target AI and script flavor.

    Args:
        raw: Canonical prompt markdown.
        ai: Target AI flavor.
        script_type: Script flavor (`sh` or `ps`).
        prompt_name: Canonical prompt filename.
        guardrails: Shared generation guardrail markdown.

    Returns:
        str: Rendered prompt content.
    """
    fm, body = parse_frontmatter(raw)
    script = resolve_script(extract_script_path(fm), script_type)
    body = inject_generation_guardrails(body, prompt_name, guardrails)

    if ai == "claude":
        body = body.replace("{{USER_INPUT_TOKEN}}", "$ARGUMENTS")
        body = body.replace("{SCRIPT}", script)
        for token in [
            "{{SCRIPT_CHECK_PREREQ}}",
            "{{SCRIPT_SETUP_BOOK}}",
            "{{SCRIPT_SETUP_OUTLINE}}",
            "{{SCRIPT_BUILD_WORLD_INDEX}}",
        ]:
            body = body.replace(token, resolve_token_script(token, script_type))
        if script:
            has_scripts = any(x.strip() == "scripts:" for x in fm)
            if has_scripts:
                fm = remove_block(fm, "scripts")
            fm += ["scripts:", f"  {script_type}: {script.replace('.authorkit/', '')}"]
        fm_text = "\n".join(fm)
        return f"---\n{fm_text}\n---\n{body}"

    fm = remove_block(fm, "scripts")
    fm = remove_block(fm, "handoffs")
    fm = [line for line in fm if not line.startswith("mode:")]
    fm.insert(1 if fm else 0, "mode: agent")

    body = body.replace("{{USER_INPUT_TOKEN}}", "${input}")
    body = body.replace("$ARGUMENTS", "${input}")
    body = body.replace("{SCRIPT}", script)
    for token in [
        "{{SCRIPT_CHECK_PREREQ}}",
        "{{SCRIPT_SETUP_BOOK}}",
        "{{SCRIPT_SETUP_OUTLINE}}",
        "{{SCRIPT_BUILD_WORLD_INDEX}}",
    ]:
        body = body.replace(token, resolve_token_script(token, script_type))

    fm_text = "\n".join(fm)
    return f"---\n{fm_text}\n---\n{body}"


def instruction_text(ai: str, script_type: str) -> tuple[str, str]:
    """Render AI-specific instruction file from canonical templates.

    Args:
        ai: Target AI flavor.
        script_type: Script flavor (`sh` or `ps`).

    Returns:
        tuple[str, str]: Output relative path and rendered content.
    """
    script_dir = ".authorkit/scripts/bash/" if script_type == "sh" else ".authorkit/scripts/powershell/"
    command_source = {
        "claude": ".claude/commands/",
        "copilot": ".github/prompts/",
        "codex": ".codex/prompts/",
    }[ai]
    template = read_text(asset_root() / ".authorkit" / "instructions" / f"{ai}.md.tmpl")
    body = template.replace("{{SCRIPT_DIR}}", script_dir).replace("{{COMMAND_SOURCE}}", command_source)

    path = {
        "claude": "CLAUDE.md",
        "copilot": ".github/copilot-instructions.md",
        "codex": ".codex/AGENTS.md",
    }[ai]
    return path, body


def prompt_out_path(ai: str, prompt_name: str) -> str:
    """Return output prompt path for a target AI flavor.

    Args:
        ai: Target AI flavor.
        prompt_name: Canonical prompt filename.

    Returns:
        str: Destination relative path.
    """
    if ai == "claude":
        return f".claude/commands/{prompt_name}"
    if ai == "copilot":
        return f".github/prompts/{prompt_name.replace('.md', '.prompt.md')}"
    return f".codex/prompts/{prompt_name}"


def ensure_shell_exec_bits(root: Path) -> None:
    """Ensure bash scripts are executable on non-Windows systems.

    Args:
        root: Project root.
    """
    if os.name == "nt":
        return
    bash_root = root / ".authorkit" / "scripts" / "bash"
    if not bash_root.is_dir():
        return
    for sh_file in bash_root.rglob("*.sh"):
        mode = sh_file.stat().st_mode
        sh_file.chmod(mode | 0o755)


def ensure_repo_gitignore(root: Path) -> None:
    """Ensure repo-level .gitignore includes local secrets and generated artifacts."""
    gitignore = root / ".gitignore"
    required_entries = [
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

    if not gitignore.exists():
        gitignore.write_text("".join(f"{entry}\n" for entry in required_entries), encoding="utf-8")
        return

    content = gitignore.read_text(encoding="utf-8")
    existing = {line.strip() for line in content.splitlines() if line.strip()}
    missing = [entry for entry in required_entries if entry not in existing]
    if not missing:
        return

    suffix = "" if (not content or content.endswith("\n")) else "\n"
    additions = "".join(f"{entry}\n" for entry in missing)
    gitignore.write_text(f"{content}{suffix}{additions}", encoding="utf-8")


def tool_exists(tool: str) -> bool:
    """Check if a CLI tool is available in PATH.

    Args:
        tool: Executable name.

    Returns:
        bool: True when tool exists.
    """
    return shutil.which(tool) is not None


def normalize_ai_selection(ai_values: list[str] | None, previous: dict) -> list[str]:
    """Normalize AI selections from flags and manifest defaults.

    Args:
        ai_values: Raw `--ai` option values.
        previous: Previous install manifest data.

    Returns:
        list[str]: Ordered unique AI flavor list.
    """
    if not ai_values:
        prev = previous.get("ais")
        if isinstance(prev, list) and prev:
            return [str(x) for x in prev if str(x) in AGENT_CONFIG]
        old = previous.get("ai")
        if isinstance(old, str) and old in AGENT_CONFIG:
            return [old]
        return ["copilot"]

    expanded: list[str] = []
    for item in ai_values:
        parts = [x.strip() for x in item.split(",") if x.strip()]
        expanded.extend(parts)

    unique: list[str] = []
    seen: set[str] = set()
    for ai in expanded:
        if ai not in seen:
            seen.add(ai)
            unique.append(ai)
    return unique


def load_manifest(project_path: Path) -> dict:
    """Load installer manifest from project if present.

    Args:
        project_path: Target project root.

    Returns:
        dict: Parsed manifest or empty dictionary.
    """
    manifest = project_path / ".authorkit" / "install-manifest.json"
    if not manifest.exists():
        return {}
    try:
        return json.loads(read_text(manifest))
    except Exception:
        return {}


def remove_old_managed_paths(project_path: Path, previous: dict) -> None:
    """Remove files tracked by previous installation manifest.

    Args:
        project_path: Target project root.
        previous: Parsed previous manifest.
    """
    for rel in previous.get("managed_paths", []):
        if rel in PROTECTED_MANAGED_PATHS:
            continue
        p = project_path / rel
        if p.is_file():
            p.unlink(missing_ok=True)


def write_manifest(project_path: Path, ais: list[str], script: str, managed: set[str]) -> None:
    """Write installation manifest for future updates.

    Args:
        project_path: Target project root.
        ais: Installed AI flavor list.
        script: Installed script flavor.
        managed: Managed relative path set.
    """
    manifest_path = project_path / ".authorkit" / "install-manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "installed_at": datetime.now(timezone.utc).isoformat(),
        "version": get_cli_version(),
        "ai": ais[0] if ais else "copilot",
        "ais": ais,
        "script": script,
        "managed_paths": sorted(managed),
    }
    manifest_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def get_cli_version() -> str:
    """Resolve CLI version from package metadata with source fallback.

    Returns:
        str: Version string.
    """
    try:
        return metadata.version("authorkit-cli")
    except Exception:
        pyproject = package_root().parents[1] / "pyproject.toml"
        if pyproject.exists():
            text = read_text(pyproject)
            match = re.search(r'(?m)^version\s*=\s*"([^"]+)"\s*$', text)
            if match:
                return match.group(1)
    return "unknown"


@app.command()
def init(
    project_name: str | None = typer.Argument(None, help="Project directory name, or '.' for current directory"),
    ai: list[str] | None = typer.Option(None, "--ai", help="One or more of: claude, copilot, codex (repeat --ai or pass comma-separated)"),
    script: str | None = typer.Option(None, "--script", help="sh or ps"),
    ignore_agent_tools: bool = typer.Option(False, "--ignore-agent-tools"),
    no_git: bool = typer.Option(False, "--no-git"),
    here: bool = typer.Option(False, "--here"),
    force: bool = typer.Option(False, "--force"),
) -> None:
    """Install or update Author Kit in a target directory.

    Args:
        project_name: New target directory name or "." for current directory.
        ai: One or more AI flavors.
        script: Script flavor (`sh` or `ps`).
        ignore_agent_tools: Skip AI tool checks.
        no_git: Skip git initialization.
        here: Install in current directory.
        force: Skip non-empty directory confirmation.
    """
    show_banner()

    if project_name == ".":
        here = True
        project_name = None

    if here and project_name:
        raise typer.BadParameter("Cannot pass both project name and --here")
    if not here and not project_name:
        raise typer.BadParameter("Provide project name, '.' or --here")

    selected_script = script or ("ps" if os.name == "nt" else "sh")
    if selected_script not in SCRIPT_CHOICES:
        raise typer.BadParameter("Invalid --script. Use sh or ps")

    project_path = Path.cwd() if here else (Path.cwd() / project_name).resolve()

    if here:
        if any(project_path.iterdir()) and not force:
            if not typer.confirm("Current directory is not empty. Merge and overwrite managed files?"):
                raise typer.Exit(0)
    else:
        if project_path.exists():
            raise typer.BadParameter(f"Directory already exists: {project_path}")
        project_path.mkdir(parents=True)

    ensure_repo_gitignore(project_path)

    previous = load_manifest(project_path)
    selected_ais = normalize_ai_selection(ai, previous)
    invalid = [x for x in selected_ais if x not in AGENT_CONFIG]
    if invalid:
        raise typer.BadParameter(f"Invalid --ai value(s): {', '.join(invalid)}. Use: {', '.join(AGENT_CONFIG)}")

    if not ignore_agent_tools:
        missing_tools: list[str] = []
        for selected_ai in selected_ais:
            if AGENT_CONFIG[selected_ai]["requires_cli"]:
                tool = AGENT_CONFIG[selected_ai]["tool"]
                if tool and not tool_exists(tool):
                    missing_tools.append(tool)
        if missing_tools:
            missing_display = ", ".join(sorted(set(missing_tools)))
            details = (
                f"Required tool(s) not found in PATH: {missing_display}. "
                "Use --ignore-agent-tools to skip check."
            )
            if "codex" in missing_tools:
                details += (
                    " Note: this PATH check is about the Codex executable; "
                    "CODEX_HOME is a separate setting used after install."
                )
            raise typer.BadParameter(details)

    previous_ais = previous.get("ais") or ([previous["ai"]] if isinstance(previous.get("ai"), str) else [])
    dropped_ais = [ai for ai in previous_ais if ai not in selected_ais]
    if dropped_ais and not force:
        # Count files that would be removed for the dropped AI flavor(s) so the
        # user can see the blast radius before confirming. These are tracked in
        # managed_paths from the previous manifest.
        dropped_paths = [
            rel
            for rel in previous.get("managed_paths", [])
            if any(rel.startswith(AGENT_CONFIG[ai]["folder"] + "/") for ai in dropped_ais if ai in AGENT_CONFIG)
            or any(rel == ("CLAUDE.md" if ai == "claude" else f"{AGENT_CONFIG[ai]['folder']}/copilot-instructions.md" if ai == "copilot" else f"{AGENT_CONFIG[ai]['folder']}/AGENTS.md") for ai in dropped_ais)
        ]
        dropped_names = ", ".join(AGENT_CONFIG[ai]["name"] for ai in dropped_ais if ai in AGENT_CONFIG)
        kept_names = ", ".join(AGENT_CONFIG[ai]["name"] for ai in selected_ais)
        console.print(
            f"[yellow]Switching AI flavors.[/yellow] Re-installing for [bold]{kept_names}[/bold] "
            f"will remove {len(dropped_paths)} file(s) installed for [bold]{dropped_names}[/bold]."
        )
        console.print(
            f"[dim]To keep both, re-run with `--ai {' --ai '.join(previous_ais + [ai for ai in selected_ais if ai not in previous_ais])}`. "
            f"Pass `--force` to skip this prompt.[/dim]"
        )
        if not typer.confirm("Continue?", default=False):
            raise typer.Exit(0)

    remove_old_managed_paths(project_path, previous)

    managed: set[str] = set()
    assets = asset_root()
    prompt_files = sorted((assets / ".authorkit" / "prompts").glob("authorkit*.md"))
    shared_guardrails = load_generation_guardrails()
    total_steps = 4 + (len(selected_ais) * (len(prompt_files) + 1)) + 1 + (0 if no_git else 1) + 1

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    ) as progress:
        install_task = progress.add_task("Installing Author Kit files...", total=total_steps)

        copy_tree(assets / ".authorkit" / "templates", project_path / ".authorkit" / "templates", project_path, managed)
        progress.advance(install_task)

        copy_tree(
            assets / ".authorkit" / "memory",
            project_path / ".authorkit" / "memory",
            project_path,
            managed,
            skip_overwrite_paths=PROTECTED_MANAGED_PATHS,
        )
        progress.advance(install_task)

        copy_tree(assets / ".authorkit" / "prompts", project_path / ".authorkit" / "prompts", project_path, managed)
        progress.advance(install_task)

        selected_script_src = assets / ".authorkit" / "scripts" / ("bash" if selected_script == "sh" else "powershell")
        copy_tree(
            selected_script_src,
            project_path / ".authorkit" / "scripts" / ("bash" if selected_script == "sh" else "powershell"),
            project_path,
            managed,
        )
        progress.advance(install_task)

        for selected_ai in selected_ais:
            for prompt in prompt_files:
                progress.update(install_task, description=f"Rendering prompts for {selected_ai}...")
                raw = read_text(prompt)
                rendered = render_prompt(raw, selected_ai, selected_script, prompt.name, shared_guardrails)
                out_rel = prompt_out_path(selected_ai, prompt.name)
                write_text(project_path / out_rel, rendered, project_path, managed)
                progress.advance(install_task)

            instr_rel, instr_content = instruction_text(selected_ai, selected_script)
            write_text(project_path / instr_rel, instr_content, project_path, managed)
            progress.advance(install_task)

        progress.update(install_task, description="Writing install manifest...")
        write_manifest(project_path, selected_ais, selected_script, managed)
        progress.advance(install_task)

        if not no_git:
            progress.update(install_task, description="Preparing git repository...")
            try:
                subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=project_path, check=True, capture_output=True)
            except Exception:
                subprocess.run(["git", "init"], cwd=project_path, check=False, capture_output=True, text=True)
            progress.advance(install_task)

        ensure_shell_exec_bits(project_path)
        progress.advance(install_task)

    console.print(f"Installed Author Kit in [bold]{project_path}[/bold].")
    console.print(f"AI flavors: [bold]{', '.join(selected_ais)}[/bold], script flavor: [bold]{selected_script}[/bold].")
    if "codex" in selected_ais:
        codex_home = project_path / ".codex"
        if os.name == "nt":
            console.print(f"Set CODEX_HOME: setx CODEX_HOME {codex_home}")
        else:
            console.print(f"Set CODEX_HOME: export CODEX_HOME={codex_home}")

    instructions_file = {
        "claude": "CLAUDE.md",
        "copilot": ".github/copilot-instructions.md",
        "codex": ".codex/AGENTS.md",
    }[selected_ais[0]]
    console.print()
    console.print("[bold green]Next steps:[/bold green]")
    console.print(f"  1. Open your AI agent (e.g. {AGENT_CONFIG[selected_ais[0]]['name']}) in this directory.")
    console.print("  2. Run [bold]/authorkit.constitution[/bold] to set your voice/tone/style rules.")
    console.print('  3. Run [bold]/authorkit.conceive "your book idea here"[/bold] to create the workspace.')
    console.print(f"  4. See [bold]{instructions_file}[/bold] or the project README for the full workflow.")


@app.command()
def check() -> None:
    """Check local environment for supported tools."""
    show_banner()
    # Python is required by the bash world-index script. Either `python3` or `python` works.
    python_present = tool_exists("python3") or tool_exists("python")
    console.print("Tool checks:")
    console.print(f"- git: {'ok' if tool_exists('git') else 'missing'}")
    console.print(f"- claude: {'ok' if tool_exists('claude') else 'missing'}")
    console.print(f"- codex: {'ok' if tool_exists('codex') else 'missing'}")
    console.print(f"- copilot (optional for Copilot CLI workflows): {'ok' if tool_exists('copilot') else 'missing'}")
    console.print(f"- python (world index, bash flavor): {'ok' if python_present else 'missing'}")
    console.print(f"- pandoc (book build): {'ok' if tool_exists('pandoc') else 'missing'}")
    console.print(f"- ffmpeg (book audio): {'ok' if tool_exists('ffmpeg') else 'missing'}")


@app.command()
def version() -> None:
    """Print CLI and Python runtime versions."""
    show_banner()
    console.print(f"authorkit-cli {get_cli_version()}")
    console.print(f"Python {platform.python_version()}")


@app.command()
def status() -> None:
    """Print a project health dashboard for the current book.

    Aggregates chapter status (pending/planned/drafted/review/approved),
    parked-decision counts, world-entity totals, and drift between chapters.md
    and the chapters/ directory. Run from the project root.
    """
    repo_root = find_repo_root()
    try:
        book_dir = resolve_book_dir(repo_root)
    except FileNotFoundError as exc:
        console.print(f"[red]No book workspace found:[/red] {exc}")
        console.print("[dim]Run /authorkit.conceive to create the book/ workspace.[/dim]")
        raise typer.Exit(code=1) from exc

    report = collect_status(book_dir, repo_root)
    for line in format_status_lines(report):
        console.print(line)


def main() -> None:
    """Run Typer application."""
    app()


if __name__ == "__main__":
    main()
