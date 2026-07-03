---
description: Plan and draft manuscript prose — outline if needed, plan a chapter, draft it (full or section by section), revise, or polish a passage. Always reconciles state after writes.
handoffs:
  - label: Review What You Wrote
    agent: authorkit.review
    prompt: Review chapter [N]
  - label: Discuss A Creative Problem
    agent: authorkit.discuss
    prompt: Talk through a creative problem in chapter [N]
  - label: Research A Topic
    agent: authorkit.research
    prompt: Research a topic that came up while drafting
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --include-chapters
  ps: scripts/powershell/check-prerequisites.ps1 -Json -IncludeChapters
---

## User Input

```text
{{USER_INPUT_TOKEN}}
```

You **MUST** consider the user input before proceeding (if not empty). The input typically names a chapter (number, range, or "next") and may carry a sub-mode keyword: `plan`, `draft`, `revise`, `help`, `continue`, `scene N`, `from scene N`, `interactive`, `outline`.

## Goal

This is the manuscript-generation command. It produces prose and the planning artifacts that feed prose. It also reconciles state after writing — extracting new world details from drafts, refreshing the outline summary, and updating chapter statuses — so the author never has to remember to run a follow-up.

Under one command, this absorbs outlining, chapters-list generation, chapter planning, chapter drafting (full or partial modes), revision, passage-level help, and world extraction. The model dispatches based on what artifacts exist and what the input asks for.

## Mode Dispatch

State the mode you're entering in one short opening line. Multiple modes may chain within a single invocation — that is normal.

| Trigger | Mode | What happens |
|---|---|---|
| No `outline.md` exists, user input mentions a chapter | **Outline first** | Generate or extend `outline.md` (then proceed to chapters / plan) |
| `outline.md` exists, no `chapters.md`, user input mentions a chapter | **Chapters first** | Generate `chapters.md` from outline (then proceed to plan) |
| User input includes "outline" or "outline N-M" | **Outline (explicit)** | Full / partial / extend outline workflow |
| User input adds "plan" (e.g. `7 plan`) | **Plan (only)** | Plan the chapter and stop — do **not** draft. Produces `chapters/NN/plan.md`, sets status `[P]` |
| User input is a chapter number with no plan yet | **Plan + draft** | Plan the chapter, then draft it (full mode) |
| User input is a chapter number with an existing plan, no draft | **Draft** | Draft the chapter; reconcile after |
| User input adds "interactive" / "scene N" / "continue" / "from scene N" | **Draft (partial mode)** | Per-scene drafting with progress marker |
| User input adds "revise" or chapter status is `[R]` | **Revise** | Apply targeted edits to existing draft |
| User input adds "help" / "improve" / "alternatives" / "stuck" / "trim" / "dialogue" / "describe" / "voice" | **Passage help** | Scalpel-level refinement of a passage; minimal footprint |
| Post-draft, automatically | **Reconcile** | Extract world deltas, refresh outline summary, update chapters.md, scan for new ambiguities |

If the input is genuinely ambiguous (e.g., just a number with no context), default to **Plan + draft** for a chapter without a plan, **Draft** for one with a plan and no draft, **Revise** for one with a draft in `[R]` status.

## Always-on Behavior

1. **Setup**: Run `{{SCRIPT_CHECK_PREREQ}}` from repo root. Parse `BOOK_DIR`, `STYLE_ANCHOR`, and `AVAILABLE_DOCS`. All paths must be absolute.

2. **Parse chapter number** if the input names one. Accept `1`, `01`, `CH01`, `chapter 1`, `Chapter 1`. Normalize to two-digit (`01`, `02`, etc.). For ranges (`5-10`), keep both endpoints. For "next", look at `chapters.md` and pick the lowest chapter whose status is `[ ]` or `[P]`.

3. **Always-loaded context**:
   - `.authorkit/memory/constitution.md` (writing principles — the style bible)
   - `concept.md` (voice, tone, themes)
   - `chapters.md` if it exists (chapter status and dependencies)
   - `STYLE_ANCHOR` at `BOOK_DIR/style-anchor.md` (refreshed below before any drafting/revising/help)

4. **Targeted context** (load per the mode chosen):
   - `outline.md` (overall structure, chapter entry)
   - `characters.md` (profiles, voices)
   - `world/` files — if `world/_index.md` exists, use the Chapter Manifest to find entities from the previous chapter (carry-over context) and resolve entity names in the chapter plan or draft via the Alias Lookup. Load only matched files. Within each, treat the `## Current State` block as the canonical now-truth to write from; `## History` is provenance, not the current picture.
   - **Voice texture exemplar** — for character/scene/arc voice the style anchor leaves open (a POV character's interiority, an arc's tonal colour, a recurring character's dialogue voice), load the **earliest *relevant* approved (`[X]`) chapter**: the lowest-numbered approved draft featuring this chapter's POV/focus characters or the same arc register (use the `world/_index.md` Chapter Manifest + Alias Lookup). Match its texture, but it may only *add* what the fixed origin (step 5) leaves open — where it conflicts with the constitution or the origin, the origin wins. Pick the *earliest* relevant draft, never the most recent, so you match a representative instance, not a trailing (possibly drifted) one. Fall back to the fixed origin when no more-relevant chapter exists.
   - **Voice pairs** — load `book/voice-pairs.md` (the **Active Pairs** section only) whenever this run will draft, revise, or refine prose. Frame the pairs positively per the shared guardrails' Voice Conditioning Protocol: *in this book, prose like the left column gets revised to the right column — write right-column prose directly.* If the file doesn't exist yet, skip silently. **Quarantine (binding)**: never load `book/tic-ledger.md` or the seed tic catalog while drafting — tic knowledge enters generation only as these pairs.
   - **Continuity & arc references** — for plot/thread/state (where an arc currently stands), choose by *relevance* to this chapter, not just `N-1`: the previous chapter draft/plan, plus the **most recent** chapter(s) featuring this chapter's POV/focus characters and the chapter that last advanced an arc converging here. This is *current-state* context for what happens; voice still grades and matches against the fixed origin (global) + the earliest-relevant exemplar (texture), never against these recent chapters.
   - `research.md` and relevant `research/` topic files (recursive scan, prefer scope `general`, `outline`, `chapter CHNN`)
   - `parked-decisions.md` — scan for OPEN decisions whose deadline is at or before this chapter. If any found, **list them inline** at the top of the run and recommend resolving via `/authorkit.discuss` (Park mode). **Do not block** — the author can proceed.
   - `[NEEDS CLARIFICATION]` markers and unresolved `## Clarifications` questions in `concept.md` — same treatment: list inline, recommend `/authorkit.discuss`, don't block.

5. **Style anchor refresh** before any drafting / revising / passage help: regenerate the style anchor from the **fixed origin** — the constitution, the concept's voice & tone section, and the origin chapter(s). Resolve the origin: if the constitution's `## Voice Origin` names exemplar chapter(s) (`From CHnn:`) for this stage, use them; otherwise default to the *earliest* approved (`[X]`) chapters (lowest numbers), **not** the most recent ones. **Always also fold in any `### Voice Exemplars` excerpts under `## Voice Origin`** — author prose samples that are part of the fixed origin, and the concrete voice bar before any chapter is approved. Anchoring to the origin keeps the style anchor a stable standard the book is held to, rather than a trailing average that follows drift downward. Fallbacks: if one approved chapter exists, use constitution + concept voice/tone + any `### Voice Exemplars` excerpts + that chapter; if none, constitution + concept voice/tone + any `### Voice Exemplars` excerpts. Continuity with the *recent* chapters is handled separately by loading relevant prior chapters (targeted context); character/scene/arc *texture* is matched from the **earliest-relevant** voice exemplar (step 4), which may add to but never lower this bar. The anchor is the fixed *global* voice bar, not a recency snapshot. (Re-pinning the origin is a constitution-sanctioned voice evolution recorded in `## Voice Origin`; you may *propose* a better/stage-appropriate pin, but never switch the bar silently.) Load `.authorkit/templates/style-anchor-template.md` for the canonical section order and headings; write the resolved style anchor to `BOOK_DIR/style-anchor.md` following the template structure exactly.

6. **Report writes.** Every turn ends with a list of files written and a one-line summary each.

## Mode: Outline (implicit or explicit)

Triggered when `outline.md` doesn't exist or the input explicitly asks for outlining. Sub-shapes:

- **Full** (default if no scope keyword): generate all chapters.
- **Partial** ("part 1", "act I", "chapters 1-8", "first 5 chapters"): full structural overview for the whole book, but detailed chapter entries only for the requested range.
- **Extend** ("extend", "continue", "next part", "next section"): extend an existing partial outline. Requires `outline.md` with a Continuation Notes section. If missing: error *"No outline to extend. Run /authorkit.write outline first."* If `outline.md` exists but has no Continuation Notes, treat as already complete; warn and ask if the author wants more chapters beyond it.

### Workflow

1. Run `{{SCRIPT_SETUP_OUTLINE}}` from repo root. Parse JSON for `BOOK_CONCEPT`, `OUTLINE`, `BOOK_DIR`, `CHAPTERS_DIR`.
2. Load `BOOK_CONCEPT` and constitution. Load the OUTLINE template (already copied by the script). Load `research.md` and `research/` topic files if present (scope `general`, `outline`, and chapter-targeted files).
3. **Concept clarity gate (soft)**: scan `concept.md` for `[NEEDS CLARIFICATION]` markers or an unresolved `## Clarifications` section. If any are found, list them inline and recommend `/authorkit.discuss` to resolve, but proceed by default. The author may explicitly stop and run clarify if they prefer.
4. Execute the outline workflow using the template:
   - **Phase 0 — Research & World-Building check**:
     - If `world/` exists (built earlier via `/authorkit.discuss`): read all entries as primary context. Refresh `research.md` as a supplementary summary index for findings that don't fit `world/`. Generate `characters.md` as a summary index pointing to `world/characters/`, plus any characters not yet in `world/`. Validate `world/` against `concept.md` — flag inconsistencies. If `world/` feels incomplete, suggest `/authorkit.discuss` (World Seed) to deepen.
     - If `world/` doesn't exist: identify research needs from the concept (settings, historical/technical claims, character backgrounds). Generate or refresh `research.md` entries with Decision / Rationale / Sources. Generate `characters.md` profiles (fiction: full profiles with arc; non-fiction: concept definitions and prerequisite knowledge). For complex world-building genres, suggest `/authorkit.discuss` (World Seed) before structural design.
   - **Phase 1 — Structural Design**:
     - Determine structure (linear vs non-linear, parts/acts, POV rotation). Map narrative arc / argument flow across chapters. **Always for the full book**, even in partial mode.
     - Create chapter entries scope-dependent. Full: detailed for all. Partial: detailed for requested range, one-line directional notes in the Structural Overview for the rest. Extend: read `outline.md` Continuation Notes + any chapters drafted since the last outline session (check `chapters.md` for `[D]`/`[X]`). Generate detailed entries for the next logical section (next part/act, or 3-8 chapters). **Append** to existing Chapter Breakdown — do NOT replace.
     - Each chapter entry: title, purpose, summary, key events/points, characters/concepts, closing beat, connections. Verify pacing (mix of high-tension and breathing-room chapters).
     - Map character arcs and thematic threads across outlined chapters. For partial/extend, note expected directions for un-outlined portions.
   - **Continuation Notes** (partial and extend only): populate the section with **Last Outlined Through**, **Open Plot Threads**, **Character Arc Positions**, **Thematic Threads In Progress**, **Notes for Next Outlining Session**. On extend, **replace** Continuation Notes entirely (do not merge with previous notes; chapter entries are the historical record). For full mode: remove the section or leave it empty with a "complete" note.
   - **Phase 2 — Validation**: Constitution check, Completeness check, Arc check (scope-aware), Pacing check, **Disclosure-horizon check** (per the Disclosure Horizon Protocol): no chapter entry's summary, key events, or closing beat may prescribe disclosing a plot fact the outline assigns to a *later* chapter — a reveal, death, twist, or identity stated ahead of the chapter that owns it. Keep cross-chapter links as setups/payoffs, not spoilers. A deliberate non-linear structure (frame narrative, flash-forward prologue) is allowed only when it is an explicit, recorded structural choice for this book; otherwise flag it and resolve via `/authorkit.discuss`.
5. Stop and report: OUTLINE path, artifacts generated (research.md, characters.md), whether research/ was consumed, scope, partial-outline reminder if applicable.

After Outline mode produces an outline, **continue automatically into Chapters mode** if `chapters.md` doesn't exist and the user originally asked for a chapter. Otherwise stop and let the author decide.

## Mode: Chapters (generate chapters.md)

Triggered when `outline.md` exists, `chapters.md` doesn't, and a chapter operation is needed.

1. Read `outline.md` (structure, full chapter entries) and `concept.md` (voice, themes, scope). If `outline.md` has a Continuation Notes section with "Last Outlined Through": treat the outline as partial — only chapters with full detailed entries (purpose, summary, key events, connections) get entries here.
2. Map character appearances to chapters (if `characters.md` exists). Map research scope/chapter-targets to relevant chapters (recursive scan).
3. Generate `chapters.md` from `.authorkit/templates/chapters-template.md`:
   - Book title from `concept.md`
   - Chapters grouped by parts/acts — only those with detailed outline entries
   - Each entry format: `- [ ] CHNN [Part?] Title - One-line summary`
   - Part checkpoints with verification criteria
   - Drafting strategy recommendation (sequential, key-scene-first, or part-by-part)
   - Dependencies & connections section
   - Status markers: `[ ]`, `[P]`, `[D]`, `[R]`, `[X]`
   - If `chapters.md` already exists: merge new entries after existing ones, **preserving existing statuses**. Never overwrite or reset.
   - Partial outline: include the "Incremental Outlining" section from the template.
4. Report: path, total chapter count, chapters per part/act, key dependencies, recommended drafting order, estimated total word count. If partial outline: how many outlined vs estimated total, and remind the author to run the Outline (extend) sub-mode after drafting.

Then continue into **Plan** or **Plan + draft** for the requested chapter.

## Mode: Plan (single chapter)

For a chapter number N with no plan yet (or to overwrite an existing plan with author consent).

1. **Verify**: read `chapters.md` for the chapter entry. If status is `[P]`, `[D]`, `[R]`, or `[X]`, warn that a plan already exists and ask whether to overwrite or skip. If previous chapters aren't drafted and this chapter depends on them, warn but allow proceeding.

2. **Reconcile outline against drafted chapters** (critical for mid-book consistency):
   - Read this chapter's outline entry. Identify every factual claim it makes about events from **already-drafted** chapters (e.g., "arrived with instructions from X to…", "after the argument in CH03…").
   - For each claim, grep the actual `chapters/NN/draft.md` text of the referenced chapter to verify.
   - **Drafted chapters are canonical.** If the outline says X happened but the draft says Y, the draft is correct and the outline is stale.
   - On mismatch: use the draft's version in the plan; note the discrepancy under a "Reconciliation Notes" section in the plan. After the plan is written, correct the stale outline entry to match the draft.

3. **Refresh the style anchor** (Always-on step 5).

4. **Create chapter directory**: ensure `BOOK_DIR/chapters/NN/` exists.

5. **Generate the chapter plan** using `.authorkit/templates/chapter-plan-template.md`:
   - **Chapter Purpose**: extract from outline entry
   - **Context**: what the previous chapter ended with, what this chapter must accomplish, what the next chapter needs
   - **Scene/Section Breakdown**:
     - Fiction: scenes with setting, POV, key beats, emotional tone
     - Non-fiction: logical sections with key points, evidence, examples
     - Each with a clear purpose; ordered for maximum impact
   - **Emotional Arc / Argument Flow**: opening to closing progression
   - **Key Revelations / Points**: what the reader learns
   - **Characters/Concepts**: who appears, how they develop
   - **Connections**: setups planted, payoffs delivered
   - **Opening Hook**: compelling first line or paragraph concept
   - **Closing Beat**: how the chapter ends to propel the reader forward
   - **Voice & Style Notes**: chapter-specific style considerations
   - **Estimated Length**: target word count based on overall scope

6. **Disclosure-horizon check (before writing the plan)** — per the Disclosure Horizon Protocol, applied to the plan itself: no Key Revelation, closing beat, or scene beat may state or proleptically narrate a plot fact the outline assigns to a *later* chapter. A plan that prescribes a premature reveal is executed faithfully by Draft mode, so the leak must be caught here, not left for review. Keep setups as **planted foreshadowing** (an image/object/unease that pays off later without naming the payoff), not disclosure. A genuine flash-forward/frame device is allowed **only** if the concept, constitution, or outline structure records it as intended — otherwise escalate the structural question via `/authorkit.discuss` instead of planning the reveal in.

7. **Write the plan** to `BOOK_DIR/chapters/NN/plan.md`.

8. **Update chapter status** in `chapters.md`: change `- [ ] CHNN` to `- [P] CHNN`.

9. **Fix stale outline entries** if step 2 found mismatches: update `outline.md` to match drafted reality.

10. **Report**: path to plan, summary of scenes/sections planned, key connections, suggested next step (continue to Draft mode for this chapter, or stop if the author wanted plan-only).

## Mode: Plan + draft

The default for a chapter number with no plan and no draft. Sequence:

1. Run **Plan** for the chapter.
2. Run **Draft** for the chapter (Full mode below).
3. Run **Reconcile** after drafting.

## Mode: Draft (Full / Partial)

For a chapter with an existing plan (or a plan just generated by step 1 of Plan + draft).

### Mode detection

- **Full** (default, no mode keyword): write the entire chapter in one pass.
- **Interactive** ("interactive", "section by section"): write one scene/section at a time, pausing between each.
- **Scene** ("scene N", "section N"): write only the specified scene from the plan.
- **Continue** ("continue", "next"): find where the current partial draft ends and write the next scene/section.
- **From-scene** ("from scene N"): write from scene N through the end of the chapter.

### Pre-flight

1. **Verify chapter plan exists** at `chapters/NN/plan.md`. If not, run Plan mode first. Verify `chapters.md` status is at least `[P]`.
2. **Refresh style anchor** (Always-on step 5).
3. **Load constitution + style anchor** and internalize voice/style rules. **All draft modes (Full, Interactive, Scene, Continue, From-scene) use the Voice Conditioning Protocol and the two-pass scene protocol defined under Full mode** — conditioning context, Pass A content, Pass B voice, only Pass B saved.
4. **Draft state detection**:
   - Check if `chapters/NN/draft.md` exists. If so, check for a partial-draft marker: `<!-- PARTIAL DRAFT: Scenes X-Y of Z complete -->`
   - **Full mode + complete draft**: ask user whether to overwrite or skip.
   - **Full mode + partial draft**: ask user whether to overwrite, continue from where it left off, or skip.
   - **Interactive / Scene / Continue / From-scene + draft exists**: read existing draft content (treat all as canonical — it may contain author-written or AI-written content).
   - **No draft**: proceed normally.
5. **Mixed authorship awareness**: the existing draft may contain content the author wrote directly. Treat all existing content as canonical. Match the voice of what's on the page (via style-anchor + the prose itself).

### Full mode

**Condition the context first** (per the shared guardrails' Voice Conditioning Protocol): assemble the drafting context so the model *continues* the book rather than follows instructions about it — immediately before writing prose, place in order (1) the resolved origin excerpt(s) **verbatim** (~2–4 pages of the fixed origin from Always-on step 5's resolution), (2) the tail of the existing draft (or the previous chapter's closing scene when starting fresh), (3) a *minimal* beat sheet distilled from the plan for the scene at hand — then continue the prose from there.

**Before drafting**, if this chapter introduces new names or new arbitrary numbers not already fixed by the plan/concept/outline/world, roll them with the entropy tool per the Entropy Protocol — `authorkit entropy name [--culture …]` for each new name (build a setting-fit name from the returned seed) and `authorkit entropy number --min A --max B [--kind …]` for each new arbitrary number (within context-justified bounds). Rolled values land in Pass A and become canon. (Headless-safe — runs the same under AutoPilot.)

**Draft each scene in two passes** (only Pass B is ever saved to `draft.md`):

- **Pass A — content**: deliberately flat camera prose — events, dialogue, concrete physical fact; no figurative language, no interiority glosses, no rhythm performance. All entropy rolls happen here. Pass A is working material only — never written to `book/`.
- **Pass B — voice**: rewrite Pass A into the anchored voice with the origin excerpts and Active voice pairs in context. **Hard rule: Pass B adds no new facts, names, or numbers** — it is a translation of Pass A; the self-check diffs B against A to confirm.

Follow the scene/section breakdown from the plan. For each scene (Pass A establishes the material; Pass B must preserve it while carrying the voice):

a. **Set the stage**: establish setting/context with sensory detail (fiction) or clear framing (non-fiction).
b. **Execute the beats**: write through each key beat in order. Each beat advances the story/argument; transitions feel natural; the emotional/intellectual progression follows the planned arc.
c. **Character voice** (fiction): each character speaks distinctly per their `characters.md` profile.
d. **Pacing**: vary sentence length and paragraph size. Short for tension, longer for reflection. White space intentionally.
e. **Show don't tell** (unless constitution says otherwise): demonstrate emotions through action and dialogue, not statement.
f. **Scene transitions**: clear but not heavy-handed.
g. **Opening**: start strong with the planned opening hook. The first paragraph compels continued reading.
h. **Closing**: end with the planned closing beat. Leave the reader wanting to turn the page.

### Interactive mode

1. Identify the first unwritten scene from the plan.
2. Write that scene to the same quality standard as Full mode.
3. Add or update the progress marker at the top of `draft.md`: `<!-- PARTIAL DRAFT: Scenes 1-N of TOTAL complete -->`
4. Report (scene summary, word count) and ask: *"Continue to scene [N+1]? Review or adjust? Write the next scene yourself?"*
5. Wait for author input before the next scene.
6. If the author wrote content between sessions (e.g., they wrote scene 3 themselves), detect it on continuing and skip to the next unwritten scene.

### Scene mode

1. Identify the target scene from the plan.
2. If a partial draft exists, read it for voice continuity.
3. Write the target scene.
4. If inserting into an existing draft: place it in its correct position relative to existing content.
5. Update the progress marker.
6. Report and suggest next steps.

### Continue mode

1. Read the existing draft (mixed authorship).
2. Determine which scenes/sections are already covered by comparing draft content against the plan.
3. Identify the next unwritten scene.
4. Match the voice and style of existing content.
5. Write the next scene, appending.
6. Update the progress marker.
7. Report and ask whether to continue.

### From-scene mode

1. Identify the starting scene.
2. Read earlier scenes for continuity if they exist.
3. Write from the starting scene through the final scene, including the closing beat.
4. Update or remove the progress marker (remove when all scenes are complete).

### Progress tracking (non-Full modes)

- Maintain a progress marker at the top of `draft.md`.
- Do NOT update `chapters.md` to `[D]` until ALL scenes are written.
- When the final scene is written, remove the marker and set status to `[D]`.
- If the author wrote a scene that deviates from the plan, **follow the author's lead** — the draft is canonical over the plan.

### Quality self-check (before saving any new content)

Run the **Analysis Passes** roster (shared guardrails) on the new prose, plus the craft items:

- **Pass 1 — Style**: constitution voice/style compliance; `book/style-anchor.md` match on POV, tense, narrative distance, cadence, diction, imagery density, dialogue profile.
- **Pass 2 — AI-Tic**: origin-contrast self-check (per the shared guardrails' Pre-output Audit — do NOT load the tic ledger or the seed catalog): no construction, sentence shape, or beat-closer recurs in the new prose that the origin never uses; nothing reads like left-column prose from the Active voice pairs; Pass B introduced no facts, names, or numbers absent from Pass A. Explicit constitution waivers noted.
- **Pass 3/4 — Logical & quantitative consistency**: new quantities are internally consistent and arithmetically sound, and contradict no prior chapter or `world/` `## Current State` (per the Quantitative & Logical Continuity Protocol).
- **Pass 5 — Disclosure horizon**: no premature disclosure / proleptic narration of a later chapter's content (per the Disclosure Horizon Protocol).
- **Pass 6 — Standalone readability**: the chapter parses for a reader with only the shipped chapters — no scaffolding-only references, no transcribed `world/` exposition.
- Each scene/section achieves its planned purpose.
- For Full mode or final scene: opening hook + closing beat both effective.
- Pacing varied and appropriate.
- Character voices distinct (fiction); argument clear and supported (non-fiction).
- Word count in target range (Full mode: 10-15% variance OK).

### Style match pass

- Compare new content against constitution + `book/style-anchor.md`.
- Also check that new content is consistent in voice with any existing author-written content in the draft.
- Run the tic self-check by **contrast, not by list** (the ledger and seed catalog stay quarantined from drafting): re-read the new prose against the origin excerpts and Active voice pairs already in context. Any recurring construction the origin never uses, or anything reading like left-column pair prose, gets rewritten in place before saving — the fix is whatever the origin does for the same job. Check `.authorkit/memory/constitution.md` + style anchor for explicit waivers before rewriting; if a waiver is in effect, name it in the run report.
- Correct drift before saving.
- **Entropy derivation**: any new name should have been built from an `authorkit entropy name` seed, and any new arbitrary number drawn from `authorkit entropy number` within context-justified bounds (per the Entropy Protocol) — not free-associated. Record new numeric facts so later chapters and review can hold the line (they are now canon).
- If new numeric facts were introduced, verify each has rationale. If multiple values were plausible, the selected value should be context-bounded and not a repetitive default.

### Write the draft

- File: `BOOK_DIR/chapters/NN/draft.md`
- Header: `# Chapter [NN]: [Title]`
- Use `---` between scenes (fiction) or `##` between sections (non-fiction)
- No meta-commentary in the draft — pure prose only. The only exception is the `<!-- PARTIAL DRAFT: … -->` marker for non-Full modes.
- For non-Full modes: preserve existing content and append/insert new content in the correct position.

### Chapter status (mode-dependent)

- **Full mode** or **all scenes now complete**: change status `[P] → [D]`
- **Partial (not all scenes yet)**: leave at `[P]` until the chapter is complete

After **Full mode** or **all scenes complete**, proceed automatically into **Reconcile** mode below.

## Mode: Revise

Triggered when `chapters/NN/draft.md` exists and the user input includes "revise", "fix", a chapter status is `[R]`, or the input describes specific issues to address.

1. **Determine revision scope** from input: specific chapter, specific issue (e.g., "fix the timeline contradiction between 3 and 7"), or analysis-driven ("address the critical issues from the last review"). If unclear, ask the author to specify.
2. **Load context**: the draft, the plan, the chapter's review (`chapters/NN/review.md` if it exists), concept, constitution, characters, style anchor (refresh first per Always-on step 5), `world/` files for entities in this chapter (check chapter-tagged details that may need updating), adjacent chapter drafts (continuity), any analysis findings relevant to this chapter.

3. **Revise pass-by-pass (the Analysis Passes roster).** Revision is explicitly multi-pass: **walk the roster in order** — 1 Style → 2 AI-Tic → 3 In-Chapter Logic → 4 Cross-Chapter/Arc Logic → 5 Disclosure → 6 Standalone → 7 Craft — and for **each pass**:
   - **Ingest that pass's findings** from the matching `review.md` section heading (the headings are keyed to the roster), **plus** any issue named in the invocation (`revise: <issue>`) mapped to the pass it belongs to. Critical/Important first.
   - **Apply the fixes** as targeted edits to `chapters/NN/draft.md` — smallest change that resolves the finding; don't rewrite working sections; preserve voice; follow constitution + match `book/style-anchor.md`. For new/changed numbers or names, derive via the Entropy Protocol and keep quantities consistent with prior chapters/`world/` (Quantitative & Logical Continuity).
   - **Harvest voice pairs (Pass 2 fixes only)**: for each AI-Tic finding fixed, append the before→after pair to `book/voice-pairs.md` **Active Pairs** (create the file from `.authorkit/templates/voice-pairs-template.md` if missing): `- TIC-NNN (CHnn): "<original sentence>" → "<revised sentence>"`. Keep Active at ~20 pairs, newest first, preferring one instructive pair per tic shape; rotate the oldest to **Archive**. These pairs are how the next draft learns — harvesting is not optional.
   - **Re-run that pass's own check** on the edited prose before advancing, so a Style fix that introduces a tic (Pass 2), or a logic fix (Pass 4) that breaks voice (Pass 1), is caught in-loop. A pass with no findings is verified-and-skipped, never silently ignored.
   - If no `review.md` exists (a direct `revise: <issue>`), still walk the roster but act only on the passes the issue touches, running those passes' checks yourself.
   - **Final gate sweep (mandatory, after the last pass)**: re-check every span edited during passes 3–7 against Pass 1 (voice vs the fixed origin) and Pass 2 (tic budgets vs the ledger). The per-pass re-check only covers each pass's own remit, so a logic or craft fix made after the gating passes ran can still drift voice or introduce a ledger shape — this sweep is what catches it before the draft is saved.

4. **Update the plan** at `chapters/NN/plan.md` if the revision changes the chapter's structure.
5. **Update status** in `chapters.md`:
   - `[R]` → `[D]` (re-drafted, ready for re-review)
   - `[X]` + revision requested → `[D]`
6. **Check for ripple effects**: if a revision changes a fact, character detail, or plot point, identify all other chapters that reference it. List them as ripple flags for the author. Do NOT auto-edit other chapters. Recommend the **Reconcile** sub-step below to capture world/ deltas and surface downstream impact systematically.
7. **Report** which passes ran, their before/after status, and the fixes applied per pass.
8. Proceed automatically into **Reconcile** mode.

## Mode: Passage Help

Targeted, scalpel-level refinement of a specific passage. Detected when input includes keywords like "help", "improve", "alternatives", "stuck", "trim", "tighten", "dialogue", "describe", "sensory", "show", "voice", "style", "check", or names a specific passage ("the opening", "the dialogue between X and Y").

**Scope boundary**: this is passage-level. For writing whole scenes, fall back to Draft mode (Scene / Continue / From-scene).

1. **Parse user input**:
   - Chapter number (required). If absent: error *"Please specify a chapter (e.g., /authorkit.write chapter 3 improve the opening)"*.
   - Target passage: a scene reference ("scene 2", "the tavern scene", "opening", "closing"), a text reference ("the paragraph about the door"), pasted content, or a general area ("the transition between scene 1 and 2").
   - Help mode (auto-detected): `alternatives` (2-3 options), `improve` (specific suggestions), `stuck`/`continue` (2-3 paragraphs to unblock — for a full scene, redirect to Draft Continue), `dialogue`, `describe`/`show`/`sensory`, `trim`/`tighten`/`cut`, `check`/`voice`/`style`. **Default**: read the passage and propose the help mode that fits before doing anything.

2. **Load context**: constitution, style anchor (refreshed per Always-on step 5), `chapters/NN/draft.md`, `chapters/NN/plan.md`, concept, characters, `world/` files relevant to the passage, previous chapter draft for continuity, research as appropriate. If no draft exists yet for this chapter, that's fine — the author may be drafting outside the tool or planning what to write. Adapt.

3. **Locate the target passage**:
   - Scene number → map to plan's scene breakdown → find in draft
   - Specific text → search the draft for it
   - Pasted content → use it directly (may or may not be in draft)
   - "opening" → first 1-3 paragraphs; "closing" → last 1-3 paragraphs
   - Can't find it → ask for clarification

4. **Deliver help by mode**. All suggestion text generated below is manuscript prose, held to Pass-B grade: condition on the origin excerpts and Active voice pairs (Voice Conditioning Protocol), and run the origin-contrast self-check on every suggestion before presenting it — continuations (`stuck`/`continue`) are where AI-flavoured constructions creep in most:
   - **alternatives**: present original (quoted), then 2-3 options with one-line rationales. Each option takes a meaningfully different approach, not word swaps.
   - **improve**: analyze for clarity, impact, voice consistency, show vs tell, pacing, rhythm, character distinctiveness. Specific actionable suggestions with exact text and replacement.
   - **stuck / continue**: read draft up to where the author indicates they're stuck. Summarize what the plan expects next (if a plan exists). Write 2-3 paragraphs of continuation. Match voice and style. Offer: *"Does this direction feel right? For a full next scene, run /authorkit.write [N] continue."*
   - **dialogue**: ensure distinct character voices, dialogue serves purpose, suggest more natural phrasing where stiff, check tags and action beats.
   - **describe / show**: identify telling passages and suggest showing alternatives. Add sensory detail where appropriate. Ground emotions in physical sensation. Check imagery density against constitution.
   - **trim / tighten**: identify redundancy, over-explanation, unnecessary adverbs. Show word count savings. Flag load-bearing content before cutting.
   - **check / voice / style**: compare against constitution + style anchor — POV, tense, narrative distance, cadence, diction, register. Flag drift with specific examples.

5. **Always end with an interactive prompt**:
   - *"Would you like me to apply [option/suggestion], try a different approach, or help with another passage?"*
   - On "apply": edit `chapters/NN/draft.md` at the target location.
   - On "try another approach": adjust and re-present.
   - On help elsewhere: repeat from step 3 with the new target.

6. **When applying changes**:
   - Edit `draft.md` at the specific location — do not rewrite surrounding content.
   - Do NOT change `chapters.md` status.
   - Do NOT update the partial-draft progress marker.
   - Confirm: *"Applied to chapters/NN/draft.md. [Brief description of what changed.]"*

Passage help does NOT run Reconcile — it's a scalpel edit, not a fresh draft.

## Mode: Reconcile (auto-runs after Draft / Revise)

After a Full-mode draft or a complete chapter (or a revision), reconcile state automatically. The author can decline this when prompted, but the default is to run it.

### Phase 1: Extract world details from the chapter

1. Read the chapter draft thoroughly (or, for revision, re-read it).
2. Determine mode for each chapter being reconciled:
   - If `world/_index.md` exists, check Entity Registry for `(CHxx)` tags for this chapter.
   - **No existing tags**: Fresh extraction mode.
   - **Existing tags**: Revision reconciliation mode.
   - Report the mode before proceeding.
3. **Fresh extraction** (per chapter):
   a. Identify new or updated details: Characters, Organizations, Places, History/Events, Systems.
   b. For each detail:
      - Resolve entity via `world/_index.md` Alias Lookup (or recursive scan if no index)
      - **Existing entity**: append the detail tagged `(CHxx)` to the file's `## History` section, then surgically refresh the affected `## Current State` line so the now-truth stays accurate (supersede in place — don't leave Current State contradicting the new detail).
      - **New entity**: create file in the appropriate category folder with YAML frontmatter (per `.authorkit/templates/world-entity-frontmatter.md`). Seed both a `## Current State` block (the now-truth) and a `## History` section holding the `(CHxx)` entry. Default to category root; only nest when a clear grouping reason exists.
   c. Cross-reference: if a detail connects entities, update both files.
4. **Revision reconciliation** (per chapter, when existing tags found):
   a. Catalog existing `(CHxx)` entries.
   b. Re-read the revised draft.
   c. Unchanged details: keep as-is. Changed details: append a `(CHxx-rev)` entry to `## History` AND supersede the affected `## Current State` line in place. Removed details: check if other chapters reference them — keep with note in History if yes (drop from Current State), deprecate if no.
   d. Scan for new details not previously captured; add tagged `(CHxx-rev)`.
   e. Generate a Downstream Impact section in the report listing which other chapters may be affected.

### Phase 2: Refresh outline summary

For this chapter's entry in `outline.md`: update Summary, Key Events, Characters Present, Ends With, and Connections so they match what was drafted. Drafted chapters are canonical — the outline reflects the draft, not the other way around. **Surgical edits only.**

### Phase 3: Update chapters.md status

- Full-mode chapter complete or final scene of partial draft: `[P] → [D]` (already done in Draft mode for Full; do it here for the final scene of partial).
- For revisions completing: `[R] → [D]` (already done in Revise mode).
- Ensure the row's one-line summary matches the draft if it had drifted.

### Phase 4: Ambiguity scan

Scan the new prose for things that surfaced as new uncertainty (e.g., a character behavior whose motivation isn't in `characters.md` / `world/characters/`, a setting detail that contradicts an existing entry, a rule that wasn't in `world/systems/`). For each:
- If it's a direct contradiction with an existing `(CONCEPT)` or `(CHxx)` entry, flag for `/authorkit.discuss` (Cross-cutting change) to propagate.
- If it's a new ambiguity worth surfacing, suggest `/authorkit.discuss <topic>` to clarify.

### Phase 4b: Voice-pair harvest from author edits (best-effort)

If the draft shows author hand-edits since the last AI write (mixed authorship — e.g. `git log` / `git diff` on `chapters/NN/draft.md` shows changes this tool didn't produce, or content diverging from what the previous run reported writing), harvest the clearly **stylistic** small rewrites — a sentence reworded, a beat-closer replaced, a simile cut — as voice pairs tagged `(author)` in `book/voice-pairs.md` Active Pairs (create from `.authorkit/templates/voice-pairs-template.md` if missing). Author pairs are the highest-value conditioning examples; prefer keeping them when rotating Active down to ~20. Skip content-level edits (plot/fact changes — Phase 1 captures those). Interactive runs: list the candidate pairs and confirm before saving. Unattended runs (`[AUTOPILOT-UNATTENDED]`): save clearly-stylistic pairs and report them; when in doubt whether an edit is stylistic, skip it.

### Phase 5: Rebuild the world index

Run `{{SCRIPT_BUILD_WORLD_INDEX}}` from repo root. This regenerates the Entity Registry, Alias Lookup, and Chapter Manifest.

### Reconcile report

```markdown
## Reconcile Report

**Chapter(s) reconciled**: [list]
**Mode(s)**: [Fresh / Revision] per chapter

### World Extraction
- Files created: [N] (paths)
- Files updated: [N] (paths)
- New entities discovered: [N]
- Details added to existing entities: [N]

### Revision Impact (if applicable)
| World File | Detail | Old Value | New Value | Downstream Chapters |

### Outline Summary Refresh
- Entries updated: [N]
- [Optional list of small edits]

### Chapters.md
- Statuses updated: [list]

### Ambiguity Scan
- Direct contradictions surfaced: [N] (each with proposed `/authorkit.discuss` follow-up)
- New ambiguities worth clarifying: [N]

### Voice Pairs
- Pairs harvested this run: [N] ([TIC-refs and/or (author)]; 0 if none)

### Index Stats
- Entities indexed: [N]
- Aliases registered: [N]
- Chapters covered: [N]
- Files without frontmatter: [N]
```

### Reconcile rules

- **Reference format, not narrative.** World entries are factual and concise.
- **Every detail MUST be chapter-tagged.** `(CHxx)` fresh, `(CHxx-rev)` revisions, `(CONCEPT)` pre-writing.
- **Don't speculate.** Only record what is explicitly in the chapter text.
- **Update incrementally.** Add to existing files; don't rewrite them.
- **Maintain Current State.** `## History` is append-only and chapter-tagged; `## Current State` is the untagged now-truth, surgically superseded in place. Drafting and review read Current State as canonical — keep it accurate after every extraction. See `.authorkit/templates/world-entity-frontmatter.md`.
- **Preserve file layout.** Keep human-organized subfolders.
- **Cross-reference generously.** Connected entities update each other.
- **Respect (CONCEPT) entries.** If a chapter contradicts a `(CONCEPT)` entry, flag and update with the chapter tag. If substantive, recommend `/authorkit.discuss` (Cross-cutting change) for systematic propagation.
- **Flag, don't fix downstream.** Downstream impacts are reported, not auto-fixed.

## Reporting (end of every invocation)

End every turn with:

1. **Mode summary**: which modes ran (e.g., *Plan + draft + reconcile* for chapter 7).
2. **Files written** with paths and one-line summaries each.
3. **Status changes** in `chapters.md`.
4. **Drift / ambiguity flags** surfaced by reconcile (with proposed follow-ups).
5. **Suggested next step**:
   - Full chapter drafted and reconciled clean → `/authorkit.review N` to review craft, then `/authorkit.write N+1` (or "next").
   - Partial draft in progress → `/authorkit.write N continue` or "write the next scene yourself".
   - Drift surfaced → `/authorkit.discuss <topic>` for the specific issue.
   - Multiple chapters drafted recently → `/authorkit.review` for a manuscript-wide drift sweep.

## Key Rules

- **The draft is prose, not notes.** Full sentences, paragraphs, dialogue, descriptions.
- **Follow the constitution religiously.** It is the style bible.
- **Follow the style anchor religiously.** `book/style-anchor.md` is the continuity baseline across model switches.
- **The plan is a guide, not a prison.** A better idea while writing? Follow it — but note the deviation.
- **Voice consistency (two layers)**: hold **global** voice (POV, tense, distance, cadence, register, imagery) to the fixed origin via the style anchor; match **character/scene/arc texture** to the *earliest relevant* approved chapter (step 4), never to a trailing one. A drifted recent chapter is not the standard. Match author-written passages in mixed-authorship drafts.
- **No meta-commentary**: drafts contain only book content. The only exception is the `<!-- PARTIAL DRAFT: … -->` marker for non-Full draft modes.
- **Dialogue formatting**: genre-standard.
- **Length**: Full mode aims for target word count (10-15% variance OK).
- **Mixed authorship**: all existing draft content is canonical. Match what's on the page. Author-written deviations are canonical over the plan.
- **Seamless transitions**: when continuing or inserting, re-read the surrounding paragraphs to ensure continuity.
- **Minimal surgery in revision and passage help**: smallest change that fixes the issue; preserve voice; do not rewrite working sections.
- **Reconcile is automatic** after Draft / Revise unless the author declines.
- **Soft gates only**: parked decisions and unresolved clarifications are listed but never block writing.
- **Track changes**: every report says what was changed and why.
- **Approved chapters need user attention**: never silently downgrade `[X]` status during revision — flag and let the author decide.
