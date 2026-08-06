# Catalogue de tics littéraires — français (bootstrap seed)

**Lang: fr** — the French-language companion to
`.authorkit/prompts/_shared/literary-tic-catalog.md`. That catalog holds the
**universal** shapes (structural and constructional attractors of the model,
which surface in any language); this pack holds what it cannot: the strings and
constructions that only exist in French.

**Same status as the seed catalog: a bootstrap hypothesis, not a normative
gate.** `/authorkit.review` Pass 2 seeds a book's `book/tic-ledger.md` from
this pack on its first run when `BOOK_LANGUAGE` resolves to the primary subtag
`fr` (`fr-FR`, `fr-CA`, `French` all match), alongside the universal entries.
From then on the ledger — discovered by blind contrast against the book's own
fixed voice origin — is what review checks. Entries seed as `Status: seed` with
`Lang: fr`; unconfirmed non-`phrase` seeds retire after 4 reviews, while
zero-budget `phrase` seeds never retire (their literal Grep sweep is free).

**Never load this file while drafting.** The quarantine rule is identical:
pattern descriptions in the drafting context prime the constructions they
prohibit. Tic knowledge reaches generation only as contrastive pairs in
`book/voice-pairs.md`.

**Ids.** `FR-nn` ids below are references *within this pack*. A seeded ledger
entry gets a normal `TIC-NNN` id allocated by review; record the provenance as
`**Seeded from**: tic-catalog-fr #FR-nn`.

**A note on these lists.** They are drawn from the recognizable register of
model-written French — genre-corpus clichés and the constructions the model
reaches for when asked to write "littéraire". Like the English canon, the
`lexical` tier rotates with model generations and is deliberately never seeded;
the `phrase` tier is stable because it comes from the corpus, not the model.
Confirm every entry against *this* book's drafts before treating it as active.

## FR-1. Canon de clichés — chaînes exactes (greppables)

**Class:** phrase · **Lang: fr** · **Budget: 0** — flag on sight, every
instance.

Exact strings inherited from the mass of French genre fiction in the training
corpus. Verified in review Step B by literal search (Grep, case-insensitive),
not by read-through — **cover elision, gender/number, tense and accent
variants** (`lui parcourut` / `lui parcourait`, `l'échine` / `le dos`,
`submergea` / `submergeait`, with or without accents in a badly-encoded draft).

Le corps :
- « un frisson lui parcourut l'échine » / « … le dos » / « … la nuque »
- « son cœur manqua un battement » / « son cœur rata un battement »
- « son sang ne fit qu'un tour »
- « elle retint son souffle » / « le souffle coupé » / « à bout de souffle »
- « une boule au ventre » / « un nœud à l'estomac » / « la gorge nouée »
- « les mots restèrent coincés dans sa gorge »
- « une vague de [émotion] la submergea » / « … le submergea »

Le décor et le silence :
- « l'air était lourd de » / « l'air était chargé de »
- « un silence pesant » / « le silence retomba » / « un silence de plomb »
- « le temps sembla suspendu » / « le temps s'arrêta »

Le temps et la clôture :
- « l'espace d'un instant » / « l'espace d'une seconde »
- « à cet instant précis »
- « pour la première fois depuis » (en clôture de scène)
- « n'était plus qu'un lointain souvenir »
- « et c'était tout » / « ce fut tout » (en clôture de narration)

Les gestes stock :
- « esquissa un sourire » / « un sourire en coin »
- « planta son regard dans le sien »
- « sans un mot » (en tête de phrase, comme transition)
- « comme si de rien n'était »
- « elle ne put s'empêcher de »

**Pourquoi ça échoue :** ce sont les tells les plus reconnaissables de la prose
française produite par un modèle ; une seule occurrence suffit à faire lire la
page comme du remplissage de corpus.

**Correction :** couper, ou remplacer par le détail concret propre à la scène.

## FR-2. Canon lexical — la liste de mots « littéraires »

**Class:** lexical · **Lang: fr** · **Volatility: high** — **never seeded**;
enters a ledger only via blind discovery in *this* book's drafts.

Registre :
- indicible, ineffable, insondable, viscéral, palpable, lancinant, ténu,
  imperceptible / imperceptiblement, feutré, ouaté, diaphane, éthéré
- empreint de, teinté de, nimbé de, « une symphonie de », « un ballet de »
- inexorablement, inéluctable, immuable, « non sans », « il n'en demeurait pas
  moins »

Adjectifs de fausse profondeur : profond, véritable, saisissant, poignant,
bouleversant, remarquable, fascinant, magistral.

**Budget:** at most **two hits per 1,000 words** combined. Weight this entry
**below** the constructional ones: a manuscript scrubbed of every word here can
still read as model-written.

**Correction :** le mot simple, ou une image concrète.

## FR-3. Correction par négation — « ce n'était pas X, mais Y »

**Class:** constructional · **Lang: fr** — the French realization of universal
pattern 13.

Formes :
- « Ce n'était pas de la peur, mais de la colère. »
- « Ce n'était pas tant X que Y. »
- « Non pas X, mais Y. »
- « Il ne s'agissait pas de X. Il s'agissait de Y. »

**Pourquoi ça échoue :** la définition par retrait remplace l'affirmation ;
répétée, elle donne à la narration un tic de correcteur.

**Correction :** affirmer Y directement.
**Budget:** at most **two per chapter**.

## FR-4. Composé « un mélange de X et de Y »

**Class:** constructional · **Lang: fr**

Formes : « un mélange de X et de Y », « à mi-chemin entre X et Y », « un
mélange étrange de… », « entre X et Y » comme description d'émotion.

**Pourquoi ça échoue :** l'émotion est dosée comme une recette au lieu d'être
jouée ; c'est le pendant français de la fausse balance.

**Correction :** choisir l'émotion dominante et la montrer en acte.
**Budget:** at most **two per chapter**.

## FR-5. Nominalisation de caractérisation — « la [qualité] de sa [partie] »

**Class:** constructional · **Lang: fr**

Formes : « le calme de sa voix », « la dureté de son regard », « la lenteur de
ses gestes », « la fermeté de sa poignée de main » — la qualité abstraite
extraite en tête de groupe nominal, par défaut, pour caractériser.

**Pourquoi ça échoue :** propre au français du modèle, qui préfère la
nominalisation au verbe. Une fois, c'est du style ; en série, chaque personnage
est décrit par la même machine grammaticale.

**Correction :** rendre la qualité au verbe (« il parlait sans hâte »).
**Budget:** at most **three per 1,000 words**.

## FR-6. Modalisation en cascade — « sembler », « paraître », « comme si »

**Class:** constructional · **Lang: fr** — French sibling of universal
patterns 2 and 31.

Formes : « il sembla », « elle parut », « on aurait dit que », « comme si »
enchaînés ; « quelque chose comme de la [abstraction] ».

**Pourquoi ça échoue :** la narration refuse d'affirmer ; le doute permanent
lit comme de la prudence de modèle, pas comme de la distance narrative.

**Correction :** affirmer le fait, ou donner l'observation qui produit le doute.
**Budget:** at most **three per 1,000 words** combined.

## FR-7. Incises expressives — « souffla-t-il », « murmura-t-elle »

**Class:** constructional · **Lang: fr** — French realization of universal
pattern 34.

Formes : souffla, murmura, lâcha, articula, siffla, asséna, glissa — l'incise
porte l'émotion à la place de la réplique.

**Pourquoi ça échoue :** en français l'incise inversée est déjà visible ;
chargée d'émotion à chaque réplique, elle devient un métronome.

**Correction :** « dit » / « demanda », ou une action ; laisser la réplique
porter.
**Budget:** at most **three per chapter** beyond `dit` / `demanda` / `répondit`.

## FR-8. Intériorité vague — « quelque chose en elle »

**Class:** constructional · **Lang: fr** — French realization of universal
pattern 14 (and 27).

Formes : « quelque chose en elle se brisa », « une part de lui-même », « un
sentiment qu'il n'aurait su nommer », « sans qu'elle sût pourquoi ».

**Correction :** nommer le sentiment, ou montrer le geste qui le trahit.
**Budget:** at most **two per chapter**; la forme « qu'il/elle n'aurait su
nommer » : **budget 0**.

## FR-9. Prolepse du narrateur — « il ne le savait pas encore, mais… »

**Class:** constructional · **Lang: fr** · **Budget: 0**

Formes : « il ne le savait pas encore, mais… », « elle ne comprendrait que bien
plus tard… », « ce jour-là allait… ».

**Pourquoi ça échoue :** double faute — tic de narration *et* violation du
Disclosure Horizon Protocol (la révélation appartient à un chapitre ultérieur).
Zero budget for that reason; a hit is Critical under both Pass 2 and Pass 5.

**Correction :** semer l'indice sans nommer la conséquence.

## FR-10. Regard agissant — « ses yeux s'assombrirent »

**Class:** constructional · **Lang: fr** — French realization of universal
pattern 35.

Formes : « ses yeux s'assombrirent », « son regard se durcit », « une lueur de
[abstraction] dans le regard », « ses yeux balayèrent la pièce ».

**Correction :** une action, une réplique, ou l'émotion nommée.
**Budget:** at most **two per chapter**; la forme « une lueur de [abstraction]
dans le regard » : **budget 0**.

## FR-11. Unités de temps précieuses

**Class:** constructional · **Lang: fr** — French realization of universal
pattern 6.

Formes : « une fraction de seconde », « le temps d'un battement de cils »,
« quelques battements de cœur plus tard ».

**Budget:** at most **one per chapter** (les chaînes exactes listées en FR-1
restent à budget 0).

## Typographie française (règles de comptage, pas des tics)

French typography is not a tic — but it changes how punctuation-shaped budgets
are counted, and getting it wrong flags correct prose:

- **Dialogue.** Guillemets français « … » (with non-breaking spaces inside) and
  the tiret cadratin `—` opening a reply are **standard dialogue punctuation**.
  They do **not** count toward universal pattern 20 (em-dash interruption
  density). Only an interruptive dash **inside narration** counts there — see
  *Language Scope* in the seed catalog.
- **Espaces insécables** before `;` `:` `!` `?` and inside `« »`: a typographic
  correctness item. Report inconsistency as a craft/consistency finding, never
  as a tic.
- **Mixed conventions** (straight `"` quotes in one chapter, guillemets in
  another) is a manuscript-consistency finding for the drift sweep, not a Pass 2
  entry.
- **Dialogue-ratio metrics** count `«` and `—` openers (`authorkit book stats`),
  so dash-led dialogue is measured, not invisible.

## Tableau de référence — budgets

| # | Forme | Budget par défaut |
|---|-------|-------------------|
| FR-1 | Clichés de corpus (chaînes exactes) | 0 |
| FR-2 | Canon lexical (volatile) | 2 pour 1 000 mots — jamais seedé |
| FR-3 | « ce n'était pas X, mais Y » | 2 par chapitre |
| FR-4 | « un mélange de X et de Y » | 2 par chapitre |
| FR-5 | Nominalisation de caractérisation | 3 pour 1 000 mots |
| FR-6 | « sembler » / « paraître » / « comme si » | 3 pour 1 000 mots |
| FR-7 | Incises expressives | 3 par chapitre |
| FR-8 | « quelque chose en elle » | 2 par chapitre ; « n'aurait su nommer » : 0 |
| FR-9 | Prolepse du narrateur | 0 |
| FR-10 | Regard agissant | 2 par chapitre ; « une lueur de […] » : 0 |
| FR-11 | Unités de temps précieuses | 1 par chapitre |

**Calibration.** Every budget here is subject to the same origin-canary rule as
the seed catalog's: a budget at or below the origin's own measured rate for that
shape is mis-set — raise it clear of the origin rather than taxing prose for
sounding like the book's own voice.
