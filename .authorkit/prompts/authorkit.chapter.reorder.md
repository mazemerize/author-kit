---
description: Reorder, split, or merge chapters with automatic renumbering and cross-reference updates.
handoffs:
  - label: Update Outline
    agent: authorkit.outline
    prompt: Update the outline to reflect the restructured chapters
  - label: Verify World Tags
    agent: authorkit.world.verify
    prompt: Verify chapter tags in World/ files after reorder
  - label: Run Analysis
    agent: authorkit.analyze
    prompt: Analyze consistency after chapter restructuring
scripts:
  ps: scripts/powershell/check-prerequisites.ps1 -Json -IncludeChapters
---

## User Input

```text
{{USER_INPUT_TOKEN}}
```

You **MUST** consider the user input before proceeding (if not empty). The user input describes the structural change: reorder, split, or merge.

## Goal

Handle structural rearrangements of the chapter order — moves, splits, and merges — with automatic renumbering of files, chapter IDs, cross-references, and World/ tags. This avoids the error-prone manual process of renaming folders, updating chapters.md, and fixing all references.

## Outline

1. **Setup**: Run `{{SCRIPT_CHECK_PREREQ}}` from repo root and parse BOOK_DIR and AVAILABLE_DOCS. All paths must be absolute.

2. **Parse the operation** from user input:

   - **Reorder / Move**: "Move CH05 to after CH02", "Swap CH03 and CH07", "Move chapters 8-10 to before chapter 5"
   - **Split**: "Split CH04 into two chapters", "Split CH04 at scene 3"
   - **Merge**: "Merge CH06 and CH07", "Combine chapters 3, 4, and 5 into one"
   - **Insert**: "Insert a new chapter between CH03 and CH04"
   - **Remove**: "Remove CH08" (moves to an archive, doesn't delete)

   If unclear: ask the user to specify the operation.

3. **Assess current state**:

   a. Read chapters.md for the full chapter list and statuses.
   b. Identify which chapters have existing files (plan.md, draft.md, review.md).
   c. Read outline.md for chapter descriptions and connections.
   d. Scan World/ files for `(CHxx)` tags that reference affected chapters. **If `World/_index.md` exists**: Use the Entity Registry `Chapters` column to find all files with tags for the affected chapter numbers — no need to scan every World/ file.
   e. Scan chapter plans and drafts for cross-references to other chapters.

4. **Generate the reorder plan**:

   ```markdown
   ## Chapter Reorder Plan

   **Operation**: [Move / Split / Merge / Insert / Remove]
   **Date**: [DATE]

   ### Current Structure

   | # | ID | Title | Status | Has Plan | Has Draft | Has Review |
   |---|-----|-------|--------|----------|-----------|------------|
   | 1 | CH01 | [Title] | [X] | Yes | Yes | Yes |
   | 2 | CH02 | [Title] | [D] | Yes | Yes | No |
   | ... |

   ### Proposed Structure

   | # | Old ID | New ID | Title | Status | Action |
   |---|--------|--------|-------|--------|--------|
   | 1 | CH01 | CH01 | [Title] | [X] | Unchanged |
   | 2 | CH05 | CH02 | [Title] | [D] | Moved from position 5 |
   | 3 | CH02 | CH03 | [Title] | [D] | Renumbered (was CH02) |
   | ... |

   ### File Operations

   | Operation | Source | Destination |
   |-----------|--------|-------------|
   | Rename dir | chapters/05/ | chapters/02/ |
   | Rename dir | chapters/02/ | chapters/03/ |
   | ... |

   ### Cross-Reference Updates

   | File | Current Reference | New Reference |
   |------|------------------|---------------|
   | chapters/01/plan.md | "CH05" | "CH02" |
   | World/Characters/elena.md | "(CH05)" | "(CH02)" |
   | outline.md | "Chapter 5" | "Chapter 2" |
   | ... |

   ### Risk Assessment

   - **Drafted chapters affected**: [N]
   - **Approved chapters affected**: [N]
   - **World/ tags to update**: [N]
   - **Cross-references to update**: [N]
   ```

5. **Wait for user approval**. The user may:
   - Approve the full plan
   - Modify the plan
   - Abandon the operation
   - Request a snapshot first

6. **Execute the reorder**:

   **IMPORTANT**: Use temporary directories to avoid file collisions during renaming.

   a. **Phase 1 — Move files to temporary locations**:
      - For each chapter being renumbered: move `chapters/NN/` to `chapters/tmp_NN/`
      - This prevents collisions (e.g., when swapping CH03 and CH07)

   b. **Phase 2 — Move files to final locations**:
      - For each chapter: move `chapters/tmp_NN/` to `chapters/[NEW_NN]/`
      - Create new directories as needed

   c. **Phase 3 — Handle operation-specific logic**:

      **For splits**:
      - Create new chapter directory
      - If a draft exists: Split the draft content at the specified point (scene break, heading, etc.)
      - Create separate plan.md files for each resulting chapter
      - Set status of both new chapters to `[P]` (need re-planning with new scope)

      **For merges**:
      - Combine draft content into a single file (with clear section breaks)
      - Combine plan content into a single plan
      - Archive the removed chapter's directory to `chapters/archived/`
      - Set status to `[D]` (needs re-review as combined chapter)

      **For inserts**:
      - Create empty chapter directory with placeholder plan
      - Set status to `[ ]` (pending)

      **For removes**:
      - Move chapter directory to `chapters/archived/[NN]-[title]/`
      - Do NOT delete — archive for potential recovery

   d. **Phase 4 — Update chapters.md**:
      - Rewrite the chapter list with new numbering
      - Preserve existing statuses (adjusted for splits/merges)
      - Update part/act boundaries if affected

   e. **Phase 5 — Update cross-references**:
      - **outline.md**: Update all chapter references
      - **World/ files**: Update all `(CHxx)`, `(CHxx-rev)`, `(RETCON-date)` tags
      - **Chapter plans**: Update references to other chapters (e.g., "continues from CH03")
      - **Chapter drafts**: Update any explicit chapter references in prose (rare but possible in non-fiction)
      - **parked-decisions.md** (if exists): Update deadline references (e.g., "Before CH12")
      - **Pivot logs** (if exist): Note the renumbering but don't rewrite history

   f. **Phase 6 — Update outline.md**:
      - Reorder chapter entries to match new structure
      - Update arc and theme maps if chapters moved between parts/acts

   g. **Phase 7 — Update World/ frontmatter and rebuild index**:
      - For every World/ file whose `(CHxx)` tags were renumbered: update the YAML frontmatter `chapters` field to reflect the new chapter numbers. Update `last_updated`.
      - Run `.authorkit/scripts/powershell/build-world-index.ps1 -Json` from the repo root to rebuild `World/_index.md`.

7. **Post-reorder validation**:
   - Verify all chapter directories exist at their new locations
   - Verify chapters.md has the correct count and no duplicate IDs
   - Verify no orphaned World/ tags (tags referencing chapters that no longer exist at that number)
   - Verify no broken cross-references in plans

8. **Report completion**:

   ```markdown
   ## Reorder Complete

   **Operation**: [description]
   **Chapters affected**: [N]

   ### Changes Made

   | Old ID | New ID | Files Moved |
   |--------|--------|-------------|
   | CH05 | CH02 | plan.md, draft.md |

   ### Cross-References Updated

   - [N] references in outline.md
   - [N] tags in World/ files
   - [N] references in chapter plans
   - [N] entries in chapters.md

   ### Validation

   - All chapter directories: OK
   - chapters.md consistency: OK
   - World/ tag integrity: OK
   - Cross-references: OK

   ### Next Steps

   - `/authorkit.analyze` — verify cross-chapter consistency after restructure
   - `/authorkit.world.verify` — check World/ tag integrity
   - [For splits]: `/authorkit.chapter.plan [N]` — plan the new chapter(s)
   - [For merges]: `/authorkit.chapter.review [N]` — review the combined chapter
   ```

## Operation-Specific Rules

### Reorder / Move
- Chapters keep their existing content — only the numbering changes
- Status markers are preserved
- The most complex part is updating all cross-references

### Split
- The original chapter's draft (if any) is divided at the specified point
- Both resulting chapters need re-planning (status reset to `[P]`)
- If no split point is specified, suggest natural break points (scene breaks, heading boundaries)
- Word counts should be roughly balanced unless the author specifies otherwise

### Merge
- Drafts are concatenated with a clear break marker between them
- The merged chapter likely needs re-review (status set to `[D]`)
- Removed chapter is archived, not deleted
- The surviving chapter gets the lower chapter number by default

### Insert
- Creates an empty chapter slot with `[ ]` status
- All subsequent chapters are renumbered
- The outline needs updating to describe the new chapter

### Remove
- The chapter is archived to `chapters/archived/`
- All subsequent chapters are renumbered
- References to the removed chapter in other plans/drafts are flagged for manual attention

## Key Rules

- **Use temp directories.** Never rename directly from old to new — this causes collisions when numbers overlap.
- **Archive, never delete.** Removed or merged-away chapters go to `chapters/archived/`, not the trash.
- **Update everything.** The value of this command is that it handles ALL the renumbering — chapters.md, outline.md, World/ tags, plan cross-references, parked decision deadlines.
- **Validate after.** Always run the post-reorder validation to catch any missed references.
- **Recommend snapshot for large reorders.** If 5+ chapters are affected, suggest `/authorkit.snapshot` first.

