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
- Author Kit is a single-book-per-repo model; use `book/` as the canonical workspace path.
- Use lowercase directory names under `book/...` (`world/`, `chapters/`, `checklists/`, `dist/` and `world/<entity-subdirs>/`).

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

## Testing From a Branch Build

If you want to validate CLI behavior from an unmerged branch, install/run directly from that branch ref:

```bash
uv tool install authorkit-cli --from git+https://github.com/mazemerize/author-kit.git@your-branch-name
```

One-shot execution without a persistent tool install:

```bash
uvx --from git+https://github.com/mazemerize/author-kit.git@your-branch-name authorkit version
```

## Documentation Expectations

If your change affects install flow, CLI flags, supported agents, or script behavior, update `README.md` in the same PR.

If your change affects contribution workflow, update this file.

## Pull Request Guidelines

- Keep PRs focused and scoped.
- Include a short summary of what changed and why.
- Include validation steps you ran (commands + outcome).
- Mention any known limitations or follow-up work.
