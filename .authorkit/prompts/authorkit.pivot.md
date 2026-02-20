---
description: Propagate a mid-process direction change across all book artifacts with impact analysis.
handoffs:
  - label: Revise Affected Chapters
    agent: authorkit.revise
    prompt: Address the changes identified in the pivot plan
  - label: Re-Outline
    agent: authorkit.outline
    prompt: Regenerate the outline to reflect the pivot
  - label: Verify World After Pivot
    agent: authorkit.world.verify
    prompt: Verify world consistency after the pivot
  - label: Snapshot Before Pivot
    agent: authorkit.snapshot
    prompt: Create a snapshot before applying the pivot
scripts:
  ps: scripts/powershell/check-prerequisites.ps1 -Json -IncludeChapters
---

## User Input

```text
{{USER_INPUT_TOKEN}}
```

You **MUST** consider the user input before proceeding (if not empty). The user input describes the direction change in natural language (e.g., "Merge characters A and B", "The story should end with X instead of Y", "Cut the romance subplot entirely", "Change the setting from London to Paris").

## Goal

When the author's vision changes mid-process — not because a review found issues, but because the author wants to take the book in a different direction — propagate that change across all existing artifacts in a structured, traceable way.

This is different from `/authorkit.revise` (which fixes issues found by review/analyze). Pivot handles **author-initiated direction changes** that may affect concept, outline, chapters, plans, drafts, and world files.

## Outline

1. **Setup**: Run `{{SCRIPT_CHECK_PREREQ}}` from repo root and parse BOOK_DIR and AVAILABLE_DOCS. All paths must be absolute.

2. **Parse the pivot request** from user input:
   - If empty: ERROR "Please describe the direction change (e.g., /authorkit.pivot Cut the romance subplot entirely)"
   - Classify the pivot type:
     - **Character pivot**: Merge, cut, add, or fundamentally change a character
     - **Plot pivot**: Change ending, cut/add subplot, alter key event
     - **Setting pivot**: Change location, time period, or world rules
     - **Structural pivot**: Change POV, tense, chapter order, add/remove parts
     - **Theme pivot**: Add, remove, or redefine a core theme
     - **Scope pivot**: Significantly expand or contract the book's scope
   - A single pivot may span multiple types

3. **Impact analysis** — scan ALL existing artifacts for references to the changing elements:

   a. **concept.md**: Which sections reference the changing elements?
   b. **outline.md**: Which chapter entries, arcs, and thematic maps are affected?
   c. **chapters.md**: Which chapter summaries reference the changing elements?
   d. **characters.md**: Which profiles need updating?
   e. **world/ files**: Which entity files reference the changing elements? **If `world/_index.md` exists**: Use the Alias Lookup to find all name variants for the affected entities. Read their frontmatter `relationships` fields to identify connected entities. Use the Entity Registry to get file paths. Search only the identified files, rather than all world/ files.
   f. **Chapter plans** (`chapters/NN/plan.md`): Which plans reference the changing elements?
   g. **Chapter drafts** (`chapters/NN/draft.md`): Which drafted chapters contain the changing elements?
   h. **Chapter reviews** (`chapters/NN/review.md`): Which reviews reference the changing elements?
   i. **constitution**: Does the pivot conflict with any writing principles?

   For each artifact, record:
   - File path
   - What specifically needs to change
   - Whether the change is minor (wording) or major (structural)
   - Dependencies (e.g., "outline must be updated before chapter plans")

4. **Present the pivot plan** to the user:

   ```markdown
   ## Pivot Plan: [SHORT DESCRIPTION]

   **Pivot Type**: [Character / Plot / Setting / Structural / Theme / Scope]
   **Date**: [DATE]
   **Description**: [User's stated change]

   ### Impact Summary

   | Artifact | Impact Level | Changes Needed |
   |----------|-------------|----------------|
   | concept.md | [None/Minor/Major] | [What needs to change] |
   | outline.md | [None/Minor/Major] | [What needs to change] |
   | chapters.md | [None/Minor/Major] | [What needs to change] |
   | characters.md | [None/Minor/Major] | [What needs to change] |
   | world/ | [None/Minor/Major] | [N files affected: list] |
   | Chapter plans | [None/Minor/Major] | [N plans affected: list] |
   | Chapter drafts | [None/Minor/Major] | [N drafts affected: list] |
   | Constitution | [None/Conflict] | [Any conflicts] |

   ### Execution Order

   1. [First artifact to update] — [why first]
   2. [Second artifact] — [depends on first because...]
   3. ...

   ### Risk Assessment

   - **Cascade risk**: [Low/Medium/High] — [how many downstream artifacts are affected]
   - **Consistency risk**: [Low/Medium/High] — [likelihood of introducing contradictions]
   - **Effort estimate**: [N artifacts to update, M chapters to revise]

   ### Recommendation

   [Suggest whether to proceed, suggest snapshotting first, flag any concerns]
   ```

5. **Wait for user approval** before making any changes. The user may:
   - Approve the full plan
   - Modify the plan (e.g., "Don't touch chapters 1-3, they're fine")
   - Abandon the pivot
   - Request a snapshot first (`/authorkit.snapshot`)

6. **Execute the pivot** top-down (upstream artifacts first, downstream last):

   a. **Update concept.md**: Modify affected sections to reflect the new direction.

   b. **Update outline.md**: Modify affected chapter entries, arcs, and thematic maps. If the pivot is structural (adding/removing chapters), regenerate the affected sections.

   c. **Update chapters.md**: Modify affected chapter summaries. If chapters are added/removed, renumber accordingly.

   d. **Update characters.md**: Modify affected character profiles.

   e. **Update world/ files**: Modify affected entity files. Tag changes with `(PIVOT-[DATE])` to distinguish from chapter-driven updates. Add cross-references as needed. After modifying world/ files, update their YAML frontmatter: add `PIVOT-YYYY-MM-DD` to the `chapters` field, update any changed `aliases` or `relationships`, update `last_updated`. Run `.authorkit/scripts/powershell/build-world-index.ps1 -Json` to rebuild the index.

   f. **Update chapter plans**: Modify affected plans. Reset chapter status to `[P]` if the plan changed significantly.

   g. **Update chapter drafts**: For minor pivots (name changes, small detail changes), apply targeted edits directly. For major pivots (structural changes, subplot removal), reset chapter status to `[P]` and flag for re-drafting rather than attempting to patch.

   h. **Reset chapter statuses** as appropriate:
      - Chapters with minor edits: keep current status
      - Chapters with significant plan changes: reset to `[P]`
      - Chapters needing re-draft: reset to `[P]` (re-plan first)
      - Chapters needing re-review: reset to `[D]`

7. **Write pivot log** to `BOOK_DIR/pivots/YYYY-MM-DD-[short-description].md`:

   ```markdown
   # Pivot: [SHORT DESCRIPTION]

   **Date**: [DATE]
   **Type**: [Character / Plot / Setting / Structural / Theme / Scope]

   ## Change Description

   [User's original description]

   ## Artifacts Modified

   | File | Change Summary |
   |------|---------------|
   | [path] | [what was changed] |

   ## Chapter Status Changes

   | Chapter | Before | After | Reason |
   |---------|--------|-------|--------|
   | CH03 | [X] | [P] | Major plot restructure |

   ## Deferred Items

   - [Items the user chose not to update now]

   ## Notes

   - [Any observations or recommendations for future work]
   ```

8. **Report completion**:
   - Summary of all changes made
   - Files modified (with paths)
   - Chapter statuses reset
   - Deferred items (artifacts not yet updated)
   - Suggested next steps:
     - `/authorkit.chapter.plan [N]` for chapters reset to `[ ]` or `[P]`
     - `/authorkit.analyze` to verify cross-chapter consistency after the pivot
     - `/authorkit.world.verify` to check world consistency

## Pivot Principles

- **Top-down propagation**: Always update upstream artifacts (concept, outline) before downstream ones (plans, drafts). This prevents cascading inconsistencies.
- **Snapshot first for large pivots**: If the impact analysis shows 5+ artifacts affected, recommend creating a snapshot before proceeding.
- **Preserve what works**: Don't rewrite sections unaffected by the pivot. Targeted edits over wholesale replacement.
- **Tag changes**: Use `(PIVOT-YYYY-MM-DD)` tags in world/ files to distinguish pivot-driven changes from chapter-driven updates.
- **Flag, don't force**: For chapters with approved `[X]` status, flag them for user attention rather than silently resetting.
- **Log everything**: The pivot log is the historical record. It should capture both what changed and what was deliberately left unchanged.
- **Constitution check**: If the pivot conflicts with writing principles (e.g., changing POV mid-book), flag the conflict and suggest a constitution amendment.

