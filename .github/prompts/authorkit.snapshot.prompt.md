---
description: Bookmark the current book state with narrative context before a risky change.
mode: agent
---

## User Input

```text
${input:snapshotInput}
```

You **MUST** consider the user input before proceeding (if not empty).

## Goal

Create a named, contextual bookmark of the book's current state before making risky changes. Unlike a bare git tag, a snapshot includes **narrative reasoning** — what's working, what's uncertain, and what decision is being contemplated.

The command operates in three modes:

- **Create** (default): Bookmark the current state
- **List**: Show all snapshots
- **Compare**: Diff the current state against a snapshot with narrative context

## Outline

1. **Setup**: Run `.authorkit/scripts/powershell/check-prerequisites.ps1 -Json -IncludeChapters` from repo root and parse BOOK_DIR and AVAILABLE_DOCS. All paths must be absolute.

2. **Determine mode** from user input:
   - **Create mode** (default): User provides a description (e.g., "Before cutting the romance subplot")
   - **List mode**: Input like "list", "show", "snapshots"
   - **Compare mode**: Input like "compare with 2026-02-01-pre-romance-cut"

3. **Create Mode**:
   - Generate slug from description
   - Assess current book state (chapters.md statuses, word counts, World/ files, parked decisions)
   - Create snapshot file at `BOOK_DIR/snapshots/YYYY-MM-DD-[slug].md` with: progress table, what's working well, current uncertainties, decision being contemplated, context for future comparison
   - Create git tag: `snapshot/YYYY-MM-DD-[slug]`
   - Report: file path, git tag, state summary

4. **List Mode**:
   - Check `BOOK_DIR/snapshots/` and git tags matching `snapshot/*`
   - Present summary table with date, description, tag, chapter counts

5. **Compare Mode**:
   - Load snapshot file for narrative context
   - Generate narrative diff: progress changes, decision outcome, key narrative differences
   - Optionally run `git diff` for file-level overview
   - Report comparison with context

## Key Rules

- **Snapshots are lightweight.** Narrative summary + git tag. Git handles actual state.
- **Always create a git tag.** The file provides context; the tag provides the revertible state.
- **Capture narrative, not just metrics.** "What's working" and "what's uncertain" are more valuable than chapter counts.
- **Don't clutter.** Snapshots are for decision points, not routine checkpoints.
