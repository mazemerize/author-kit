### Reader-Facing Surface

- The reader of the finished book sees **only the drafted chapters** (the manuscript exported by `authorkit book build`). Every other artifact — `concept.md`, `outline.md`, `chapters.md`, `world/`, `research/`, chapter plans, reviews, and the constitution — is **internal scaffolding that never ships**.
- Write so the prose **stands on its own**: anything the reader needs to follow the story must be established *in the chapters themselves*. Never assume the reader can consult a world entry, the outline, or a research note — they cannot.
- Scaffolding is an **input, not content**. Do not transcribe the world bible or research into the prose; surface only what the scene needs, dramatized, and leave the rest as background pressure. No exposition dumps, "as you know" briefings, or encyclopedia voice sourced from `world/`.
- The converse holds too: do not withhold something load-bearing because "it's already in the world file." If the reader needs it to understand the scene, it must appear in the prose.
- `world/` and the outline exist to keep the chapters **consistent for the reader**, not to be read by the reader. When reviewing, check that each chapter is self-sufficient for someone with no access to the scaffolding, and flag anything that only parses if you have read the bible or outline.

### Name Originality Protocol

- Do not reuse generic stock names or repeated defaults from prior runs.
- Derive names from setting, culture, era, and class signals in the active project context.
- When introducing multiple entities of one type in the same deliverable, ensure names are not phonetic lookalikes and do not share the same structural pattern.
- Before final output, run a local uniqueness pass across newly introduced names in this command output.

### Numeric Fact Protocol

- Treat every new concrete number as a factual claim, not filler.
- For each new number, include a narrative, logistical, historical, or domain rationale from available context.
- If context does not support a precise value, prefer a bounded range, approximation, or explicit uncertainty marker.
- When multiple values are plausible, pick a context-bounded varied value to avoid repetitive defaults; variability is allowed only after rationale is established.
- Avoid repeating arbitrary fallback numbers across unrelated facts.

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

### Literary Tic Avoidance

- The canonical list of LLM-typical prose tics, with default budgets and the
  constitution-override clause, lives at
  `.authorkit/prompts/_shared/literary-tic-catalog.md`. Load it for any
  command that drafts, revises, or reviews manuscript prose.
- Treat the catalog's budgets as defaults. A pattern is permitted beyond its
  budget only when the constitution (or the style anchor's **Avoid** /
  **Imagery Density** sections) **explicitly** names the pattern, raises its
  budget, or states a voice/genre rationale. A generic "literary register"
  note does not waive a pattern.
- A book's constitution can also tighten a budget (e.g., zero negations).
  Treat tightening as binding.
- Drafting commands: write within budget on the first pass; do not generate
  tic-rich prose and clean it up after.
- Review commands: count instances per pattern (per chapter and per 1,000
  words for density patterns), compare against the budgets, and report any
  active constitution waivers at the top of the review.

### Tag and Placeholder Conventions

Author Kit uses three distinct bracket conventions. Do not mix them.

- **`(CONCEPT)` / `(CHxx)` / `(CHxx-rev)` / `(AMEND-YYYY-MM-DD)`** — *Evolution tags* written into world/ entity files (and amendment logs) to mark when a detail was established or changed. Round parentheses, written verbatim into the file content. Example: `aliases: [Vadek, Dr. Ellhar]  # (CH03)`.
- **`[N]` / `[N+1]` / `[PD-NNN]` / `[topic]` / `[focus area]`** — *Handoff placeholders* that appear in `handoffs:` frontmatter `prompt:` strings. They are templates, not literal text. When a user picks the handoff, substitute the relevant value (current chapter number, parked-decision id, etc.) before forwarding. Never forward literal bracketed text.
- **`CHxx`** (no brackets) — *Canonical chapter id* in body text and file paths (e.g., `chapters/03/draft.md`, "Plan CH03"). Always two-digit, zero-padded. In user-facing prose, "Chapter 3" is acceptable; in tags, file references, and structured fields, use `CH03`.

Status markers `[ ]`, `[P]`, `[D]`, `[R]`, `[X]` appearing in `chapters.md` are a fourth convention — square brackets *with* a space or single letter inside — and are scoped exclusively to that file and the commands that read it.

### Pre-output Audit

- Name audit:
  - List all newly introduced names and verify distinctiveness and setting-fit.
- Numeric audit:
  - List all newly introduced numeric facts and confirm rationale or explicit uncertainty treatment.
- Style audit:
  - Confirm alignment with constitution and `book/style-anchor.md`.
  - Flag and correct drift before final output.
- Literary tic audit:
  - Count instances of each pattern in `literary-tic-catalog.md` over the new
    prose (per chapter, and per 1,000 words for density patterns).
  - Compare to the catalog's budgets. For any pattern over budget, either
    rewrite to comply or — if a constitution waiver applies — note the waiver
    in the run report.
  - Zero-budget patterns (3, 7, and the named zero-budget variants of 14
    and 15) and high-signal patterns (10, 13, 16) get a dedicated pre-output
    sweep before saving.
