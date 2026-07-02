# Literary Tic Catalog (bootstrap seed)

A reference catalog of LLM-typical literary tics — constructions that signal AI
prose even when each instance is grammatically correct and individually
defensible. Most fail through repetition: one instance is voice; a dozen is a
verbal tell.

**This file is a bootstrap seed, not a normative gate.** The living, normative
tic catalog for a book is `book/tic-ledger.md`, which `/authorkit.review`
(Pass 2 — AI-Tic Audit) maintains by blind contrast against the fixed voice
origin — discovering the tics the *current* model actually produces in *this*
book, tracking their per-chapter trends, and retiring shapes that stop
occurring. This seed's role is limited to review's first run on a book: its
high-signal patterns become the ledger's initial `Status: seed` hypotheses,
which the discovery pass then confirms or retires. Once `book/tic-ledger.md`
exists, the ledger — not this file — is what review checks and what severity is
mapped from.

**Never load this file while drafting.** Pattern descriptions in the drafting
context prime the constructions they prohibit; tic knowledge reaches generation
only as contrastive pairs in `book/voice-pairs.md` (see the shared guardrails'
*Tic Ledger & Voice Pairs* and *Voice Conditioning Protocol*).

## Constitution Waivers

If `.authorkit/memory/constitution.md` (or `book/style-anchor.md`'s **Avoid** /
**Imagery Density** sections) explicitly sanctions a pattern listed here — by
naming it by example or description with a voice/genre rationale — review
records the waiver on the matching `book/tic-ledger.md` entry's `Waiver:` field
and reports (never flags) the shape (e.g., *"Polysyndeton waived by
constitution §II (McCarthy-inflected register)"*). A constitution can also ban
a shape outright; treat that as binding regardless of trend. Vague register
language ("literary style") is neither a waiver nor a ban.

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

### 14. Vague interiority — "something" as emotional load-bearer

Emotion gestured at through an unnamed "something" instead of a named feeling
or a concrete physical fact.

Examples:
- "something in her chest loosened"
- "something passed between them"
- "something like grief, but not grief"
- "a feeling she couldn't name"

**Why it fails:** Simulates depth by refusing specificity. Once a book it
reads as restraint; once a scene it reads as evasion. The "something like X,
but not X" variant is pattern 13 wearing a coat.

**Fix:** name the feeling, or show its physical fact instead.
**Budget:** at most **two per chapter** combined. The "a feeling (s)he
couldn't name" family ("couldn't quite name," "had no name for"):
**budget 0**.

### 15. Stock somatic beats

The same small set of body responses rotating as emotional shorthand.

Examples:
- "her chest tightened" / "his stomach dropped" / "her breath caught"
- "his heart hammered" / "her jaw clenched" / "his knuckles whitened"
- Sibling form — agentive body parts: "her hand found the rail," "his eyes
  found hers"

**Why it fails:** Each beat is fine alone. In rotation, emotion becomes
physiological boilerplate — the reader gets a vitals readout instead of a
person.

**Budget:** at most **three per 1,000 words** combined across the stock set.
"Released a breath (s)he didn't know (s)he'd been holding" (any phrasing):
**budget 0** — it is the single most recognizable AI-prose cliché.

### 16. Appositive thematic tail

A concrete sentence with an abstraction bolted on as a trailing appositive.

Examples:
- "She set the cup down between them, a small truce."
- "He signed his name, the weight of it settling."
- "…, a kind of answer."
- "…, the shape of an apology."

**Why it fails:** Bolts the theme onto the sentence so the reader cannot miss
it. Serial use turns every action into a captioned museum exhibit. Tell-words:
"a kind of," "the shape of," "the weight of."

**Fix:** trust the concrete sentence; cut the caption.
**Budget:** at most **two per chapter**, never in consecutive paragraphs.

### 17. Triadic litany with the abstract third slot

Rule-of-three structures — anaphoric sentences or in-sentence lists — where
the third item escalates from concrete to abstract.

Examples:
- "She had packed his books. She had packed his letters. She had packed the
  years."
- "It was in the floorboards, in the curtains, in the quiet between them."

**Why it fails:** Concrete-concrete-abstract is the model's default rhetorical
figure. Litanies repeated across a chapter become a metronome.

**Budget:** at most **one anaphoric litany per chapter**; lists whose third
item goes abstract, at most **two per chapter**.

### 18. Personified atmosphere

Ambient nouns given agency whenever characters stop talking.

Examples:
- "the silence stretched" / "the quiet pressed in"
- "the air thickened" / "darkness pooled"
- "the silence settled over the room"

**Why it fails:** It is the model's default scene-glue between dialogue beats.
The room starts acting so the characters don't have to.

**Budget:** at most **two per 1,000 words**, and never the same noun-verb pair
twice in a chapter.

### 19. Epiphany cadence closer

Chapter endings that land on a quiet thematic zoom-out coda of earned wisdom.

Examples:
- "And for the first time in a long time, that was enough."
- "Maybe that was the point."
- "It wasn't forgiveness. But it was a start." (also trips pattern 13)

**Why it fails:** One is an ending; eight is a stamp. When every chapter
closes on the same cadence, the book audibly ends the same way over and over.

**Budget:** "for the first time" at most **one per chapter**. Zoom-out coda
endings on no more than **two consecutive chapters** — the consecutive-chapter
check belongs to manuscript-wide review, since no single chapter trips it.

### 20. Em-dash interruption density

Appositive interruptions and dramatic dashes as the default rhythm move.

Example:
- "She reached for the letter — the one he'd left — and stopped."

**Why it fails:** The em-dash appositive is the model's favorite punctuation
gesture and the most publicly cited AI tell. In density it gives prose a
breathless, over-qualified rhythm. It is also legitimate style in many hands —
which is exactly what the constitution waiver mechanism is for.

**Budget:** at most **four per 1,000 words**, no more than **two in a single
paragraph**, unless the constitution names the em-dash as a voice choice.

### 21. Composure beats and trailing minimizers — the "let it go" family

Narration that closes a beat by performing the character's (or the narrator's
own) self-possession, or by measuring how little was said, needed, or given.

Examples — composure form:
- "she named it for what it was and let it go"
- "he let that sit" / "filing it somewhere behind his eyes"
- "she took it as no more than her due"
- "whatever she was reckoning she kept behind her teeth"

Examples — trailing-minimizer form:
- "…and left it there" / "…and left it at that"
- "and that was the whole of it" / "and that was all" / "and nothing more"
- "all the answer she was going to get"
- "and not one gesture more"

**Why it fails:** Each instance is defensible; as a recurring closer it reads
as poise instead of feeling — prose commenting on its own restraint. It is one
of the highest-signal AI tells in literary fiction precisely because it
survives line-level review: every sentence is grammatical, economical, and
"good." High-signal pattern.

**Fix:** close beats on an action, a line of speech, or a plain statement.
Character-voiced terseness in dialogue ("Your call. The whole of it.") is
exempt — the ban is on narration measuring itself.
**Budget:** at most **one per chapter** as a narration beat-closer, never the
same phrasing twice in a manuscript.

### 22. Decoder narration — POV-as-analyst

The viewpoint character continuously converting observation into filed
conclusions.

Examples:
- "she understood X as Y" / "Zoe understood the silence as practice"
- "she came to understand that…"
- "she read the room as…" / "the look of a woman moving a token from one
  string to another"

**Why it fails:** Each decode is plausible characterization; in density the
POV stops experiencing the scene and starts annotating it, and every
observation arrives pre-interpreted. The reader is handed conclusions instead
of evidence.

**Fix:** let the character observe, feel, wonder, guess, or *ask* — move the
interpretation into dialogue, a named emotion, or an open question.
**Budget:** at most **two per chapter**.

### 23. Looping self-echo — antimetabole / anadiplosis / confirming echo

A phrase repeated within or across clauses — inverted, handed off, or confirmed — to
manufacture gravitas the sentence has not earned. Three sibling forms:

- **Antimetabole** (invert and repeat): "for a man who weighs his nods has learned that
  nods are weighed."
- **Anadiplosis** (end-word becomes the next clause's start): "because that was his trade
  and his trade was to trust nothing he had not summed himself."
- **Confirming echo / competence tag** (posit a rare skill as a condition, then immediately
  confirm the character has it): "a man might read the health of the whole world in those
  rolls if he knew the hand, and Crescens knew the hand."

**Why it fails:** the rhetorical loop *sounds* like hard-won wisdom, but the repetition is
doing the work an image or an action should. It is one of the highest-signal markers of
LLM literary pastiche (McCarthy / King-James inflection), and it survives line-level review
because each clause is grammatical and "resonant."

**Fix:** say the thing once, plainly, and trust it; or replace the loop with a concrete
detail. **Budget:** at most **one per chapter** across all three forms; the competence-tag
form ("…if he knew X, and he knew X") is **budget 0**.

### 24. Creed / trade-maxim characterization

Narration summing a character up through a portable, essential-truth maxim — usually about
their profession or fundamental nature — instead of showing them act.

Examples:
- "his trade was to trust nothing he had not summed himself"
- "to record what was and add nothing to it was the whole of his trade"
- "she was a woman who kept her debts in her head and her grief in her hands"

**Why it fails:** it is the aphoristic-character gesture in narration form — cousin of
pattern 1 (the relative-clause version) and pattern 10 (aphorism in dialogue). One is a
thesis statement; a habit of them turns every figure into a proverb about themselves. The
"…was the whole of his trade/work/life" closer also trips pattern 21 (trailing minimizer).

**Fix:** let the character's actions and choices establish the creed; cut the summary.
**Budget:** at most **one per character per chapter**, and **never** the "…was the whole of
his X" closer absent an explicit constitution waiver.

### 25. Participial / absolute-phrase scene-setting openers

Sentences (especially paragraph or scene openers) led by a stacked present-participle or
absolute phrase instead of a subject and verb.

Examples:
- "Standing at the window, she watched the harbour fill."
- "Hands trembling, he set the cup down."
- "The lamp guttering, the room half in shadow, they waited."

**Why it fails:** one is fine; as a default opening move it gives every beat the same
front-loaded, slightly breathless shape, and the participle often dangles or implies a
simultaneity that isn't real.

**Budget:** at most **three per 1,000 words**, and no more than **two consecutive**
sentences or paragraph openers built this way.

### 26. Correlative simultaneity — "at once X and Y" / "both X and Y"

Rendering mixed feeling through a correlative pair rather than a concrete, particular
reaction.

Examples:
- "she felt at once afraid and exhilarated"
- "his voice was both gentle and final"
- "it was at once an apology and a threat"

**Why it fails:** it is the model's default formula for ambivalence — tidy, abstract, and
interchangeable across characters and scenes. It names the poles instead of dramatizing the
tension.

**Fix:** show the contradiction in behaviour or pick the dominant note. **Budget:** at most
**two per chapter**.

### 27. Partitioned interiority — "part of her" / "some part of him"

Locating feeling in a fractional self instead of naming it or showing it.

Examples:
- "part of her wanted to stay"
- "some part of him already knew"
- "a small part of her hated him for it"

**Why it fails:** sibling of pattern 14 (vague "something" interiority). It simulates
psychological depth by splitting the character into committee members, and the device
becomes a verbal habit for any moment of hesitation.

**Fix:** name the feeling, or show the hesitation as an action or a beat of dialogue.
**Budget:** at most **two per chapter**.

## How to Apply

**Seeding only** (`/authorkit.review` Pass 2, first run on a book): when
`book/tic-ledger.md` does not exist, create it from
`.authorkit/templates/tic-ledger-template.md` and seed `Status: seed` entries
from the high-signal patterns here (7, 13, 21, 22, 23, 24 and the zero-budget
forms of 3, 14, 15, 23, 24). Seeds are hypotheses: the blind discovery pass
confirms the ones this book's drafts actually exhibit (they become `active`
with a quoted instance and an origin counter-example) and retires the rest
after 2 unconfirmed reviews. After seeding, this file is out of the loop.

**Why the ledger outranks this catalog.** These budgets catch *known* patterns
of the models this file was written against; they do not certify fidelity, and
a chapter can respect every budget here and still read as AI-authored against
the book's own corpus — typically through poised low-affect cadence, silent POV
analysis where the corpus uses conversation, or restraint-measuring closers
(patterns 21–22). The ledger exists precisely because tics are model- and
book-specific: discovery by contrast against the fixed origin finds what this
list cannot name in advance, and the trend/decay lifecycle keeps the ledger
describing the model currently drafting. *(Lesson from the Ab Imo Pectore
CH13–CH15 fidelity passes, 2026-06-11.)*

**The budgets below are seed-calibration data, not live thresholds.** Severity
in review is density/trend-based and defined in the review prompt; the per-1,000
budgets here indicate how tolerant a pattern's *seed* should be when judging
whether a discovered recurrence is deliberate voice or a tell.

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
| 14 | "Something" vague interiority | 2 per chapter; "couldn't name" variants 0 |
| 15 | Stock somatic beats | 3 per 1,000 words; breath-holding cliché 0 |
| 16 | Appositive thematic tail | 2 per chapter, non-consecutive paragraphs |
| 17 | Triadic litany / abstract third slot | 1 litany per chapter; 2 abstract-third lists |
| 18 | Personified atmosphere | 2 per 1,000 words; no repeated noun-verb pair |
| 19 | Epiphany cadence closer | "for the first time" 1 per chapter; ≤2 consecutive coda endings |
| 20 | Em-dash interruptions | 4 per 1,000 words, max 2 per paragraph |
| 21 | Composure beats / trailing minimizers | 1 per chapter as narration closer; dialogue exempt; high-signal |
| 22 | Decoder narration ("understood X as Y") | 2 per chapter |
| 23 | Looping self-echo (antimetabole/anadiplosis/confirming echo) | 1 per chapter; competence-tag form 0; high-signal |
| 24 | Creed / trade-maxim characterization | 1 per character per chapter; "the whole of his X" closer 0; high-signal |
| 25 | Participial / absolute-phrase openers | 3 per 1,000 words; max 2 consecutive |
| 26 | Correlative simultaneity ("at once X and Y") | 2 per chapter |
| 27 | Partitioned interiority ("part of her") | 2 per chapter |
