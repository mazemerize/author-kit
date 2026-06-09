# Literary Tic Catalog

A catalog of LLM-typical literary tics — constructions that signal AI prose even
when each instance is grammatically correct and individually defensible. Most
fail through repetition: one instance is voice; a dozen is a verbal tell.

This catalog is normative for any command that generates manuscript prose or
audits it. Treat the budgets as defaults; honor explicit constitution overrides.

## Constitution Override

If `.authorkit/memory/constitution.md` (or `book/style-anchor.md`'s **Avoid** /
**Imagery Density** sections) explicitly permits a pattern listed here — by
naming the pattern, raising its budget, or stating a voice/genre rationale —
defer to the constitution. Note the override at the top of any review that
involves the affected pattern (e.g., *"Polysyndeton waived by constitution
§II (McCarthy-inflected register)"*). Absent an explicit waiver, the budgets
below apply.

A book's constitution can also tighten a budget (e.g., zero negations). Treat
tightening as binding; honor it without further checks.

## The Patterns

### 1. "The [noun] of a [noun] who [past habitual]" — character-by-aphorism

Constructing a character or object through a relative clause about what kind
of person/thing they are.

Examples:
- "the eyes of a man who had stopped sleeping years ago"
- "the unhurried movement of a man who had done this before"
- "the closed face of a woman who had read more reports than she trusted"

**Why it fails:** Sounds literary on first pass. By the third instance, every
character is being introduced through the same syntactic gesture, and the
prose reads as authored by a model trained on Cormac McCarthy.

**Budget:** at most **one per character per chapter**.

### 2. "The way [X verbs]" / "as though [Y]" — comparison-as-default

Subordinate-clause comparisons substituting for direct description.

Examples:
- "wind moving through the fronds the way wind moves through wheat"
- "he stood at the rail the way a man stands at a rail when he has done the approach before"
- "as though distance were itself a solvent the silence answered to"

**Why it fails:** Each comparison is reasonable. Cumulatively, every observation
arrives wrapped in poetic simile and the prose loses the texture of direct
attention.

**Budget:** at most **three "the way / as though" comparisons per 1,000 words**.

### 3. "Particular" as empty specifier

The word does no work; it signals significance without naming what is
significant.

Examples:
- "the sun went down in a particular colour"
- "the lights came up in a particular discipline"
- "a knot tied in a particular pattern by a particular hand"

**Why it fails:** "Particular" is a verbal shrug pretending to be a verbal point.

**Fix:** name the thing, or drop the word entirely. **Budget: 0** unless the
constitution waives.

### 4. Denial-as-description ("did not X" / "had not Y")

Describing through negation rather than positive observation.

Examples:
- "she did not smile"
- "he did not raise his voice"
- "she had not needed to ask"

**Why it fails:** Each negation is fine. Two dozen of them in 5,000 words make
restraint the chapter's mannerism.

**Budget:** at most **one per ~250 words**. Prefer positive description
("she kept her face level" rather than "she did not smile").

### 5. "Without [X]" stacked as modifier — sibling of #4

The positive form of denial, same effect.

Examples:
- "without ceremony" / "without a hail" / "without a word"
- "without unkindness" / "without intent"

**Budget:** counted together with #4. Combined density above one per ~250 words
trips the audit.

### 6. Overprecious time-units

Poetic measurements of duration that become verbal habits.

Examples:
- "for the length of one held breath"
- "for the space of a heartbeat"
- "for a long moment"
- "for the time it took to draw a single breath"

**Budget:** at most **one per chapter** across all variants. Replace others
with concrete duration or a beat of action.

### 7. Reflexive deepening — "She did X. She did X again, more X, the way one Xs"

Repeating an action with each iteration claiming more honesty / depth /
meaning than the last, often closed with a "the way one [verbs]" gloss.

Example:
- "She named it gone. She had named it gone before. She named it gone again,
  more honestly, the way one names a thing more honestly the second time."

**Why it fails:** Telegraphs that the model is reaching for poetic effect. The
"the way one [verbs]" gloss is the single most LLM-flavoured construction in
literary AI prose.

**Budget: 0.** Eliminate the gloss. Trust the repetition or drop it.

### 8. Single-sentence paragraphs in clusters

Used singly for emphasis; in clusters, becomes a metronome.

Examples:
- Three consecutive one-sentence paragraphs
- A closing sequence of five short paragraphs, each a single line
- The same one-line sentence repeated as its own paragraph two or three times
  in close succession

**Budget:** at most **two consecutive one-sentence paragraphs**. After that,
combine or expand.

### 9. "Perhaps [N]" / hedged numerics

Hedging numbers to suggest POV-bound uncertainty.

Examples:
- "of perhaps forty"
- "perhaps fifty"
- "perhaps a boy, perhaps a girl"

**Budget:** at most **two per chapter**.

### 10. Aphoristic dialogue — characters speaking in epigrams

Dialogue that sermonizes inside the line; dialogue trying to be quotable.

Examples:
- "It held because they let it hold. That is what it means when the cover
  holds. Remember it."
- "The trouble with the water is that it always remembers."
- "Some things are like that."

**Why it fails:** Characters stop speaking and start delivering theme. The
"Remember it" / "That is what it means when X" closers are the worst form.

**Fix:** strip the gloss. Let the line do its work without the underline.
**Budget:** at most **one aphoristic line per speaking character per chapter**,
and never the "Remember it" / "That is what it means" closer absent an
explicit constitution waiver.

### 11. Polysyndeton — "X and Y and Z and W"

McCarthy-inflected cumulative "and"-builds.

Example:
- "the canvas worked on her new tack and the wake settled and the hull came
  on and the basin went on"

**Budget:** at most **one per chapter** unless the constitution names
polysyndeton as a deliberate voice choice (then unlimited, but track for
cross-chapter consistency).

### 12. Default diminutive qualifiers — "small," "thin," "quiet"

Placeholder words the model reaches for when avoiding a more specific adjective.

Examples:
- "small reluctance" / "small sounds" / "small recognition"
- "thin thread" / "thin man" / "quiet moment"

**Fix:** count instances. **Budget:** replace at least half with specific
descriptors or strike them. Soft cap: **no more than five combined per 1,000
words**.

### 13. Negation-correction two-beat ("not X, but Y" / "It did not X. It X'd Y")

The single most identifiable AI-prose construction in literary fiction. Negate,
then recast.

Examples:
- "It was not anger. It was the look of someone calculating cost."
- "She did not run. She walked, with the gait of someone who knew they were
  being watched."
- "Not the green of the lagoon, but a thinner colour."

**Fix:** lead with the positive. Drop the negated clause entirely.
**Budget:** at most **two per chapter** unless the constitution waives.

## How to Apply

**At generation time** (`/authorkit.write` draft / revise / passage help):
- Internalize the budgets before writing. Don't draft tic-rich prose and clean
  it up after — write within budget on the first pass.
- The "Style match pass" and "Quality self-check" steps explicitly count
  instances of patterns 1, 7, 10, 13 (the zero / near-zero budgets) and the
  high-density patterns (2, 4+5, 12) per 1,000 words before saving.
- If a constitution waiver is in effect, name it in the run report so the
  author sees which budget was bypassed.

**At review time** (`/authorkit.review`):
- Count instances per pattern, per chapter (and per 1,000 words for density
  patterns).
- Compare against the budgets. Patterns over budget become findings under the
  **LLM Tic Audit** dimension.
- Cite specific line references (or paragraph-anchored quotes) for every flag.
- Severity triage lives in the review prompt, not here: this catalog owns the
  patterns and budgets; the consuming command maps overages onto its own
  severity ladder.
- Manuscript-wide drift: track cumulative density across drafted chapters —
  a pattern can sit at budget in every chapter and still mark voice drift in
  aggregate. The cross-chapter threshold is defined in the review prompt.

**Constitution waivers must be explicit.** A vague "literary register" line in
the constitution does not waive a pattern. The constitution must name the
pattern by number, by example, or by description ("polysyndeton is part of
the voice"). Otherwise the budgets apply.

## Quick-reference budget table

| # | Pattern | Default budget |
|---|---------|----------------|
| 1 | "The [noun] of a [noun] who…" | 1 per character per chapter |
| 2 | "the way…" / "as though…" | 3 per 1,000 words |
| 3 | "particular" as specifier | 0 |
| 4+5 | "did not X" / "without X" combined | 1 per ~250 words |
| 6 | Overprecious time-units | 1 per chapter |
| 7 | Reflexive deepening + "the way one Xs" gloss | 0 |
| 8 | Single-sentence paragraph clusters | 2 consecutive max |
| 9 | "Perhaps [N]" hedged numerics | 2 per chapter |
| 10 | Aphoristic dialogue | 1 per speaking character per chapter |
| 11 | Polysyndeton "and…and…and" | 1 per chapter |
| 12 | "small / thin / quiet" qualifiers | 5 per 1,000 words combined |
| 13 | Negation-correction two-beat | 2 per chapter |
