# Contributing to Author Kit

Thanks for contributing to Author Kit.

This repository is an installer-driven toolkit. Please read this before opening a PR so changes stay consistent with the project structure.

## Development Setup

Prerequisites:

- Python 3.11+
- `uv`
- Git
- Access to a coding agent (Claude, Copilot, Codex)

Clone the repo and run commands from the repository root.

## Project Model

Author Kit uses one canonical source of truth for toolkit content:

- `.authorkit/prompts/` - canonical prompt definitions
- `.authorkit/instructions/` - canonical instruction templates per agent
- `.authorkit/scripts/` - canonical automation scripts (`bash/` and `powershell/`)
- `.authorkit/templates/` and `.authorkit/memory/` - canonical content templates

The CLI (`src/authorkit_cli`) installs and renders agent-specific outputs into a target project (for example `.claude/commands`, `.github/prompts`, `.codex/prompts`).

Do not re-introduce duplicated prompt sources across agent folders in this repo.

## Key Contribution Rules

- Keep prompts centralized in `.authorkit/prompts`.
- Keep script behavior aligned across shell flavors (`.sh` and `.ps1`) when applicable.
- Preserve backward-compatible CLI behavior unless the change explicitly updates docs and migration expectations.
- Avoid destructive behavior in installer updates; managed files should be tracked through `.authorkit/install-manifest.json`.

## Running Local Checks

Basic Python syntax check:

```bash
python -m py_compile src/authorkit_cli/__init__.py
```

Run CLI from source (without installing globally):

```bash
uv run --with typer --with rich python -m authorkit_cli version
uv run --with typer --with rich python -m authorkit_cli check
```

Smoke test install in a temp folder:

```bash
uv run --with typer --with rich python -m authorkit_cli init . --ai claude,copilot,codex --script sh --here --force --ignore-agent-tools
```

On Windows, use `--script ps` if needed.

## Documentation Expectations

If your change affects install flow, CLI flags, supported agents, or script behavior, update `README.md` in the same PR.

If your change affects contribution workflow, update this file.

## Pull Request Guidelines

- Keep PRs focused and scoped.
- Include a short summary of what changed and why.
- Include validation steps you ran (commands + outcome).
- Mention any known limitations or follow-up work.

## Good First Contributions

- Prompt quality and clarity improvements in canonical prompts.
- Script parity fixes between bash and PowerShell.
- CLI UX improvements for installer output and error messaging.
- Docs improvements with concrete examples.
