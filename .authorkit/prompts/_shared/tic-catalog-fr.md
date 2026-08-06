# Catalogue de tics — réalisations françaises (bootstrap seed)

**Lang: fr** — the French-language pack for
`.authorkit/prompts/_shared/literary-tic-catalog.md`. That file defines the
*shapes*; this one supplies how they are realized in French: the examples, the
exact strings, the lexical canon, and the French-only constructions the shape
catalog does not name.

**Same status as the shape catalog: a bootstrap hypothesis, not a normative
gate.** `/authorkit.review` Pass 2 seeds a book's `book/tic-ledger.md` from the
shapes plus this pack on its first run when `BOOK_LANGUAGE` resolves to the
primary subtag `fr` (`fr-FR`, `fr-CA`, `français` all match). From then on the
ledger — discovered by blind contrast against the book's own fixed voice origin
— is what review checks. Entries seed as `Status: seed` with `Lang: fr`;
unconfirmed non-`phrase` seeds retire after 4 reviews, while zero-budget
`phrase` seeds never retire (their literal Grep sweep is free).

**Never load this file while drafting.** Same quarantine as the shape catalog:
pattern descriptions in the drafting context prime the constructions they
prohibit. Tic knowledge reaches generation only as contrastive pairs in
`book/voice-pairs.md`.

**Ids.** Sections keyed by a number realize that shape from the catalog — a
seeded ledger entry records `**Seeded from**: catalog #NN (fr)`. Sections keyed
`FR-nn` are French-only shapes with no catalog equivalent; they seed under their
own id (`**Seeded from**: tic-catalog-fr #FR-nn`).

**A note on these lists.** They are drawn from the recognizable register of
model-written French — genre-corpus clichés and the constructions the model
reaches for when asked to write "littéraire". Like the English canon, the
`lexical` tier rotates with model generations and is never seeded; the `phrase`
tier is stable because it comes from the corpus, not the model. Confirm every
entry against *this* book's drafts before treating it as active.

*Les motifs sans section ici n'ont pas de réalisation française distinctive : ils
sont seedés comme formes, depuis le catalogue, sans balayage de chaînes.*

## 2. Comparaison par défaut

Marqueurs canoniques : « comme si », « on aurait dit que », « à la manière de ».

Exemples :
- « le vent passait dans les palmes comme il passe dans le blé »
- « comme si la distance était elle-même un solvant »

## 3. Spécificateur vide

Formes canoniques : **« un certain » / « une certaine »**, **« particulier »**,
« un je-ne-sais-quoi ». **Budget : 0** sauf dérogation de la constitution.

Exemples :
- « le jour tombait avec une certaine douceur »
- « une lumière particulière »
- « un certain calme s'installa »

## 6. Unités de temps précieuses

Exemples :
- « l'espace d'un instant » / « l'espace d'une seconde »
- « une fraction de seconde »
- « le temps d'un battement de cils »
- « quelques battements de cœur plus tard »

## 13. Correction par négation

Formes canoniques : « ce n'était pas X, mais Y » / « ce n'était pas X. C'était
Y. » / « non pas X, mais Y » / « ce n'était pas tant X que Y » / « il ne
s'agissait pas de X, mais de Y ».

Exemples :
- « Ce n'était pas de la peur, mais de la colère. »
- « Elle ne courait pas. Elle marchait, du pas de quelqu'un qui se sait
  observé. »

## 14. Intériorité vague

Placeholder canonique : **« quelque chose »**.

Exemples :
- « quelque chose en elle se brisa »
- « quelque chose passa entre eux »
- « quelque chose comme du chagrin, mais pas du chagrin »

**Forme à budget 0** (chaînes exactes) : « un sentiment qu'il n'aurait su
nommer », « sans qu'elle sût pourquoi », « qu'elle n'aurait pu nommer ».

## 15. Somatique stock

Exemples :
- « son cœur manqua un battement » / « son cœur rata un battement »
- « un frisson lui parcourut l'échine » / « … le dos » / « … la nuque »
- « son sang ne fit qu'un tour »
- « une boule au ventre » / « un nœud à l'estomac » / « la gorge nouée »
- « les mots restèrent coincés dans sa gorge »
- « une vague de [émotion] la submergea »
- Forme sœur — parties du corps agissantes : « sa main trouva la rambarde »

**Forme à budget 0** (chaîne exacte) : « elle retint son souffle » / « il retint
son souffle » — l'équivalent français du cliché le plus reconnaissable.

## 18. Atmosphère personnifiée

Exemples :
- « un silence pesant » / « le silence retomba » / « un silence de plomb »
- « l'air était lourd de » / « l'air était chargé de »
- « le temps sembla suspendu » / « le temps s'arrêta »

## 19. Clôture en épiphanie

Marqueur canonique : **« pour la première fois (depuis) »** (1 par chapitre).

Exemples :
- « Et pour la première fois depuis longtemps, cela suffisait. »
- « n'était plus qu'un lointain souvenir »
- « Peut-être était-ce cela, au fond. »

## 20. Densité de tirets cadratins

**La typographie française marque le dialogue au tiret cadratin.** Ne comptez
que les tirets **interruptifs à l'intérieur de la narration** ; un tiret qui
ouvre une réplique est de la ponctuation, pas un geste stylistique. Appliquer le
budget anglais au dialogue au tiret reviendrait à signaler la typographie
standard du français comme un tic. Voir *Language Scope & Packs*.

## 21. Clôtures de composure et minimiseurs

Exemples :
- « sans un mot » (en tête de phrase, comme transition)
- « comme si de rien n'était »
- « elle en resta là » / « elle laissa passer »
- « elle ne put s'empêcher de »

**Famille à budget 0** (chaînes exactes, clôture-résumé ; voir aussi 29) :
« et c'était tout », « ce fut tout », « rien de plus ».

## 25. Ouvertures participiales / absolues

Exemples :
- « Le regard fixé sur la porte, elle attendit. »
- « Les mains tremblantes, il reposa la tasse. »
- « Sans un mot, il sortit. »
- Ouverture adverbiale d'habitude : « Alors que le soleil déclinait, elle… »

## 26. Simultanéité corrélative

Formes canoniques : « à la fois X et Y » / « un mélange de X et de Y » /
« à mi-chemin entre X et Y » / « entre X et Y » pour dire une émotion.

Exemples :
- « elle éprouvait à la fois de la peur et de l'exaltation »
- « un mélange étrange de tendresse et de rancune »
- « sa voix était à la fois douce et sans appel »

## 27. Intériorité partitionnée

Formes canoniques : « une part d'elle-même » / « une partie de lui ».

Exemples :
- « une part d'elle-même voulait rester »
- « une partie de lui savait déjà »

## 28. Canon lexical (français)

**Class:** lexical · **Volatility: high** — **jamais seedé** ; n'entre au
registre que par découverte à l'aveugle dans les brouillons de *ce* livre. La
liste tourne d'un modèle à l'autre : échantillon vivant, pas liste
d'interdits.

Échantillon courant :
- indicible, ineffable, insondable, viscéral, palpable, lancinant, ténu,
  imperceptible / imperceptiblement, feutré, ouaté, diaphane, éthéré
- empreint de, teinté de, nimbé de, « une symphonie de », « un ballet de »
- inexorablement, inéluctable, immuable, « non sans », « il n'en demeurait pas
  moins »
- Adjectifs de fausse profondeur : profond, véritable, saisissant, poignant,
  bouleversant, remarquable, fascinant, magistral

**Budget :** au plus **deux occurrences pour 1 000 mots**.

## 29. Canon de clichés (français)

**Class:** phrase · **Budget: 0** — signalé à chaque occurrence. Vérifié par
recherche littérale (Grep, insensible à la casse), pas à la lecture — **couvrez
les variantes d'élision, de genre, de nombre, de temps et d'accentuation**
(« lui parcourut » / « lui parcourait », « l'échine » / « le dos »,
« submergea » / « submergeait »).

L'ensemble greppable :
- « un frisson lui parcourut l'échine »
- « son cœur manqua un battement »
- « son sang ne fit qu'un tour »
- « l'air était lourd de » / « l'air était chargé de »
- « un silence pesant » / « le silence retomba »
- « l'espace d'un instant »
- « à cet instant précis »
- « le temps sembla suspendu »
- « n'était plus qu'un lointain souvenir »
- « esquissa un sourire » / « un sourire en coin »
- « planta son regard dans le sien »
- « comme si de rien n'était »
- « elle ne put s'empêcher de »
- « et c'était tout » / « ce fut tout » — clôture-résumé ; trippe aussi 21 et 24

## 31. Empilements de modalisation

Formes canoniques : « il sembla » / « elle parut » / « on aurait dit que » /
« quelque chose comme de la [abstraction] », enchaînés.

Exemples :
- « il sembla, un instant, qu'elle allait peut-être répondre »
- « quelque chose comme du soulagement, ou presque »

**Pourquoi ça échoue en français :** la narration refuse d'affirmer ; le doute
permanent lit comme de la prudence de modèle, pas comme de la distance
narrative.

## 33. Verbes de perception

Ensemble canonique : voir, entendre, sentir, remarquer, comprendre, sembler.

Exemples :
- « elle vit la porte s'ouvrir » (au lieu de « la porte s'ouvrit »)
- « il entendit le plancher craquer » / « elle sentit le froid s'installer »

## 34. Incises expressives

Le français marque l'incise par inversion, ce qui la rend déjà visible ;
chargée d'émotion à chaque réplique, elle devient un métronome.

Exemples : « souffla-t-il », « murmura-t-elle », « lâcha-t-il »,
« articula-t-elle », « siffla-t-il », « asséna-t-elle », « glissa-t-il ».

Verbes neutres pour la correction : « dit », « demanda », « répondit ».
**Budget :** au plus **trois par chapitre** au-delà des verbes neutres.

## 35. Regard agissant

Exemples :
- « ses yeux s'assombrirent » / « son regard se durcit »
- « ses yeux balayèrent la pièce »
- « son regard se perdit au loin »

**Forme à budget 0** (chaîne exacte) : « une lueur de [abstraction] dans le
regard ».

## 44. Variation élégante des noms

Le français littéraire y est particulièrement porté — la répétition du nom
propre y est perçue comme une faute de style, ce qui pousse le modèle à
l'épithète systématique.

Exemples :
- « le jeune homme » / « la rousse » / « le plus grand des deux »
- « l'inspecteur » pour un personnage-POV qu'on connaît par son nom

## 46. Inflation d'importance

Exemples :
- « un moment qui allait tout changer »
- « d'une manière qu'elle ne comprenait pas encore »
- « la maison se dressait comme un témoignage de… »
- « tout le monde savait que… » / « on disait que… » (autorité collective non
  gagnée)

## FR-1. Nominalisation de caractérisation — « la [qualité] de sa [partie] »

**Class:** constructional · **French-only** — no catalog equivalent.

Formes : « le calme de sa voix », « la dureté de son regard », « la lenteur de
ses gestes », « la fermeté de sa poignée de main » — la qualité abstraite
extraite en tête de groupe nominal, par défaut, pour caractériser.

**Pourquoi ça échoue :** propre au français du modèle, qui préfère la
nominalisation au verbe. Une fois, c'est du style ; en série, chaque personnage
est décrit par la même machine grammaticale — et le procédé passe la relecture
ligne à ligne parce que chaque phrase est correcte.

**Correction :** rendre la qualité au verbe (« il parlait sans hâte »).
**Budget :** au plus **trois pour 1 000 mots**.

## FR-2. Prolepse du narrateur — « il ne le savait pas encore, mais… »

**Class:** constructional · **French-only** · **Budget: 0**

Formes : « il ne le savait pas encore, mais… », « elle ne comprendrait que bien
plus tard… », « ce jour-là allait… ».

**Pourquoi ça échoue :** double faute — tic de narration *et* violation du
Disclosure Horizon Protocol (la révélation appartient à un chapitre ultérieur).
Zero budget for that reason; a hit is Critical under both Pass 2 and Pass 5.

**Correction :** semer l'indice sans nommer la conséquence.

## Typographie française (règles de comptage, pas des tics)

- **Dialogue.** Les guillemets français « … » (avec espaces insécables) et le
  tiret cadratin `—` ouvrant une réplique sont la **ponctuation standard du
  dialogue**. Ils ne comptent **pas** au budget du motif 20 — voir la section 20
  ci-dessus.
- **Espaces insécables** avant `;` `:` `!` `?` et à l'intérieur des `« »` : point
  de correction typographique. À signaler comme défaut de cohérence, jamais
  comme tic.
- **Conventions mélangées** (guillemets droits dans un chapitre, guillemets
  français dans un autre) relèvent du balayage de dérive manuscrit, pas du
  Pass 2.
- **Métriques de dialogue** : `authorkit book stats` compte les ouvertures `«` et
  `—`, donc le dialogue au tiret est mesuré, pas invisible.

## Référence rapide — budgets propres au français

Les motifs prennent les budgets du tableau du catalogue. Ce pack n'en modifie
aucun ; il ajoute les formes à budget 0 ci-dessous, qui bloquent dès la première
occurrence, et les deux entrées françaises FR-1 / FR-2.

| Motif | Forme française à budget 0 |
|---|---|
| 3 | « un certain » / « une certaine » / « particulier » |
| 14 | « qu'il/elle n'aurait su nommer » |
| 15 | « (il/elle) retint son souffle » |
| 21 | « et c'était tout » / « ce fut tout » |
| 29 | l'ensemble greppable ci-dessus |
| 35 | « une lueur de […] dans le regard » |
| FR-2 | prolepse du narrateur |

| Entrée française | Budget |
|---|---|
| FR-1 Nominalisation de caractérisation | 3 pour 1 000 mots |
| FR-2 Prolepse du narrateur | 0 |

**Calibration.** Tout budget reste soumis à la règle du canari d'origine : un
budget égal ou inférieur au taux mesuré de l'origine pour ce motif est mal
réglé — il faut le relever au-dessus de l'origine plutôt que de pénaliser une
prose qui sonne comme la voix du livre.
