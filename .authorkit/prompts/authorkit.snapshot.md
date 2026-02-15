---
description: Bookmark the current book state with narrative context before a risky change.
handoffs:
  - label: Apply Pivot
    agent: authorkit.pivot
    prompt: Now apply the pivot I was planning
  - label: Compare With Snapshot
    agent: authorkit.snapshot
    prompt: Compare current state with snapshot...
  - label: Start What-If Branch
    agent: authorkit.whatif
    prompt: Start an experimental branch from this snapshot
scripts:
  ps: scripts/powershell/check-prerequisites.ps1 -Json -IncludeChapters
---

## User Input

```text
{{USER_INPUT_TOKEN}}
```

You **MUST** consider the user input before proceeding (if not empty).

## Goal

Create a named, contextual bookmark of the book's current state before making risky changes. Unlike a bare git tag, a snapshot includes **narrative reasoning** — what's working, what's uncertain, and what decision is being contemplated. This makes it meaningful to compare against later.

The command operates in three modes:

- **Create** (default): Bookmark the current state
- **List**: Show all snapshots
- **Compare**: Diff the current state against a snapshot with narrative context

## Outline

1. **Setup**: Run `{{SCRIPT_CHECK_PREREQ}}` from repo root and parse BOOK_DIR and AVAILABLE_DOCS. All paths must be absolute.

2. **Determine mode** from user input:

   - **Create mode** (default): User provides a description or context
     - Input like: "Before cutting the romance subplot", "Decision point: Marcus lives or dies", "Pre-restructure of Act 3"
   - **List mode**: User asks to see snapshots
     - Input like: "list", "show", "snapshots"
   - **Compare mode**: User wants to diff against a snapshot
     - Input like: "compare with 2026-02-01-pre-romance-cut", "diff snapshot 3"

3. **Create Mode** — Bookmark current state:

   a. Generate a short description slug from user input (e.g., "pre-romance-cut", "marcus-decision-point", "act3-restructure").

   b. **Assess current book state** by reading:
      - chapters.md: Count chapters by status (`[ ]`, `[P]`, `[D]`, `[R]`, `[X]`)
      - concept.md: Current premise summary
      - outline.md: Structure overview
      - World/ folder: Count of entity files per category
      - parked-decisions.md (if exists): Count of OPEN decisions
      - pivots/ (if exists): Count of previous pivots

   c. **Create snapshot file** at `BOOK_DIR/snapshots/YYYY-MM-DD-[slug].md`:

      ```markdown
      # Snapshot: [DESCRIPTION]

      **Date**: [DATE]
      **Git Tag**: snapshot/YYYY-MM-DD-[slug]
      **Branch**: [current git branch]

      ## Book State

      ### Progress

      | Status | Count | Chapters |
      |--------|-------|----------|
      | Pending [ ] | [N] | CH06-CH20 |
      | Planned [P] | [N] | CH05 |
      | Drafted [D] | [N] | CH04 |
      | Reviewed [R] | [N] | - |
      | Approved [X] | [N] | CH01-CH03 |

      **Total word count**: [estimated from drafts]
      **World/ files**: [N] across [N] categories

      ### What's Working Well

      - [Key strength — e.g., "The mystery structure is tight through chapters 1-3"]
      - [Another strength]

      ### Current Uncertainties

      - [What's not yet decided — e.g., "Whether Marcus survives Act 3"]
      - [Parked decisions, if any]

      ### Decision Being Contemplated

      [The reason for this snapshot — what change is being considered]

      ## Context for Future Comparison

      - **Key plot points so far**: [Brief summary of major events in drafted chapters]
      - **Character states**: [Where each major character is at this point]
      - **Open threads**: [Unresolved story threads or pending arguments]
      ```

   d. **Create git tag**: Run `git tag snapshot/YYYY-MM-DD-[slug]` to bookmark the exact commit state.

   e. Report: Snapshot created, file path, git tag name, summary of captured state.

4. **List Mode** — Show all snapshots:

   a. Check for snapshot files in `BOOK_DIR/snapshots/` and git tags matching `snapshot/*`.

   b. Present a summary table:

      ```markdown
      ## Snapshots

      | # | Date | Description | Git Tag | Chapters at Time |
      |---|------|-------------|---------|-----------------|
      | 1 | 2026-02-01 | Pre-romance-cut | snapshot/2026-02-01-pre-romance-cut | 3 drafted, 2 approved |
      | 2 | 2026-02-05 | Marcus-decision | snapshot/2026-02-05-marcus-decision | 5 drafted, 3 approved |
      ```

   c. Report list with paths to snapshot files.

5. **Compare Mode** — Diff current state against a snapshot:

   a. Identify the snapshot (by date slug, number from list, or partial match).

   b. Load the snapshot file for context.

   c. **Narrative diff** (not just file diff):

      ```markdown
      ## Comparison: Current vs [SNAPSHOT NAME]

      **Snapshot Date**: [DATE]
      **Days Since**: [N]

      ### Progress Changes

      | Metric | At Snapshot | Now | Change |
      |--------|-----------|-----|--------|
      | Chapters drafted | [N] | [N] | +[N] |
      | Chapters approved | [N] | [N] | +[N] |
      | Total word count | [N] | [N] | +[N] |
      | World/ files | [N] | [N] | +[N] |
      | Pivots since | - | [N] | [list] |

      ### Decision Outcome

      **Contemplated**: [What was being considered at snapshot time]
      **What happened**: [What was actually decided and how it played out]

      ### Key Narrative Differences

      - [Major plot/structure difference from the snapshot state]
      - [Characters added/removed/changed since snapshot]
      - [Themes shifted]

      ### Files Changed Since Snapshot

      [Summary of git diff --stat between snapshot tag and current HEAD]
      ```

   d. Optionally run `git diff snapshot/[tag]..HEAD --stat` for a file-level overview.

   e. Report comparison with narrative context.

## Key Rules

- **Snapshots are lightweight.** The file is a narrative summary, not a copy of all artifacts. Git handles the actual state preservation.
- **Always create a git tag.** The snapshot file provides context; the git tag provides the actual revertible state.
- **Capture narrative, not just metrics.** "What's working well" and "what's uncertain" are more valuable than chapter counts.
- **Recommend before risky changes.** When `/authorkit.pivot` detects 5+ artifacts affected, it should suggest snapshotting first.
- **Don't clutter.** Snapshots are for decision points, not routine checkpoints. Git commits handle the latter.

