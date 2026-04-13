---
description: Apply revisions to specific chapters based on analysis findings or user feedback.
handoffs:
  - label: Re-Review Chapter
    agent: authorkit.chapter.review
    prompt: Review chapter [N] after revision
  - label: Sync World After Revision
    agent: authorkit.world.sync
    prompt: Sync world files after revising chapter [N]
  - label: Run Analysis Again
    agent: authorkit.analyze
    prompt: Run a fresh cross-chapter analysis
    send: true
scripts:
  ps: scripts/powershell/check-prerequisites.ps1 -Json -IncludeChapters
---

## User Input

```text
{{USER_INPUT_TOKEN}}
```

You **MUST** consider the user input before proceeding (if not empty). The user input should specify which chapter(s) to revise and/or what issues to address.

## Outline

1. **Setup**: Run `{{SCRIPT_CHECK_PREREQ}}` from repo root and parse BOOK_DIR, STYLE_ANCHOR, and AVAILABLE_DOCS. All paths must be absolute.

2. **Determine revision scope** from user input:
   - Specific chapter: "Revise chapter 3" or "Fix CH05"
   - Specific issue: "Fix the timeline contradiction between chapters 3 and 7"
   - Analysis-driven: "Address the critical issues from the last analysis"
   - If unclear: ask user to specify which chapter(s) and what to fix

3. **Load context for each chapter being revised**:
   - The chapter's draft (`chapters/NN/draft.md`)
   - The chapter's plan (`chapters/NN/plan.md`)
   - The chapter's review if it exists (`chapters/NN/review.md`)
   - concept.md, constitution, characters.md
   - `STYLE_ANCHOR` at `BOOK_DIR/style-anchor.md` (refresh before revising each chapter)
   - `world/` folder files for entities appearing in this chapter (check which details are chapter-tagged to this chapter — these may need updating after revision)
   - Adjacent chapter drafts (for continuity)
   - Any analysis report findings relevant to this chapter

4. **For each chapter to revise**:

   a. **Identify specific changes needed**:
      - From review.md: address critical and important issues
      - From analysis: fix continuity, consistency, pacing issues
      - From user input: apply requested changes

   b. **Plan the revision**:
      - List each change to make
      - Note which sections of the draft are affected
      - Consider ripple effects on other chapters

   b1. **Build or refresh style anchor** at `STYLE_ANCHOR`:
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

   c. **Apply revisions to the draft**:
      - Make targeted edits to `chapters/NN/draft.md`
      - Preserve what works well (don't rewrite from scratch unless necessary)
      - Ensure voice consistency is maintained
      - Follow constitution principles and match `book/style-anchor.md`
      - If introducing or changing numeric facts, ensure each number has explicit rationale; if multiple values are plausible, choose a context-bounded varied value

   d. **Update the chapter plan** if the revision changes the chapter's structure:
      - Update `chapters/NN/plan.md` to reflect the actual content

   e. **Update chapter status** in chapters.md:
      - If it was `[R]` (reviewed/needs revision): change to `[D]` (re-drafted, ready for re-review)
      - If it was `[X]` (approved) and revision was requested: change to `[D]`

   f. **Style match pass**:
      - Compare revised draft against constitution + `book/style-anchor.md`.
      - Fix prose style drift before reporting completion.

5. **Check for ripple effects**:
   - If a revision changes a fact, character detail, or plot point: identify all other chapters that reference it
   - List any other chapters that may need updates as a result
   - Do NOT automatically edit other chapters - flag them for the user
   - **world/ synchronization**: Recommend running `/authorkit.world.sync [N]` after revision to update world/ files and get a full downstream impact report of what changed and which chapters may be affected

6. **Report completion**:
   - Chapters revised and their paths
   - Summary of changes made per chapter
   - Ripple effects identified (other chapters that may need attention)
   - Suggested next steps:
     - `/authorkit.chapter.review [N]` to re-review revised chapters
     - `/authorkit.analyze` to check cross-chapter consistency after revisions
     - Other chapters that need attention due to ripple effects

## Revision Principles

- **Minimal surgery**: Make the smallest changes that fix the issue. Don't rewrite sections that are working well.
- **Preserve voice**: Revisions should be indistinguishable in style from the original draft.
- **Track changes**: Be explicit about what was changed and why in the report.
- **Ripple awareness**: Always consider whether a change in one chapter affects others.
- **Constitution compliance**: All revisions must comply with the book constitution.

