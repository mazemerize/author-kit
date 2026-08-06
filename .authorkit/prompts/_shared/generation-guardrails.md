### Project Kind (book | collection)

Every project has a **kind**, recorded as the `**Kind**:` field in `concept.md`. **If the field is absent, treat the project as `book`** — this preserves all default behavior for existing projects.

- **`book`** *(default)* — one continuous work: a single arc (or argument) told across numbered chapters, with cross-chapter continuity, threads, and a disclosure horizon. All continuity machinery is on. This is what every command implements by default; the rest of this file assumes `book` unless it says otherwise.
- **`collection`** — independent or loosely-ordered pieces that share an author voice (and optionally a broad theme and a shared reference), but **not** a single dramatic arc: an article series, an essay collection, a set of standalone guides. Each numbered unit is self-contained. The voice/tic/style defense stays **fully on** — it is the whole reason to run a collection through Author Kit; only the *cross-piece continuity* apparatus relaxes.

**Vocabulary & substrate are unchanged for both kinds.** The on-disk layout stays `chapters/NN/`, `chapters.md`, and `CHxx` tags regardless of kind — for a `collection`, a "chapter" is simply one piece (article / essay / part). Do not rename anything; the substrate is an implementation detail. In author-facing prose you may call a unit a "piece" or "article" when the kind is `collection`.

**Collection relaxations (apply only when kind = `collection`).** Wherever the default flow assumes cross-piece continuity, relax it:

- **Outline (`/authorkit.write` Outline mode).** Do not synthesize a single cross-piece arc. Omit the outline's aggregate continuity sections — *Narrative Arc / Argument Flow*, *Character Arcs / Concept Progression*, *Thematic Thread Map*, *Continuation Notes* — and leave each entry's *Connections* (setup/payoff) empty or "N/A". Keep the per-piece fields (purpose, summary, key points, subjects/characters, closing beat). Skip cross-chapter pacing and the disclosure-horizon validation. A shared editorial theme across pieces is allowed, but without the Introduced → Developed → Resolved lifecycle.
- **Review — craft roster (Analysis Passes).** **Pass 4 (Cross-Chapter & Plot-Arc)**: run its **World & canon consistency** bullet (per-piece, against `world/`) **and its Voice texture continuity bullet** (which still governs any persona, subject, or register recurring across pieces — the voice machinery does not relax); skip the cross-chapter flow/contradiction, quantitative-drift-across-chapters, backstory-verification, knowledge-boundary, and plot-arc-convergence bullets. **Pass 5 (Disclosure Horizon)**: **skip** — N/A, no later piece owns a reveal. Passes 1, 2, 3, 6, 7 run unchanged.
- **Review — manuscript drift sweep (Step 2).** Skip the continuity passes **A (Continuity & Timeline)**, **D (Pacing Analysis)**, **G (Plot Thread Tracking)**, **J (Quantitative Continuity Ledger)**, and **K (Premature Disclosure)**. Relax **B (Character Consistency)** and **C (Theme & Motif)** to a shared-persona / shared-theme check across pieces (drop foreshadowing-payoff and cross-piece arc expectations). Relax **F (Argument Coherence)** to *within a single piece*. Keep **E / E1 (voice & drift trajectory)**, **H (parked decisions)**, **I (world consistency — read as glossary consistency)**, and **L (scaffolding leakage — it reinforces per-piece independence)**. In **Step 1**, skip **1e (Outline Aggregate-Section Resynthesis)** in lockstep, since those outline sections are not produced.
- **World (`/authorkit.write` Reconcile, `/authorkit.discuss` World Seed).** `world/` is an **optional shared glossary / reference** for recurring people, terms, and facts across pieces — not a narrative-continuity canon. `(CHxx)` tags act as per-piece namespacing, not a timeline; "previous chapter carry-over" is optional.
- **Voice origin stays shared (unchanged).** A `collection` carries **one author voice** by default, so the single fixed origin (earliest approved pieces) still governs every piece. Do not weaken the style / tic / voice machinery — it is identical for both kinds.

### Language Protocol (prose language)

Every project has a **prose language**, recorded as `language` in `book/book.toml`'s `[book]` table and surfaced to every command as **`BOOK_LANGUAGE`** by its setup script (`check-prerequisites` / `setup-book`). **If the field is absent, empty, or unreadable, treat the language as `en-US`** — this preserves all default behavior for existing projects. The value may be a BCP-47 tag (`fr-FR`, `de`, `pt-BR`) or a plain name (`French`); resolve it to the human language name before writing anything. Author Kit itself — its commands, prompts, and templates — stays in English regardless.

- **Written in the book's language**: the manuscript and everything that ships (chapter drafts, chapter titles, epigraphs), **and** the author-facing content of the scaffolding — `outline.md` entries, `chapters/NN/plan.md` bodies, `concept.md` prose, `world/` entry bodies, `research/` notes, review findings prose, discussion notes. The author reads these; they are not machine input.
- **Always English, never translated** — the structural layer the commands and AutoPilot read back: file and directory names, template section headings, YAML frontmatter keys, status markers `[ ]` `[P]` `[D]` `[R]` `[X]`, evolution tags `(CONCEPT)` / `(CHxx)` / `(CHxx-rev)` / `(AMEND-…)`, `CHxx` ids, `TIC-NNN` ids and tic-ledger field names, severity labels, verdict labels (`APPROVED` / `NEEDS REVISION`), and the review's `**Gating Shapes**:` line. These are greppable contracts: a translated label silently breaks convergence detection and the carry-over rule.
- **Quotes are verbatim.** Prose quoted into a review, `book/tic-ledger.md`, or `book/voice-pairs.md` keeps its original language — never translate a quoted instance, a counter-example, or a voice pair. The voice origin and `book/style-anchor.md` are built from the book's own prose and are therefore in the book's language by construction.
- **Typography follows the target language**, not English defaults: French guillemets `« »` with non-breaking spaces and dash-led dialogue, German `„ "`, Spanish `¿ ¡`, and each language's own quotation, spacing, and dash conventions. Punctuation-shaped tic budgets are read against those conventions (see the seed catalog's *Language Scope*) — dialogue punctuation is typography, not a tic.
- **Tic defense is language-scoped.** The seed catalog's structural and constructional patterns transfer to any language (the shape is the target, not the English example); its `Lang: en` entries — the lexical canon and the greppable exact-string clichés — apply only to English books, and a non-English book seeds instead from `.authorkit/prompts/_shared/tic-catalog-<lang>.md` when one ships for its language. The quarantine is unchanged: no catalog, no pack, and no ledger ever enters a drafting context.
- **A language change mid-book is an author decision.** If `BOOK_LANGUAGE` disagrees with the language of the existing drafts, say so and ask — never silently retranslate existing prose, and never start drafting in a different language than the manuscript without flagging it.
- The Entropy Protocol is unaffected: `authorkit entropy name` seeds phonemes from a culture signal, which is chosen for the setting and is independent of the prose language.

### Reader-Facing Surface

- The reader of the finished book sees **only the drafted chapters** (the manuscript exported by `authorkit book build`). Every other artifact — `concept.md`, `outline.md`, `chapters.md`, `world/`, `research/`, chapter plans, reviews, and the constitution — is **internal scaffolding that never ships**.
- Write so the prose **stands on its own**: anything the reader needs to follow the story must be established *in the chapters themselves*. Never assume the reader can consult a world entry, the outline, or a research note — they cannot.
- Scaffolding is an **input, not content**. Do not transcribe the world bible or research into the prose; surface only what the scene needs, dramatized, and leave the rest as background pressure. No exposition dumps, "as you know" briefings, or encyclopedia voice sourced from `world/`.
- The converse holds too: do not withhold something load-bearing because "it's already in the world file." If the reader needs it to understand the scene, it must appear in the prose.
- `world/` and the outline exist to keep the chapters **consistent for the reader**, not to be read by the reader. When reviewing, check that each chapter is self-sufficient for someone with no access to the scaffolding, and flag anything that only parses if you have read the bible or outline.

**Standalone Readability self-check** (run before saving prose, and the basis of the review's Standalone pass): would this chapter be fully comprehensible to a reader with **zero** access to `world/`, the outline, the concept, or earlier scaffolding — only the shipped chapters so far? Flag and fix any sentence that parses *only* with the scaffolding: a name/term/relationship dropped without in-prose grounding, an "as established" reliance on an unstated fact, or encyclopedia voice transcribed from a `world/` entry. The converse guard still holds — do not withhold something load-bearing because "it's already in the world file."

### Unattended Mode (AutoPilot)

When your input carries the `[AUTOPILOT-UNATTENDED]` directive, you were dispatched non-interactively by an `authorkit autopilot` run and **cannot ask the author and receive a reply this turn**. Adjust the normal interactive gates:

- **Grounded elaboration proceeds without the approval gate.** For work the established concept / outline / research already implies — World Seed (building out `world/`), folding research into `world/` and the outline, and clarify-routing whose answer those sources already determine — invent the specifics, write the entries (tagged), rebuild the world index, and **report exactly what you wrote**, instead of waiting for a "Save? (yes/no)" you cannot receive. Everything is git-committed per tick and reviewable, and the reader never sees `world/`.
- **Skip optional gated prompts** — take the safe default (e.g. a review's drift-fix offer = Skip; stay read-only there), complete the non-gated work, and report.
- **Genuine forks still escalate — never invent a resolution.** For anything the concept/outline does **not** settle — a direction choice, a contradiction with a `(CONCEPT)` / `(CHxx)` fact, a restructure — make only the grounded writes that are safe and **flag the open fork clearly in your report** so the loop or author can escalate it. Do not pick a side the source material has not decided.
- Ground every invention in the concept/outline/research; do not introduce canon the concept doesn't imply. Snapshots and amendment logging still apply to cross-cutting changes.

### Entropy Protocol (code-driven names & numbers)

A model left to itself reaches for the same stock names (Elena, Marcus, Kael, Aria…) and
the same default numbers (three, a dozen, forty, 1,247). To break that attractor, derive
new names and new arbitrary numbers from **real randomness produced by code**, not from
free association.

- **When you introduce a new name** with no name already fixed by the concept/outline/world,
  call `authorkit entropy name` (optionally `--culture <signal> --syllables N --count N`).
  It returns *construction seeds* — syllable/phoneme skeletons, an initial-letter
  constraint, a length target, an optional culture/era tag — **not** finished names. Build a
  setting-fit name *from the seed*: honor the seed's letters/shape, then adjust for
  pronounceability and culture/era/class fit. The seed is the anti-stock-name lever; the
  craft is yours.
- **When you introduce a new concrete number** that the context does not already pin (a
  count, age, distance, duration, year, time), call `authorkit entropy number --min A --max B`
  (`--kind int|float|year|time`, `--count N`) and use a returned value. Choose bounds the
  context justifies; let the tool pick within them.
- The tool runs headless (a plain CLI call), so it works the same in interactive and
  AutoPilot/unattended runs — no approval needed.
- **A rolled value, once written into prose, is canon** (see Quantitative & Logical
  Continuity). Record new numeric facts so later chapters and review can hold the line.

After deriving, run the originality/rationale audit that used to *be* these protocols:

- **Names**: no generic stock name or repeated default; distinct from prior runs; when
  multiple entities of one type appear together, names are not phonetic lookalikes and do
  not share one structural pattern. Run a local uniqueness pass across new names.
- **Numbers**: every new concrete number is a factual claim, not filler — it has a
  narrative/logistical/historical/domain rationale, or, where context can't support a
  precise value, a bounded range / approximation / explicit uncertainty marker. Do not
  repeat arbitrary fallback numbers across unrelated facts.

### Quantitative & Logical Continuity Protocol

- Treat every concrete quantity, count, age, date, duration, distance, and ordinal as a
  **fact of record**. Once it is in the prose it is canon.
- **Never silently change a committed quantity** (nine guards do not become twelve a chapter
  later; a character aged forty does not become thirty-eight). If the story genuinely
  changes a quantity, it must be **dramatized as an in-story change**, not slipped in as a
  contradiction.
- Keep intra-chapter quantities internally consistent (three established ≠ "the four" later
  in the same scene) and arithmetically sound.
- Before final output, list new/changed numeric facts and confirm none contradicts a prior
  chapter or the matching `world/` `## Current State`.

### Disclosure Horizon Protocol

You can see the whole outline; the reader cannot. **Plan and write** from the **knowledge
horizon of the chapter's present** and do not betray that foreknowledge — at either layer.

- Do **not** state or reveal a plot fact the outline assigns to a *later* chapter. The
  narrator-prophecy / proleptic flash-forward construction ("what she would only understand
  years later…", "this was the day that would…") is **disallowed** unless the referenced
  fact is already disclosed to the reader.
- **This binds planning, not just prose.** A chapter plan or outline entry must not
  *prescribe* a premature reveal — no "Key Revelation", closing beat, or scene beat that
  states a later chapter's twist, and no plan note calling for a proleptic flash-forward or
  narrator-prophecy. A leak planted in the plan is executed faithfully by the drafter and
  only caught downstream at review; catch it at the plan instead.
- **Exception — story-sanctioned structure.** A deliberate non-linear device (a frame
  narrative recounted from a known future, a flash-forward prologue, an outline explicitly
  built to open ahead of its timeline) is allowed **only when the concept, constitution, or
  outline structure records it as intended** — never as an incidental plan beat. When in
  doubt, treat it as a leak: seed the future instead of disclosing it, and escalate the
  structural question rather than planning the reveal in.
- The construction *"later, XXX, but for now, YYY"* is allowed **only when XXX is already
  known to the reader** (you are sequencing the known, not spoiling the unknown).
- Planted foreshadowing remains welcome: an image, object, or unease that *pays off* later
  without naming the payoff is craft, not a leak. The ban is on disclosing the future, not
  on seeding it.

### Alias Lookup Disambiguation

- When resolving a name through `world/_index.md`'s Alias Lookup, check the `Ambiguous` column.
- If the matching row is flagged `Ambiguous=YES`, do **not** pick automatically. Surface the candidate entity IDs to the user with their types and chapter tags, ask which entity is meant, and use the user's choice.
- If only one entity matches and the column is empty, proceed with that entity.

### Style Continuity Protocol

Voice lives at two layers; keep them distinct so intelligent matching never erodes the drift bar.

- **Layer 1 — global voice (the fixed origin / drift bar).** Constitution is the primary style authority. Resolve the **voice origin**: if the constitution's `## Voice Origin` names exemplar chapter(s) (`From CHnn:`) for the target stage, use them; otherwise default to the *earliest* approved (`[X]`) chapters (lowest numbers). **Always also include any `### Voice Exemplars` excerpts under `## Voice Origin`** — author prose samples that are part of the fixed origin, and the concrete voice bar before any chapter is approved. The pin is a recorded, author-sanctioned override — propose it via `/authorkit.discuss` (Constitution mode); never switch the voice bar silently per run. The origin governs POV, tense, narrative distance, cadence, diction/register, imagery density, and dialogue behaviour, and it does **not** move as the book grows — that fixedness is what makes drift measurable.
- **Build or refresh `book/style-anchor.md` from that fixed origin** — constitution + concept voice/tone + the resolved origin chapter(s), never the most recent ones:
  - Two or more approved chapters: constitution + concept voice/tone + the earliest one or two approved drafts.
  - One approved chapter: constitution + concept voice/tone + that draft.
  - None approved: constitution + concept voice/tone + any `### Voice Exemplars` excerpts.
- **Layer 2 — character/scene/arc texture (the voice exemplar; matched, never the bar).** For texture the global origin under-specifies — how a given POV character's interiority reads, an arc's tonal colour, a recurring character's dialogue voice — match the **earliest *relevant* approved chapter**: the lowest-numbered approved draft featuring this chapter's POV/focus characters or the same arc register (use the `world/_index.md` Chapter Manifest + Alias Lookup). Pick the *earliest* relevant draft, not the most recent, so the exemplar is a representative instance rather than a trailing (possibly drifted) one. The exemplar may only *add* detail the origin leaves open; where it conflicts with the constitution or the fixed origin, the origin wins and the divergence is drift, not licence. Fall back to the fixed origin when no more-relevant approved chapter exists.
- Ground prose decisions in `book/style-anchor.md` and keep prose aligned on POV, tense, narrative distance, cadence, diction/register, imagery density, and dialogue behaviour defined there. (Plot/thread/state continuity — where an arc currently stands — comes from the *most recent* relevant chapter, a reference separate from the earliest-relevant voice exemplar.)

### Voice Conditioning Protocol (generation-side)

Models imitate the register of the text immediately preceding their output far
more faithfully than they follow style instructions — and negated instructions
prime the very patterns they name. So drafting **conditions** the model on the
voice instead of policing it with rules:

- **Continuation conditioning.** Assemble the drafting context so the model
  *continues* the book rather than follows instructions about it. Immediately
  before writing prose, place in order: (1) the resolved origin excerpt(s)
  **verbatim** (~2–4 pages of the fixed origin — see Style Continuity
  Protocol), (2) the tail of the current draft (or the previous chapter's
  closing scene when starting a chapter), (3) a *minimal* beat sheet for the
  scene, then continue the prose from there.
- **Voice pairs.** Load `book/voice-pairs.md` (**Active Pairs section only**)
  into the drafting context, framed positively: *in this book, prose like the
  left column gets revised to the right column — write right-column prose
  directly.* If the file doesn't exist yet, skip silently.
- **Two-stage drafting.** Draft each scene in two passes:
  - **Pass A — content**: deliberately flat camera prose — events, dialogue,
    concrete physical fact; no figurative language, no interiority glosses,
    no rhythm performance. All Entropy Protocol rolls (names, numbers) happen
    here. Pass A is working material only — never written to `book/`.
  - **Pass B — voice**: rewrite Pass A into the anchored voice with the origin
    excerpts and Active Pairs in context. Hard rule: **Pass B adds no new
    facts, names, or numbers** — it is a translation of Pass A, and the
    self-check diffs B against A to confirm. Only Pass B is saved.
- **Quarantine (see the next section):** the drafting context never contains
  the tic catalog, the tic ledger, or any enumeration of bad-prose patterns.

### Tic Ledger & Voice Pairs (self-learning tic defense)

AI-typical prose tics are model-specific attractors: a static list goes stale
the moment the model changes, and pattern descriptions in the drafting context
prime the constructions they prohibit. The defense is therefore **learned per
book** and split across two artifacts with a strict boundary:

- **`book/tic-ledger.md` — review-side memory.** The living, book-specific tic
  catalog, maintained by `/authorkit.review` Pass 2 via blind contrast against
  the fixed voice origin (the prose anchor). Each entry carries: a one-line
  shape, a **budget** (instances per chapter or per 1,000 words; `0` = flag on
  sight — seeded from the catalog, defaulting to 3 per chapter for discovered
  shapes), a quoted instance *from this book's drafts*, a counter-example showing
  how the *origin* does the same job, a per-chapter occurrence trend, a status
  (`seed | active | dormant | retired`), and an optional constitution waiver.
  Lifecycle: active → dormant after 1 clean reviewed chapter → retired after 2
  more consecutive clean chapters; `seed` entries (bootstrap hypotheses) retire
  if unconfirmed after 4 reviews — except zero-budget `phrase`-class seeds
  (exact strings, checked by literal search on every review), which never
  retire, dormant at most; a rediscovered retired shape reactivates with
  its history. Follow `.authorkit/templates/tic-ledger-template.md`.
- **`book/voice-pairs.md` — the only generation-side artifact.** Contrastive
  before→after pairs harvested when Revise fixes a Pass 2 finding (and from
  author hand-edits surfaced during Reconcile, tagged `author`). Keep ~20
  Active pairs, newest first, one instructive pair per shape; rotate the rest
  to Archive. Follow `.authorkit/templates/voice-pairs-template.md`.
- **Quarantine rule (binding).** Commands while *drafting* prose MUST NOT load
  the tic catalog or the tic ledger. Tic knowledge crosses into generation
  exclusively as Active voice pairs. Review and revision (which read existing
  prose rather than generate fresh register) hold the ledger.
- **The shipped catalog is a bootstrap seed only.**
  `.authorkit/prompts/_shared/literary-tic-catalog.md` seeds the first ledger
  entries when a book has no `book/tic-ledger.md` yet; once the ledger exists,
  the ledger — not the catalog — is normative.
- **Constitution waivers stay explicit.** The author sanctions a pattern by
  naming it in the constitution (by example or description — a generic
  "literary register" note is not a waiver; a legacy waiver naming a
  seed-catalog pattern number stays binding, resolved against the catalog). Review records the waiver on the
  matching ledger entry's `Waiver:` field; waived entries are reported at the
  top of the review, never flagged as findings. A constitution can also name a
  shape as banned outright — treat that as binding regardless of trend.

### Analysis Passes (canonical roster)

The single source of truth for how manuscript prose is analysed. `/authorkit.review` *finds*
per pass, `/authorkit.write` Revise *fixes* per pass, the writer's pre-output self-check
runs them on new prose, and AutoPilot inherits all three. The passes, in order (1–2 are
**gating** — a chapter that fails them is NEEDS REVISION regardless of the rest):

1. **Style Fidelity** *(gating)* — global voice vs the fixed origin (POV, tense, narrative
   distance, cadence, diction/register, imagery), style-anchor alignment, constitution voice
   rules. (See Style Continuity Protocol.)
2. **AI-Tic Audit** *(gating)* — self-learning tic discovery & contrast: a blind pass over
   the draft against the fixed origin prose (no list in hand) discovers recurring
   constructions the origin never uses, then reconciles them into `book/tic-ledger.md`
   (trends, decay, new entries); reconciliation includes a **literal sweep** — zero-budget
   `phrase`-class shapes (exact corpus-cliché strings) are verified by Grep, not
   read-through. **Discovery is unbounded; gating is convergent (carry-over
   rule).** A shape is over budget (Critical) at/above its ledger entry's budget — 3 per
   chapter by default (per 1,000 words in long chapters), **any single instance for a
   zero-budget form** — or on a rising active ledger
   entry; density also compounds — a paragraph carrying 3+ distinct shapes is a cluster
   finding, and a chapter-wide **tic-load** — the *mean* budget utilization
   `Σ(instances÷budget) ÷ N`, not a sum, so the index stays invariant as the discovery
   ledger grows — at/above the configured threshold gates even with every shape
   individually under budget (thresholds tunable per book in `book/book.toml` `[review]`:
   `cluster_min_shapes` and `persistence_chapters`, both default 3;
   `tic_load_mean_threshold`, default 0.75). The tic-load gate is calibrated by an
   **origin canary**: the index is computed for the fixed voice origin chapter first, and
   if the origin cannot clear the threshold the threshold is mis-set, not the prose —
   review reports it and does not gate on tic-load. A bar the fixed origin cannot clear is
   measuring the ruler, not the manuscript. On a *re-review* only the prior review's still-over-budget gating shapes gate,
   plus any regression the last revise introduced; freshly-discovered non-regression shapes
   are logged and reported as non-gating residual/seeds, not blockers, so the blind pass can
   keep finding new tics without re-opening the gate every cycle. The gate clears
   (converged-with-residual) when the carry-over set is empty; the review records it as
   `**Gating Shapes**:`. Constitution waivers honored via the ledger. On a re-review, Revise
   treats each carry-over gating shape as a *failed prior fix* — its harvested voice pair is
   the rewrite that didn't hold — and re-anchors on the ledger entry's origin counter-example
   instead of retrying a variant of that pair. To make the gate actually shrink, Revise drives
   a gating shape's **whole-draft** count below budget (the review's citations are a starting
   point, not the full set) — fixing only the cited spans leaves uncited instances the next
   blind pass re-finds, so the gate never clears; for a zero-budget `phrase`-class shape,
   Revise Greps the whole draft for the exact strings and clears every hit before declaring
   the finding fixed. (See Tic Ledger & Voice
   Pairs and `/authorkit.review` Pass 2 for the full rule.)
3. **In-Chapter Logical Consistency** — *within the one chapter*: quantities/counts/ages/
   dates/durations/distances/ordinals internally consistent and arithmetically sound;
   per-scene headcount and physical possibility within the established geometry; a character
   acts only on what they could know at this point in this chapter. (See Quantitative &
   Logical Continuity Protocol.)
4. **Cross-Chapter & Plot-Arc Logical Consistency** — vs prior drafted chapters and `world/`
   `## Current State`: numeric/fact drift across chapters, backstory verified against the
   referenced *draft* (not the outline), knowledge boundaries across chapters, and plot-arc
   convergence (a thread advanced here matches where prior chapters left it). The world/canon
   cross-check runs whenever `world/` exists — including on chapter 1, against the
   `(CONCEPT)`-seeded entries; only the cross-chapter items need prior chapters. *Kind
   `collection`: run the world/canon cross-check and voice-texture continuity; skip the
   plot/timeline cross-chapter bullets (see Project Kind).*
5. **Disclosure Horizon** — no premature disclosure / proleptic narration leaking
   future-chapter content. (See Disclosure Horizon Protocol.) *Kind `collection`: N/A — skip
   this pass; independent pieces have no later chapter to leak into.*
6. **Standalone Readability** — the chapter stands on its own without the scaffolding. (See
   Reader-Facing Surface → Standalone Readability self-check.)
7. **Craft & Structure** — plan adherence, pacing, show-vs-tell, dialogue, description,
   transitions, opening/closing, character behaviour, world consistency, theme integration.

Passes share one findings shape (severity + location/quote + suggested fix) and stable
names, so a finding written under a pass is the section Revise reads when it reaches that
pass. When the runtime offers parallel sub-agents, each pass may run as an independent
sub-agent against a baseline the parent resolves once (fixed origin, this roster,
`book/tic-ledger.md` — held by the parent; Pass 2's discovery step runs blind); otherwise
run them sequentially. Either way the names, order, and gating are these.

### Tag and Placeholder Conventions

Author Kit uses three distinct bracket conventions. Do not mix them.

- **`(CONCEPT)` / `(CHxx)` / `(CHxx-rev)` / `(AMEND-YYYY-MM-DD)`** — *Evolution tags* written into world/ entity files (and amendment logs) to mark when a detail was established or changed. Round parentheses, written verbatim into the file content. Example: `aliases: [Vadek, Dr. Ellhar]  # (CH03)`.
- **`[N]` / `[N+1]` / `[PD-NNN]` / `[topic]` / `[focus area]`** — *Handoff placeholders* that appear in `handoffs:` frontmatter `prompt:` strings. They are templates, not literal text. When a user picks the handoff, substitute the relevant value (current chapter number, parked-decision id, etc.) before forwarding. Never forward literal bracketed text.
- **`CHxx`** (no brackets) — *Canonical chapter id* in body text and file paths (e.g., `chapters/03/draft.md`, "Plan CH03"). Always two-digit, zero-padded. In user-facing prose, "Chapter 3" is acceptable; in tags, file references, and structured fields, use `CH03`.

Status markers `[ ]`, `[P]`, `[D]`, `[R]`, `[X]` appearing in `chapters.md` are a fourth convention — square brackets *with* a space or single letter inside — and are scoped exclusively to that file and the commands that read it.

### Pre-output Audit

- Name audit:
  - For each new name, confirm it was derived from an `authorkit entropy name` seed (not free-associated), then verify distinctiveness and setting-fit.
- Numeric audit:
  - For each new arbitrary number, confirm it came from `authorkit entropy number` within context-justified bounds, then confirm rationale or explicit uncertainty treatment.
- Quantitative & logical continuity audit:
  - List new/changed quantities (counts, ages, dates, durations, distances, ordinals); confirm none contradicts the same chapter (arithmetic, headcount), a prior chapter, or the matching `world/` `## Current State`. A silent change is a defect — dramatize it or revert it.
- Disclosure horizon audit:
  - Scan for premature disclosure / proleptic narration that reveals a fact the outline assigns to a later chapter. Allowed only if already disclosed (incl. the "later XXX, but for now YYY" form). Planted foreshadowing that names no payoff is fine.
- Standalone readability audit:
  - Confirm the chapter parses for a reader with only the shipped chapters — no scaffolding-only references, no transcribed `world/` exposition; load-bearing facts appear in the prose.
- Language audit:
  - Confirm the prose is in the book's language (`BOOK_LANGUAGE`) and follows that language's dialogue punctuation and typographic conventions; confirm no structural marker, tag, id, or status label was translated out of English.
- Style audit:
  - Confirm alignment with constitution and `book/style-anchor.md`.
  - Flag and correct drift before final output.
- Tic self-check (origin contrast — do NOT load the catalog or the ledger):
  - Contrast the new prose against the origin excerpts and Active voice pairs
    already in the drafting context. Does any construction, sentence shape, or
    beat-closer recur here that the origin prose never uses? Does anything read
    like left-column prose from `book/voice-pairs.md`?
  - Rewrite what fails the contrast before saving — the fix is whatever the
    origin does for the same job. If a constitution waiver sanctions the
    pattern, note the waiver in the run report instead.
  - Two-stage confirmation: diff Pass B against Pass A — no new facts, names,
    or numbers may have entered during the voice pass.
