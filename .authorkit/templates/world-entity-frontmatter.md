# World Entity Frontmatter Schema

This document defines the YAML frontmatter schema for world/ entity files. Both index builders (`build-world-index.sh`, `build-world-index.ps1`) and the AI assistant reference this schema.

## Frontmatter Block

Every world/ entity file should have a YAML frontmatter block between `---` delimiters at the top of the file, before the H1 heading. The body content below the frontmatter is unchanged.

```yaml
---
id: char-iria-calder
type: character
name: Iria Calder
aliases: [Iria, Captain Calder, the Navigator, Calder]
chapters: [CONCEPT, CH01, CH03, CH05]
first_appearance: CH01
relationships:
  - target: char-jonas-hale
    type: mentor-of
    since: CONCEPT
  - target: org-iron-guild
    type: member-of
    since: CH03
tags: [protagonist, magic-user]
last_updated: 2026-02-13
---
# Iria Calder

## Current State

[Canonical now-truth as of the latest drafted chapter. Concise, factual, NO chapter tags.]

## History

- (CONCEPT) [Detail established in pre-writing.]
- (CH01) [Detail confirmed/added when CH01 was drafted.]
- (CH03-rev) [Detail changed in the CH03 revision — supersedes the matching Current State line.]
```

## Body Structure: Current State + History

The body below the frontmatter has two parts. This split is what keeps an entity file legible as a book grows — without it, a long-running character file becomes a palimpsest where the current truth has to be reconstructed by reading every tagged layer in order.

### `## Current State` (canonical now-truth)

Concise factual statements describing the entity **as it stands at the latest drafted chapter** — appearance, role, relationships, status. This is the authoritative view: drafting (`/authorkit.write`) and consistency-checking (`/authorkit.review`) read Current State as truth and must not have to reconstruct it from the full history.

- **No chapter tags in Current State.** Tags live in History. Because the index builders (`build-world-index.sh`/`.ps1`) extract the `chapters` field by scanning the body for `(CONCEPT)`/`(CHxx)` patterns, the untagged Current State block is invisible to them and never pollutes the tag aggregation.
- When a later chapter changes a fact, **supersede the matching Current State line in place** (surgical edit) — never append a contradicting one. Current State is a summary, not a log; keep it short.

### `## History` (provenance / audit trail)

The append-only, chapter-tagged log of how the entity evolved. Every detail is tagged: `(CONCEPT)` pre-writing, `(CHxx)` first appearance/confirmation, `(CHxx-rev)` revision, `(AMEND-YYYY-MM-DD)` amendment. Routine reconciliation only **appends** here — it never rewrites History. It answers "when did this fact enter the book?" and lets a consolidation pass reconstruct or repair Current State.

A superseded History line stays in place (provenance is the point); the supersession is reflected by updating Current State, not by deleting history. A consolidation pass (`/authorkit.review`) may move long-dead History entries under a `### Superseded` subheading, but only with author approval and a snapshot — it still never deletes provenance.

**Legacy files** with a flat tagged body (no headings) remain valid: treat the whole body as History with an empty Current State. The next reconcile, or a `/authorkit.review` consolidation pass, populates Current State from the draft-verified now-truth.

## Field Reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique entity identifier: `{type_prefix}-{kebab-name}` |
| `type` | enum | Yes | One of: `character`, `place`, `organization`, `event`, `system`, `note` |
| `name` | string | Yes | Display name matching the H1 heading |
| `aliases` | string[] | Yes (can be `[]`) | All known name variants, nicknames, titles, abbreviated forms |
| `chapters` | string[] | Yes | All chapter tags found in this file: `CONCEPT`, `CH01`, `CH03-rev`, etc. |
| `first_appearance` | string | Yes | First chapter where the entity appears in manuscript (not counting CONCEPT) |
| `relationships` | object[] | Yes (can be `[]`) | Structural connections to other entities |
| `relationships[].target` | string | Yes | The `id` of the related entity |
| `relationships[].type` | string | Yes | Freeform relationship descriptor (see guidelines below) |
| `relationships[].since` | string | Yes | When established: `CONCEPT`, `CHxx`, etc. |
| `tags` | string[] | No | Freeform classification tags for filtering |
| `last_updated` | date | Yes | ISO date of last modification (YYYY-MM-DD) |

## Entity ID Format

IDs use the format: `{type_prefix}-{kebab-case-name}`

### Type Prefixes

| world/ Directory | `type` Value | ID Prefix | Example |
|-----------------|-------------|-----------|---------|
| characters/ | `character` | `char-` | `char-iria-calder` |
| places/ | `place` | `place-` | `place-iron-quarter` |
| organizations/ | `organization` | `org-` | `org-iron-guild` |
| history/ | `event` | `event-` | `event-great-war` |
| systems/ | `system` | `sys-` | `sys-blood-magic` |
| notes/ | `note` | `note-` | `note-naming-conventions` |

### Kebab-Case Rules

- Lowercase all characters
- Replace spaces with hyphens
- Remove leading articles ("The Iron Guild" -> `iron-guild`)
- Remove punctuation
- Collapse multiple hyphens

### Stability

IDs **never change** once assigned, even if the entity is renamed. If "Iria Calder" becomes "Iria Nareth", the ID remains `char-iria-calder` and "Iria Nareth" is added to `aliases`. This prevents cascading updates to cross-references.

### Uniqueness

The type prefix prevents collisions between entity types sharing a name. Within a type, uniqueness comes from the kebab name. If two characters share a name (two "Marcus"), disambiguate: `char-marcus-reid` vs `char-marcus-thorne`.

## Alias Guidelines

Aliases capture all name variants readers or writers might use:

- **Shortened forms**: "Iria" for "Iria Calder"
- **Titles/honorifics**: "Captain Calder", "Commander Hale", "Queen Lyra"
- **Nicknames**: "the Doctor", "the Iron Hand"
- **Former names**: "Iria Calder" after she becomes "Iria Nareth"
- **Role references**: "the protagonist", "the mentor" (only when unambiguous)

The entity's `name` field is implicitly an alias (not listed in `aliases` since it's in `name`). The index builder includes both `name` and all `aliases` entries in the Alias Lookup.

**Ambiguity**: If an alias maps to multiple entities (e.g., "Marcus" could be two characters), it's still listed in both entities' `aliases`. The index builder flags it as ambiguous. Resolution uses chapter context: if only one "Marcus" appears in a given chapter, the alias resolves to that entity.

## Chapter Tag Vocabulary

The `chapters` field aggregates all evolution tags found in the file body:

| Tag Pattern | Meaning | Example |
|-------------|---------|---------|
| `CONCEPT` | Established during pre-writing world-building | `CONCEPT` |
| `CHxx` | First appeared or confirmed in chapter xx | `CH01`, `CH03` |
| `CHxx-rev` | Updated when chapter xx was revised | `CH07-rev` |
| `AMEND-YYYY-MM-DD` | Changed during a direction or fact amendment (`/authorkit.discuss` Cross-cutting change) | `AMEND-2026-02-13` |

## Relationship Conventions

Relationship types are freeform strings but should be descriptive and consistent. Common patterns:

**Character-to-Character**: `mentor-of`, `mentored-by`, `parent-of`, `child-of`, `sibling-of`, `spouse-of`, `ally-of`, `rival-of`, `enemy-of`, `friend-of`, `employer-of`, `employed-by`, `commands`, `commanded-by`, `betrayed`, `betrayed-by`

**Character-to-Organization**: `member-of`, `has-member`, `leader-of`, `led-by`, `founder-of`, `founded-by`

**Character-to-Place**: `resides-at`, `inhabited-by`, `born-at`, `birthplace-of`, `works-at`, `rules`, `ruled-by`

**Character-to-System**: `practitioner-of`, `practiced-by`, `creator-of`, `created-by`, `bound-by`, `binds`

**Character-to-Event**: `participated-in`, `involved`, `caused`, `caused-by`, `victim-of`

**Organization-to-Organization**: `ally-of`, `rival-of`, `subsidiary-of`, `parent-org-of`

**Organization-to-Place**: `based-at`, `hosts`, `operates-in`, `controls`, `controlled-by`

**Event-to-Place**: `occurred-at`, `site-of`

Relationships should ideally be reciprocal: if Iria has `member-of` → Iron Guild, the Iron Guild file should have `has-member` → Iria. The reconcile pass (`/authorkit.write`) cross-references connected entities so the reciprocal is added to the other file.

## Backward Compatibility

Files without frontmatter remain valid. The index builders (`build-world-index.sh`, `build-world-index.ps1`) handle them by:

1. Deriving `id` from the file path (e.g., `characters/iria-calder.md` → `char-iria-calder`)
2. Extracting `name` from the first H1 heading
3. Extracting `chapters` by scanning the body for `(CONCEPT)`, `(CHxx)`, etc.
4. Setting `aliases` to empty
5. Flagging the file as `[NO FRONTMATTER]` in the index

Run `build-world-index.ps1 -AddFrontmatter` to batch-add frontmatter to files that lack it.
