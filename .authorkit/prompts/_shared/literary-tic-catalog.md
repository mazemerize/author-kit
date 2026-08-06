# Literary Tic Catalog — shapes (bootstrap seed)

A reference catalog of LLM-typical literary tics — constructions that signal AI
prose even when each instance is grammatically correct and individually
defensible. Most fail through repetition: one instance is voice; a dozen is a
verbal tell.

**This file defines the *shapes* only — it is language-neutral.** How a shape is
realized in a given language (its examples, its exact strings, its lexical
canon) lives in that language's pack, `tic-catalog-<lang>.md`, next to this
file. English is a language like any other here: its realizations are in
`tic-catalog-en.md`, not in this file. See *Language Scope & Packs*.

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

**Never load this file while drafting**, nor any language pack. Pattern
descriptions in the drafting context prime the constructions they prohibit; tic
knowledge
reaches generation only as contrastive pairs in `book/voice-pairs.md` (see the
shared guardrails' *Tic Ledger & Voice Pairs* and *Voice Conditioning
Protocol*).

## Constitution Waivers

If `.authorkit/memory/constitution.md` (or `book/style-anchor.md`'s **Avoid** /
**Imagery Density** sections) explicitly sanctions a pattern listed here — by
naming it by example or description with a voice/genre rationale — review
records the waiver on the matching `book/tic-ledger.md` entry's `Waiver:` field
and reports (never flags) the shape (e.g., *"Polysyndeton waived by
constitution §II (McCarthy-inflected register)"*). A legacy waiver that names a
pattern *number* from this catalog ("waive pattern 13") remains binding —
resolve the number here. A constitution can also ban a shape outright; treat
that as binding regardless of trend. Vague register language ("literary style")
is neither a waiver nor a ban.

## Pattern Classes & Weighting

Patterns 28+ carry a **`Class:`** field; patterns 1–27 predate it and are all
implicitly `constructional`. The classes calibrate how much weight a match
deserves — three principles from the published detection research (stylometric
studies, Wikipedia's *Signs of AI writing* field guide):

- **Density over presence.** A single instance of any non-zero-budget shape is
  voice, not a tell. The signal is clustering — several shapes in one
  paragraph, or one shape recurring across a manuscript. Budgets, the cluster
  rule, and the tic-load index — the *mean* budget utilization across tracked
  shapes, so that tracking more shapes never by itself tightens the gate
  (review Pass 2's severity mapping) — encode this; never flag an isolated
  under-budget instance as if it were diagnostic. A budget set at or below the
  origin's own measured rate for that shape is mis-set: it penalizes prose for
  sounding like the book's own voice.
- **Structure over vocabulary.** `structural` and `constructional` tells
  (clause symmetry, scene-shape repetition, negation-correction, tailing
  appositives) are stable across model generations *and across languages*;
  `lexical` tells rotate fast — "delve" was the canonical English tell of
  2023–24 and has already faded. Entries marked **`Volatility: high`** are
  never seeded into a new ledger by default, are weighted lower in severity
  judgment, and retire faster; they enter a book's ledger only when blind
  discovery confirms them in *this* book's drafts.
- **`phrase`-class zero-budget forms are exact strings.** They are verified by
  literal search (Grep, case-insensitive, with pronoun/tense variants) in
  review Step B's targeted sweep — not by read-through alone. This is the one
  place mechanical matching outperforms model judgment: these are
  training-corpus clichés, stable across models precisely because they come
  from the corpus, not the model. **The strings themselves are per-language and
  live in the packs**; this file only records which shapes have them.

## Language Scope & Packs

A tic has two layers, and they do not travel together:

- **The shape** — the structural or rhetorical move the model reaches for. This
  is an attractor of the *model*, not of any language, and it surfaces wherever
  the model writes. The 47 entries below are shapes.
- **The realization** — the words, strings, and idioms the shape takes in one
  language. These are per-language and live in
  `.authorkit/prompts/_shared/tic-catalog-<lang>.md`.

Every book seeds from **this file plus its own language pack**, resolved from
`BOOK_LANGUAGE` (the shared guardrails' *Language Protocol*; absent ⇒ `en-US`)
on the **primary subtag** — `en-US`/`en-GB`/`English` → `en`,
`fr-FR`/`fr-CA`/`français` → `fr`. English is not a special case: its
realizations are in `tic-catalog-en.md`.

Packs shipped today: **`en`**, **`fr`**.

Three rules follow from the split:

- **Never seed a realization from the wrong language.** An English corpus
  cliché cannot occur in French prose, so sweeping it costs a search and buys
  nothing — and seeding it as a tracked entry is worse than useless: a
  permanently-zero non-zero-budget entry joins `N` in the tic-load mean and
  drags the index down, which is exactly the coupling that index exists to
  remove.
- **No pack for the book's language?** Seed the shapes alone and say so in the
  review. The first chapters then run with no language-specific string sweep
  while blind discovery builds the ledger from this book's own drafts — the
  designed fallback, not a failure. Contributing a pack is the fix: copy an
  existing one, keep the section shape, replace the realizations.
- **Punctuation-shaped budgets are read against the language's own
  conventions.** Where the em-dash or guillemets *mark dialogue* (French,
  Spanish, Russian, Polish…), dialogue-marking punctuation is typography, not a
  tic; only interruptive marks inside narration count. Each pack states its own
  conventions.

## The Patterns

### 1. Character-by-aphorism — definition through a relative clause

Constructing a character or object through a relative clause about what kind
of person/thing they are, rather than through what they do.

**Why it fails:** Sounds literary on first pass. By the third instance, every
character is being introduced through the same syntactic gesture, and the
prose reads as authored by a model trained on Cormac McCarthy.

**Budget:** at most **one per character per chapter**.

### 2. Comparison-as-default — the subordinate-clause simile

Subordinate-clause comparisons ("the way X does Y", "as though Z") substituting
for direct description.

**Why it fails:** Each comparison is reasonable. Cumulatively, every observation
arrives wrapped in poetic simile and the prose loses the texture of direct
attention.

**Budget:** at most **three comparisons per 1,000 words**.

### 3. Empty specifier — the significance marker that names nothing

A modifier that signals something is meaningful without naming what is
meaningful; it does no descriptive work.

**Why it fails:** it is a verbal shrug pretending to be a verbal point.

**Fix:** name the thing, or drop the word entirely. **Budget: 0** for the
language's canonical form(s) unless the constitution waives.

### 4. Denial-as-description

Describing through negation — what did not happen, was not said, was not
needed — rather than through positive observation.

**Why it fails:** Each negation is fine. Two dozen of them in 5,000 words make
restraint the chapter's mannerism.

**Budget:** at most **one per ~250 words**. Prefer positive description.

### 5. Privative modifier stacked as description — sibling of #4

The positive form of denial: a "without X" modifier used as the default
descriptive move. Same effect.

**Budget:** counted together with #4. Combined density above one per ~250 words
trips the audit.

### 6. Overprecious time-units

Poetic measurements of duration — held breaths, heartbeats, long moments —
that become verbal habits.

**Budget:** at most **one per chapter** across all variants. Replace others
with concrete duration or a beat of action.

### 7. Reflexive deepening — repetition claiming more depth each time

Repeating an action with each iteration claiming more honesty / depth /
meaning than the last, often closed with a generalizing gloss ("the way one
does X when…").

**Why it fails:** Telegraphs that the model is reaching for poetic effect. The
generalizing gloss is the single most LLM-flavoured construction in literary AI
prose.

**Budget: 0.** Eliminate the gloss. Trust the repetition or drop it.

### 8. Single-sentence paragraphs in clusters

Used singly for emphasis; in clusters, becomes a metronome.

**Budget:** at most **two consecutive one-sentence paragraphs**. After that,
combine or expand.

### 9. Hedged numerics

Hedging numbers ("perhaps forty") to suggest POV-bound uncertainty.

**Budget:** at most **two per chapter**.

### 10. Aphoristic dialogue — characters speaking in epigrams

Dialogue that sermonizes inside the line; dialogue trying to be quotable.

**Why it fails:** Characters stop speaking and start delivering theme. The
underlining closers ("Remember it", "That is what it means when X") are the
worst form.

**Fix:** strip the gloss. Let the line do its work without the underline.
**Budget:** at most **one aphoristic line per speaking character per chapter**,
and never the language's underlining closer absent an explicit constitution
waiver.

### 11. Polysyndeton — cumulative conjunction builds

McCarthy-inflected "X and Y and Z and W" cumulative builds.

**Budget:** at most **one per chapter** unless the constitution names
polysyndeton as a deliberate voice choice (then unlimited, but track for
cross-chapter consistency).

### 12. Default diminutive qualifiers

Placeholder adjectives the model reaches for when avoiding a more specific one
— the language's equivalents of "small", "thin", "quiet".

**Fix:** count instances. **Budget:** replace at least half with specific
descriptors or strike them. Soft cap: **no more than five combined per 1,000
words**.

### 13. Negation-correction two-beat — negate, then recast

The single most identifiable AI-prose construction in literary fiction: deny a
reading, then supply the "true" one ("not X, but Y"; "It was not X. It was Y").
The additive variant ("not just X, but Y") is the same hinge, manufacturing an
illusion of insight without adding information.

**Fix:** lead with the positive. Drop the negated clause entirely.
**Budget:** at most **two per chapter** unless the constitution waives; the
additive form counts toward the same budget.

### 14. Vague interiority — an unnamed placeholder as emotional load-bearer

Emotion gestured at through an unnamed "something" instead of a named feeling
or a concrete physical fact.

**Why it fails:** Simulates depth by refusing specificity. Once a book it
reads as restraint; once a scene it reads as evasion. The "something like X,
but not X" variant is pattern 13 wearing a coat.

**Fix:** name the feeling, or show its physical fact instead.
**Budget:** at most **two per chapter** combined. The unnameable-feeling family
(the language's "a feeling she couldn't name" forms): **budget 0**.

### 15. Stock somatic beats

The same small set of body responses rotating as emotional shorthand, plus the
sibling form where body parts act on their own.

**Why it fails:** Each beat is fine alone. In rotation, emotion becomes
physiological boilerplate — the reader gets a vitals readout instead of a
person.

**Budget:** at most **three per 1,000 words** combined across the stock set;
the language's single most recognizable somatic cliché: **budget 0**.

### 16. Appositive thematic tail

A concrete sentence with an abstraction bolted on as a trailing appositive.

**Why it fails:** Bolts the theme onto the sentence so the reader cannot miss
it. Serial use turns every action into a captioned museum exhibit.

**Fix:** trust the concrete sentence; cut the caption.
**Budget:** at most **two per chapter**, never in consecutive paragraphs.

### 17. Triadic litany with the abstract third slot

Rule-of-three structures — anaphoric sentences or in-sentence lists — where
the third item escalates from concrete to abstract.

**Why it fails:** Concrete-concrete-abstract is the model's default rhetorical
figure. Litanies repeated across a chapter become a metronome. The same
applies to suspiciously clean tricolons with parallel rhythm or alliteration —
real human triplets are lumpier and less symmetrical.

**Budget:** at most **one anaphoric litany per chapter**; lists whose third
item goes abstract, at most **two per chapter**; polished parallel tricolons
count toward the same budget.

### 18. Personified atmosphere

Ambient nouns — silence, air, darkness — given agency whenever characters stop
talking.

**Why it fails:** It is the model's default scene-glue between dialogue beats.
The room starts acting so the characters don't have to.

**Budget:** at most **two per 1,000 words**, and never the same noun-verb pair
twice in a chapter.

### 19. Epiphany cadence closer

Chapter endings that land on a quiet thematic zoom-out coda of earned wisdom.

**Why it fails:** One is an ending; eight is a stamp. When every chapter
closes on the same cadence, the book audibly ends the same way over and over.

**Budget:** the language's canonical epiphany marker ("for the first time"),
at most **one per chapter**. Zoom-out coda endings on no more than **two
consecutive chapters** — the consecutive-chapter check belongs to
manuscript-wide review, since no single chapter trips it.

### 20. Em-dash interruption density

Appositive interruptions and dramatic dashes as the default rhythm move.

**Why it fails:** The em-dash appositive is the model's favorite punctuation
gesture and the most publicly cited AI tell. In density it gives prose a
breathless, over-qualified rhythm. It is also legitimate style in many hands —
which is exactly what the constitution waiver mechanism is for.

**Budget:** at most **four per 1,000 words**, no more than **two in a single
paragraph**, unless the constitution names the em-dash as a voice choice.

*Typography-conditional (see Language Scope & Packs).* In languages where the
em-dash opens dialogue, a dialogue-marking dash is punctuation, not a gesture:
count only interruptive dashes inside narration. Applying the English budget to
dash-led dialogue flags the language's standard typography as a tic and would
gate every correctly-typeset chapter.

### 21. Composure beats and trailing minimizers

Narration that closes a beat by performing the character's (or the narrator's
own) self-possession, or by measuring how little was said, needed, or given.

**Why it fails:** Each instance is defensible; as a recurring closer it reads
as poise instead of feeling — prose commenting on its own restraint. It is one
of the highest-signal AI tells in literary fiction precisely because it
survives line-level review: every sentence is grammatical, economical, and
"good." High-signal pattern.

**Fix:** close beats on an action, a line of speech, or a plain statement.
Character-voiced terseness in dialogue is exempt — the ban is on narration
measuring itself.
**Budget:** at most **one per chapter** as a narration beat-closer, never the
same phrasing twice in a manuscript. The language's summary-closer boilerplate
family: **budget 0** — greppable exact strings (see pattern 29).

### 22. Decoder narration — POV-as-analyst

The viewpoint character continuously converting observation into filed
conclusions.

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

- **Antimetabole** — invert and repeat.
- **Anadiplosis** — the end-word becomes the next clause's start.
- **Confirming echo / competence tag** — posit a rare skill as a condition,
  then immediately confirm the character has it.

**Why it fails:** the rhetorical loop *sounds* like hard-won wisdom, but the repetition is
doing the work an image or an action should. It is one of the highest-signal markers of
LLM literary pastiche (McCarthy / King-James inflection), and it survives line-level review
because each clause is grammatical and "resonant."

**Fix:** say the thing once, plainly, and trust it; or replace the loop with a concrete
detail. **Budget:** at most **one per chapter** across all three forms; the competence-tag
form is **budget 0**.

### 24. Creed / trade-maxim characterization

Narration summing a character up through a portable, essential-truth maxim — usually about
their profession or fundamental nature — instead of showing them act.

**Why it fails:** it is the aphoristic-character gesture in narration form — cousin of
pattern 1 (the relative-clause version) and pattern 10 (aphorism in dialogue). One is a
thesis statement; a habit of them turns every figure into a proverb about themselves. The
totalizing closer ("…was the whole of his trade") also trips pattern 21 (trailing
minimizer).

**Fix:** let the character's actions and choices establish the creed; cut the summary.
**Budget:** at most **one per character per chapter**, and **never** the totalizing closer
absent an explicit constitution waiver.

### 25. Participial / absolute-phrase scene-setting openers

Sentences (especially paragraph or scene openers) led by a stacked present-participle or
absolute phrase instead of a subject and verb.

**Why it fails:** one is fine; as a default opening move it gives every beat the same
front-loaded, slightly breathless shape, and the participle often dangles or implies a
simultaneity that isn't real. The mirror form — a sentence that *ends* by bolting on a
vague participial clause to manufacture significance — is the same tic tailing instead of
fronting. So is the habitual fronted-adverbial opener.

**Budget:** at most **three per 1,000 words** counted across fronted, tailing, and
fronted-adverbial forms, and no more than **two consecutive** sentences or paragraph
openers built this way.

### 26. Correlative simultaneity — the correlative pair for mixed feeling

Rendering mixed feeling through a correlative pair ("at once X and Y", "both X and Y")
rather than a concrete, particular reaction.

**Why it fails:** it is the model's default formula for ambivalence — tidy, abstract, and
interchangeable across characters and scenes. It names the poles instead of dramatizing the
tension.

**Fix:** show the contradiction in behaviour or pick the dominant note. **Budget:** at most
**two per chapter**.

### 27. Partitioned interiority — feeling located in a fractional self

Locating feeling in a part of the character ("part of her wanted to…") instead of naming it
or showing it.

**Why it fails:** sibling of pattern 14 (vague placeholder interiority). It simulates
psychological depth by splitting the character into committee members, and the device
becomes a verbal habit for any moment of hesitation.

**Fix:** name the feeling, or show the hesitation as an action or a beat of dialogue.
**Budget:** at most **two per chapter**.

### 28. Vocabulary canon — the model's favoured word list of the moment

**Class:** lexical · **Volatility: high**

Words overused to the point of self-parody in AI prose. **The list is
per-language and rotates model-to-model and season-to-season** — "delve" was
the English canon of 2023–24 and has largely faded — so a pack's list is a
living sample, never a fixed ban list.

**Why it fails:** each word is legitimate; density betrays the statistical
mean. Because the list goes stale fast, weight this entry below the
structural patterns — a manuscript can be scrubbed of every canon word and
still read as AI-authored.

**Fix:** replace with the plain word or a specific image.
**Budget:** at most **two canon hits per 1,000 words**. Never seeded by
default — enters a ledger only via blind discovery.

### 29. Stock-phrase canon — greppable corpus clichés

**Class:** phrase

Exact strings inherited from the mass of genre fiction in every model's
training corpus — stable across model generations precisely because they come
from the corpus, not the model. Review Step B verifies these by literal
search (case-insensitive, with the language's pronoun/tense/elision variants),
not read-through. **The strings are per-language: take them from the book's
pack.**

**Why it fails:** these are the most recognizable AI-prose tells in
circulation; a single instance reads as boilerplate to any editor who has
seen model output.

**Fix:** cut or replace with the scene's own concrete detail.
**Budget: 0** — flag on sight, every instance.

### 30. Rhetorical question → self-answer

**Class:** constructional

The narration poses a question and immediately answers it for effect.

**Why it fails:** manufactured drama — a human writer would state the fact.
In narration it reads as the model performing thoughtfulness.

**Fix:** state the fact; keep genuine open questions genuinely open.
**Budget:** at most **one per chapter** in narration; dialogue exempt.

### 31. Hedging stacks

**Class:** constructional

Multiple hedges piled into a single clause, defensively rather than for
genuine epistemic texture.

**Why it fails:** one hedge is POV texture (pattern 9 covers hedged
numerics); stacked hedges add no information and blur every observation into
the same soft focus.

**Fix:** keep at most one hedge per clause; commit the rest.
**Budget:** at most **two stacked-hedge clauses per 1,000 words**.

### 32. False-balance seesaw

**Class:** constructional

Hedge-and-pivot constructions that grant every observation an equal and
opposite counter-observation, resolving nothing.

**Why it fails:** feels safe, avoids commitment, and rarely resolves the
tension it stages. Reflexive even-handedness is a deep model habit — humans
play favorites.

**Fix:** pick the dominant note, or dramatize the contradiction in action.
**Budget:** at most **two per chapter**.

### 33. Filter words — perception routed through the POV verb

**Class:** constructional

Experience narrated through the viewpoint character's perception verbs (saw,
heard, felt, noticed, realized) instead of rendered directly.

**Why it fails:** each filter adds narrative distance the scene didn't ask
for; in density the reader watches the character watching instead of being
in the scene. (Deliberate distance sanctioned by the constitution is a
waiver case.)

**Fix:** cut the filter and render the perception directly.
**Budget:** at most **five per 1,000 words** combined.

### 34. Dialogue tags doing emotional labor

**Class:** constructional

The tag carries the emotion the line and beat should carry — expressive speech
verbs, adverbial tags, and tags that gloss the feeling outright.

**Why it fails:** the tag explains what the dialogue was supposed to show;
adverb and non-speech-verb tags are the model's shortcut to feeling. Cousin
of pattern 45 (every line getting a gesture beat).

**Fix:** the plain speech verb plus a concrete action beat, or rewrite the line
so it carries its own tone.
**Budget:** at most **three per chapter**.

### 35. Ocular agency — eyes and gazes doing the acting

**Class:** constructional

Emotion delegated to autonomous eyes. Sibling of pattern 15's agentive body
parts.

**Why it fails:** eyes can't glint with an abstraction; the construction is
stock shorthand that tells the emotion while pretending to show it.

**Fix:** give the character an action, a line, or a named feeling.
**Budget:** at most **two per chapter**; the eyes-plus-abstraction form:
**budget 0**.

### 36. Portentous one-liner scene enders

**Class:** structural

Every scene or section break landing on a short, vaguely ominous line for
"impact." Extends pattern 19 (chapter-ending codas) down to scene level.

**Why it fails:** one is an ending; a habit is a drumbeat. When every scene
exits on the same clipped portent, the device stops landing and the seams
show.

**Fix:** let some scenes end mid-gesture, on a plain fact, or simply stop.
**Budget:** at most **one scene per chapter** may end this way.

### 37. Templated scene shape

**Class:** structural

Scenes built on the same beat-skeleton: orienting weather/light opener →
dialogue exchange → interior gloss → exit beat, at roughly uniform length.

**Why it fails:** chapters become interchangeable; the reader feels the
template before they can name it. Scene-shape uniformity is among the most
durable structural tells — it survives line-level revision entirely.

**Fix:** vary entry point (in medias res, mid-dialogue), length, and exit;
let one scene run long and another cut off early.
**Budget:** **three or more same-shaped scenes in a chapter** is a finding.

### 38. Over-neat resolution

**Class:** structural

Every tension raised inside a scene or chapter is resolved inside it —
conflicts settled through mutual understanding a little too often, no
residue, ambiguity, or open contradiction carried forward.

**Why it fails:** real accounts have loose ends and unresolved friction; the
model's drive toward closure files every edge smooth. This is the
fiction-shaped version of compulsive summarizing.

**Fix:** leave at least one raised tension genuinely open past the chapter;
let a conflict end unresolved or badly.
**Budget:** review-judged — habitual (most scenes resolving clean) is
**Important**; a single tidy scene is not a finding.

### 39. Sermonizing antagonist — TED-talk aphorism chains

**Class:** constructional

Villains, mentors, and authority figures speaking in chained, quotable
soundbites. The antagonist-flavored escalation of pattern 10.

**Why it fails:** the character stops being a person with wants and becomes
a theme-delivery mechanism; chained epigrams are pure model register.

**Fix:** give the speaker a concrete, self-interested point; cut the chain
to one line at most.
**Budget:** at most **one aphoristic line per chapter** for any single
antagonist/mentor figure; **chains of two or more consecutive aphorisms:
budget 0**.

### 40. Metronomic rhythm — uniform cadence

**Class:** structural

Sentences and paragraphs of near-uniform length and identical internal shape;
no digression, interruption, fragment, or run-on — no burstiness.

**Why it fails:** stylometric studies converge on rhythmic uniformity as one
of the most durable AI signals — more stable than any word list. Human
writing has uneven rhythm: a paragraph that sprawls, a sentence that snaps.

**Fix:** during revision, deliberately vary — fuse two sentences, break one,
let a paragraph run past its natural stop, or end one early.
**Budget:** review-judged — the reviewer contrasts the draft's cadence
variance against the origin's; markedly flatter than the origin is a
finding (**Important**; chapter-wide flatness **Critical**).

### 41. Stated moral — theme over-explanation

**Class:** structural

The narration articulates the story's lesson outright, usually via a
character "finally understanding" it.

**Why it fails:** the fiction-writing version of the essay's compulsive
conclusion — the model states the significance instead of trusting the
story to have earned it. One of the highest-measured AI-vs-human deltas in
narrative studies.

**Fix:** cut the statement; if the scene hasn't made the point, fix the
scene.
**Budget:** at most **one per chapter**, and never in the chapter's final
paragraph (there it also trips pattern 19).

### 42. Therapy-speak dialogue

**Class:** structural

Characters naming their feelings and motives with counselor precision.

**Why it fails:** real people mostly don't have this articulacy about
themselves in the moment — and when every character does, they all share one
voice. Kin of pattern 22 (decoder narration) moved into quoted speech.

**Fix:** let characters misname, deflect, or half-say the feeling; put the
insight in subtext or in the wrong mouth.
**Budget:** at most **one per chapter**.

### 43. No-silence dialogue

**Class:** structural

Every question gets answered; nobody evades, interrupts, trails off, changes
the subject, or talks past anyone. Exchanges are grammatically complete and
perfectly cooperative.

**Why it fails:** models are not trained to generate silence — evasion and
non-answer are among the deepest human tells. A scene where everyone answers
the question asked reads as an interview transcript.

**Fix:** let at least one line per scene dodge, interrupt, or die
unfinished; let a question hang.
**Budget:** review-judged — a chapter whose dialogue scenes are uniformly
cooperative is a finding (**Important**).

### 44. Epithet slop — elegant variation for names

**Class:** constructional

Synonym-cycling to avoid repeating a name or pronoun ("the older man", "the
detective" for a character we know by name).

**Why it fails:** a repetition-penalty artifact. Names and pronouns are
invisible; epithets make the reader re-derive who is speaking and imply a
distance from the POV that isn't intended.

**Fix:** use the name or the pronoun.
**Budget:** at most **two per chapter** (epithets carrying genuine POV
information — a stranger's-eye view before a name is known — are exempt).

### 45. Dialogue-beat metronome

**Class:** structural

Every line of speech arrives with an attached gesture, expression, or
micro-action tag.

**Why it fails:** beats exist to pace dialogue; attached to every line they
become wallpaper and the exchange reads as choreographed. Cousin of pattern
34.

**Fix:** strip beats until they mark only shifts — a decision, a lie, a
turn.
**Budget:** review-judged density — an exchange of six or more consecutive
tagged lines is a finding.

### 46. Importance inflation and copulative avoidance

**Class:** constructional

Narration asserting significance ("puffery"), often while dodging the plain
copula for grander verbs ("stood as", "served as"), plus unearned crowd
authority ("everyone knew…").

**Why it fails:** telling the reader a moment is significant instead of
making it feel significant; the grand verb is the model dodging the plain
copula to sound writerly.

**Fix:** plain verbs, earned significance; cut the crowd chorus or name who
actually said it.
**Budget:** at most **two per chapter** combined.

### 47. Pathetic-fallacy default and reflex sensory register

**Class:** structural

Weather and setting reliably mirroring the character's inner state, and the
same sensory channel (usually smell) as the reflex scene-opener.

**Why it fails:** used once it's a device; used habitually the world becomes
the protagonist's mood ring, and the recurring sensory register becomes a
verbal habit (smell-imagery density is a measured AI-vs-human delta).

**Fix:** let the weather disagree with the mood; rotate or cut the sensory
opener.
**Budget:** at most **two mirroring instances per chapter**; sensory-opener
repetition counts toward pattern 37's scene-shape finding.

## How to Apply

**Seeding only** (`/authorkit.review` Pass 2, first run on a book): when
`book/tic-ledger.md` does not exist, create it from
`.authorkit/templates/tic-ledger-template.md` and seed `Status: seed` entries
from **two sources**:

1. **This file** — the high-signal shapes
   7, 13, 21, 22, 23, 24, 29, 33, 35, 36, 41,
   plus the zero-budget forms of 3, 14, 15, 21, 23, 24, 29, 35, 39.
   Record `Lang: universal` on each.
2. **The book's language pack** — `tic-catalog-<lang>.md` resolved from
   `BOOK_LANGUAGE` on the primary subtag. Attach each seeded shape's
   realization (its exact strings and examples) from the pack, and seed the
   pack's own language-only entries with `Lang: <subtag>` and the pack's
   budgets. A shape whose only content is its realization — 28, 29, and the
   zero-budget string forms of 3, 14, 15, 21, 23, 24, 35 — seeds **only** when
   the pack supplies it.

`Volatility: high` entries (28) are never seeded either way — they enter a
ledger only via blind discovery. Seeds are hypotheses: the blind discovery pass
confirms the ones this book's drafts actually exhibit (they become `active`
with a quoted instance and an origin counter-example) and retires the rest
after 4 unconfirmed reviews — except zero-budget `phrase`-class seeds, which
never retire (dormant at most): their literal Step B sweep costs nothing
regardless of ledger status. After seeding, this file is out of the loop.

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

**The budgets below live on through the ledger, not this file.** At bootstrap
each seeded entry copies its pattern's budget into the ledger's `Budget:` field
(zero-budget forms stay 0 — flag on sight); from then on the *ledger's*
per-entry budget is the live threshold review enforces, and this table is only
consulted again when seeding a rediscovered pattern. Severity and gating are
defined in the review prompt's Pass 2 severity mapping.

## Quick-reference budget table

These are the shapes' default budgets. A pack may override one for its language
where the language's own frequency justifies it, and states the override
explicitly; row 20 is counted per the typography rule in *Language Scope &
Packs*.

| # | Pattern | Default budget |
|---|---------|----------------|
| 1 | Character-by-aphorism (relative clause) | 1 per character per chapter |
| 2 | Comparison-as-default | 3 per 1,000 words |
| 3 | Empty specifier | 0 |
| 4+5 | Denial-as-description / privative modifier combined | 1 per ~250 words |
| 6 | Overprecious time-units | 1 per chapter |
| 7 | Reflexive deepening + generalizing gloss | 0 |
| 8 | Single-sentence paragraph clusters | 2 consecutive max |
| 9 | Hedged numerics | 2 per chapter |
| 10 | Aphoristic dialogue | 1 per speaking character per chapter |
| 11 | Polysyndeton | 1 per chapter |
| 12 | Default diminutive qualifiers | 5 per 1,000 words combined |
| 13 | Negation-correction two-beat | 2 per chapter |
| 14 | Vague placeholder interiority | 2 per chapter; unnameable-feeling forms 0 |
| 15 | Stock somatic beats | 3 per 1,000 words; the canonical cliché 0 |
| 16 | Appositive thematic tail | 2 per chapter, non-consecutive paragraphs |
| 17 | Triadic litany / abstract third slot | 1 litany per chapter; 2 abstract-third lists |
| 18 | Personified atmosphere | 2 per 1,000 words; no repeated noun-verb pair |
| 19 | Epiphany cadence closer | epiphany marker 1 per chapter; ≤2 consecutive coda endings |
| 20 | Em-dash interruptions | 4 per 1,000 words, max 2 per paragraph |
| 21 | Composure beats / trailing minimizers | 1 per chapter as narration closer; summary-closer family 0; dialogue exempt; high-signal |
| 22 | Decoder narration | 2 per chapter |
| 23 | Looping self-echo (antimetabole/anadiplosis/confirming echo) | 1 per chapter; competence-tag form 0; high-signal |
| 24 | Creed / trade-maxim characterization | 1 per character per chapter; totalizing closer 0; high-signal |
| 25 | Participial / absolute-phrase openers | 3 per 1,000 words; max 2 consecutive |
| 26 | Correlative simultaneity | 2 per chapter |
| 27 | Partitioned interiority | 2 per chapter |
| 28 | Vocabulary canon (lexical, volatile) | 2 hits per 1,000 words; never seeded |
| 29 | Stock-phrase canon (greppable exact strings) | 0 |
| 30 | Rhetorical question → self-answer | 1 per chapter; dialogue exempt |
| 31 | Hedging stacks | 2 per 1,000 words |
| 32 | False-balance seesaw | 2 per chapter |
| 33 | Filter words | 5 per 1,000 words |
| 34 | Dialogue tags doing emotional labor | 3 per chapter |
| 35 | Ocular agency | 2 per chapter; eyes-plus-abstraction form 0 |
| 36 | Portentous one-liner scene enders | 1 scene per chapter |
| 37 | Templated scene shape | ≥3 same-shaped scenes per chapter is a finding |
| 38 | Over-neat resolution | review-judged; habitual = Important |
| 39 | Sermonizing antagonist / aphorism chains | 1 per chapter; chains of ≥2 aphorisms 0 |
| 40 | Metronomic rhythm | review-judged vs origin cadence |
| 41 | Stated moral / theme over-explanation | 1 per chapter; never in final paragraph |
| 42 | Therapy-speak dialogue | 1 per chapter |
| 43 | No-silence dialogue | review-judged; uniformly cooperative chapter = Important |
| 44 | Epithet slop | 2 per chapter; genuine-POV epithets exempt |
| 45 | Dialogue-beat metronome | ≥6 consecutive tagged lines is a finding |
| 46 | Importance inflation / copulative avoidance | 2 per chapter combined |
| 47 | Pathetic fallacy / reflex sensory register | 2 mirroring instances per chapter |
