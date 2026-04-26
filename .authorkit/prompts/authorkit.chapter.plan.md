---
description: Plan a specific chapter in detail - scenes/sections, beats, emotional arc, and connections.
handoffs:
  - label: Draft This Chapter
    agent: authorkit.chapter.draft
    prompt: Draft chapter [N]
  - label: Discuss Direction First
    agent: authorkit.discuss
    prompt: Talk through the chapter's direction, character motivation, or scene purpose before drafting
  - label: Park a Blocker
    agent: authorkit.park
    prompt: Defer a decision that is blocking this chapter plan
  - label: Get Help Writing
    agent: authorkit.chapter.help
    prompt: Help with chapter [N]
  - label: Plan Next Chapter
    agent: authorkit.chapter.plan
    prompt: Plan chapter [N+1]
scripts:
  ps: scripts/powershell/check-prerequisites.ps1 -Json -IncludeChapters
---

## User Input

```text
{{USER_INPUT_TOKEN}}
```

You **MUST** consider the user input before proceeding (if not empty). The user input should contain the chapter number (e.g., "1", "CH03", "chapter 5").

## Outline

1. **Setup**: Run `{{SCRIPT_CHECK_PREREQ}}` from repo root and parse BOOK_DIR, STYLE_ANCHOR, and AVAILABLE_DOCS. All paths must be absolute.

2. **Parse chapter number** from user input:
   - Accept formats: "1", "01", "CH01", "chapter 1", "Chapter 1"
   - Normalize to two-digit format: "01", "02", etc.
   - If no chapter number provided: ERROR "Please specify a chapter number (e.g., /authorkit.chapter.plan 1)"

3. **Load context** (read all available):
   - **Required**: outline.md (this chapter's entry + overall structure)
   - **Required**: concept.md (voice, tone, themes, characters)
   - **Required**: chapters.md (chapter status, dependencies)
   - **Optional**: `parked-decisions.md` — if it exists, scan for any OPEN decisions whose deadline is at or before this chapter number. If found, warn: "⚠️ Parked decision [PD-NNN] is due before or at this chapter: [summary]. Consider resolving it with `/authorkit.park resolve PD-NNN` before planning."
   - **Required**: `STYLE_ANCHOR` at `BOOK_DIR/style-anchor.md` (create or refresh before planning)
   - **Recommended**: characters.md (character profiles for this chapter)
   - **Optional**: research.md and relevant `research/` topic files discovered recursively (prefer scope `general`, `outline`, `chapter CHNN`; if many files exist, load only those matching this chapter's entities/topics)
   - **Optional**: `/memory/constitution.md` (writing principles)
   - **Optional**: `world/` folder files relevant to this chapter's characters, locations, and systems (ensures world consistency). **If `world/_index.md` exists**: Read it. Use the Chapter Manifest to find entities from the previous chapter (carry-over context). Resolve entity names mentioned in the outline entry for this chapter via the Alias Lookup. Load only the world/ files identified by these lookups, rather than all world/ files.
   - **Optional**: Previous chapter drafts in `chapters/NN-1/draft.md` (for continuity)
   - **Optional**: Previous chapter plans in `chapters/NN-1/plan.md` (for context)

4. **Verify chapter is ready to plan**:
   - Check chapters.md for the chapter entry
   - If chapter status is already `[P]`, `[D]`, `[R]`, or `[X]`: warn user that a plan already exists and ask whether to overwrite or skip
   - If previous chapters are not yet drafted and this chapter depends on them: warn but allow proceeding

5. **Reconcile outline against drafted chapters** (critical for mid-book consistency):
   - Read this chapter's outline entry. Identify every factual claim it makes about events from **already-drafted** chapters (e.g., "arrived with instructions from X to...", "after the argument in CH03...").
   - For each such claim, grep the actual `chapters/NN/draft.md` text of the referenced chapter to verify the claim matches what was written.
   - **Drafted chapters are canonical.** If the outline says X happened but the draft says Y, the draft is correct and the outline is stale.
   - If mismatches are found:
     - Use the draft's version in the plan, not the outline's.
     - Note the discrepancy in the plan under a "Reconciliation Notes" section.
     - After the plan is written, correct the stale outline entry to match the draft.
   - This step prevents upstream planning documents from introducing continuity errors into new chapters.

6. **Build or refresh style anchor** at `STYLE_ANCHOR` before planning:
   - Source style from constitution + the last two approved chapters (`[X]`) before this chapter number.
   - Fallbacks:
     - If one approved chapter exists: use constitution + that chapter.
     - If none exist: use constitution only.
   - Write the style anchor using this fixed schema:
     - `## Non-Negotiables (POV, Tense, Narrative Distance)`
     - `## Cadence Profile (Sentence and Paragraph Rhythm)`
     - `## Dialogue Profile`
     - `## Diction and Register`
     - `## Imagery Density and Taboo Patterns`
     - `## Drift Red Flags`
     - `## Provenance`

7. **Create chapter directory**: Ensure `BOOK_DIR/chapters/NN/` exists (create if needed).

8. **Generate chapter plan**: Load `templates/chapter-plan-template.md` and fill it with:

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

9. **Write plan** to `BOOK_DIR/chapters/NN/plan.md`.

10. **Update chapter status**: In chapters.md, change this chapter's status from `[ ]` to `[P]`:
   - Find the line matching `- [ ] CHNN`
   - Replace `- [ ]` with `- [P]`

11. **Fix stale outline entries**: If step 5 found any mismatches, update the relevant outline.md entries to match the drafted chapters. This keeps the outline accurate for future chapter planning.

12. **Report completion**:
   - Path to chapter plan
   - Summary of scenes/sections planned
   - Key connections to other chapters
   - Suggested next step: `/authorkit.chapter.draft [N]`

## Key Rules

- The plan must be detailed enough that the chapter can be drafted without re-reading the full outline
- Respect the constitution's voice and style principles
- Style continuity is mandatory: planning assumptions must align with `book/style-anchor.md` and constitution.
- If you introduce new numeric facts in the plan, include rationale; when multiple values fit, pick a context-bounded varied value.
- Each scene/section needs a clear "why" - if it doesn't advance plot/argument or develop character/concept, question whether it belongs
- Opening hooks and closing beats are critical - spend extra thought on these
- For fiction: ensure dialogue-heavy scenes have clear purpose; ensure action scenes have emotional stakes
- For non-fiction: ensure each section builds on the previous; ensure examples are concrete and relevant

