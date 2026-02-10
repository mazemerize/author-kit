---
description: Plan a specific chapter in detail - scenes/sections, beats, emotional arc, and connections.
handoffs:
  - label: Draft This Chapter
    agent: authorkit.chapter.draft
    prompt: Draft chapter [N]
  - label: Plan Next Chapter
    agent: authorkit.chapter.plan
    prompt: Plan chapter [N+1]
scripts:
  ps: scripts/powershell/check-prerequisites.ps1 -Json -IncludeChapters
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty). The user input should contain the chapter number (e.g., "1", "CH03", "chapter 5").

## Outline

1. **Setup**: Run `{SCRIPT}` from repo root and parse BOOK_DIR and AVAILABLE_DOCS. All paths must be absolute.

2. **Parse chapter number** from user input:
   - Accept formats: "1", "01", "CH01", "chapter 1", "Chapter 1"
   - Normalize to two-digit format: "01", "02", etc.
   - If no chapter number provided: ERROR "Please specify a chapter number (e.g., /authorkit.chapter.plan 1)"

3. **Load context** (read all available):
   - **Required**: outline.md (this chapter's entry + overall structure)
   - **Required**: concept.md (voice, tone, themes, characters)
   - **Required**: chapters.md (chapter status, dependencies)
   - **Recommended**: characters.md (character profiles for this chapter)
   - **Optional**: research.md (relevant research notes)
   - **Optional**: `/memory/constitution.md` (writing principles)
   - **Optional**: `World/` folder files relevant to this chapter's characters, locations, and systems (ensures world consistency)
   - **Optional**: Previous chapter drafts in `chapters/NN-1/draft.md` (for continuity)
   - **Optional**: Previous chapter plans in `chapters/NN-1/plan.md` (for context)

4. **Verify chapter is ready to plan**:
   - Check chapters.md for the chapter entry
   - If chapter status is already `[P]`, `[D]`, `[R]`, or `[X]`: warn user that a plan already exists and ask whether to overwrite or skip
   - If previous chapters are not yet drafted and this chapter depends on them: warn but allow proceeding

5. **Create chapter directory**: Ensure `BOOK_DIR/chapters/NN/` exists (create if needed).

6. **Generate chapter plan**: Load `templates/chapter-plan-template.md` and fill it with:

   a. **Chapter Purpose**: Extract from outline.md entry for this chapter

   b. **Context**: What the previous chapter ended with, what this chapter must accomplish, what the next chapter needs

   c. **Scene/Section Breakdown**:
      - For FICTION: Individual scenes with setting, POV, key beats, emotional tone
      - For NON-FICTION: Logical sections with key points, evidence, examples
      - Each scene/section should have a clear purpose
      - Order scenes for maximum narrative/argumentative impact

   d. **Emotional Arc / Argument Flow**: Map the chapter's internal progression from opening to closing

   e. **Key Revelations / Points**: What the reader learns or discovers in this chapter

   f. **Characters/Concepts**: Who appears and how they develop

   g. **Connections**: Setups being planted and payoffs being delivered

   h. **Opening Hook**: A compelling first line or paragraph concept

   i. **Closing Beat**: How the chapter ends to propel the reader forward

   j. **Voice & Style Notes**: Any chapter-specific style considerations

   k. **Estimated Length**: Target word count based on the book's overall scope

7. **Write plan** to `BOOK_DIR/chapters/NN/plan.md`.

8. **Update chapter status**: In chapters.md, change this chapter's status from `[ ]` to `[P]`:
   - Find the line matching `- [ ] CHNN`
   - Replace `- [ ]` with `- [P]`

9. **Report completion**:
   - Path to chapter plan
   - Summary of scenes/sections planned
   - Key connections to other chapters
   - Suggested next step: `/authorkit.chapter.draft [N]`

## Key Rules

- The plan must be detailed enough that the chapter can be drafted without re-reading the full outline
- Respect the constitution's voice and style principles
- Each scene/section needs a clear "why" - if it doesn't advance plot/argument or develop character/concept, question whether it belongs
- Opening hooks and closing beats are critical - spend extra thought on these
- For fiction: ensure dialogue-heavy scenes have clear purpose; ensure action scenes have emotional stakes
- For non-fiction: ensure each section builds on the previous; ensure examples are concrete and relevant
