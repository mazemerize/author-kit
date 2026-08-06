# Tic catalog — English realizations (bootstrap seed)

**Lang: en** — the English-language pack for
`.authorkit/prompts/_shared/literary-tic-catalog.md`. That file defines the
*shapes*; this one supplies how they are realized in English: the examples, the
exact strings, the lexical canon, and any English-specific budget note.

**Same status as the shape catalog: a bootstrap hypothesis, not a normative
gate.** `/authorkit.review` Pass 2 seeds a book's `book/tic-ledger.md` from the
shapes plus this pack on its first run when `BOOK_LANGUAGE` resolves to the
primary subtag `en` (`en-US`, `en-GB`, `English` all match). From then on the
ledger — discovered by blind contrast against the book's own fixed voice origin
— is what review checks. Entries seed as `Status: seed`; unconfirmed non-`phrase`
seeds retire after 4 reviews, while zero-budget `phrase` seeds never retire
(their literal Grep sweep is free).

**Never load this file while drafting.** Same quarantine as the shape catalog:
pattern descriptions in the drafting context prime the constructions they
prohibit. Tic knowledge reaches generation only as contrastive pairs in
`book/voice-pairs.md`.

**Ids.** Sections are keyed by the shape number they realize, so a seeded ledger
entry records `**Seeded from**: catalog #NN (en)`. Shapes with no distinctive
English realization beyond their definition (38, 40, 43 — all review-judged) do
not appear here.

## 1. Character-by-aphorism

Examples:
- "the eyes of a man who had stopped sleeping years ago"
- "the unhurried movement of a man who had done this before"
- "the closed face of a woman who had read more reports than she trusted"

## 2. Comparison-as-default

Canonical markers: "the way [X verbs]", "as though [Y]".

Examples:
- "wind moving through the fronds the way wind moves through wheat"
- "he stood at the rail the way a man stands at a rail when he has done the approach before"
- "as though distance were itself a solvent the silence answered to"

## 3. Empty specifier

Canonical form: **"particular"**. **Budget: 0** unless the constitution waives.

Examples:
- "the sun went down in a particular colour"
- "the lights came up in a particular discipline"
- "a knot tied in a particular pattern by a particular hand"

## 4. Denial-as-description

Examples:
- "she did not smile"
- "he did not raise his voice"
- "she had not needed to ask"

Prefer positive description ("she kept her face level" rather than "she did not
smile").

## 5. Privative modifier stacked as description

Examples:
- "without ceremony" / "without a hail" / "without a word"
- "without unkindness" / "without intent"

## 6. Overprecious time-units

Examples:
- "for the length of one held breath"
- "for the space of a heartbeat"
- "for a long moment"
- "for the time it took to draw a single breath"

## 7. Reflexive deepening

The generalizing gloss is **"the way one [verbs]"** — the single most
LLM-flavoured construction in English literary AI prose. **Budget: 0.**

Example:
- "She named it gone. She had named it gone before. She named it gone again,
  more honestly, the way one names a thing more honestly the second time."

## 8. Single-sentence paragraphs in clusters

Examples:
- Three consecutive one-sentence paragraphs
- A closing sequence of five short paragraphs, each a single line
- The same one-line sentence repeated as its own paragraph two or three times
  in close succession

## 9. Hedged numerics

Canonical marker: **"perhaps [N]"**.

Examples:
- "of perhaps forty"
- "perhaps fifty"
- "perhaps a boy, perhaps a girl"

## 10. Aphoristic dialogue

Underlining closers ("Remember it", "That is what it means when X") are the
worst form and are barred absent an explicit waiver.

Examples:
- "It held because they let it hold. That is what it means when the cover
  holds. Remember it."
- "The trouble with the water is that it always remembers."
- "Some things are like that."

## 11. Polysyndeton

Example:
- "the canvas worked on her new tack and the wake settled and the hull came
  on and the basin went on"

## 12. Default diminutive qualifiers

Canonical set: **small, thin, quiet**.

Examples:
- "small reluctance" / "small sounds" / "small recognition"
- "thin thread" / "thin man" / "quiet moment"

## 13. Negation-correction two-beat

Canonical forms: "not X, but Y" / "It did not X. It X'd Y" / additive
"not just X, but Y" / "It's not X, it's Y".

Examples:
- "It was not anger. It was the look of someone calculating cost."
- "She did not run. She walked, with the gait of someone who knew they were
  being watched."
- "Not the green of the lagoon, but a thinner colour."

## 14. Vague placeholder interiority

Canonical placeholder: **"something"**.

Examples:
- "something in her chest loosened"
- "something passed between them"
- "something like grief, but not grief"
- "a feeling she couldn't name"

**Zero-budget family** (exact strings): "a feeling (s)he couldn't name",
"couldn't quite name", "had no name for".

## 15. Stock somatic beats

Examples:
- "her chest tightened" / "his stomach dropped" / "her breath caught"
- "his heart hammered" / "her jaw clenched" / "his knuckles whitened"
- The genre-corpus set: "a shiver/chill ran down her spine," "his blood ran
  cold," "her heart skipped a beat," "a lump formed in her throat,"
  "butterflies in her stomach," "tears welled up," "his heart sank/swelled,"
  "her legs were like lead," "every muscle screamed in protest"
- Sibling form — agentive body parts: "her hand found the rail," "his eyes
  found hers"

**Zero-budget form** (exact string, any phrasing): "released a breath (s)he
didn't know (s)he'd been holding" — the single most recognizable AI-prose
cliché in English.

## 16. Appositive thematic tail

Tell-words: "a kind of", "the shape of", "the weight of".

Examples:
- "She set the cup down between them, a small truce."
- "He signed his name, the weight of it settling."
- "…, a kind of answer."
- "…, the shape of an apology."

## 17. Triadic litany with the abstract third slot

Examples:
- "She had packed his books. She had packed his letters. She had packed the
  years."
- "It was in the floorboards, in the curtains, in the quiet between them."
- Polished parallel tricolons: "fast, cheap, and out of control"

## 18. Personified atmosphere

Examples:
- "the silence stretched" / "the quiet pressed in"
- "the air thickened" / "darkness pooled"
- "the silence settled over the room"

## 19. Epiphany cadence closer

Canonical epiphany marker: **"for the first time"** (1 per chapter).

Examples:
- "And for the first time in a long time, that was enough."
- "Maybe that was the point."
- "It wasn't forgiveness. But it was a start." (also trips pattern 13)

## 20. Em-dash interruption density

English uses the em-dash for interruption, not for dialogue, so the full budget
applies: **four per 1,000 words, max two per paragraph.**

Example:
- "She reached for the letter — the one he'd left — and stopped."

## 21. Composure beats and trailing minimizers

Examples — composure form:
- "she named it for what it was and let it go"
- "he let that sit" / "filing it somewhere behind his eyes"
- "she took it as no more than her due"
- "whatever she was reckoning she kept behind her teeth"

Examples — trailing-minimizer form:
- "…and left it there" / "…and left it at that"
- "all the answer she was going to get"
- "and not one gesture more"

**Zero-budget family** (exact strings, summary-closer boilerplate; also listed
under 29): "(and) that was the whole of it", "and that was all (of it)",
"and nothing more".

Character-voiced terseness in dialogue ("Your call. The whole of it.") is
exempt — the ban is on narration measuring itself.

## 22. Decoder narration

Examples:
- "she understood X as Y" / "Zoe understood the silence as practice"
- "she came to understand that…"
- "she read the room as…" / "the look of a woman moving a token from one
  string to another"

## 23. Looping self-echo

Examples:
- **Antimetabole**: "for a man who weighs his nods has learned that nods are
  weighed."
- **Anadiplosis**: "because that was his trade and his trade was to trust
  nothing he had not summed himself."
- **Confirming echo / competence tag**: "a man might read the health of the
  whole world in those rolls if he knew the hand, and Crescens knew the hand."

**Zero-budget form**: the competence tag — "…if he knew X, and he knew X".

## 24. Creed / trade-maxim characterization

Examples:
- "his trade was to trust nothing he had not summed himself"
- "to record what was and add nothing to it was the whole of his trade"
- "she was a woman who kept her debts in her head and her grief in her hands"

**Zero-budget form** (exact string, absent an explicit waiver): the totalizing
closer "…was the whole of his trade/work/life".

## 25. Participial / absolute-phrase openers

Examples:
- "Standing at the window, she watched the harbour fill."
- "Hands trembling, he set the cup down."
- "The lamp guttering, the room half in shadow, they waited."
- Tailing mirror form: "…, cementing its legacy," "…, the lamp guttering as if
  in answer"
- Fronted-adverbial opener: "As the sun dipped below the horizon, she…"

## 26. Correlative simultaneity

Canonical forms: "at once X and Y" / "both X and Y".

Examples:
- "she felt at once afraid and exhilarated"
- "his voice was both gentle and final"
- "it was at once an apology and a threat"

## 27. Partitioned interiority

Canonical forms: "part of her" / "some part of him".

Examples:
- "part of her wanted to stay"
- "some part of him already knew"
- "a small part of her hated him for it"

## 28. Vocabulary canon (English)

**Class:** lexical · **Volatility: high** — **never seeded**; enters a ledger
only via blind discovery in *this* book's drafts. The list rotates
model-to-model and season-to-season: "delve" was the 2023–24 canon and has
largely faded. Treat it as a living sample, not a fixed ban list.

Current sample:
- delve, tapestry, testament (to), palpable, myriad, plethora, intricate,
  nuanced, liminal, gossamer, thrum/thrumming, ministrations, sentinel,
  "a symphony of," nestled, ever-present, unspoken
- Puffery adjectives: profound, remarkable, storied, vibrant, unwavering,
  enduring, iconic

**Budget:** at most **two canon hits per 1,000 words**.

## 29. Stock-phrase canon (English)

**Class:** phrase · **Budget: 0** — flag on sight, every instance. Verified by
literal search (Grep, case-insensitive, pronoun/tense variants), not
read-through.

The greppable set:
- "little did (she|he|they) know"
- "the air was thick with"
- "a wave of [emotion] washed over"
- "hung in the air"
- "sent a shiver down" / "sent shivers down"
- "heart skipped a beat"
- "in that moment"
- "without waiting for a response"
- "despite (herself|himself)"
- "worried her bottom lip"
- "knuckles turning white" / "knuckles whitening" (dense form of 15's sibling)
- "(and) that was the whole of it" / "and that was all (of it)" —
  summary-closer boilerplate; also trips patterns 21 and 24

## 30. Rhetorical question → self-answer

Examples:
- "Was it worth it? Perhaps. But the cost…"
- "What changed? The math did."
- "The result? Total chaos."

## 31. Hedging stacks

Examples:
- "perhaps, in some way, she had almost known"
- "it seemed, somehow, as if it might"
- "a little like something that could have been grief"

## 32. False-balance seesaw

Examples:
- "It was X. And yet it was also Y."
- "not without its dangers"
- "While she trusted him, she also knew better."

## 33. Filter words

Canonical set: saw, heard, felt, noticed, watched, realized, seemed to.

Examples:
- "she saw the door open" (vs "the door opened")
- "he heard the floor creak" / "she felt the cold settle"

## 34. Dialogue tags doing emotional labor

Examples:
- "she said, her voice heavy with the weight of unshed tears"
- "he breathed" / "she managed" / "he gritted" as speech verbs
- "she said softly, sadly"

Plain speech verbs for the fix: "said" / "asked".

## 35. Ocular agency

Examples:
- "her eyes glinted with mischief" / "his eyes darkened"
- "her eyes flashed" / "his gaze hardened"
- "her gaze swept the room"

**Zero-budget form** (exact string): "eyes glinted with [abstraction]".

## 36. Portentous one-liner scene enders

Examples:
- "She would remember that later."
- "Then the lights went out."
- "'Then we're already too late.'" (curt cliffhanger dialogue closer)

## 37. Templated scene shape

Examples:
- Three consecutive scenes opening on light/weather ("The morning came grey…")
- Every scene closing on a short interior summary before the break
- Scene lengths within ±15% of each other across a chapter

## 39. Sermonizing antagonist

Examples:
- "Power isn't taken. It's conceded. And you, my dear, have been conceding
  all your life."
- Mentor speeches built from three consecutive aphorisms

## 41. Stated moral

Examples:
- "She finally understood that grief was just love with nowhere to go."
- "In the end, it had never been about the money."
- "He realized, at last, what his father had tried to tell him."

## 42. Therapy-speak dialogue

Examples:
- "I think I'm pushing you away because I'm scared of being left first."
- "You're not angry at me. You're angry at what I represent."

## 44. Epithet slop

Examples:
- "the older man" / "the redhead" / "the taller of the two"
- "the detective" for a POV character we know by name

## 45. Dialogue-beat metronome

Examples:
- "…she said, eyes narrowing." / "…he replied, running a hand through his
  hair." — on every consecutive line
- Alternating tag-beat-tag-beat through an entire exchange

## 46. Importance inflation and copulative avoidance

Examples:
- "a moment that would change everything"
- "in ways she couldn't yet understand"
- "the house stood as a testament to…" / "the scar served as a reminder"
- "people always said…" / "everyone in town knew…" (unearned crowd authority)

## 47. Pathetic-fallacy default and reflex sensory register

Examples:
- Storm breaking at the argument's climax; rain at the funeral; sun on the
  reconciliation — every time
- "The air smelled of rain and old paper" as the default orienting beat

## English typography (counting rules, not tics)

- **Dialogue** is marked with quotation marks (`"…"`, or `'…'` in British
  practice), never with a dash. The em-dash is therefore always an interruption
  in English prose, and pattern 20's full budget applies to every instance.
- **Dialogue-ratio metrics** (`authorkit book stats`) count straight and
  typographic quote openers, so English dialogue is measured as written.

## Quick-reference — English-specific budgets

Shapes take the budgets in the catalog's table. This pack overrides nothing;
it adds the zero-budget exact-string forms below, which gate at one instance:

| Shape | Zero-budget English form |
|---|---|
| 3 | "particular" as specifier |
| 7 | "the way one [verbs]" gloss |
| 14 | "a feeling (s)he couldn't name" family |
| 15 | "released a breath (s)he didn't know (s)he'd been holding" |
| 21 | "that was the whole of it" / "and that was all" family |
| 23 | competence tag — "…if he knew X, and he knew X" |
| 24 | "…was the whole of his X" closer |
| 29 | the full greppable set above |
| 35 | "eyes glinted with [abstraction]" |
| 39 | chains of two or more consecutive aphorisms |

**Calibration.** Every budget is subject to the origin-canary rule: a budget at
or below the origin's own measured rate for that shape is mis-set — raise it
clear of the origin rather than taxing prose for sounding like the book's own
voice.
