from __future__ import annotations

import json
import os
import platform
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import typer
from rich.console import Console

console = Console()
app = typer.Typer(add_completion=False, help="Author Kit project installer")

AGENT_CONFIG = {
    "claude": {"name": "Claude Code", "folder": ".claude", "requires_cli": True, "tool": "claude"},
    "copilot": {"name": "GitHub Copilot", "folder": ".github", "requires_cli": False, "tool": None},
    "codex": {"name": "Codex CLI", "folder": ".codex", "requires_cli": True, "tool": "codex"},
}

SCRIPT_CHOICES = {"sh": "POSIX Shell", "ps": "PowerShell"}


def package_root() -> Path:
    return Path(__file__).resolve().parent


def asset_root() -> Path:
    packaged = package_root() / "assets"
    if (packaged / ".authorkit").exists():
        return packaged

    # Dev fallback: use repository root .authorkit when running from source.
    for parent in package_root().parents:
        candidate = parent / ".authorkit"
        if candidate.exists():
            return parent

    return packaged


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def record_managed(path: Path, root: Path, managed: set[str]) -> None:
    managed.add(str(path.relative_to(root).as_posix()))


def write_text(path: Path, content: str, root: Path, managed: set[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    record_managed(path, root, managed)


def copy_tree(src: Path, dst: Path, root: Path, managed: set[str]) -> None:
    if not src.exists():
        return
    for p in src.rglob("*"):
        rel = p.relative_to(src)
        target = dst / rel
        if p.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, target)
        record_managed(target, root, managed)


def parse_frontmatter(text: str) -> tuple[list[str], str]:
    if not text.startswith("---\n"):
        return [], text
    end = text.find("\n---\n", 4)
    if end < 0:
        return [], text
    fm = text[4:end].splitlines()
    body = text[end + 5 :]
    return fm, body


def remove_block(lines: list[str], key: str) -> list[str]:
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
    for i, line in enumerate(frontmatter_lines):
        if line.strip() == "scripts:" and i + 1 < len(frontmatter_lines):
            j = i + 1
            while j < len(frontmatter_lines) and re.match(r"^\s{2,}", frontmatter_lines[j]):
                m = re.match(r"^\s{2,}(?:ps|sh):\s*(.+)$", frontmatter_lines[j])
                if m:
                    return m.group(1).strip()
                j += 1
    return None


def resolve_script(path_from_frontmatter: str | None, script_type: str) -> str:
    if not path_from_frontmatter:
        return ""
    script_name = Path(path_from_frontmatter).name
    if script_type == "sh":
        script_name = script_name.replace(".ps1", ".sh")
        return f".authorkit/scripts/bash/{script_name}"
    return f".authorkit/scripts/powershell/{script_name}"


def resolve_token_script(token: str, script_type: str) -> str:
    token_map = {
        "{{SCRIPT_CHECK_PREREQ}}": "check-prerequisites",
        "{{SCRIPT_CREATE_BOOK}}": "create-new-book",
        "{{SCRIPT_SETUP_OUTLINE}}": "setup-outline",
        "{{SCRIPT_BUILD_WORLD_INDEX}}": "build-world-index",
    }
    stem = token_map.get(token)
    if not stem:
        return ""
    if script_type == "sh":
        return f".authorkit/scripts/bash/{stem}.sh"
    return f".authorkit/scripts/powershell/{stem}.ps1"


def render_prompt(raw: str, ai: str, script_type: str) -> str:
    fm, body = parse_frontmatter(raw)
    script = resolve_script(extract_script_path(fm), script_type)

    if ai == "claude":
        body = body.replace("{{USER_INPUT_TOKEN}}", "$ARGUMENTS")
        body = body.replace("{SCRIPT}", script)
        for token in ["{{SCRIPT_CHECK_PREREQ}}", "{{SCRIPT_CREATE_BOOK}}", "{{SCRIPT_SETUP_OUTLINE}}", "{{SCRIPT_BUILD_WORLD_INDEX}}"]:
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
    for token in ["{{SCRIPT_CHECK_PREREQ}}", "{{SCRIPT_CREATE_BOOK}}", "{{SCRIPT_SETUP_OUTLINE}}", "{{SCRIPT_BUILD_WORLD_INDEX}}"]:
        body = body.replace(token, resolve_token_script(token, script_type))

    fm_text = "\n".join(fm)
    return f"---\n{fm_text}\n---\n{body}"


def instruction_text(ai: str, script_type: str) -> tuple[str, str]:
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
    if ai == "claude":
        return f".claude/commands/{prompt_name}"
    if ai == "copilot":
        return f".github/prompts/{prompt_name.replace('.md', '.prompt.md')}"
    return f".codex/prompts/{prompt_name}"


def ensure_shell_exec_bits(root: Path) -> None:
    if os.name == "nt":
        return
    bash_root = root / ".authorkit" / "scripts" / "bash"
    if not bash_root.is_dir():
        return
    for sh_file in bash_root.rglob("*.sh"):
        mode = sh_file.stat().st_mode
        sh_file.chmod(mode | 0o755)


def tool_exists(tool: str) -> bool:
    return shutil.which(tool) is not None


def load_manifest(project_path: Path) -> dict:
    manifest = project_path / ".authorkit" / "install-manifest.json"
    if not manifest.exists():
        return {}
    try:
        return json.loads(read_text(manifest))
    except Exception:
        return {}


def remove_old_managed_paths(project_path: Path, previous: dict) -> None:
    for rel in previous.get("managed_paths", []):
        p = project_path / rel
        if p.is_file():
            p.unlink(missing_ok=True)


def write_manifest(project_path: Path, ai: str, script: str, managed: set[str]) -> None:
    manifest_path = project_path / ".authorkit" / "install-manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "installed_at": datetime.now(timezone.utc).isoformat(),
        "version": "0.1.0",
        "ai": ai,
        "script": script,
        "managed_paths": sorted(managed),
    }
    manifest_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


@app.command()
def init(
    project_name: str | None = typer.Argument(None, help="Project directory name, or '.' for current directory"),
    ai: str | None = typer.Option(None, "--ai", help="claude, copilot, or codex"),
    script: str | None = typer.Option(None, "--script", help="sh or ps"),
    ignore_agent_tools: bool = typer.Option(False, "--ignore-agent-tools"),
    no_git: bool = typer.Option(False, "--no-git"),
    here: bool = typer.Option(False, "--here"),
    force: bool = typer.Option(False, "--force"),
) -> None:
    if project_name == ".":
        here = True
        project_name = None

    if here and project_name:
        raise typer.BadParameter("Cannot pass both project name and --here")
    if not here and not project_name:
        raise typer.BadParameter("Provide project name, '.' or --here")

    selected_ai = ai or "copilot"
    if selected_ai not in AGENT_CONFIG:
        raise typer.BadParameter(f"Invalid --ai. Use one of: {', '.join(AGENT_CONFIG)}")

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

    if not ignore_agent_tools and AGENT_CONFIG[selected_ai]["requires_cli"]:
        tool = AGENT_CONFIG[selected_ai]["tool"]
        if tool and not tool_exists(tool):
            raise typer.BadParameter(f"Required tool not found in PATH: {tool}. Use --ignore-agent-tools to skip check.")

    previous = load_manifest(project_path)
    remove_old_managed_paths(project_path, previous)

    managed: set[str] = set()
    assets = asset_root()

    copy_tree(assets / ".authorkit" / "templates", project_path / ".authorkit" / "templates", project_path, managed)
    copy_tree(assets / ".authorkit" / "memory", project_path / ".authorkit" / "memory", project_path, managed)

    prompts_dir = project_path / ".authorkit" / "prompts"
    copy_tree(assets / ".authorkit" / "prompts", prompts_dir, project_path, managed)

    selected_script_src = assets / ".authorkit" / "scripts" / ("bash" if selected_script == "sh" else "powershell")
    copy_tree(
        selected_script_src,
        project_path / ".authorkit" / "scripts" / ("bash" if selected_script == "sh" else "powershell"),
        project_path,
        managed,
    )

    for prompt in sorted((assets / ".authorkit" / "prompts").glob("authorkit*.md")):
        raw = read_text(prompt)
        rendered = render_prompt(raw, selected_ai, selected_script)
        out_rel = prompt_out_path(selected_ai, prompt.name)
        write_text(project_path / out_rel, rendered, project_path, managed)

    instr_rel, instr_content = instruction_text(selected_ai, selected_script)
    write_text(project_path / instr_rel, instr_content, project_path, managed)

    write_manifest(project_path, selected_ai, selected_script, managed)

    if not no_git:
        try:
            subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=project_path, check=True, capture_output=True)
        except Exception:
            subprocess.run(["git", "init"], cwd=project_path, check=False)

    ensure_shell_exec_bits(project_path)

    console.print(f"Installed Author Kit in [bold]{project_path}[/bold]")
    console.print(f"AI flavor: [bold]{selected_ai}[/bold], script flavor: [bold]{selected_script}[/bold]")
    if selected_ai == "codex":
        codex_home = project_path / ".codex"
        if os.name == "nt":
            console.print(f"Set CODEX_HOME: setx CODEX_HOME {codex_home}")
        else:
            console.print(f"Set CODEX_HOME: export CODEX_HOME={codex_home}")


@app.command()
def check() -> None:
    console.print("Tool checks:")
    console.print(f"- git: {'ok' if tool_exists('git') else 'missing'}")
    console.print(f"- claude: {'ok' if tool_exists('claude') else 'missing'}")
    console.print(f"- codex: {'ok' if tool_exists('codex') else 'missing'}")


@app.command()
def version() -> None:
    console.print("authorkit-cli 0.1.0")
    console.print(f"Python {platform.python_version()}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
