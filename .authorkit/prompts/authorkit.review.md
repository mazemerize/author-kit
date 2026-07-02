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
- A single chapter with `style` (`7 style`, `style 7`, "check the voice of 7") → **Style Fidelity** (the gating style pass run alone; writes `chapters/NN/style-review.md`)
- A range (`5-10`, `chapters 5-10`) → **Range review** (per-chapter craft + drift scan scoped to the range)
- Empty, `all`, `manuscript`, `book`: → **Manuscript drift** (cross-chapter consistency, threads, pacing, voice)

## Goal

This is the review command. It does a few distinct jobs and infers which is needed from scope:

1. **Chapter craft review**: assess a single drafted chapter against its plan, the concept, the constitution, the style anchor, the `world/` entries, and adjacent chapters. Output a `review.md` file with strengths, issues by severity, dimension scores, and a verdict.
2. **Manuscript drift**: cross-chapter analysis for continuity errors, character drift, theme tracking, pacing, voice/style consistency, world-building integrity, overdue parked decisions, and upstream drift (concept/outline/chapters.md/world out of sync with drafts). Output a structured Markdown report; offer upstream drift fixes gated by approval; **never** modify drafts.
3. **Style Fidelity** (`N style`): runs *only* the gating style pass the craft review leads with — voice vs the fixed origin + the literary-tic audit — and writes `chapters/NN/style-review.md`. A fast, explicit voice check to run right after a chapter is written.

A range invocation runs the chapter craft review on each chapter in the range, then a drift scan limited to that range.

## Operating Constraints

- **Read-only by default.** Analysis itself never modifies files — with one carve-out: Pass 2 maintains `book/tic-ledger.md` (bootstrap + Step B write-back). The ledger is review-owned memory, not manuscript or planning state.
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
   - **Origin reference (the fixed drift baseline — global voice)** — resolve the voice origin: if the constitution's `## Voice Origin` names exemplar chapter(s) (`From CHnn:`) covering this stage, load those, **and load any `### Voice Exemplars` excerpts present there** (author prose samples that are part of the origin); otherwise default to the *earliest* (lowest-numbered) approved (`[X]`) chapters, still folding in any excerpts. Two or more approved: load the earliest one or two drafts; exactly one approved: load that one draft; none approved: the origin is the constitution + the concept's voice & tone section + any `### Voice Exemplars` excerpts (the excerpts are the concrete voice bar before any chapter is approved). This origin governs *global* voice and does **not** move as the book grows. If you judge a different chapter to be a better voice exemplar (e.g. the opening is an atypical prologue), *propose* pinning it via `/authorkit.discuss` (Constitution mode) — never silently switch the bar, which would let drift hide behind a convenient anchor.
   - `STYLE_ANCHOR` at `BOOK_DIR/style-anchor.md` — cadence, diction/register, imagery density, dialogue profile, drift flags. Use it as a continuity aid, but remember it is only a *derived* view of the origin (and may be stale or hand-edited): where it disagrees with the constitution or the origin, the constitution and origin win.

4. **Report** at the end with a clear summary and concrete next-command suggestions.

## Mode: Style Fidelity (single chapter, style-only)

Triggered by `N style` / `style N` (or a chapter plus "style" / "voice" / "fidelity"). A focused, **read-only** pass that runs **only** the gating passes — Pass 1 (Style Fidelity) + Pass 2 (AI-Tic Audit) — against the **fixed origin**, nothing about plot, world, theme, or pacing. Run it right after a chapter is written for a fast, explicit voice check. (The full craft review runs these same passes first; this mode is them in isolation.)

1. Resolve the **fixed origin** exactly as the craft review does (Always-on step 3 → Origin reference): the `## Voice Origin` pin/excerpts if set, else the earliest approved (`[X]`) chapters, else constitution + concept voice/tone. Load `book/style-anchor.md` as a derived aid only — where it disagrees with the origin, the origin wins.
2. Run **Pass 1 (Style Fidelity)** and **Pass 2 (AI-Tic Audit)** in full — voice vs origin (global), style-anchor alignment, constitution voice rules, and the two-step tic discovery & contrast (blind Step A against the origin prose, then Step B ledger reconciliation, including the first-run bootstrap and the write-back to `book/tic-ledger.md`) — quoting the specific lines that diverge.
3. Write `BOOK_DIR/chapters/NN/style-review.md`:

   ```markdown
   # Style Fidelity: Chapter [NN] - [Title]

   **Reviewed**: [DATE]
   **Origin**: [pin/excerpts | earliest [X] chapters | constitution + concept]
   **Verdict**: [STYLE PASS / NEEDS STYLE REVISION]

   ## Voice vs Origin
   - [Axis / line ref] — [origin expectation] vs [chapter]; [OK / drift]. **Fix**: [in-voice replacement]

   ## Literary Tics
   | TIC (id / new) | Shape | Instances | Trend | Status | Lines |

   ## Verdict
   **Status**: [STYLE PASS / NEEDS STYLE REVISION]
   ```

4. **Status & report**: NEEDS STYLE REVISION → set `[D] → [R]` (the revise step addresses voice); STYLE PASS → leave status unchanged (a clean style pass does not approve the chapter — the full craft review does). Report the verdict, the top drift findings, and the next step: PASS → `/authorkit.review N` (full craft) or `/authorkit.write N+1`; NEEDS → `/authorkit.write N revise: <the style fixes>`.
5. **Read-only except the verdict and the ledger** — writes only `chapters/NN/style-review.md`, the `book/tic-ledger.md` update (Pass 2's Step B write-back), and the `[D]→[R]` flip; never edits the draft, and says nothing about plot, world, theme, or pacing.

## Mode: Chapter Craft Review (single chapter)

For a single chapter number `N`.

### Pre-flight

1. **Verify draft exists** at `chapters/NN/draft.md`. If not: ERROR *"Chapter draft not found. Run /authorkit.write N first."*
2. **Verify status** in `chapters.md` is at least `[D]` (drafted).

### Load chapter context

- **Required**: `chapters/NN/draft.md` (the chapter to review)
- **Required**: `chapters/NN/plan.md` (what was planned)
- **Required**: concept, constitution, style anchor (already loaded)
- **Required**: `book/tic-ledger.md` — Pass 2's memory (created from `.authorkit/templates/tic-ledger-template.md` during Pass 2 if missing). Held by the parent only — never handed to the blind discovery step.
- **Recommended**: `characters.md` (consistency checks)
- **Recommended**: `outline.md` (chapter's role in overall structure)
- **Optional**: `research.md` and relevant `research/` topic files (recursive — scope `general` and `chapter CHNN`) for accuracy checks
- **Recommended**: `world/` files — load entity files across all categories for entities appearing in or relevant to this chapter. If `world/_index.md` exists, scan the draft for entity names and resolve them via the Alias Lookup (catches variants like "Captain Iri" ↔ "Iria Calder"); use the Chapter Manifest to identify entities tagged for this chapter; load only matched files.
- **Recommended — voice texture exemplar**: for character/scene/arc voice the origin leaves open, load the **earliest *relevant* approved chapter** — the lowest-numbered `[X]` draft featuring this chapter's POV/focus characters or the same arc register (use the `world/_index.md` Chapter Manifest + Alias Lookup). It is the bar for *texture* (this character's cadence, this arc's register), but it may only *add* to the fixed origin, never lower it. Pick the *earliest* relevant draft, not the most recent.
- **Recommended — continuity & arc references**: for plot/thread/state, choose by *relevance*, not just `N±1` — the adjacent drafts, plus the **most recent** chapter(s) featuring this chapter's POV/focus characters and the chapter that last advanced an arc converging here. This is current-state context for *what happens*; voice is still graded against the fixed origin (global) and matched to the earliest-relevant exemplar (texture), never against a drifted neighbour.
- **Optional**: Previous review at `chapters/NN/review.md` (if revision cycle)

### Assess in passes (canonical roster)

Run the **Analysis Passes** defined in the shared generation guardrails, in order. Passes 1–2
are **gating**: a chapter that fails either is **NEEDS REVISION** regardless of how it scores
elsewhere. Each pass becomes its own section in `review.md` (heading keyed to the roster
name) and its own row in the Dimension Scores table. Every finding carries the shared shape:
severity + a line/paragraph citation or quote + a one-line fix.

**Sub-agent fan-out (when available).** If the runtime offers parallel sub-agents (Claude's
Task/Agent tool), first resolve the **shared baseline once** — the fixed voice origin, this
roster, `book/tic-ledger.md`, scope and absolute paths — then spawn **one sub-agent per pass in
parallel**, handing each only its remit and the context it needs (Pass 1: origin + style
anchor; Pass 2: the origin prose only — **blind**, no ledger and no seed catalog, so
discovery is unbiased; the parent holds the ledger and runs Step B reconciliation on the
sub-agent's findings; Pass 3: this draft alone; Pass 4: prior drafted chapters +
`world/` `## Current State`; Pass 5: the outline; Pass 6: this draft with scaffolding
withheld; Pass 7: plan + concept + world). Each returns findings in the shared shape; the
**parent** aggregates them into the single `review.md`, applies the Pass 1–2 gate, dedups
cross-pass overlaps (e.g. a creed-maxim beat-closer trips both a Pass 2 ledger entry and
Pass 1 register drift), computes the scores/verdict, and updates `chapters.md`. **Independence guard:** sub-agents
never re-derive the voice bar — the parent owns the fixed origin and passes it down. Where
sub-agents are unavailable (other flavors, headless without the Task tool), run the **same**
passes sequentially in-context against the **same** roster, emitting the **same** findings.

#### Pass 1 — Style Fidelity (gating)

The dedicated style pass, and the whole of the focused `/authorkit.review N style` mode. A chapter that has drifted from the voice origin, or carries a recurring non-waived tic shape (Pass 2), is **automatically NEEDS REVISION** — not approved while it is out of voice, however well it scores elsewhere.

- **Voice fidelity vs origin (global)**: compare the chapter's *global* voice — POV, narrative distance, sentence rhythm, diction/register, imagery — against the **fixed origin** (constitution + concept voice/tone + the resolved origin: the `## Voice Origin` pin/excerpts if set, else the earliest approved chapters), not merely against the style anchor or the previous chapter. Flag drift from the origin even when the chapter reads as locally consistent with its neighbors. Character/scene/arc *texture* (a POV character's cadence, an arc's register) is matched against the earliest-relevant exemplar and assessed under Pass 4, not here. Distinguish *unsanctioned* drift (a finding, at least Important; Critical if it is also a constitution violation) from *constitution-sanctioned* evolution (not a finding). Quote the specific lines that diverge.
- **Style-anchor alignment**: does the chapter align with `book/style-anchor.md` on cadence, diction/register, imagery density, and dialogue profile? The anchor is a derived view of the origin — where they disagree, the origin wins.
- **Constitution voice rules**: voice matches the constitution's specifications; POV consistent; tense correct throughout; prose style matches the standards; no principle violated.

#### Pass 2 — AI-Tic Audit (gating) — Tic Discovery & Contrast

The self-learning tic pass (see the shared guardrails' *Tic Ledger & Voice Pairs*). It maintains `book/tic-ledger.md` — the living, book-specific tic catalog — by contrasting the draft against the **fixed origin prose**, in two mandatory steps in this order:

- **Bootstrap (first run only)**: if `book/tic-ledger.md` does not exist, create it from `.authorkit/templates/tic-ledger-template.md`, seeding entries with `Status: seed` from the shipped seed catalog's high-signal patterns (`.authorkit/prompts/_shared/literary-tic-catalog.md` — patterns 7, 13, 21, 22, 23, 24 and its zero-budget forms). Seeds are hypotheses; the steps below confirm or retire them.
- **Step A — blind discovery.** Read the draft against ONLY the resolved origin prose — deliberately without the ledger or the seed catalog in hand, so discovery is not biased toward known patterns and can surface tics nobody has named yet. Remit: find constructions, sentence shapes, beat-closers, and rhetorical gestures that **recur in the draft but are absent or rare in the origin**. For each: quote every instance with line/paragraph citations, describe the shape in one line, and show how the origin prose accomplishes the same job (the counter-example). When sub-agents are available this step IS the Pass 2 sub-agent (see fan-out); otherwise run it as a first, list-free read.
- **Step B — ledger reconciliation** (the parent, holding the ledger): merge Step A's discoveries into `book/tic-ledger.md` — increment trends on recurring entries; create new `TIC-NNN` entries (book quote + origin counter-example) for new shapes; tick the decay counter on active entries Step A did not see (active → dormant after 1 clean chapter, dormant → retired after 2 more; unconfirmed `seed` entries retire after 2 reviews; a rediscovered retired shape reactivates with its history). Then run **one targeted sweep** of the draft for still-active ledger entries Step A missed — a shape appearing only once this chapter still ticks its trend. Write the updated ledger back to `book/tic-ledger.md`.
- **Constitution waivers**: check `.authorkit/memory/constitution.md` (and the style anchor's **Avoid** / **Imagery Density** sections) for explicitly named patterns — by example or description; a vague "literary register" line is not a waiver. Record the waiver on the matching ledger entry's `Waiver:` field, note active waivers at the top of the review, and report (never flag) waived shapes. A constitution that bans a shape outright is binding regardless of trend.
- **Findings**: every non-waived discovered/recurring shape becomes a finding with: TIC id (or "new"), instance count, citations for each instance, and a one-line rewrite grounded in the origin counter-example (the fix is what the origin does for the same job — never a rewrite that introduces another ledger shape).
- **Severity mapping** (density- and trend-based, gating):
  - A shape recurring **≥3 times** in this chapter, or an **active ledger entry with a rising trend** (more instances than the previous reviewed chapter) → **Critical**
  - A shape with **2 instances**, or a recurring active entry holding steady → **Important**
  - A **single instance** of an active ledger entry → **Minor**

#### Pass 3 — In-Chapter Logical Consistency

*Within this chapter only* — internal logic and arithmetic. A hard internal contradiction is **Critical**.

- **Quantities**: every concrete count/age/date/duration/distance/ordinal stated in the chapter is internally consistent (three guards established ≠ "the four guards" later in the same scene) and arithmetically sound.
- **Headcount & logistics (intra-chapter)**: trace every character's location scene by scene. At each transition verify (1) the number stated or implied present matches who could be there given prior movement within the chapter; (2) no character appears in a scene they couldn't have reached; (3) claims like "three watched" or "all four" match the actual count of bodies. Especially critical when characters split up or are introduced mid-chapter.
- **Physical possibility**: all actions are possible within the established geometry — no exiting a dead-end "out the other side," no seeing a landmark without line-of-sight, no crossing a distance faster than established. Check any place "Physical Constraints."
- **Knowledge-at-this-point**: a character acts only on what they could know *by this moment in this chapter*; if they react to a lie/plan/schedule, it was established earlier in the chapter (cross-chapter knowledge is Pass 4).
- **Narrative necessity**: when the narrator frames an action as necessary ("the lie needed updating," "they had to," "there was no choice"), verify it against the story's own established logic; if their own system makes it pointless, the action, justification, or commentary is wrong.

#### Pass 4 — Cross-Chapter & Plot-Arc Logical Consistency

Vs prior **drafted** chapters and `world/` `## Current State` — the canonical now-truth (`## History` tells whether a discrepancy is a genuine contradiction or an established later-chapter evolution). The cross-chapter bullets apply only when previous drafted chapters exist, but the **World & canon consistency** bullet runs whenever `world/` exists — **including on chapter 1**, whose draft must already agree with the `(CONCEPT)`-seeded world files. Score this pass N/A only when there are no previous chapters *and* no `world/`.

- **Flow & contradictions**: does this chapter follow naturally from the prior relevant ones? Any contradiction with what earlier chapters established?
- **Quantitative drift across chapters**: a quantity/fact committed in an earlier chapter (nine guards, age forty, a two-day journey) must not silently change here. Flag any referent whose value differs without an in-story change. **Critical** for a hard contradiction.
- **Backstory verification**: for every factual claim this chapter makes about events from prior chapters ("he had done X in CH03"), grep the actual draft text of that chapter and verify it. Do not trust the plan or outline — verify against the drafted prose. Especially arrival details, exact lines of dialogue, who instructed whom.
- **Knowledge boundaries across chapters**: a character knows only what they were told, witnessed, or could infer in prior chapters; cross-check `world/characters/` profiles.
- **Plot-arc convergence**: a thread/arc this chapter advances is consistent with where prior chapters left it (use the `world/_index.md` Chapter Manifest + the most recent chapter that advanced the arc).
- **Voice texture continuity**: the chapter's character/scene/arc voice *texture* matches the earliest **relevant** approved chapter (same POV/focus or arc register), not merely the previous chapter. (Global voice is graded under Pass 1.)
- **World & canon consistency (if `world/` exists)**: cross-check entities appearing here against ALL relevant world/ categories — **Characters** (appearance, age, traits, speech, relationships, background), **Places** (descriptions, features, spatial relationships), **Organizations** (membership, hierarchy, purpose), **Systems** (rules, limits, scope — flag violations), **History** (dates, participants, outcomes). Flag contradictions with `(CONCEPT)` and `(CHxx)` entries, citing the world/ file, the tagged entry, and the draft location. **New entities** with no world/ entry are **Minor** (informational — Reconcile captures them post-draft). Established-entry contradictions are **Critical**/**Important** by reader-visible impact.

#### Pass 5 — Disclosure Horizon

Per the Disclosure Horizon Protocol. Scan for the chapter revealing a plot fact the outline/plan assigns to a *later* chapter — narrator-prophecy / proleptic flash-forward ("what she would only understand years later…") that names an undisclosed future, or a "later XXX, but for now YYY" where XXX is not yet known to the reader. Distinguish from **allowed** planted foreshadowing (an image/object that pays off later without naming the payoff). A reader-visible spoiler of a later reveal is **Critical**; a softer proleptic leak is **Important**.

#### Pass 6 — Standalone Readability

Per the Standalone Readability self-check. Would the chapter be fully comprehensible to a reader with **zero** access to `world/`/outline/concept — only the shipped chapters? Flag any sentence that parses *only* with the scaffolding: a name/term/relationship dropped without in-prose grounding, "as established" reliance on an unstated fact, or encyclopedia voice transcribed from a `world/` entry. Also flag the converse — something load-bearing withheld because "it's in the world file." An unexplained scaffolding-dependent reference is at least **Important**.

#### Pass 7 — Craft & Structure

- **Plan adherence**: did the draft cover all planned scenes/sections and key beats? Did the opening hook land and the closing beat create momentum? Any significant deviations — are they improvements?
- **Craft quality**: pacing (sections that drag or rush); show vs tell (emotions shown, not stated); dialogue (natural, distinct per character); description (concrete, sensory, right amount); transitions; opening hook; compelling close.
- **Character/content behaviour**: characters behave consistently with their profiles and motivations; voices distinct. Non-fiction: claims accurate, examples relevant, argument logical.
- **Theme integration**: the book's themes are present where they should be, and integrated organically (not heavy-handed).

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

## Pass Scores

| Pass | Score | Notes |
|------|-------|-------|
| 1 — Style Fidelity *(gating)* | [A/B/C/D] | [Global-voice drift vs origin (pin / earliest [X]); style-anchor + constitution voice; note if sanctioned] |
| 2 — AI-Tic Audit *(gating)* | [A/B/C/D] | [Shapes discovered vs origin; recurring/rising ledger entries; active waivers, if any] |
| 3 — In-Chapter Logical Consistency | [A/B/C/D] | [Intra-chapter quantities/arithmetic/headcount/geometry/knowledge] |
| 4 — Cross-Chapter & Plot-Arc Logic | [A/B/C/D/N/A] | [Numeric drift, backstory, knowledge, arc convergence, world/canon — world/canon runs even on CH01; N/A only with no prior chapters and no world/] |
| 5 — Disclosure Horizon | [A/B/C/D] | [Premature disclosure / proleptic leaks of later chapters] |
| 6 — Standalone Readability | [A/B/C/D] | [Scaffolding-only references; self-sufficiency] |
| 7 — Craft & Structure | [A/B/C/D] | [Plan adherence, craft, character behaviour, theme] |

## Verdict

**Status**: [PASS - ready to move on / NEEDS REVISION - see critical issues]

**Next Steps**:
- [Specific action items if revision needed]
- [Or: "Proceed to next chapter"]
```

### Update chapter status

- **PASS**: change status `[D] → [X]` (approved) in `chapters.md`. PASS **requires the gating passes (1 Style Fidelity and 2 AI-Tic Audit) to pass**, and **no unresolved logical/quantitative contradiction (Pass 3/4) and no premature-disclosure leak (Pass 5)** — never approve a chapter that drifted from the voice origin, carries a recurring non-waived tic shape or a rising active ledger entry, contradicts an established quantity/fact, or spoils a later reveal, however well it scores elsewhere.
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

**Sub-agent fan-out (when available).** These detection passes are independent and operate over the whole manuscript, so when the runtime offers parallel sub-agents, dispatch each pass (A–L) as its own sub-agent against a baseline the parent resolves once (fixed origin, roster, `book/tic-ledger.md`, the chapter set), then aggregate, dedup, and cap at 50. Otherwise run them sequentially. Either way the passes and severities are the same.

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
- **Ledger trend review across chapters**: load `book/tic-ledger.md` and read each entry's per-chapter trend across the drafted chapters in scope (honor `Waiver:` fields — report, don't flag). Flag any entry whose trend **rises across recent chapters**, or that recurs at a steady rate in most chapters, even if no single chapter's count was gating on its own — this catches voice drift toward AI-flavoured prose that any single chapter could plausibly defend. Surface **retire candidates** (entries clean for 3+ reviewed chapters still marked active) so the ledger stays current. Also check the manuscript-only shapes no single chapter can trip: three or more chapters in a row ending on the same zoom-out coda cadence, or the same distinctive phrase/beat-closer recurring across chapters. A recurring shape found here that has no ledger entry gets one (this is still Pass 2 territory — write it back). Severity: HIGH for a rising trend; MEDIUM for steady recurrence.

#### E1. Drift Trajectory (slope vs origin)

Per-chapter checks catch absolute violations but miss *gradual* drift where every chapter is individually defensible yet the book has slid a long way from where it started. Establish the **fixed origin** (constitution + concept voice/tone + the resolved origin chapters — the `## Voice Origin` pin if set, else the earliest approved) and trace the *direction* of change across the chapter sequence, not just per-chapter compliance:

- Read the chapters in order and track the trend of: average and variance of sentence length, paragraph shape, dialogue ratio, diction/register, and tic density.
- Flag a **monotonic slope away from the origin** even when no single chapter trips a gating threshold — e.g. sentence length creeping up act over act, dialogue steadily thinning, register drifting more (or less) literary, the same epiphany-coda cadence recurring across runs of chapters.
- **Origin jump test**: compare the latest chapters directly against the origin chapters (the `## Voice Origin` pin if set, else the earliest approved). If a reader started at the origin and jumped to the latest chapter, would it read as the same book, same narrator, same voice? Quote the divergence.
- **Calibration sanity check**: re-read the *resolved origin* chapter (the `## Voice Origin` pin if set, else the earliest approved) against the *current* constitution and style anchor. If that origin chapter would no longer pass today's bar, the **bar has drifted** — e.g. a stale or hand-edited style anchor, or a voice evolution that was never recorded in the constitution. (If a pin already excludes an atypical opening, grade against the pinned exemplar — do not re-flag the excluded chapter.) Flag it and recommend re-grounding the anchor via `/authorkit.write` (which regenerates it from the origin), or recording the shift in `## Voice Origin`.

Severity: HIGH if the trajectory crosses a constitution principle or a Pass 2 gating threshold by the latest chapters; MEDIUM for a clear unsanctioned slope short of that. Distinguish constitution-sanctioned evolution from unsanctioned drift; when ambiguous, surface it for the author to judge.

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

#### J. Quantitative Continuity Ledger

Build a ledger of every concrete quantitative/temporal fact across the drafted chapters in scope — counts, ages, dates, durations, distances, ordinals, headcounts — **keyed by referent** (e.g. "guards at the gate", "Crescens's age", "Carthage→Rome voyage"). For each referent, list the value each chapter asserts.

- Flag any referent whose value **changes without an in-story justification** (the "nine guards in CH04 → twelve in CH09" case). A change dramatized as in-story change is fine; a silent contradiction is not.
- Cross-check stated values against the matching `world/` `## Current State` where one exists.
- Severity: **CRITICAL** for a hard contradiction a reader would catch; **HIGH** for an unexplained drift; **MEDIUM** for a value that is merely imprecise across chapters.

#### K. Premature Disclosure (Disclosure Horizon, manuscript-wide)

Scan for any chapter disclosing a plot fact the outline/plan assigns to a **later** chapter — a reveal, a death, a twist, an identity — stated or proleptically narrated before its intended chapter. Distinguish from allowed planted foreshadowing (names no payoff). Cite the leaking chapter and the chapter that owns the reveal. Severity: **CRITICAL** if it spoils a major later reveal; **HIGH** otherwise.

#### L. Scaffolding Leakage (Standalone Readability, manuscript-wide)

Scan for prose that only parses with access to `world/`/outline/concept — names/terms/relationships used before any chapter grounds them, "as established" reliance on unstated facts, or encyclopedia voice transcribed from `world/`. A reader of the shipped chapters alone should never hit an unexplained dependency. Cite chapter and location. Severity: **HIGH** if comprehension breaks; **MEDIUM** otherwise.

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

### Quantitative Continuity Ledger

| Referent | Per-chapter values | Consistent? | Severity |
|----------|--------------------|-------------|----------|
| Guards at the gate | CH04: nine; CH09: twelve | NO — silent change | CRITICAL |
| Crescens's age | CH01: 52; CH06: 52 | yes | - |

### Premature Disclosure

| Leaking chapter | Fact disclosed | Owned by | Severity |
|-----------------|----------------|----------|----------|
| CH05 | the steward is the informant | CH11 reveal | CRITICAL |

### Scaffolding Leakage

| Chapter | Reference | Why it only parses with scaffolding | Severity |
|---------|-----------|-------------------------------------|----------|
| CH02 | "the Concordat" | named, never grounded in any drafted chapter | HIGH |

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
| Tic density (ledger trends) | [n] | [n] | [rising/flat/falling] | [OK/Watch/Flag] |
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
- If a recurring AI-flavoured shape shows up that has no `book/tic-ledger.md` entry: add the entry (Pass 2 write-back applies here too). If the author should *sanction* a shape instead (it's deliberate voice), recommend recording the waiver in the constitution via `/authorkit.discuss` (Constitution mode) — review will then mark the ledger entry waived. Do not park either in the style anchor's **Avoid** section — the anchor is regenerated from the constitution on every refresh, so hand-added entries there are overwritten.
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
- **PASS threshold**: no critical issues, no more than 2 important issues, the gating passes (1 Style Fidelity and 2 AI-Tic Audit) are B or above (no significant *unsanctioned* drift from the origin, no recurring non-waived tic shape and no rising active ledger entry), and **no unresolved logical/quantitative contradiction (Pass 3/4) and no premature-disclosure leak (Pass 5)**.
- **Reviews are gated**: a chapter review writes only `chapters/NN/review.md` and updates the chapter row in `chapters.md`. A manuscript drift run writes nothing unless the author approves drift fixes — and those fixes touch only upstream planning artifacts (concept / outline / chapters.md / world), never chapter drafts. Consolidation fixes (1e/1f) additionally write a pre-consolidate snapshot before applying.
- **Cap manuscript findings at 50** to keep reports actionable.
- **Use absolute paths.**
