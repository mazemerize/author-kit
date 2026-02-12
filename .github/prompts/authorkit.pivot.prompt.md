---
description: Propagate a mid-process direction change across all book artifacts with impact analysis.
mode: agent
---

## User Input

```text
${input:pivotDescription}
```

You **MUST** consider the user input before proceeding (if not empty). The user input describes the direction change in natural language (e.g., "Merge characters A and B", "The story should end with X instead of Y", "Cut the romance subplot entirely", "Change the setting from London to Paris").

## Goal

When the author's vision changes mid-process — not because a review found issues, but because the author wants to take the book in a different direction — propagate that change across all existing artifacts in a structured, traceable way.

This is different from `authorkit.revise` (which fixes issues found by review/analyze). Pivot handles **author-initiated direction changes** that may affect concept, outline, chapters, plans, drafts, and world files.

## Outline

1. **Setup**: Run `.authorkit/scripts/powershell/check-prerequisites.ps1 -Json -IncludeChapters` from repo root and parse BOOK_DIR and AVAILABLE_DOCS. All paths must be absolute.

2. **Parse the pivot request** from user input:
   - If empty: ERROR "Please describe the direction change"
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
   e. **World/ files**: Which entity files reference the changing elements?
   f. **Chapter plans** (`chapters/NN/plan.md`): Which plans reference the changing elements?
   g. **Chapter drafts** (`chapters/NN/draft.md`): Which drafted chapters contain the changing elements?
   h. **Chapter reviews** (`chapters/NN/review.md`): Which reviews reference the changing elements?
   i. **constitution**: Does the pivot conflict with any writing principles?

   For each artifact, record: file path, what specifically needs to change, whether the change is minor or major, and dependencies.

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
   | World/ | [None/Minor/Major] | [N files affected] |
   | Chapter plans | [None/Minor/Major] | [N plans affected] |
   | Chapter drafts | [None/Minor/Major] | [N drafts affected] |
   | Constitution | [None/Conflict] | [Any conflicts] |

   ### Execution Order

   1. [First artifact to update] — [why first]
   2. [Second artifact] — [depends on first because...]

   ### Risk Assessment

   - **Cascade risk**: [Low/Medium/High]
   - **Consistency risk**: [Low/Medium/High]
   - **Effort estimate**: [N artifacts to update, M chapters to revise]
   ```

5. **Wait for user approval** before making any changes.

6. **Execute the pivot** top-down (upstream artifacts first):
   - Update concept.md, outline.md, chapters.md, characters.md
   - Update World/ files (tag changes with `(PIVOT-YYYY-MM-DD)`)
   - Update chapter plans and drafts (minor: targeted edits; major: reset to `[P]`)
   - Reset chapter statuses as appropriate

7. **Write pivot log** to `BOOK_DIR/pivots/YYYY-MM-DD-[short-description].md` documenting all changes.

8. **Report completion**:
   - Summary of all changes made
   - Chapter statuses reset
   - Suggested next steps:
     - Use `authorkit.chapter.plan` for chapters needing re-planning
     - Use `authorkit.analyze` to verify consistency after the pivot
     - Use `authorkit.world.verify` to check world consistency

## Pivot Principles

- **Top-down propagation**: Update upstream artifacts (concept, outline) before downstream ones (plans, drafts).
- **Snapshot first for large pivots**: If 5+ artifacts are affected, recommend creating a snapshot first.
- **Preserve what works**: Targeted edits over wholesale replacement.
- **Tag changes**: Use `(PIVOT-YYYY-MM-DD)` tags in World/ files.
- **Flag, don't force**: For approved `[X]` chapters, flag for user attention.
- **Log everything**: The pivot log captures what changed and what was deliberately left unchanged.
- **Constitution check**: Flag conflicts with writing principles; suggest amendments if needed.
