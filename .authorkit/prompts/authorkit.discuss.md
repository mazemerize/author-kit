---
description: Talk through anything about the book — brainstorm, clarify, decide, propagate changes, defer, restructure. Writes are always confirmed and reported.
handoffs:
  - label: Write Next Chapter
    agent: authorkit.write
    prompt: Plan and draft the next chapter using what we discussed
  - label: Review Manuscript
    agent: authorkit.review
    prompt: Run a manuscript-wide review
  - label: Research a Topic
    agent: authorkit.research
    prompt: Research a topic we surfaced in the discussion
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --include-chapters
  ps: scripts/powershell/check-prerequisites.ps1 -Json -IncludeChapters
---

## User Input

```text
{{USER_INPUT_TOKEN}}
```

You **MUST** consider the user input before proceeding (if not empty). The input is free-form — it might be a topic, a question, a proposed change, a request to restructure, or a creative dead-end. Adapt to whatever the author brings.

## Goal

This is the single entry point for any author-facing conversation about the book that is not pure manuscript writing. It is read-only by default and never silently mutates files. When a decision crystallizes, you **propose a write, name the destination, and wait for explicit approval** before doing anything.

Under one command, this absorbs every form of discussion, clarification, deferral, propagation, restructuring, and voice/style update. The author should never have to think about which sub-command applies — describe what they want, and the model dispatches.

## Mode Dispatch

Read the user input and current book state, then pick the matching mode. Multiple modes may apply within a single conversation — that is normal. Switch when the conversation shifts. **State the mode you're entering** in one short opening line so the author can correct you (e.g., *"Treating this as a cross-cutting change — I'll surface an impact plan first. Tell me to switch if I'm wrong."*).

| Trigger in user input or state | Mode | What happens |
|---|---|---|
| Empty repo (no `concept.md`) | **Conceive** | Conversation produces the initial concept; write only on author approval |
| "Let's talk about…", "I'm stuck on…", "what if…" without commitment | **Brainstorm** | Read-only creative conversation; offer concrete options |
| "The X feels vague", "clarify the magic system", focused Q&A | **Clarify** | One-question-at-a-time Q&A; each accepted answer routes to the right file |
| "Change X to Y across the book", "cut the romance subplot", "Marcus is now a spy" | **Cross-cutting change** | Impact plan first, auto-snapshot, then propagate top-down |
| "Defer this", "park this question", "decide later", "list parked", "resolve PD-NNN" | **Park** | Add / list / resolve parked decisions |
| "Move CH05 to after CH02", "split CH04", "merge 6 and 7", "insert a chapter" | **Restructure** | Reorder, split, merge, insert, or remove chapters |
| "Try first person for flashbacks", "what if Marcus dies", "explore an alternative" + commitment to test it | **What-if** | Create experimental git branch; compare / merge / discard later |
| "Update the voice", "make the tone more X", "tighten the style rules" | **Constitution** | Update voice/tone/style rules in `.authorkit/memory/constitution.md` |
| "Build the magic system", "flesh out the world for X", and `world/` is empty or thin | **World seed** | Create initial world/ entries from concept; tag `(CONCEPT)` |
| "Save this", "note this" mid-conversation | **Save notes** | Write a discussion-notes file using the template |

If the user input is genuinely ambiguous, ask one clarifying question — do not guess silently between two modes that have different write footprints.

## Always-on Behavior

1. **Setup**: Run `{{SCRIPT_CHECK_PREREQ}}` from repo root and parse BOOK_DIR and AVAILABLE_DOCS. All paths must be absolute. If the script returns no BOOK_DIR (fresh repo, no `book/` workspace), enter **Conceive** mode below — do not error.

2. **Load whatever is available** (none are required except for specific modes):
   - `concept.md`, `outline.md`, `chapters.md`, `characters.md`
   - `.authorkit/memory/constitution.md`
   - `world/` and `world/_index.md` (use the Alias Lookup and Chapter Manifest for targeted entity loading when present)
   - `parked-decisions.md`
   - `research.md` and relevant `research/` topic files (recursively)
   - The last 2-3 drafted chapters under `chapters/NN/draft.md`
   - `BOOK_DIR/notes/discuss-*.md` (prior discussion notes — distinct from `world/notes/`)

3. **No silent writes.** Every file mutation goes through this gate:
   - State what you want to write: file path, section, and a short summary of the change.
   - Ask the author: *"Save? (yes / no / defer)"*
   - Only proceed on `yes`. `defer` routes to Park mode for that single item.

4. **Auto-snapshot before risk.** If a proposed write touches 5+ artifacts or any approved (`[X]`) chapter draft, create a snapshot first (see Snapshot Helper below). Do not skip even on user pressure — the snapshot is fast and reversible.

5. **Report what changed.** End every turn with an explicit list of files written (paths, sections, one-line summary each). If nothing was written, say so.

6. **The author's instinct is canonical.** If they push back on a recommendation, support their choice. Do not argue for the "correct" narrative or structural answer.

## Mode: Conceive (empty repo or no concept.md)

When `concept.md` does not exist:

1. Run `setup-book` if the workspace itself doesn't exist (use the `{{SCRIPT_SETUP_BOOK}}` token — substituted at install time). Parse the JSON for `BOOK_DIR`, `CONCEPT_FILE`, `STYLE_ANCHOR`, `BOOK_TOML`, `HAS_GIT`. Do not create or rename git branches.
2. Load `.authorkit/templates/concept-template.md` to know the required sections.
3. Treat the user input as the initial book description. If empty, ask one open question: *"What's the book about? A sentence or two is enough."*
4. Extract key concepts: genre, characters/subjects, setting, themes, tone, conflict/thesis.
5. For unclear aspects, make **informed guesses** based on genre conventions. Mark with `[NEEDS CLARIFICATION: specific question]` only when:
   - The choice significantly impacts the book's direction
   - Multiple reasonable interpretations exist with different implications
   - No reasonable default exists
   - **Cap at 3 markers total.** Prioritize: premise > audience > structure > style details.
6. Fill the concept template:
   - **Premise** — if no clear premise: ERROR "Cannot determine book premise"
   - **Genre & Audience** — use genre conventions for defaults
   - **Themes** — extract from description; infer from genre if not explicit
   - **Characters/Subjects** — for fiction: motivations and arcs; for non-fiction: topics and relationships
   - **Tone & Voice** — infer from genre and description
   - **Scope** — genre-standard word/chapter counts (literary fiction 70-90k, thriller 80-100k, non-fiction 40-80k)
   - **Success Criteria** — book-specific, measurable
7. Validate inline (no separate checklist file): premise is one-sentence-clear, genre/audience defined, themes distinct, voice specific, no contradictions, success criteria measurable.
8. **Propose the write**, get approval, then write to `CONCEPT_FILE`.
9. If any `[NEEDS CLARIFICATION]` markers remain after writing, **immediately offer to enter Clarify mode** to resolve them, one at a time. Do not require a separate command.

Reasonable defaults to use silently (do not ask about these): chapter count, POV (genre-typical), tense (past unless genre suggests otherwise), structure (linear unless concept implies otherwise).

## Mode: Brainstorm

Open, read-only creative conversation. Used when the author is exploring rather than deciding.

- **Offer concrete options.** For each topic, propose 2-3 specific possibilities with brief pros and cons. Never stay abstract.
- **One question at a time.** Let the conversation flow.
- **Build on the author's ideas.** When they propose something, develop it — add depth, complications, consequences. Don't replace it.
- **Flag implications.** If an idea conflicts with established elements (concept, outline, world/, drafted chapters), name the conflict as information — not a veto.
- **Stay in genre.** Thriller writer for thrillers, systems thinker for fantasy world-building, etc.
- **Track decisions in your head.** Periodically summarize: *"So far we've decided X, Y, and Z."*
- **No writes** unless the author says "save"/"note this" (see Save Notes below) or a decision crystallizes and you offer to route it (see Clarify).

If the conversation turns into focused decisions, switch to **Clarify** mode. If it turns into a structural change to existing material, switch to **Cross-cutting change** mode. Announce the switch in one line.

## Mode: Clarify

Resolve specific ambiguities in concept, world, characters, or planned direction.

1. **Identify the focus**: explicit from user input (e.g., "clarify the magic system") or implicit (next likely-drafted chapter's gaps, `[NEEDS CLARIFICATION]` markers anywhere, parked decisions near deadline, drift signals).
2. **Prioritize** the most impactful ambiguities. Order: premise > audience > structure > voice > details. Cap at **5 questions per session** to keep things focused.
3. **Ask one question at a time.** Each question is answerable with a short answer or multiple-choice. Provide a **recommended answer** with reasoning grounded in genre conventions and existing context.
4. **Route each accepted answer** to the right destination (see Routing Table below). Propose the write, ask for approval, then write.
5. **Continue** until ambiguities resolve, the author says "done", or 5 questions have been asked.
6. **Report**: count of clarifications recorded, files updated, suggested next step.

### Routing Table (where answers land)

| Answer is about… | Write destination | How to write |
|---|---|---|
| Premise / scope / one-sentence pitch | `concept.md` Premise section + `## Clarifications` audit line under `### Session YYYY-MM-DD` | Surgical section edit + append to log |
| Genre / audience | `concept.md` Genre & Audience + Clarifications log | Surgical + log |
| Themes | `concept.md` Themes + Clarifications log | Surgical + log |
| Voice / tone / register / cadence | `.authorkit/memory/constitution.md` (Constitution mode below handles version bump) + `concept.md` Voice & Tone summary | Constitution + concept summary |
| Character profile detail (backstory, traits, speech, appearance) | `world/characters/<entity>.md` if it exists, else `characters.md`. Tag the new fact `(CLARIFY-YYYY-MM-DD)`. Add to YAML `chapters` field. | World entry edit |
| Place / setting detail | `world/places/<entity>.md`. Tag `(CLARIFY-YYYY-MM-DD)`. | World entry edit |
| Organization / faction | `world/organizations/<entity>.md`. Tag. | World entry edit |
| System rule (magic, tech, social, economic) | `world/systems/<entity>.md`. Tag. | World entry edit |
| History / event | `world/history/<entity>.md`. Tag. | World entry edit |
| Other world note | `world/notes/<topic>.md`. Tag. | World entry edit |
| Plot direction / structural shift | `outline.md` chapter entry or Structural Overview | Surgical edit |
| Specific chapter scene / beat | `chapters/NN/plan.md` (if it exists) or a new "Pre-plan notes" section if not | Append note |
| Author wants to defer | `parked-decisions.md` via Park mode | See Park below |

After any write that adds new world frontmatter or tags, **rebuild the index** by running `{{SCRIPT_BUILD_WORLD_INDEX}}` from repo root.

### Clarifications log shape (in `concept.md`)

```markdown
## Clarifications

### Session YYYY-MM-DD
- Q: <question> -> A: <answer>
```

Create the section near the top of `concept.md` if missing. Append, never rewrite — the log is the audit trail. The substantive answer goes into the relevant concept section (Premise/Audience/Voice/etc.), not into the log.

## Mode: Cross-cutting Change

Used when the author wants to change something established across the manuscript: a character's identity, a plot direction, a world rule, a setting fact, a cut subplot. Auto-classifies as fact change, direction change, or mixed.

1. **Parse the change request** from user input. If too vague, ask one targeted question (e.g., *"To confirm: change Marcus's profession from soldier to spy, everywhere it shows up?"*).
2. **Comprehensive search** for direct, indirect, and derivative references:
   - Use `world/_index.md` Alias Lookup to find name variants. Use the Entity Registry `Chapters` column to target specific files. Read frontmatter `relationships` to identify connected entities.
   - Scan `concept.md`, `outline.md`, `chapters.md`, `characters.md`, every `world/` category, every `chapters/NN/plan.md`, every `chapters/NN/draft.md`, and `.authorkit/memory/constitution.md` for conflicts.
   - For each hit, record: file path, what specifically needs to change, severity (minor wording / major structural), dependencies.
3. **Present the Amendment Plan** (this is the contract — never skip):

   ```markdown
   ## Amendment Plan: [SHORT DESCRIPTION]

   **Type**: [Fact Change / Direction Change / Mixed]
   **Date**: [DATE]
   **Description**: [User's stated change]

   ### Impact Summary

   | Artifact | Impact Level | Changes Needed |
   |----------|-------------|----------------|
   | concept.md | [None/Minor/Major] | [What] |
   | outline.md | [None/Minor/Major] | [What] |
   | chapters.md | [None/Minor/Major] | [What] |
   | characters.md | [None/Minor/Major] | [What] |
   | world/ | [None/Minor/Major] | [N files affected: list] |
   | Chapter plans | [None/Minor/Major] | [N plans: list] |
   | Chapter drafts | [None/Minor/Major] | [N drafts: list] |
   | Constitution | [None/Conflict] | [Any conflicts] |

   ### Change Details

   **Direct references** (exact mentions):
   | File | Location | Current Text | Proposed Change |

   **Indirect references** (implications):
   | File | Location | Current Text | Why Affected | Proposed Change |

   **Derivative details** (logical consequences):
   | File | Location | Current Detail | Issue | Proposed Change |

   **Unchanged** (works with old and new state):
   | File | Location | Text | Why It's Fine |

   ### Execution Order
   1. [First artifact] — [why first]
   2. [Second artifact] — [depends on first because…]

   ### Risk Assessment
   - **Cascade risk**: [Low/Medium/High]
   - **Consistency risk**: [Low/Medium/High]
   - **Effort estimate**: [N artifacts, M chapters to revise]

   ### Recommendation
   [If 5+ artifacts: snapshot first. Flag any concerns.]
   ```

4. **Wait for explicit approval.** The author may: approve all, modify specific changes, exclude files/chapters, abandon, or request a snapshot first.
5. **Auto-snapshot** if 5+ artifacts are affected or any approved (`[X]`) chapter draft will be touched. Use the Snapshot Helper below.
6. **Execute top-down (upstream → downstream)**:
   a. **world/ files**: update entries. Append the change tagged `(AMEND-YYYY-MM-DD)` to `## History` AND supersede the affected `## Current State` lines in place so the now-truth reflects the amendment. Update YAML frontmatter: add the amend tag to `chapters`, refresh `aliases`/`relationships` if they changed, set `last_updated`. After all world edits, rebuild the index with `{{SCRIPT_BUILD_WORLD_INDEX}}`.
   b. **concept.md / outline.md / characters.md / chapters.md**: update directly.
   c. **Chapter plans**: update affected scene descriptions. If a plan changed significantly, reset chapter status to `[P]`.
   d. **Chapter drafts** — apply changes while **preserving each chapter's existing voice and style**:
      - Direct references → replace with new text
      - Indirect references → rewrite surrounding context to fit naturally
      - Derivative details → adjust logical consequences
      - Every edit must be stylistically indistinguishable from surrounding prose
      - Minor edits → status `[D]` (re-review)
      - Major structural changes → status `[P]` (re-plan + re-draft)
      - For approved (`[X]`) chapters: **flag for user attention**, don't silently reset
   e. Update `chapters.md` statuses.
7. **Post-change consistency check**: scan for remaining old-state references, check for new contradictions, report any issues.
8. **Write change log** to `BOOK_DIR/amendments/YYYY-MM-DD-[short-description].md` using `.authorkit/templates/amendment-template.md`. The template is the single source of truth; substitute bracketed placeholders.
9. **Report completion**: files modified (paths), statuses reset, residual issues, suggested next step (`/authorkit.review N` for prose-heavy changes, `/authorkit.review` for a full sweep).

## Mode: Park

Defer a creative decision when resolution can wait. Three sub-modes:

### Park a decision (default sub-mode)

1. Parse the question from input. If too terse, ask up to 3 setup questions: *Where does this matter? How urgent — `Before CHNN`, `Before final draft`, or `No deadline`? Any leading options?*
2. Ensure `BOOK_DIR/parked-decisions.md` exists; if not, seed it from `.authorkit/templates/parked-decisions-template.md`. The template is canonical — never invent the schema.
3. Generate a sequential ID `PD-NNN` based on existing entries.
4. Append using the ENTRY TEMPLATE block embedded in the template, replacing bracketed placeholders.
5. **Deadline format is strict.** Only `Before CHNN`, `Before final draft`, and `No deadline` are parsed by downstream commands. Translate free-form labels ("Before Act 3") to a chapter number before saving.
6. If any chapter currently being planned/drafted falls at or before the deadline: warn immediately.
7. Report: decision parked, ID, deadline, count of open decisions.

### List parked

If user input is "list", "show", "status", "what's parked": present a summary table with columns `ID | Title | Status | Urgency | Deadline | Parked Date`. For each OPEN row, compare deadline against current chapter progress (from `chapters.md` statuses):
- Deadline chapter is currently being planned/drafted → **URGENT — deadline reached**
- 1-2 chapters away → **APPROACHING**
- Otherwise → on track

### Resolve parked (user said "resolve PD-NNN: <decision>")

1. Find the entry in `parked-decisions.md`.
2. Update **Status** to `RESOLVED`, fill the **Resolution** block (Decided date, Decision, Rationale, Next Steps).
3. Assess downstream impact and suggest the right follow-up:

| Resolution implies… | Suggest… |
|---|---|
| Cross-chapter change | re-enter Cross-cutting change mode here with the decision content |
| Targeted fix in 1-2 chapters | `/authorkit.write N revise: <issue>` |
| New world-building | World seed sub-mode below |
| Update to existing world detail | World entry edit via Clarify routing |
| Affects upcoming unplanned chapter | `/authorkit.write N` |

## Mode: Restructure

Reorder, split, merge, insert, or remove chapters. Renumber files, IDs, cross-references, and world `(CHxx)` tags atomically.

1. **Parse the operation** from input:
   - Reorder/Move: "Move CH05 to after CH02", "Swap CH03 and CH07", "Move 8-10 before 5"
   - Split: "Split CH04", "Split CH04 at scene 3"
   - Merge: "Merge CH06 and CH07", "Combine 3, 4, 5"
   - Insert: "Insert a chapter between CH03 and CH04"
   - Remove: "Remove CH08" (archives, never deletes)
2. **Assess current state**: read `chapters.md`, identify which chapters have files (plan / draft / review), read `outline.md`, scan `world/` for `(CHxx)` tags affecting the operation (use `world/_index.md` Entity Registry `Chapters` column for targeting), scan plans and drafts for cross-references.
3. **Generate a Reorder Plan**:

   ```markdown
   ## Chapter Reorder Plan

   **Operation**: [Move / Split / Merge / Insert / Remove]
   **Date**: [DATE]

   ### Current Structure
   | # | ID | Title | Status | Has Plan | Has Draft | Has Review |

   ### Proposed Structure
   | # | Old ID | New ID | Title | Status | Action |

   ### File Operations
   | Operation | Source | Destination |

   ### Cross-Reference Updates
   | File | Current Reference | New Reference |

   ### Risk Assessment
   - Drafted chapters affected: [N]
   - Approved chapters affected: [N]
   - world/ tags to update: [N]
   - Cross-references to update: [N]
   ```

4. **Wait for approval.** If 5+ chapters are affected, recommend a snapshot first and create one on approval.
5. **Execute** (use temp directories to avoid collisions):
   a. Phase 1 — move each renumbered `chapters/NN/` to `chapters/tmp_NN/`.
   b. Phase 2 — move each `chapters/tmp_NN/` to its final `chapters/NEW_NN/`.
   c. Phase 3 — operation-specific:
      - **Split**: divide draft at specified point (or natural break — scene break / heading); split plans; both new chapters get status `[P]`.
      - **Merge**: concatenate drafts with section breaks; merge plans; archive the removed chapter's folder to `chapters/archived/`; merged chapter status `[D]`.
      - **Insert**: create empty folder with placeholder plan; status `[ ]`.
      - **Remove**: move folder to `chapters/archived/[NN]-[title]/`. Never delete.
   d. Phase 4 — rewrite `chapters.md` with new numbering. Preserve statuses (adjusted for splits/merges). Update part/act boundaries.
   e. Phase 5 — update cross-references in `outline.md`, every `world/` file's `(CHxx)`/`(CHxx-rev)`/`(AMEND-…)` tags and YAML `chapters` field, every chapter plan, every draft (prose chapter references are rare but possible in non-fiction), and `parked-decisions.md` deadlines.
   f. Phase 6 — reorder `outline.md` chapter entries; update arc and theme maps if chapters moved between parts/acts.
   g. Phase 7 — rebuild `world/_index.md` with `{{SCRIPT_BUILD_WORLD_INDEX}}`.
6. **Post-reorder validation**: every chapter folder exists at its new location, no duplicate IDs in `chapters.md`, no orphaned world tags, no broken cross-references in plans.
7. **Report** with a Changes Made table and validation results. Suggested follow-ups: `/authorkit.review` for full consistency, `/authorkit.write N` to plan inserted chapters, `/authorkit.review N` to re-review merged chapters.

## Mode: What-If

Try a creative direction on a git branch without committing to it. Four sub-modes: start, compare, merge, discard.

### Start (default — user describes an experiment)

1. Determine current branch (the "source branch").
2. Generate a what-if branch name: `whatif/[slug]` (e.g., `whatif/marcus-dies-ch5`).
3. **Auto-snapshot** the current state (see Snapshot Helper). File at `BOOK_DIR/snapshots/YYYY-MM-DD-pre-whatif-[slug].md`, git tag `snapshot/YYYY-MM-DD-pre-whatif-[slug]`. Record the source branch name in the snapshot.
4. `git checkout -b whatif/[slug]`.
5. Create `BOOK_DIR/whatif-active.md`:

   ```markdown
   # Active What-If Experiment

   **Branch**: whatif/[slug]
   **Source Branch**: [original]
   **Started**: [DATE]
   **Snapshot**: snapshot/YYYY-MM-DD-pre-whatif-[slug]

   ## Hypothesis
   [What the author wants to explore]

   ## Changes to Try
   - [Specific changes]

   ## Success Criteria
   - [How to evaluate]
   ```

6. Report: branch created, snapshot taken. Tell the author they can now use `/authorkit.write`, `/authorkit.discuss`, `/authorkit.review` normally on this branch; come back to this command with "compare", "merge", or "discard" later.

### Compare

1. Verify we're on a `whatif/*` branch (or read `whatif-active.md` to identify the experiment).
2. Use `git show [source-branch]:[file]` to read the original versions of modified files. Compare narratively, not just textually — *what's different about the story?*
3. Produce a narrative comparison report covering hypothesis, changes by artifact, plot/character/pacing/voice differences, word counts, strengths and weaknesses, and a Keep/Discard/Partial-merge recommendation.

### Merge

1. Verify we're on a `whatif/*` branch.
2. Read `whatif-active.md` for the source branch.
3. Warn: *"This merges experimental changes into [source]. Cannot be easily undone. Proceed?"* Wait for explicit approval.
4. On approval:
   - `git checkout [source-branch]`
   - `git merge whatif/[slug] --no-ff -m "Merge what-if: [description]"`
   - `git branch -d whatif/[slug]`
   - Remove `whatif-active.md`
   - Update the snapshot file to note the experiment was accepted
5. Report and **always recommend both** `/authorkit.review` (full manuscript drift) and re-running this command in **Restructure-like** post-merge verification if world tags shifted. Use `{{SCRIPT_BUILD_WORLD_INDEX}}` to rebuild the world index.

### Discard

1. Verify we're on a `whatif/*` branch.
2. Read `whatif-active.md` for the source branch.
3. Warn: *"This switches back to [source] and deletes the experimental branch. Changes are recoverable via git reflog for a limited time. Proceed?"* Wait for approval.
4. On approval:
   - `git checkout [source-branch]`
   - `git branch -D whatif/[slug]`
   - Remove `whatif-active.md`
   - Update the snapshot file to note the experiment was discarded
5. Report.

**One experiment at a time.** If `whatif-active.md` already exists, warn the author and require merging or discarding the current experiment first.

## Mode: Constitution

Update the book constitution at `.authorkit/memory/constitution.md`. This is the style bible — used by `/authorkit.write` (drafting) and `/authorkit.review` (review). The file is a template with placeholders in square brackets (`[BOOK_TITLE]`, `[PRINCIPLE_1_NAME]`, etc.).

1. Load the existing constitution. Identify every `[ALL_CAPS_IDENTIFIER]` placeholder. The `## Voice Origin` section is **not** a placeholder — it is a structured pin block (default: empty comment); handle it per the Voice Origin item in step 5.
2. Derive values: use user input where it supplies one, otherwise infer from `concept.md`, `outline.md`, prior constitution versions.
3. `CONSTITUTION_VERSION` bumps semver:
   - MAJOR: fundamental voice/style change
   - MINOR: new principle added or materially expanded
   - PATCH: clarifications, wording refinements
4. `RATIFICATION_DATE` is the original adoption date (preserve). `LAST_AMENDED_DATE` is today.
5. Areas to cover (adapt to genre):
   - **Voice**: POV, tense, narrative distance, formality
   - **Voice Origin pin** (`## Voice Origin` section): the fixed reference `/authorkit.write` builds the style anchor from and `/authorkit.review` grades global-voice drift against. Default empty = the earliest approved (`[X]`) chapter(s). Set or change a pin only to fix an unrepresentative opening (e.g. a prologue in a different register) or to record a **sanctioned** voice shift at a stage boundary. Write it in the documented format — `From CHnn: <exemplar chapter(s)>`, one line per stage, the exemplar at or after the boundary — **as active content directly under the `## Voice Origin` heading, not inside the example comment** (the write/review prompts read only an active pin) — and never switch it silently: re-pinning is a MAJOR (or significant MINOR) voice change, so recommend `/authorkit.review` afterwards to resurface drift against the new origin. (This pins only the *global* voice bar; character/scene texture is still matched dynamically against the earliest relevant chapter.)
   - **Tone**: emotional register, humor policy, darkness/lightness
   - **Audience**: target reader, assumed knowledge, accessibility
   - **Prose Standards**: show vs tell, dialogue rules, description density, sentence rhythm
   - **Naming & Numbers**: naming originality, numeric-specificity policy (rationale-first numbers, uncertainty handling when precision is unsupported)
   - **Tic Budget Overrides**: waivers or tightenings of the literary-tic budgets in `.authorkit/prompts/_shared/literary-tic-catalog.md` — each must name the pattern explicitly (by number, example, or description); vague register language is not a waiver
   - **Content Boundaries**: sensitivity guidelines, research accuracy, content warnings
   - **Structural Rules**: chapter length targets, scene transitions, cliffhanger policy
6. Each principle must be **actionable and testable** during chapter review. Include DO/DON'T examples where useful. The author may need fewer or more principles than the template provides — adjust accordingly.
7. Validate before writing: no remaining unexplained tokens; principles declarative and testable; dates ISO `YYYY-MM-DD`; each principle could be used as a review criterion.
8. Propose the write, get approval, then overwrite `.authorkit/memory/constitution.md`.
9. Report: new version + bump rationale, key principles established. If the change is material (MAJOR or significant MINOR) and chapters are already drafted, **recommend `/authorkit.review`** to surface drift, then targeted revisions in `/authorkit.write` to bring affected chapters back in line.

## Mode: World Seed

When the author asks to flesh out the world and `world/` is empty (or thin) for a category they mentioned, seed it from `concept.md` (and `research/` if grounded findings exist).

This is the "build initial world entries" path. For mid-manuscript additions, prefer Clarify routing (single entries) or invoke this mode only when seeding a whole category at once.

1. Load `concept.md` (premise, genre, themes, characters, setting), constitution, `research.md` / `research/` (recursively), and any existing `world/` files (to deepen rather than overwrite).
2. **Concept clarity check**: scan for `[NEEDS CLARIFICATION]` markers and unresolved `## Clarifications` questions on the focus area. If the author asked to build the magic system and the concept has an open clarification about magic, offer to enter Clarify mode first.
3. **Assess genre and pick categories** to populate. Not all books need all categories:

   | Category | Fantasy/Sci-fi | Historical | Contemporary | Non-fiction |
   |----------|---------------|-----------|-------------|------------|
   | characters/ | Yes | Yes | Yes | Rarely |
   | organizations/ | Yes | Often | Sometimes | Sometimes |
   | places/ | Yes | Yes | Sometimes | Rarely |
   | history/ | Yes | Yes | Rarely | Sometimes |
   | systems/ | Yes | Sometimes | Rarely | Often (frameworks) |
   | notes/ | Always | Always | Always | Always |

4. **Per category, either**: accept user-supplied details, extract from concept (preferring grounded research over unsupported assumptions), or ask up to 3 targeted questions if details are too sparse.
5. **Create folders only for categories that have content.** Don't create empty placeholder folders.
6. **File placement**: if an entity exists (resolve via `world/_index.md` `id`/aliases or recursive scan), update it in place. Never relocate or normalize existing files. New entities default to category root; only nest one level when a subfolder exists or this run creates 3+ entities sharing a clear grouping label.
7. **Write entries** using the chapter-tagged format. Each entry gets a `## Current State` block (the now-truth) and a `## History` section: seed History with `(CONCEPT)` entries and mirror those established facts into Current State. Tags become `(CHxx)` later when reconcile ingests from drafts. The full frontmatter and body schema lives in `.authorkit/templates/world-entity-frontmatter.md` — use it.
8. **Rebuild the index** with `{{SCRIPT_BUILD_WORLD_INDEX}}`.
9. **Internal consistency**: check that relationships are reciprocal, systems don't contradict, geography is plausible (travel times, climate), history is causally coherent. Flag any contradictions.
10. **Report** by category: files created, count per category, consistency warnings, gaps that could use more depth.

Reference material, not prose. Be specific. Don't over-build — only entries that will actually matter to the story.

## Mode: Save Notes

Triggered when the author says "save", "note this", "capture this" mid-conversation.

1. Create `BOOK_DIR/notes/discuss-YYYY-MM-DD-HH-MM.md` (use current timestamp). Create `BOOK_DIR/notes/` if missing.
2. Use `.authorkit/templates/discuss-notes-template.md` as the canonical structure. Substitute bracketed placeholders with the conversation content. Do not invent the schema inline.
3. Confirm the path and suggest the next command based on what was discussed (typically routing back into this command for follow-ups, or `/authorkit.write` if a chapter direction crystallized).

## Snapshot Helper (used by Cross-cutting Change and What-If Start)

When automation requires a snapshot:

1. Generate a short slug from context (e.g., `pre-amend-marcus-spy`, `pre-whatif-first-person`).
2. Assess current state by reading: `chapters.md` (counts per status `[ ]/[P]/[D]/[R]/[X]`), `concept.md` premise, `outline.md` structure, `world/` counts per category, `parked-decisions.md` OPEN count, `amendments/` count.
3. Write the snapshot file to `BOOK_DIR/snapshots/YYYY-MM-DD-[slug].md` using `.authorkit/templates/snapshot-template.md`. Substitute the placeholders; do not invent the schema inline.
4. `git tag snapshot/YYYY-MM-DD-[slug]`.
5. Report: file path, git tag, summary of captured state.

## Ending the Conversation

When the conversation naturally wraps (or the author says they're done), summarize:
- Key decisions made
- Files written this session (paths + brief description)
- Open questions remaining (with PD-NNN if parked)
- **Ready-to-run next commands** with specific invocations the author can copy:

| If we concluded with… | Suggest… |
|---|---|
| Direction or fact change to existing content | (handled inline in this command; nothing else needed) |
| New chapter direction settled | `/authorkit.write N` (with N as the concrete chapter number) |
| Chapter to review | `/authorkit.review N` |
| Topic needing grounded research | `/authorkit.research <topic>` |
| A decision still unresolved | (parked in this session; no separate command) |

Provide concrete arguments (e.g., `/authorkit.write 7`), not just command names.

## Key Rules

- **This is a conversation, not a report.** Don't dump walls of text. Keep turns focused; let the author steer.
- **The author's instinct is canonical.** If they have a strong feeling, support and develop it.
- **No writes without explicit "save".** Even when the right action is obvious, name the file and ask first.
- **Auto-snapshot before destructive operations.** Cross-cutting changes touching 5+ artifacts or approved chapters; what-if branch creation. Always.
- **Report everything written.** End every turn with a list of file paths and one-line change descriptions.
- **Preserve existing voice.** Any edit to a chapter draft must be stylistically indistinguishable from surrounding prose.
- **Approved chapters need user attention.** Never silently downgrade `[X]` status — surface the fact and let the author decide.
- **Don't over-correct.** If a reference works equally well with the old and new state, leave it unchanged.
- **One question at a time** in Clarify; **one experiment at a time** in What-If.
- **Respect existing work.** If chapters are drafted, flag the cost of changes that would invalidate them before agreeing to them.
- **Be specific, not generic.** "You could add more conflict" is useless. "What if Iria's mentor turns out to have hidden the catalogue, forcing her to choose between loyalty and truth?" is useful.
