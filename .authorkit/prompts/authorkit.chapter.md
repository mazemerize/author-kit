---
description: Automate the full chapter lifecycle — plan, draft, review, and revise until approved.
scripts:
  ps: scripts/powershell/check-prerequisites.ps1 -Json -IncludeChapters
---

## User Input

```text
{{USER_INPUT_TOKEN}}
```

You **MUST** consider the user input before proceeding (if not empty). The user input may contain a chapter number (e.g., "3", "CH05") or be empty for auto-detection.

## Goal

Automate the full chapter lifecycle for a single chapter: **plan → draft → review**, looping on **draft → review** until the chapter passes. This command does the actual work — it plans, writes, and reviews the chapter, repeating the draft-review cycle as needed.

## Outline

### Phase 0: Setup and Target Selection

1. **Setup**: Run `{{SCRIPT_CHECK_PREREQ}}` from repo root and parse BOOK_DIR, STYLE_ANCHOR, and AVAILABLE_DOCS. All paths must be absolute.

2. **Load chapters.md**: Read `BOOK_DIR/chapters.md` and parse all chapter entries.
   - Extract chapter numbers, titles, and status markers: `[ ]` pending, `[P]` planned, `[D]` drafted, `[R]` reviewed/needs revision, `[X]` approved
   - If chapters.md doesn't exist: ERROR "No chapters.md found. Run `/authorkit.chapters` first."

3. **Determine target chapter**:

   **If user specified a chapter number:**
   - Accept formats: "1", "01", "CH01", "chapter 1"
   - Normalize to two-digit format
   - Verify the chapter exists in chapters.md

   **If no chapter specified — find the frontier:**
   - Scan chapters.md for the first chapter that is NOT `[X]` (approved)
   - If all chapters are `[X]`: report book is complete, recommend `/authorkit.analyze` for cross-chapter analysis, and stop.

4. **Report initial state** before starting work:
   ```
   ## Starting Chapter [NN]: [Title]
   Current status: [status]
   Book progress: [X] of [total] chapters approved
   ```

5. **Resume from current state** — pick up wherever the chapter is:
   - `[ ]` pending → start at Phase 1 (Plan)
   - `[P]` planned → skip to Phase 2 (Draft)
   - `[D]` drafted → skip to Phase 3 (Review)
   - `[R]` needs revision → skip to Phase 2 (Re-draft with review feedback)
   - `[X]` approved → report chapter is done, stop.

### Phase 1: Plan the Chapter

Execute the full chapter planning workflow (equivalent to `/authorkit.chapter.plan`):

1. **Load context**:
   - **Required**: outline.md (this chapter's entry + overall structure)
   - **Required**: concept.md (voice, tone, themes, characters)
   - **Required**: chapters.md (chapter status, dependencies)
   - **Required**: `STYLE_ANCHOR` at `BOOK_DIR/style-anchor.md` (refresh before planning)
   - **Recommended**: characters.md (character profiles)
   - **Optional**: research.md, `/memory/constitution.md`
   - **Optional**: `world/` folder files relevant to this chapter's characters, locations, and systems
   - **Optional**: Previous chapter drafts/plans for continuity

2. **Reconcile outline against drafted chapters** (critical for mid-book consistency):
   - Read this chapter's outline entry. Identify every factual claim about events from **already-drafted** chapters.
   - For each such claim, grep the actual draft text of the referenced chapter to verify accuracy.
   - **Drafted chapters are canonical.** If the outline says X but the draft says Y, the draft is correct.
   - Use the draft's version in the plan. Note discrepancies and correct the outline entry after planning.

3. **Create chapter directory**: Ensure `BOOK_DIR/chapters/NN/` exists.

4. **Build or refresh style anchor** at `STYLE_ANCHOR`:
   - Source style from constitution + the last two approved chapters (`[X]`) before this chapter number.
   - Fallbacks:
     - If one approved chapter exists: use constitution + that chapter.
     - If none exist: use constitution only.
   - Use this fixed schema:
     - `## Non-Negotiables (POV, Tense, Narrative Distance)`
     - `## Cadence Profile (Sentence and Paragraph Rhythm)`
     - `## Dialogue Profile`
     - `## Diction and Register`
     - `## Imagery Density and Taboo Patterns`
     - `## Drift Red Flags`
     - `## Provenance`

5. **Generate chapter plan** at `BOOK_DIR/chapters/NN/plan.md` using `templates/chapter-plan-template.md`:
   - Chapter purpose (from outline.md, reconciled against drafts)
   - Context (previous chapter ending, this chapter's goals, next chapter needs)
   - Scene/section breakdown with settings, beats, emotional tone
   - Emotional arc / argument flow
   - Key revelations and character development
   - Connections (setups and payoffs)
   - Opening hook and closing beat
   - Voice/style notes and target word count

6. **Update status** in chapters.md: `[ ]` → `[P]`

7. **Fix stale outline entries**: If step 2 found mismatches, update the outline.md entries to match drafted chapters.

8. **Brief report**: "Chapter [NN] planned. [X] scenes/sections. Proceeding to draft."

→ Continue to Phase 2.

### Phase 2: Draft the Chapter

Execute the full chapter drafting workflow (equivalent to `/authorkit.chapter.draft`):

1. **Load context**:
   - **Required**: `chapters/NN/plan.md`
   - **Required**: concept.md, `/memory/constitution.md`
   - **Required**: `STYLE_ANCHOR` at `BOOK_DIR/style-anchor.md`
   - **Recommended**: characters.md, `world/` folder files for this chapter
   - **Recommended**: Previous chapter draft for continuity
   - **If re-drafting after review**: Also load `chapters/NN/review.md` and address all critical/important issues

2. **Pre-flight**:
   - Internalize the constitution's voice/style rules
   - Internalize `STYLE_ANCHOR` style constraints
   - If re-drafting: read the review feedback carefully and plan how to address each issue

3. **Write the chapter** following the plan's scene/section breakdown:
   - Execute each planned beat
   - Apply the constitution's style rules throughout
   - If re-drafting: specifically address each critical and important issue from the review
   - Opening hook and closing beat must be effective
   - Pure prose — no meta-commentary or [TODO] markers

4. **Quality self-check**: Verify constitution compliance, style-anchor alignment, plan adherence, pacing, voice consistency.

5. **Style match pass**:
   - Compare draft against constitution + `book/style-anchor.md`.
   - Fix style drift before saving.
   - Validate any new numeric facts: rationale required; context-bounded varied selection when multiple values are plausible.

6. **Write draft** to `BOOK_DIR/chapters/NN/draft.md`.

7. **Update status** in chapters.md: `[P]` → `[D]` (or keep `[D]`/`[R]` → `[D]` if re-drafting).

8. **Brief report**: "Chapter [NN] drafted. [word count] words. Proceeding to review."

→ Continue to Phase 3.

### Phase 3: Review the Chapter

Execute the full chapter review workflow (equivalent to `/authorkit.chapter.review`):

1. **Load review context**:
   - **Required**: `chapters/NN/draft.md`, `chapters/NN/plan.md`
   - **Required**: concept.md, `/memory/constitution.md`
   - **Required**: `STYLE_ANCHOR` at `BOOK_DIR/style-anchor.md`
   - **Recommended**: characters.md, outline.md
   - **Recommended**: `world/` folder — ALL entity files for entities in this chapter
   - **Optional**: Previous/next chapter drafts, previous review

2. **Assess the draft** across all dimensions:

   **A. Plan Adherence** — scenes covered, beats executed, deviations assessed
   **B. Constitution Compliance** — voice, POV, tense, prose style
   **B1. Style Anchor Compliance** — alignment to `book/style-anchor.md` (cadence, diction/register, imagery density, dialogue profile, drift flags)
   **C. Craft Quality** — pacing, show vs tell, dialogue, description, transitions, opening, closing
   **D. Character/Content Consistency** — character behavior, knowledge boundaries, narrative necessity
   **D1. World Consistency** (if world/ exists) — characters, places, headcount & logistics, organizations, systems, history vs world/ entries; flag new entities
   **E. Continuity** — flow from previous chapter, contradictions, thread continuation. **Critically: for every backstory claim about prior chapters, grep the actual draft text to verify — do not trust the outline or plan alone.**
   **F. Theme Integration** — themes present, organic integration

3. **Generate review** at `BOOK_DIR/chapters/NN/review.md` with dimension scores and issue classifications (Critical/Important/Minor).

4. **Determine verdict**: PASS or NEEDS REVISION
   - **PASS threshold**: No critical issues, no more than 2 important issues, constitution compliance is B or above

5. **Branch based on verdict**:

   **If PASS:**
   - Update status in chapters.md: `[D]` → `[X]`
   - → Proceed to Final Report. Chapter is done.

   **If NEEDS REVISION:**
   - Update status in chapters.md: `[D]` → `[R]`
   - Report: "Chapter [NN] NEEDS REVISION (cycle [N] of 3). [count] critical, [count] important issues."
   - List the critical and important issues briefly.
   - → Loop back to Phase 2 (re-draft with review feedback).

### Revision Loop Safety

- **Maximum 3 revision cycles** per chapter. If the chapter has not passed after 3 draft-review cycles, stop and report:
  - "Chapter [NN] has not passed after 3 revision attempts."
  - Summary of remaining issues
  - Recommend manual intervention or running `/authorkit.chapter.review [N]` and `/authorkit.revise [N]` separately for more targeted fixes.
- **Track cycle count**: Log which revision cycle is active (e.g., "Revision 2 of 3").
- **Each re-draft must specifically address review issues**: Don't just rewrite from scratch — target the identified problems.

## Final Report

When the chapter is approved (or the revision limit is reached), output a summary:

```markdown
## Chapter [NN] Complete

**Title**: [Chapter title]
**Status**: [APPROVED / REVISION LIMIT REACHED]
**Word Count**: [final count]
**Revision Cycles**: [N]

### Dimension Scores
| Dimension | Score |
|-----------|-------|
| Plan Adherence | [A/B/C/D] |
| Constitution Compliance | [A/B/C/D] |
| Style Anchor Compliance | [A/B/C/D] |
| Craft Quality | [A/B/C/D] |
| Character/Content | [A/B/C/D] |
| Continuity | [A/B/C/D] |
| Theme Integration | [A/B/C/D] |
| World Consistency | [A/B/C/D/N/A] |

### Book Progress
[X] of [total] chapters approved
Next: [suggestion]
```

## Key Rules

- **This command does real work.** It plans, writes, and reviews — it is not read-only.
- **Follow each sub-workflow faithfully.** The plan, draft, and review phases follow the same logic as their standalone commands (`/authorkit.chapter.plan`, `/authorkit.chapter.draft`, `/authorkit.chapter.review`).
- **Address review feedback specifically.** When re-drafting, don't ignore the review — directly address each critical and important issue.
- **Respect the revision limit.** 3 cycles max prevents infinite loops. If the chapter can't pass in 3 tries, it needs manual attention.
- **Keep inter-phase reports concise.** Between phases, report briefly (1-2 lines). Save detailed output for the final report.
- **Never skip the review.** Every draft must be reviewed, even re-drafts. The review is the quality gate.

