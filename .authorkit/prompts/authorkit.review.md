---
description: Review one chapter (craft-level) or the whole manuscript (drift, continuity, threads). Read-only by default; upstream drift fixes are gated by approval and never edit drafts.
handoffs:
  - label: Discuss a Finding
    agent: authorkit.discuss
    prompt: Talk through finding [ID] before deciding how to address it
  - label: Apply Targeted Revision
    agent: authorkit.write
    prompt: Revise chapter [N] to address the review findings
  - label: Run Research
    agent: authorkit.research
    prompt: Research a topic surfaced by the review
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-chapters --include-chapters
  ps: scripts/powershell/check-prerequisites.ps1 -Json -RequireChapters -IncludeChapters
---

## User Input

```text
{{USER_INPUT_TOKEN}}
```

You **MUST** consider the user input before proceeding (if not empty). The input determines scope:

- A single chapter (`7`, `CH07`, `chapter 7`) → **Chapter craft review**
- A range (`5-10`, `chapters 5-10`) → **Range review** (per-chapter craft + drift scan scoped to the range)
- Empty, `all`, `manuscript`, `book`: → **Manuscript drift** (cross-chapter consistency, threads, pacing, voice)

## Goal

This is the review command. It does two distinct jobs and infers which is needed from scope:

1. **Chapter craft review**: assess a single drafted chapter against its plan, the concept, the constitution, the style anchor, the `world/` entries, and adjacent chapters. Output a `review.md` file with strengths, issues by severity, dimension scores, and a verdict.
2. **Manuscript drift**: cross-chapter analysis for continuity errors, character drift, theme tracking, pacing, voice/style consistency, world-building integrity, overdue parked decisions, and upstream drift (concept/outline/chapters.md/world out of sync with drafts). Output a structured Markdown report; offer upstream drift fixes gated by approval; **never** modify drafts.

A range invocation runs the chapter craft review on each chapter in the range, then a drift scan limited to that range.

## Operating Constraints

- **Read-only by default.** Analysis itself never modifies files.
- **Drift remediation is gated.** After presenting drift findings, you MAY offer to update upstream planning documents (concept, outline, chapters.md, world/). **Never** modify chapter drafts under any circumstance. Wait for explicit user approval before any write. Decline / skip = command stays fully read-only.
- **Constitution Authority.** The book constitution (`.authorkit/memory/constitution.md`) is the authoritative style guide. Constitution violations are automatically CRITICAL.
- **Style Continuity Anchor.** `book/style-anchor.md` is the continuity baseline across model switches. Style-anchor drift is at least MEDIUM severity.

## Always-on Behavior

1. **Setup**: Run `{{SCRIPT_CHECK_PREREQ}}` from repo root and parse `BOOK_DIR`, `STYLE_ANCHOR`, and `AVAILABLE_DOCS`. All paths must be absolute. Abort with a clear error if required files are missing.

2. **Determine scope** from user input as above. Normalize chapter numbers to two-digit (`01`, `02`, …).

3. **Load core context** (used by both modes):
   - `concept.md` — premise, themes, characters/subjects, voice & tone, scope
   - `.authorkit/memory/constitution.md` — all writing principles
   - `STYLE_ANCHOR` at `BOOK_DIR/style-anchor.md` — cadence, diction/register, imagery density, dialogue profile, drift flags

4. **Report** at the end with a clear summary and concrete next-command suggestions.

## Mode: Chapter Craft Review (single chapter)

For a single chapter number `N`.

### Pre-flight

1. **Verify draft exists** at `chapters/NN/draft.md`. If not: ERROR *"Chapter draft not found. Run /authorkit.write N first."*
2. **Verify status** in `chapters.md` is at least `[D]` (drafted).

### Load chapter context

- **Required**: `chapters/NN/draft.md` (the chapter to review)
- **Required**: `chapters/NN/plan.md` (what was planned)
- **Required**: concept, constitution, style anchor (already loaded)
- **Recommended**: `characters.md` (consistency checks)
- **Recommended**: `outline.md` (chapter's role in overall structure)
- **Optional**: `research.md` and relevant `research/` topic files (recursive — scope `general` and `chapter CHNN`) for accuracy checks
- **Recommended**: `world/` files — load entity files across all categories for entities appearing in or relevant to this chapter. If `world/_index.md` exists, scan the draft for entity names and resolve them via the Alias Lookup (catches variants like "Captain Iri" ↔ "Iria Calder"); use the Chapter Manifest to identify entities tagged for this chapter; load only matched files.
- **Optional**: Previous and next chapter drafts (continuity)
- **Optional**: Previous review at `chapters/NN/review.md` (if revision cycle)

### Assess across dimensions

#### A. Plan Adherence

- Did the draft cover all planned scenes/sections?
- Were all key beats executed?
- Did the opening hook land effectively?
- Did the closing beat create forward momentum?
- Any significant deviations from the plan? Are they improvements?

#### B. Constitution Compliance

- Does the voice match the constitution's specifications?
- Is the POV consistent with the stated approach?
- Is the tense correct throughout?
- Does the prose style match the constitution's standards?
- Are any constitution principles violated?
- Does the chapter align with `book/style-anchor.md` on cadence, diction/register, imagery density, and dialogue profile?

#### C. Craft Quality

- **Pacing**: does the chapter flow well? Sections that drag or rush?
- **Show vs Tell**: emotions shown through action/dialogue rather than stated?
- **Dialogue** (fiction): natural? Each character sounds distinct?
- **Description**: concrete and sensory? Enough (or too much)?
- **Transitions**: smooth scene/section transitions?
- **Opening**: does the first paragraph hook?
- **Closing**: does the ending compel?

#### D. Character / Content Consistency

- **Fiction**: do characters behave consistently with their profiles? Voices distinct? Actions align with motivations?
- **Knowledge boundaries**: for each character in the chapter, verify they only act on information they could plausibly possess. If a character reacts to something (a lie, a plan, a schedule), trace when and how they learned it. Flag any case where a character knows something they were never told, witnessed, or could reasonably infer. Cross-check against previous chapters and `world/characters/` profiles.
- **Narrative necessity**: when the narrator frames an action as necessary ("the lie needed updating," "they had to," "there was no choice"), verify the claim against the story's own established logic. If the characters' own system makes the action pointless or unnecessary, the framing is wrong — either the action, the justification, or the narrator's commentary needs to change.
- **Non-fiction**: claims accurate? Examples relevant? Argument logical?

##### D1. World Consistency (if `world/` exists)

Cross-check this chapter against ALL relevant world/ categories. For each category, compare what appears in the chapter against the established world/ entries:

- **Characters**: compare every character appearing in this chapter against their `world/characters/` profile — physical descriptions (appearance, age, distinguishing features), personality traits, speech patterns, relationships, background details. Flag contradictions with both `(CONCEPT)` and `(CHxx)` tagged entries.
- **Places**: compare every location described or mentioned against its `world/places/` entry — physical descriptions, key features, atmosphere, spatial relationships. Flag setting details that contradict established descriptions. **Critically, verify that all character actions are physically possible within the established geometry** — characters cannot exit a dead-end cave "out the other side," cannot see a landmark from a location without line-of-sight, cannot walk between places faster than the established distance allows. Check any "Physical Constraints" section.
- **Headcount & logistics**: trace every character's physical location through the chapter scene by scene. At each scene transition, verify: (1) the number of characters stated or implied as present matches who could logistically be there, given prior movements, available transport, distances; (2) no character appears in a scene they couldn't have reached; (3) claims like "three watched" or "all four" match the actual count of bodies. Especially critical when characters split up, when new characters are introduced mid-chapter, or when a single character has multiple copies.
- **Organizations**: check any organizations referenced against their `world/organizations/` entries — membership, hierarchy, purpose, inter-organization relationships.
- **Systems**: if the chapter involves any system (magic, technology, political, economic), verify the depiction follows rules, limitations, scope, and exceptions defined in `world/systems/`. Flag rule violations.
- **History**: if past events are referenced, verify alignment with `world/history/` entries. Flag contradictory dates, participants, or outcomes.
- **New entities**: flag characters, places, organizations, systems, or historical events that appear in this chapter but have NO corresponding `world/` entry. These are candidates for `/authorkit.write` Reconcile (which captures them automatically post-draft).

For each contradiction found, cite the specific `world/` file, the tagged entry, and the location in the draft. Severity:
- Contradictions with established entries: **Critical** or **Important** depending on reader-visible impact
- Missing world/ entries: **Minor** (informational)

#### E. Continuity (if previous chapters exist)

- Does this chapter flow naturally from the previous one?
- Any contradictions with earlier chapters?
- Is voice/energy consistent across chapters?
- Are ongoing threads properly continued?
- **Backstory verification**: for every factual claim this chapter makes about events from prior chapters (flashbacks, references, "he had done X in CH03"), grep the actual draft text of that chapter and verify the claim is accurate. Do not trust the plan or outline — verify against the drafted prose. Flag any claim that contradicts what was written. Especially important for arrival details, exact lines of dialogue, and who instructed whom.

#### F. Theme Integration

- Are the book's themes present in this chapter where they should be?
- Is theme integration organic (not heavy-handed)?

### Generate review

Write the review to `BOOK_DIR/chapters/NN/review.md`:

```markdown
# Chapter Review: Chapter [NN] - [Title]

**Reviewed**: [DATE]
**Draft Word Count**: [count]
**Overall Assessment**: [PASS / NEEDS REVISION]

## Strengths

- [What works well — be specific with quotes or line references]
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
| Style Anchor Compliance | [A/B/C/D] | [Brief note] |
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

### Update chapter status

- **PASS**: change status `[D] → [X]` (approved) in `chapters.md`
- **NEEDS REVISION**: change `[D] → [R]` (reviewed, needs work)

### Report

- Overall assessment (PASS / NEEDS REVISION)
- Top 2-3 strengths
- Critical issues (if any)
- Suggested next action:
  - PASS → `/authorkit.write N+1` (plan + draft the next chapter)
  - NEEDS REVISION → `/authorkit.write N revise` (apply targeted edits based on review)

## Mode: Manuscript Drift (no chapter, "all", "manuscript")

Runs only after at least several chapters have been drafted. Identifies inconsistencies, continuity errors, pacing problems, and unresolved threads across all drafted chapters.

### Load artifacts

**From concept.md:**
- Premise, themes, characters/subjects, voice & tone, scope

**From outline.md:**
- Chapter structure, character arcs, thematic thread map, narrative arc

**From chapters.md:**
- Chapter statuses, dependencies

**From characters.md (if exists):**
- Character profiles, speech patterns, relationships

**From world/ folder (if exists):**
- If `world/_index.md` exists: read it first. Use the Chapter Manifest to load entity files per chapter (targeted loading) rather than all files at once. Use the Alias Lookup for name resolution when cross-referencing chapter text against `world/` entities.
- If no index: load all entity files (`characters/`, `places/`, `organizations/`, `history/`, `systems/`, `notes/`).
- Pay attention to chapter tags `(CHxx)` and `(CONCEPT)` for evolution tracking.

**From all drafted chapters (`chapters/NN/draft.md`):**
- Full prose for consistency checking

**From constitution and style anchor**: already loaded.

**From parked-decisions.md (if exists):**
- All OPEN parked decisions with their deadlines (`Before CHNN`, `Before final draft`, `No deadline`) — used to surface overdue items as findings (severity HIGH).

### Step 1: Upstream Drift Detection (Reconciliation)

Before analyzing cross-chapter quality, check whether upstream planning documents have drifted from what was actually drafted. **Drafted chapters are the canonical source of truth — everything else may be stale.**

**Scope**: All drafted chapters (or the user-specified range).

#### 1a. Outline Drift (`outline.md`)

For each chapter entry in `outline.md` that corresponds to a drafted chapter:
- Read the outline's Summary, Key Events, Characters Present, Ends With, and Connections fields.
- For each factual claim, grep the corresponding `chapters/NN/draft.md` for verification.
- Flag claims that don't match the draft.
- Common drift: characters acting differently, events playing out differently, endings that don't match.

For not-yet-drafted chapters: check if their claims about already-drafted chapters are accurate.

#### 1b. Concept Drift (`concept.md`)

- Focus on Synopsis, Characters, and Clarifications sections.
- Identify claims about specific events, character behaviors, or plot mechanics that have been concretized differently in drafts.

#### 1c. Chapters.md Drift

- Check each chapter's summary text against the draft. Key details should match.

#### 1d. World Drift (`world/` files)

- For `world/` files tagged `(CHxx)`: verify tagged claims against the actual draft.
- For `(CONCEPT)` entries: check if drafts now cover that topic differently.

**Drift severity**:
- **High**: a future chapter plan referencing this claim would produce a continuity error.
- **Medium**: the claim is inaccurate but unlikely to cause downstream errors.
- **Low**: technically compatible but could be more precise.

**Offer drift fixes** (gated): after presenting drift findings, ask the user: *"Fix all / Fix high-severity only / Review one by one / Skip?"* On approval, update upstream documents to match drafts (never modify drafts). Tag updates `(AMEND-YYYY-MM-DD)` in world/ files. Rebuild the world index with `{{SCRIPT_BUILD_WORLD_INDEX}}` after world edits.

### Step 2: Detection Passes

Focus on high-signal findings. Limit to 50 total findings (excluding drift findings from step 1).

#### A. Continuity & Timeline
- Events referenced in later chapters that weren't established in earlier ones
- Timeline contradictions (character in two places at once, seasonal inconsistencies)
- Character knowledge inconsistencies (knowing something before it was revealed)
- Setting details that change between chapters (eye color, building location, etc.)

#### B. Character Consistency (Fiction)
- Voice/speech pattern drift across chapters
- Motivation changes without justification
- Relationship dynamics that shift without cause
- Characters acting out of established character

#### C. Theme & Motif Tracking
- Themes introduced but never developed or resolved
- Themes that appear inconsistently
- Motifs that drift in meaning
- Foreshadowing that is never paid off

#### D. Pacing Analysis
- Consecutive chapters with similar energy levels
- Chapters significantly longer/shorter than average without justification
- Action/reflection balance across parts/acts
- Tension curve compared to intended narrative arc

#### E. Voice & Style Consistency
- POV breaks or inconsistencies
- Tense shifts (unless intentional)
- Prose style drift (more/less literary)
- Constitution principle violations
- Drift from `book/style-anchor.md` profile

#### F. Argument Coherence (Non-Fiction)
- Claims made without support
- Contradictory statements across chapters
- Prerequisites explained after they're needed
- Conclusions that don't follow from presented evidence

#### G. Plot Thread Tracking (Fiction)
- Subplots opened but not closed
- Chekhov's guns that never fire
- Mysteries raised but never resolved
- Character relationships that stall

#### H. Overdue Parked Decisions

If `parked-decisions.md` exists, surface any OPEN decision whose deadline has been reached or passed (a decision due "Before CH12" when CH12 is already drafted).
- Severity: **HIGH** by default (a past-deadline parked decision now blocks downstream consistency).
- Citation: PD identifier, deadline, summary, and the chapter(s) that should have triggered resolution.
- Recommendation: resolve via `/authorkit.discuss "resolve PD-NNN: <decision>"` (or, if the resolution requires manuscript propagation, `/authorkit.discuss <description>` will route it through Cross-cutting change).

#### I. World-Building Consistency

If `world/` exists, cross-reference world/ files against all drafted chapters:

- **Setting detail drift**: locations described differently across chapters (building changes floors, distances change, weather contradictions)
- **Character detail contradictions**: physical descriptions, ages, backgrounds that conflict between chapters or with `world/` files
- **Organization continuity**: membership, hierarchy, or purpose changes without narrative justification
- **Timeline/history contradictions**: past events described differently, contradictory dates or sequences
- **System rule violations**: magic/technology/political systems behaving inconsistently with established rules in `world/systems/`
- **Geography contradictions**: travel times, distances, spatial relationships that don't add up
- **Cultural inconsistencies**: customs, language, social norms that change without explanation
- **(CONCEPT) vs chapter conflicts**: details tagged `(CONCEPT)` in `world/` files that are contradicted by what's actually written in chapters

Each finding cites the specific `world/` file and the chapter(s) where the contradiction occurs.

### Step 3: Severity Assignment

- **CRITICAL**: Constitution violation, major plot hole, timeline contradiction, character inconsistency that breaks immersion, world rule violation that breaks established system logic, major geography/timeline contradiction
- **HIGH**: Unresolved subplot, significant pacing issue, theme dropped, important foreshadowing unfulfilled, character detail contradiction across chapters, significant setting drift, parked decision past its deadline
- **MEDIUM**: Minor continuity error, slight voice drift, pacing could be improved, minor character inconsistency, minor world detail inconsistency, cultural detail mismatch
- **LOW**: Style nitpick, optional improvement, very minor detail mismatch

### Step 4: Analysis Report

Output a Markdown report (no file write unless the author asks to save):

```markdown
## Book Analysis Report: [TITLE]

**Chapters Analyzed**: [N] of [Total]
**Analysis Date**: [DATE]

### Upstream Drift (Reconciliation)

| Source | Claim | Draft Reality | Severity | Fixed? |
|--------|-------|---------------|----------|--------|
| outline.md CH03 | [claim] | [reality] | High | [Yes/No/Skipped] |

### Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| C1 | Continuity | HIGH | CH03, CH07 | Character's eye color changes | Standardize to blue (CH03 version) |

### Thread Tracking

| Thread | Introduced | Developed | Resolved | Status |
|--------|-----------|-----------|----------|--------|
| [Thread name] | CH01 | CH03, CH07 | CH12 | Complete |
| [Thread name] | CH02 | CH05 | - | OPEN |

### Pacing Map

| Chapter | Word Count | Energy Level | Type |
|---------|-----------|-------------|------|
| CH01 | 3,200 | Medium | Setup |
| CH02 | 4,100 | High | Action |

### Constitution Compliance

| Principle | Status | Chapters with Issues |
|-----------|--------|---------------------|
| [Voice] | PASS | - |
| [Tense] | FAIL | CH04, CH09 |
| [Style Anchor] | [PASS/FAIL] | [chapters] |

### World Consistency (if world/ exists)

| Category | Entries Checked | Conflicts Found | Details |
|----------|----------------|-----------------|---------|
| Characters | [N] | [N] | [Brief] |
| Places | [N] | [N] | [Brief] |
| Organizations | [N] | [N] | [Brief] |
| Systems | [N] | [N] | [Brief] |
| (CONCEPT) Conflicts | [N] | [N] | [Pre-writing details contradicted by chapters] |

### Metrics

- Total chapters drafted: [N]
- Total word count: [N]
- Average chapter length: [N] words
- Critical issues: [N]
- Open threads: [N]
- Constitution violations: [N]
```

### Step 5: Next Actions

- If drift was found and fixed: note what upstream documents were updated (and that the world index was rebuilt if applicable).
- If drift was found but skipped: recommend re-running this command after fixing.
- If CRITICAL issues exist: recommend resolving before drafting more chapters.
- Provide specific `/authorkit.write [N] revise: <issue>` suggestions for the top issues.
- If world-building issues dominate: recommend the author run `/authorkit.write [last-drafted-N]` whose Reconcile pass deepens world extraction and rebuilds the index.
- If mostly clean: suggest continuing with `/authorkit.write next` or moving to final polish.

## Mode: Range Review

For an input like `5-10` or `chapters 5-10`:

1. Run **Chapter craft review** on each chapter in the range, in order. Each produces its own `chapters/NN/review.md`. Update status per chapter (`[D] → [X]` for PASS, `[D] → [R]` for NEEDS REVISION).
2. Run **Manuscript drift** scoped to the range:
   - Step 1 (Upstream drift): limit verification to outline/concept/world claims about chapters in the range.
   - Step 2 (Detection passes): cross-chapter checks restricted to interactions among chapters in the range (a thread introduced in CH02 and resolved in CH08 still counts when reviewing 5-10 because CH08 is in scope).
3. Report:
   - Per-chapter craft summaries (one block each)
   - Range-scoped drift findings table
   - Combined next-action suggestions

## Key Rules

- **Be constructive**: every criticism comes with a specific suggestion.
- **Be specific**: quote the draft, reference line locations, give concrete examples.
- **Respect the author's voice**: don't try to rewrite in a different style — evaluate against the constitution.
- **Prioritize ruthlessly**: one critical + three minor issues → critical first.
- **Grade fairly**: A = exceptional, B = solid, C = adequate, D = needs significant work.
- **PASS threshold**: no critical issues, no more than 2 important issues, constitution compliance is B or above.
- **Reviews are gated**: a chapter review writes only `chapters/NN/review.md` and updates the chapter row in `chapters.md`. A manuscript drift run writes nothing unless the author approves drift fixes — and those fixes touch only upstream planning artifacts (concept / outline / chapters.md / world), never chapter drafts.
- **Cap manuscript findings at 50** to keep reports actionable.
- **Use absolute paths.**
