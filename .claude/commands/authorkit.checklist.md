---
description: Generate a custom quality checklist for the book based on user requirements.
scripts:
  ps: scripts/powershell/check-prerequisites.ps1 -Json
---

## Checklist Purpose: "Quality Gates for Your Book"

**CRITICAL CONCEPT**: Checklists validate the quality, completeness, and consistency of your book's content and structure.

**Examples of good checklist items**:
- "Is each character's introduction memorable and distinct?" (character quality)
- "Does every chapter end with a reason to keep reading?" (pacing quality)
- "Are all historical facts verified against primary sources?" (accuracy)
- "Is the central argument supported by at least 3 pieces of evidence?" (non-fiction rigor)
- "Are dialogue tags varied and unobtrusive?" (craft quality)

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Execution Steps

1. **Setup**: Run `{SCRIPT}` from repo root and parse JSON for BOOK_DIR and AVAILABLE_DOCS list. All file paths must be absolute.

2. **Clarify intent**: Derive up to THREE contextual clarifying questions based on the user's request:
   - What domain is the checklist for? (craft, continuity, accuracy, sensitivity, pacing, etc.)
   - What depth level? (quick scan vs thorough review)
   - What stage of the book? (early chapters, mid-draft, final polish)

   If already clear from `$ARGUMENTS`, skip questions.

3. **Understand user request**: Combine `$ARGUMENTS` + clarifying answers:
   - Derive checklist theme (e.g., craft-quality, continuity, sensitivity, pacing, accuracy)
   - Map focus selections to category scaffolding

4. **Load book context**: Read from BOOK_DIR:
   - concept.md: Book premise, themes, voice
   - outline.md (if exists): Structure, arcs
   - chapters.md (if exists): Chapter status
   - constitution: Writing principles

5. **Generate checklist**:
   - Create `BOOK_DIR/checklists/` directory if it doesn't exist
   - Generate unique checklist filename based on domain (e.g., `craft.md`, `continuity.md`, `sensitivity.md`)
   - Number items sequentially starting from CHK001
   - Each run creates a NEW file (never overwrites existing checklists)

   **Category Examples by Type**:

   **Craft Quality:** `craft.md`
   - "Does every scene/section have a clear purpose that advances plot/argument?"
   - "Is dialogue natural and character-specific?"
   - "Are descriptions concrete and sensory rather than abstract?"
   - "Is sentence length varied for rhythm and pacing?"
   - "Are transitions between scenes smooth and purposeful?"

   **Continuity:** `continuity.md`
   - "Are character physical descriptions consistent across all chapters?"
   - "Is the timeline internally consistent?"
   - "Are established rules of the world/domain followed throughout?"
   - "Do characters remember events from previous chapters correctly?"

   **Pacing:** `pacing.md`
   - "Does each chapter end with forward momentum?"
   - "Is there a mix of high-tension and reflective chapters?"
   - "Are any chapters significantly longer/shorter than average without reason?"
   - "Does the midpoint deliver a meaningful shift?"

   **Sensitivity:** `sensitivity.md`
   - "Are cultural representations researched and respectful?"
   - "Are potentially triggering themes handled with appropriate care?"
   - "Are diverse characters portrayed with depth, not stereotypes?"
   - "Are content warnings appropriate for the target audience?"

   **Accuracy (Non-Fiction):** `accuracy.md`
   - "Are all statistical claims sourced?"
   - "Are expert opinions properly attributed?"
   - "Are counterarguments acknowledged and addressed?"
   - "Is terminology consistent and properly defined?"

6. **Structure Reference**: Use `templates/checklist-template.md` for format. Items follow: `- [ ] CHKNNN Description [Category]`

7. **Report**: Output full path to created checklist, item count, and remind user that each run creates a new file.

**Important**: Each `/authorkit.checklist` invocation creates a new checklist file. This allows multiple checklists of different types.
