---
description: Review a drafted chapter against the plan, concept, constitution, and quality criteria.
handoffs:
  - label: Revise This Chapter
    agent: authorkit.chapter.plan
    prompt: Re-plan chapter [N] based on review feedback
  - label: Update World
    agent: authorkit.world.update
    prompt: Update world files for chapter [N]
  - label: Verify World
    agent: authorkit.world.verify
    prompt: Verify world consistency for entities in chapter [N]
  - label: Draft Next Chapter
    agent: authorkit.chapter.plan
    prompt: Plan chapter [N+1]
scripts:
  ps: scripts/powershell/check-prerequisites.ps1 -Json -IncludeChapters
---

## User Input

```text
{{USER_INPUT_TOKEN}}
```

You **MUST** consider the user input before proceeding (if not empty). The user input should contain the chapter number.

## Outline

1. **Setup**: Run `{{SCRIPT_CHECK_PREREQ}}` from repo root and parse BOOK_DIR and AVAILABLE_DOCS. All paths must be absolute.

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
   - **Recommended**: `World/` folder — load entity files across all categories (Characters/, Places/, Organizations/, Systems/, History/, Notes/) for entities appearing in or relevant to this chapter. **If `World/_index.md` exists**: Read it. Scan the draft text for entity names and resolve them via the Alias Lookup (this catches variants like "Dr. Voss" ↔ "Elena Voss"). Use the Chapter Manifest to identify entities tagged for this chapter. Load only the matched World/ files, rather than all World/ files.
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
   - **Knowledge boundaries**: For each character in the chapter, verify they only act on information they could plausibly possess. If a character reacts to something (a lie, a plan, a schedule), trace when and how they learned it. Flag any case where a character knows something they were never told, witnessed, or could reasonably infer. Cross-check against previous chapters and World/Characters/ profiles.
   - **Narrative necessity**: When the narrator frames an action as necessary ("the lie needed updating," "they had to," "there was no choice"), verify the claim against the story's own established logic. If the characters' own system makes the action pointless or unnecessary, the framing is wrong — either the action, the justification, or the narrator's commentary needs to change.
   - **Non-fiction**: Are claims accurate? Are examples relevant? Is the argument logical?

   #### D1. World Consistency (if `World/` files exist)

   Cross-check this chapter against ALL relevant World/ categories. For each category, compare what appears in the chapter against the established World/ entries:

   - **Characters**: Compare every character appearing in this chapter against their World/Characters/ profile. Check physical descriptions (appearance, age, distinguishing features), personality traits, speech patterns, relationships, and background details. Flag any contradictions with both `(CONCEPT)` and `(CHxx)` tagged entries.
   - **Places**: Compare every location described or mentioned in this chapter against its World/Places/ entry. Check physical descriptions, key features, atmosphere, and spatial relationships. Flag setting details that contradict established descriptions. **Critically, verify that all character actions are physically possible within the established geometry** — e.g., characters cannot exit a dead-end cave "out the other side," cannot see a landmark from a location that doesn't have line-of-sight, cannot walk between places in less time than the established distance allows. Check any "Physical Constraints" section in the World/ entry.
   - **Headcount & logistics**: Trace every character's physical location through the chapter scene by scene. At each scene transition, verify: (1) the number of characters stated or implied as present matches who could logistically be there, given prior movements, available transport, and distances; (2) no character appears in a scene they couldn't have reached; (3) claims like "three watched" or "all four" match the actual count of bodies at that location. This is especially critical when characters split up, when new characters are introduced mid-chapter, or when a single character has multiple copies.
   - **Organizations**: Check any organizations referenced in this chapter against their World/Organizations/ entries. Verify membership, hierarchy, purpose, and inter-organization relationships are consistent.
   - **Systems**: If the chapter involves any system (magic, technology, political, economic), verify that the chapter's depiction follows the rules, limitations, scope, and exceptions defined in World/Systems/. Flag any rule violations.
   - **History**: If the chapter references past events, verify those references align with the accounts in World/History/ entries. Flag contradictory dates, participants, or outcomes.
   - **New entities**: Flag characters, places, organizations, systems, or historical events that appear in this chapter but have NO corresponding World/ entry. These are candidates for `/authorkit.world.update`.

   For each contradiction found, cite the specific World/ file, the tagged entry, and the location in the chapter draft where the contradiction occurs. Severity:
   - Contradictions with established entries: **Critical** or **Important** depending on reader-visible impact
   - Missing World/ entries: **Minor** (informational — these should be captured via `/authorkit.world.update`)

   ### E. Continuity (if previous chapters exist)
   - Does this chapter flow naturally from the previous one?
   - Are there any contradictions with earlier chapters?
   - Is the voice/energy level consistent across chapters?
   - Are ongoing threads properly continued?
   - **Backstory verification**: For every factual claim this chapter makes about events from prior chapters (flashbacks, references, "he had done X in CH03"), grep the actual draft text of that chapter and verify the claim is accurate. Do not trust the plan or outline — verify against the drafted prose. Flag any claim that contradicts what was actually written. This is especially important for details about how characters arrived, what they said, and who instructed whom.

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
   | World Consistency | [A/B/C/D/N/A] | [Brief note] |

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

