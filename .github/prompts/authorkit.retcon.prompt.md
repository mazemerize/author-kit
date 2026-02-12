---
description: Retroactively change an established fact across all chapters, plans, and world files.
mode: agent
---

## User Input

```text
${input:retconChange}
```

You **MUST** consider the user input before proceeding (if not empty). The user input should specify what fact is changing, in the format: "[old fact] -> [new fact]" or a natural language description of the change.

## Goal

When a mid-story discovery or creative decision requires changing an **established fact** across previously written chapters — a character's backstory, a place's description, a timeline detail, a world rule — find every reference and update it consistently while preserving each chapter's voice and style.

This is more specific than `authorkit.pivot` (which handles broad direction changes) and more systematic than `authorkit.revise` (which targets specific issues). Retcon handles the **search-and-replace-with-intelligence** problem.

## Outline

1. **Setup**: Run `.authorkit/scripts/powershell/check-prerequisites.ps1 -Json -IncludeChapters` from repo root and parse BOOK_DIR and AVAILABLE_DOCS. All paths must be absolute.

2. **Parse the retcon** from user input:
   - Extract: old fact, new fact, optional scope
   - Accept formats: explicit ("Elena was 42 -> Elena is 38"), natural language ("Change Marcus from a soldier to a spy"), complex ("The magic system costs blood -> The magic system costs memories")

3. **Comprehensive search** across all artifacts:
   - **Direct references**: Exact mentions of the old fact
   - **Indirect references**: Implications, consequences, reactions based on the old fact
   - **Derivative details**: Things that logically follow from the old fact
   - Search: concept.md, outline.md, characters.md, World/ files, chapter plans, chapter drafts, chapters.md

4. **Generate a change manifest** with tables showing:
   - Direct references (file, location, current text, proposed change)
   - Indirect references (file, location, current text, why affected, proposed change)
   - Derivative details (file, location, current detail, logical issue, proposed change)
   - Unchanged references (references that work with both old and new facts)

5. **Present manifest to user** for review and approval.

6. **Apply approved changes**:
   - Update World/ files with `(RETCON-DATE)` tags
   - Update concept, outline, characters, chapter plans
   - Update chapter drafts while preserving voice and style
   - Reset modified chapter statuses to `[D]` for re-review

7. **Post-retcon consistency check**: Scan for remaining old references and new contradictions.

8. **Write retcon log** to `BOOK_DIR/pivots/YYYY-MM-DD-retcon-[description].md`.

9. **Report completion**:
   - Total changes applied
   - Chapters needing re-review
   - Suggested next steps: `authorkit.chapter.review`, `authorkit.world.verify`, `authorkit.analyze`

## Retcon Principles

- **Find everything.** Search direct references, indirect implications, and logical consequences.
- **Preserve voice.** Changes must be stylistically indistinguishable from surrounding prose.
- **Show the manifest first.** Never apply changes without user review.
- **Track changes.** Use `(RETCON-DATE)` tags. Store logs in `pivots/`.
- **Check your work.** Post-retcon scan catches what initial search missed.
- **Don't over-correct.** Leave references that work with both old and new facts.
