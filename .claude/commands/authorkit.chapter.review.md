---
description: Review a drafted chapter against the plan, concept, constitution, and quality criteria.
handoffs:
  - label: Revise This Chapter
    agent: authorkit.chapter.plan
    prompt: Re-plan chapter [N] based on review feedback
  - label: Update World
    agent: authorkit.world.update
    prompt: Update world files for chapter [N]
  - label: Draft Next Chapter
    agent: authorkit.chapter.plan
    prompt: Plan chapter [N+1]
scripts:
  ps: scripts/powershell/check-prerequisites.ps1 -Json -IncludeChapters
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty). The user input should contain the chapter number.

## Outline

1. **Setup**: Run `{SCRIPT}` from repo root and parse BOOK_DIR and AVAILABLE_DOCS. All paths must be absolute.

2. **Parse chapter number** from user input:
   - Accept formats: "1", "01", "CH01", "chapter 1"
   - Normalize to two-digit format
   - If no chapter number: ERROR "Please specify a chapter number"

3. **Verify draft exists**:
   - Check that `BOOK_DIR/chapters/NN/draft.md` exists
   - If not: ERROR "Chapter draft not found. Run `/authorkit.chapter.draft [N]` first."
   - Check chapters.md status is at least `[D]` (drafted)

4. **Load review context**:
   - **Required**: `chapters/NN/draft.md` (the chapter to review)
   - **Required**: `chapters/NN/plan.md` (what was planned)
   - **Required**: concept.md (book concept, themes, voice)
   - **Required**: `/memory/constitution.md` (writing principles)
   - **Recommended**: characters.md (character consistency checks)
   - **Recommended**: outline.md (chapter's role in overall structure)
   - **Recommended**: `World/` folder files for characters, locations, and systems appearing in this chapter (for world consistency checks)
   - **Optional**: Previous and next chapter drafts (continuity)
   - **Optional**: Previous review at `chapters/NN/review.md` (if revision cycle)

5. **Execute review**: Assess the draft across these dimensions:

   ### A. Plan Adherence
   - Did the draft cover all planned scenes/sections?
   - Were all key beats executed?
   - Did the opening hook land effectively?
   - Did the closing beat create forward momentum?
   - Any significant deviations from the plan? Are they improvements?

   ### B. Constitution Compliance
   - Does the voice match the constitution's specifications?
   - Is the POV consistent with the stated approach?
   - Is the tense correct throughout?
   - Does the prose style match the constitution's standards?
   - Are any constitution principles violated?

   ### C. Craft Quality
   - **Pacing**: Does the chapter flow well? Are there sections that drag or rush?
   - **Show vs Tell**: Are emotions shown through action/dialogue rather than stated?
   - **Dialogue** (fiction): Is it natural? Does each character sound distinct?
   - **Description**: Is it concrete and sensory? Is there enough (or too much)?
   - **Transitions**: Are scene/section transitions smooth?
   - **Opening**: Does the first paragraph hook the reader?
   - **Closing**: Does the ending compel the reader forward?

   ### D. Character/Content Consistency
   - **Fiction**: Do characters behave consistently with their profiles? Are voices distinct? Do actions align with motivations?
   - **Non-fiction**: Are claims accurate? Are examples relevant? Is the argument logical?
   - **World consistency**: If `World/` files exist, cross-check character details (appearance, personality, relationships) and setting details (location descriptions, distances, features) against established World/ entries. Flag any contradictions.

   ### E. Continuity (if previous chapters exist)
   - Does this chapter flow naturally from the previous one?
   - Are there any contradictions with earlier chapters?
   - Is the voice/energy level consistent across chapters?
   - Are ongoing threads properly continued?

   ### F. Theme Integration
   - Are the book's themes present in this chapter (where they should be)?
   - Is theme integration organic (not heavy-handed)?

6. **Generate review** at `BOOK_DIR/chapters/NN/review.md`:

   ```markdown
   # Chapter Review: Chapter [NN] - [Title]

   **Reviewed**: [DATE]
   **Draft Word Count**: [count]
   **Overall Assessment**: [PASS / NEEDS REVISION]

   ## Strengths

   - [What works well - be specific with quotes or line references]
   - [Another strength]

   ## Issues

   ### Critical (Must Fix)

   - [Issue]: [Specific description with location in draft]
     **Suggestion**: [How to fix it]

   ### Important (Should Fix)

   - [Issue]: [Description]
     **Suggestion**: [Fix]

   ### Minor (Nice to Fix)

   - [Issue]: [Description]
     **Suggestion**: [Fix]

   ## Dimension Scores

   | Dimension | Score | Notes |
   |-----------|-------|-------|
   | Plan Adherence | [A/B/C/D] | [Brief note] |
   | Constitution Compliance | [A/B/C/D] | [Brief note] |
   | Craft Quality | [A/B/C/D] | [Brief note] |
   | Character/Content | [A/B/C/D] | [Brief note] |
   | Continuity | [A/B/C/D] | [Brief note] |
   | Theme Integration | [A/B/C/D] | [Brief note] |

   ## Verdict

   **Status**: [PASS - ready to move on / NEEDS REVISION - see critical issues]

   **Next Steps**:
   - [Specific action items if revision needed]
   - [Or: "Proceed to next chapter"]
   ```

7. **Update chapter status** in chapters.md:
   - If PASS: change `[D]` to `[X]` (approved)
   - If NEEDS REVISION: change `[D]` to `[R]` (reviewed, needs work)

8. **Report to user**:
   - Overall assessment (PASS/NEEDS REVISION)
   - Key strengths (top 2-3)
   - Critical issues (if any)
   - Suggested next action:
     - If PASS: `/authorkit.chapter.plan [N+1]` to continue
     - If NEEDS REVISION: re-run `/authorkit.chapter.plan [N]` to re-plan with feedback, then `/authorkit.chapter.draft [N]`

## Review Principles

- **Be constructive**: Every criticism should come with a specific suggestion
- **Be specific**: Quote the draft, reference line locations, give concrete examples of improvement
- **Respect the author's voice**: Don't try to rewrite in a different style - evaluate against the constitution
- **Prioritize ruthlessly**: A chapter with one critical issue and three minor ones needs the critical fix first
- **Grade fairly**: An A means exceptional, B means solid, C means adequate, D means needs significant work
- **PASS threshold**: No critical issues, no more than 2 important issues, constitution compliance is B or above
