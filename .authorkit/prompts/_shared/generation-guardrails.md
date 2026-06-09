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

- Constitution is the primary style authority.
- For prose continuity, also ground style decisions in `book/style-anchor.md`.
- Build or refresh `book/style-anchor.md` from the last two approved chapters before the target chapter:
  - Two approved chapters available: constitution + last two approved drafts.
  - One approved chapter available: constitution + that draft.
  - None approved: constitution only.
- Keep prose aligned on POV, tense, narrative distance, cadence, diction/register, imagery density, and dialogue behavior defined by the style anchor.

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
  - Zero-budget patterns (3, 7) and high-signal patterns (10, 13) get a
    dedicated pre-output sweep before saving.
