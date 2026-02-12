---
description: Explore an alternative direction on an experimental branch without committing to it.
mode: agent
---

## User Input

```text
${input:whatifDescription}
```

You **MUST** consider the user input before proceeding (if not empty).

## Goal

Sometimes you want to **try** a creative direction without committing to it. This command creates a safe experimental branch where you can draft, plan, or revise freely, then compare the results against the original before deciding whether to keep, merge, or discard the experiment.

The command operates in four modes:

- **Start**: Create an experimental branch
- **Compare**: Summarize narrative differences between experiment and original
- **Merge**: Accept the experiment and merge it back
- **Discard**: Abandon the experiment and return to the original

## Outline

1. **Setup**: Run `.authorkit/scripts/powershell/check-prerequisites.ps1 -Json -IncludeChapters` from repo root and parse BOOK_DIR and AVAILABLE_DOCS. All paths must be absolute.

2. **Determine mode** from user input:
   - **Start mode** (default): "What if Marcus dies in chapter 5?", "Try first person POV"
   - **Compare mode**: "compare", "what changed?"
   - **Merge mode**: "merge", "keep this", "accept"
   - **Discard mode**: "discard", "abandon", "go back"

3. **Start Mode**:
   - Auto-create a snapshot of the current state
   - Create `whatif/[slug]` branch
   - Create `whatif-active.md` recording source branch, hypothesis, and success criteria
   - Report: branch created, use normal commands to experiment

4. **Compare Mode**:
   - Load `whatif-active.md` for context
   - Generate narrative comparison: plot differences, character differences, structural changes, word count deltas
   - Recommend: keep, discard, or partial merge

5. **Merge Mode**:
   - Confirm with user
   - Switch to source branch, merge with `--no-ff`, delete what-if branch
   - Remove `whatif-active.md`, update snapshot
   - Recommend running `authorkit.analyze`

6. **Discard Mode**:
   - Confirm with user
   - Switch to source branch, delete what-if branch with `-D`
   - Remove `whatif-active.md`, update snapshot
   - Note: recoverable via `git reflog`

## Key Rules

- **One experiment at a time.** Must merge or discard before starting another.
- **Auto-snapshot on start.** No manual step needed.
- **Normal workflow on branch.** All standard commands work normally.
- **Narrative comparison.** Compare mode tells *what's different about the story*, not just files.
- **Clean up.** Both merge and discard remove metadata and clean branches.
- **Git safety.** Use `--no-ff` for merges. Mention `git reflog` recovery for discards.
