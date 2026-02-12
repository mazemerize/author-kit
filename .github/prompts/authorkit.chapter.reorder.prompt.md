---
description: Reorder, split, or merge chapters with automatic renumbering and cross-reference updates.
mode: agent
---

## User Input

```text
${input:reorderOperation}
```

You **MUST** consider the user input before proceeding (if not empty). The user input describes the structural change: reorder, split, or merge.

## Goal

Handle structural rearrangements of the chapter order — moves, splits, and merges — with automatic renumbering of files, chapter IDs, cross-references, and World/ tags.

## Outline

1. **Setup**: Run `.authorkit/scripts/powershell/check-prerequisites.ps1 -Json -IncludeChapters` from repo root and parse BOOK_DIR and AVAILABLE_DOCS. All paths must be absolute.

2. **Parse the operation** from user input:
   - **Reorder / Move**: "Move CH05 to after CH02", "Swap CH03 and CH07"
   - **Split**: "Split CH04 into two chapters", "Split CH04 at scene 3"
   - **Merge**: "Merge CH06 and CH07"
   - **Insert**: "Insert a new chapter between CH03 and CH04"
   - **Remove**: "Remove CH08" (archives, doesn't delete)

3. **Assess current state**: Read chapters.md, identify existing files, scan World/ for tags, scan plans/drafts for cross-references.

4. **Generate the reorder plan**: Show current structure, proposed structure, file operations, cross-reference updates, and risk assessment. Wait for user approval.

5. **Execute the reorder** in phases:
   - Phase 1: Move files to temporary locations (avoid collisions)
   - Phase 2: Move files to final locations
   - Phase 3: Handle splits/merges/inserts/removes
   - Phase 4: Update chapters.md with new numbering
   - Phase 5: Update cross-references (outline.md, World/ tags, plans, parked decisions)
   - Phase 6: Update outline.md structure

6. **Post-reorder validation**: Verify directories, chapters.md consistency, World/ tag integrity, cross-references.

7. **Report completion**: Changes made, cross-references updated, validation results, next steps.

## Operation-Specific Rules

- **Reorder**: Content preserved, only numbering changes, status markers preserved
- **Split**: Draft divided at specified point, both chapters reset to `[P]`, balanced word counts
- **Merge**: Drafts concatenated, set to `[D]`, removed chapter archived
- **Insert**: Empty slot created at `[ ]`, subsequent chapters renumbered
- **Remove**: Chapter archived to `chapters/archived/`, never deleted

## Key Rules

- **Use temp directories** during renaming to avoid collisions
- **Archive, never delete** removed chapters
- **Update everything**: chapters.md, outline.md, World/ tags, plans, parked decisions
- **Validate after** to catch missed references
- **Recommend snapshot** for large reorders (5+ chapters affected)
