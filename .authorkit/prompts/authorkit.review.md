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
- **Fixed voice origin is the drift baseline — not the anchor, not the neighbors.** The constitution is the *fixed* bar. Establish a **fixed origin**: the constitution, plus the concept's voice & tone section, plus the resolved origin chapters (the `## Voice Origin` pin if set, else the *earliest* approved (`[X]`) chapters). Grade *global* voice against that origin; match character/scene *texture* to the earliest relevant approved chapter (it may add to the origin, never lower it). `book/style-anchor.md` is only a derived continuity aid — `/authorkit.write` regenerates it from that same origin, but a stale or hand-edited anchor can lag, so never treat the anchor (or the immediately adjacent chapters) as the standard for what "good" sounds like. A chapter that matches its recently-drifted neighbors but has slipped from the origin **is** drifting, and that is a finding — not a defense.
- **Hunt for drift; default to flagging it.** Assume the manuscript is gradually slipping from its origin and look for where. "Consistent with recent chapters" is the *mechanism* of drift, not an excuse for it. The only sanctioned voice change is evolution the constitution (or a recorded act-boundary note) explicitly calls for; treat everything else as unsanctioned drift. When unsure whether a shift is intentional, flag it and let the author decide.

## Always-on Behavior

1. **Setup**: Run `{{SCRIPT_CHECK_PREREQ}}` from repo root and parse `BOOK_DIR`, `STYLE_ANCHOR`, and `AVAILABLE_DOCS`. All paths must be absolute. Abort with a clear error if required files are missing.

2. **Determine scope** from user input as above. Normalize chapter numbers to two-digit (`01`, `02`, …).

3. **Load core context** (used by both modes). Load the fixed references *first* and hold them as the bar **before** reading the chapter under review, so the standard is set in advance rather than calibrated to the prose in front of you:
   - `.authorkit/memory/constitution.md` — all writing principles (the fixed bar)
   - `concept.md` — premise, themes, characters/subjects, voice & tone, scope
   - **Origin reference (the fixed drift baseline — global voice)** — resolve the voice origin: if the constitution has a `## Voice Origin` pin covering this chapter's stage, load the chapter(s) it names; otherwise default to the *earliest* (lowest-numbered) approved (`[X]`) chapters. Two or more approved: load the earliest one or two drafts; exactly one approved: load that one draft; none approved: the origin is the constitution plus the concept's voice & tone section alone. This origin governs *global* voice and does **not** move as the book grows. If you judge a different chapter to be a better voice exemplar (e.g. the opening is an atypical prologue), *propose* pinning it via `/authorkit.discuss` (Constitution mode) — never silently switch the bar, which would let drift hide behind a convenient anchor.
   - `STYLE_ANCHOR` at `BOOK_DIR/style-anchor.md` — cadence, diction/register, imagery density, dialogue profile, drift flags. Use it as a continuity aid, but remember it is only a *derived* view of the origin (and may be stale or hand-edited): where it disagrees with the constitution or the origin, the constitution and origin win.

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
- **Recommended — voice texture exemplar**: for character/scene/arc voice the origin leaves open, load the **earliest *relevant* approved chapter** — the lowest-numbered `[X]` draft featuring this chapter's POV/focus characters or the same arc register (use the `world/_index.md` Chapter Manifest + Alias Lookup). It is the bar for *texture* (this character's cadence, this arc's register), but it may only *add* to the fixed origin, never lower it. Pick the *earliest* relevant draft, not the most recent.
- **Recommended — continuity & arc references**: for plot/thread/state, choose by *relevance*, not just `N±1` — the adjacent drafts, plus the **most recent** chapter(s) featuring this chapter's POV/focus characters and the chapter that last advanced an arc converging here. This is current-state context for *what happens*; voice is still graded against the fixed origin (global) and matched to the earliest-relevant exemplar (texture), never against a drifted neighbour.
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
- **Voice fidelity vs origin (global)**: compare the chapter's *global* voice — POV, narrative distance, sentence rhythm, diction/register, imagery — against the **fixed origin** (constitution + concept voice/tone + the resolved origin chapters: the `## Voice Origin` pin if one covers this stage, else the earliest approved chapters), not merely against the style anchor or the previous chapter. Flag drift from the origin even when the chapter reads as locally consistent with its neighbors. Character/scene/arc *texture* (a POV character's cadence, an arc's register) is matched against the earliest-relevant exemplar and assessed under Continuity (E), not here. Distinguish *unsanctioned* drift (a finding, at least Important; Critical if it is also a constitution violation) from *constitution-sanctioned* evolution (not a finding). Quote the specific lines that diverge.

#### B1. LLM Literary Tic Audit

Load `.authorkit/prompts/_shared/literary-tic-catalog.md` and check the chapter against every pattern in it.

- For each pattern, count instances in the chapter (and per 1,000 words for the density patterns marked per-1,000-words in the catalog's budget table).
- Compare counts against the catalog's default budgets.
- **Constitution waivers**: before flagging anything, check `.authorkit/memory/constitution.md` and the style anchor's **Avoid** / **Imagery Density** sections for explicit waivers (the pattern must be named by number, by example, or by description — a vague "literary register" line is not a waiver). If a waiver applies, note it at the top of the review (e.g., *"Polysyndeton waived by constitution §II"*) and skip the corresponding count.
- Tightened budgets in the constitution are binding — flag at the tightened threshold, not the default.
- For every pattern over its (effective) budget, write a finding with: pattern number/name, count vs. budget, line/paragraph citations for each instance, and a one-line rewrite suggestion that does NOT introduce a different pattern from the catalog.
- Severity mapping:
  - Patterns 7 and 13 over budget → **Critical**
  - Patterns 3, 10, and 16 over budget, or any instance of a named zero-budget cliché variant (patterns 14, 15) → **Important**
  - Other patterns over budget → **Minor** (single instance over) or **Important** (≥2× budget)

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

Cross-check this chapter against ALL relevant world/ categories. For each entity, compare what appears in the chapter against its `## Current State` block (the canonical now-truth); use `## History` to tell whether a discrepancy is a genuine contradiction or an established later-chapter evolution. For each category:

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
- Does this chapter's character/scene/arc voice *texture* match the earliest **relevant** approved chapter (same POV/focus character or arc register), not just whatever chapter came before it? (Global voice drift is graded separately under B / Voice Fidelity vs Origin — being "consistent with a recent chapter" does not excuse drift from the origin.)
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
| Voice Fidelity (vs Origin) | [A/B/C/D] | [Global-voice drift from the origin (pin / earliest [X]); note if sanctioned] |
| Style Anchor Compliance | [A/B/C/D] | [Brief note] |
| LLM Tic Audit | [A/B/C/D] | [Patterns over budget; active waivers, if any] |
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
- If `world/_index.md` exists: read it first. Use the Chapter Manifest to load entity files per chapter (targeted loading) rather than all files at once. Use the Alias Lookup for name resolution when cross-referencing chapter text against `world/` entities. Within each loaded file, `## Current State` is the canonical now-truth; `## History` is the tagged provenance log.
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

- Treat each file's `## Current State` block as the entity's canonical now-truth; use `## History` (the tagged log) for provenance and "when did this enter" checks.
- For `## History` entries tagged `(CHxx)`: verify the tagged claim against the actual draft.
- For `(CONCEPT)` entries: check if drafts now cover that topic differently.

#### 1e. Outline Aggregate-Section Resynthesis (`outline.md`)

Steps 1a–1d check the *per-chapter* outline entries. The synthesized cross-cutting sections drift separately, because reconcile only refreshes the chapter that was just drafted and never re-derives these:

- **Narrative Arc / Argument Flow** table — do the phase→chapter mappings still match how the drafted chapters actually function?
- **Character Arcs / Concept Progression** tables — does each row reflect where the character/concept actually stands in the drafts?
- **Thematic Thread Map** — are the Introduced / Developed / Resolved chapters accurate against what the drafts actually do with each theme?

Flag rows that no longer match drafted reality. These are **resynthesis candidates**: the fix rebuilds the section from the drafts, not a line-edit. Severity: Medium by default (these feed planning, so staleness here misleads future chapters); High if a not-yet-drafted chapter's plan would inherit a wrong arc/theme position.

#### 1f. World Entity Consolidation (`world/` files)

Long books accumulate layered `## History` in entity files. Using the `world/_index.md` Entity Registry (prioritise entities with the most chapter tags), check each entity for:

- **Stale Current State**: the `## Current State` block disagrees with the latest `(CHxx-rev)` / `(AMEND-)` entry in `## History`, or is missing entirely (legacy flat-list file).
- **Unresolved internal contradiction**: two History entries assert conflicting facts (e.g. `(CH05)` "left-handed", `(CH22)` "right-handed") with no later entry or Current State line establishing which holds. Cross-check the drafts to determine the true current value.
- **Dead weight**: details deprecated in earlier reconciles that no chapter references any more.

These are **consolidation candidates**: the fix refreshes `## Current State` to the draft-verified now-truth and may move long-dead entries under a `### Superseded` subheading in History (never deletes provenance). Severity: High if a stale Current State would mislead drafting/review of the next chapter; Medium otherwise.

**Drift severity**:
- **High**: a future chapter plan referencing this claim would produce a continuity error.
- **Medium**: the claim is inaccurate but unlikely to cause downstream errors.
- **Low**: technically compatible but could be more precise.

**Offer drift fixes** (gated): after presenting drift findings, ask the user: *"Fix all / Fix high-severity only / Review one by one / Skip?"* On approval, update upstream documents to match drafts (never modify drafts). Tag updates `(AMEND-YYYY-MM-DD)` in world/ files. Rebuild the world index with `{{SCRIPT_BUILD_WORLD_INDEX}}` after world edits.

**Consolidation fixes are snapshot-gated.** The 1e/1f fixes (outline aggregate resynthesis, world `## Current State` refresh, History archival under `### Superseded`) rewrite canonical planning state rather than correcting a single stale claim, and unlike a draft they have no "drafts are canonical" safety net. Before applying any of them, **take a snapshot first** the same way a Cross-cutting change does: write `BOOK_DIR/snapshots/YYYY-MM-DD-pre-consolidate-[slug].md` from `.authorkit/templates/snapshot-template.md` and `git tag snapshot/YYYY-MM-DD-pre-consolidate-[slug]`. A Current State refresh is tagged `(AMEND-YYYY-MM-DD)` in History; resynthesized outline sections need no tag. Rebuild the world index after world edits.

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
- **LLM tic density across chapters**: load `.authorkit/prompts/_shared/literary-tic-catalog.md` and aggregate pattern counts across all drafted chapters in scope. Honor any constitution waivers (skip the corresponding patterns). Flag any pattern whose cross-chapter density is ≥2× the per-chapter budget on average, even if no single chapter is over budget on its own — this catches voice drift toward AI-flavoured prose that any single chapter could plausibly defend. Also check pattern 19's consecutive-chapter component here: three or more chapters in a row ending on the same zoom-out coda cadence is a voice-drift finding no single chapter can trip. Severity: HIGH for patterns 7 and 13; MEDIUM for the rest.

#### E1. Drift Trajectory (slope vs origin)

Per-chapter checks catch absolute violations but miss *gradual* drift where every chapter is individually defensible yet the book has slid a long way from where it started. Establish the **fixed origin** (constitution + concept voice/tone + the resolved origin chapters — the `## Voice Origin` pin if set, else the earliest approved) and trace the *direction* of change across the chapter sequence, not just per-chapter compliance:

- Read the chapters in order and track the trend of: average and variance of sentence length, paragraph shape, dialogue ratio, diction/register, and tic density.
- Flag a **monotonic slope away from the origin** even when no single chapter breaches a budget — e.g. sentence length creeping up act over act, dialogue steadily thinning, register drifting more (or less) literary, the same epiphany-coda cadence recurring across runs of chapters.
- **Origin jump test**: compare the latest chapters directly against the origin chapters (the `## Voice Origin` pin if set, else the earliest approved). If a reader started at the origin and jumped to the latest chapter, would it read as the same book, same narrator, same voice? Quote the divergence.
- **Calibration sanity check**: re-read the *resolved origin* chapter (the `## Voice Origin` pin if set, else the earliest approved) against the *current* constitution and style anchor. If that origin chapter would no longer pass today's bar, the **bar has drifted** — e.g. a stale or hand-edited style anchor, or a voice evolution that was never recorded in the constitution. (If a pin already excludes an atypical opening, grade against the pinned exemplar — do not re-flag the excluded chapter.) Flag it and recommend re-grounding the anchor via `/authorkit.write` (which regenerates it from the origin), or recording the shift in `## Voice Origin`.

Severity: HIGH if the trajectory crosses a budget or a constitution principle by the latest chapters; MEDIUM for a clear unsanctioned slope still within budget. Distinguish constitution-sanctioned evolution from unsanctioned drift; when ambiguous, surface it for the author to judge.

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

### Consolidation (if any proposed — snapshot-gated)

| Target | Issue | Action | Severity | Applied? |
|--------|-------|--------|----------|----------|
| outline.md Character Arcs | Iria's arc row stale vs CH12–CH18 | Resynthesize from drafts | Medium | [Yes/No/Skipped] |
| world/characters/iria.md | Current State stale vs CH22-rev | Refresh + archive 3 dead History entries | High | [Yes/No/Skipped] |

*If any consolidation was applied, note the snapshot tag here.*

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

### Drift Trajectory (vs Origin)

| Metric | Origin (pin / earliest [X]) | Latest | Direction | Verdict |
|--------|----------------------|--------|-----------|---------|
| Avg sentence length | [n] | [n] | [rising/flat/falling] | [OK/Watch/Flag] |
| Dialogue ratio | [n] | [n] | [rising/flat/falling] | [OK/Watch/Flag] |
| Tic density (per 1k) | [n] | [n] | [rising/flat/falling] | [OK/Watch/Flag] |
| Register / diction | [origin feel] | [latest feel] | [drift direction] | [OK/Watch/Flag] |

*Origin jump test*: [does the latest chapter still read as the same book as the origin? quote any divergence]
*Bar calibration*: [does the resolved origin chapter (pin if set, else earliest [X]) still pass today's constitution + style anchor? if not, the anchor has drifted — recommend re-grounding]

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
- If a recurring AI-flavoured pattern shows up that is NOT in the tic catalog: recommend adding it to the constitution via `/authorkit.discuss` (Constitution mode) so drafting and review both enforce it going forward. Do not park it in the style anchor's **Avoid** section — the anchor is regenerated from the constitution on every refresh, so hand-added entries there are overwritten.
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
- **Respect the author's voice**: don't try to rewrite in a different style — evaluate against the constitution and the origin, never against your own taste.
- **Anchor to the origin, not the neighbors**: grade *global* voice against the fixed origin (constitution + concept voice/tone + the pinned-or-earliest approved chapters); match *character/scene texture* to the earliest **relevant** approved chapter. "Consistent with the last chapter" never establishes that something is correct — recent chapters may already have drifted.
- **Prioritize ruthlessly**: one critical + three minor issues → critical first.
- **Grade fairly**: A = exceptional, B = solid, C = adequate, D = needs significant work.
- **PASS threshold**: no critical issues, no more than 2 important issues, constitution compliance is B or above, and Voice Fidelity (vs Origin) is B or above (no significant *unsanctioned* drift from the origin).
- **Reviews are gated**: a chapter review writes only `chapters/NN/review.md` and updates the chapter row in `chapters.md`. A manuscript drift run writes nothing unless the author approves drift fixes — and those fixes touch only upstream planning artifacts (concept / outline / chapters.md / world), never chapter drafts. Consolidation fixes (1e/1f) additionally write a pre-consolidate snapshot before applying.
- **Cap manuscript findings at 50** to keep reports actionable.
- **Use absolute paths.**
