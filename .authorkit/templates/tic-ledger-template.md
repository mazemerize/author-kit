# Tic Ledger

**Book**: [BOOK TITLE]
**Updated**: [YYYY-MM-DD]
**Origin Reference**: [voice-origin pin | earliest approved CHs | voice exemplars]
**Origin Load**: [cached tic-load index of the origin chapter, e.g. `0.42 (N=14, as of CH07 review)` — review Pass 2's origin-canary pre-check. Recompute only when the contributing set, its budgets, or the threshold changes; if this reaches `tic_load_mean_threshold` the threshold is mis-set, not the prose.]

<!-- The living, book-specific catalog of AI-typical prose tics, maintained by
     /authorkit.review (Pass 2 — AI-Tic Audit). Entries are DISCOVERED by blind
     contrast against the fixed voice origin, not copied from a universal list;
     the shipped seed catalog (.authorkit/prompts/_shared/literary-tic-catalog.md)
     only bootstraps the first entries.

     REVIEW-SIDE ONLY. Drafting commands never load this file — tic knowledge
     reaches generation exclusively as contrastive pairs in book/voice-pairs.md.

     DISCOVERY vs GATING. Entries here are the unbounded discovery log — the blind
     pass keeps adding shapes it finds. What GATES a given chapter is narrower and
     convergent: on a re-review only the prior review's still-over-budget gating
     shapes (plus a revise-introduced regression) gate; freshly-discovered shapes are
     recorded here as non-gating residual/seeds and carried to the next chapter. See
     /authorkit.review Pass 2 (carry-over rule) and each review's **Gating Shapes** line.

     Lifecycle (review updates Status on every pass):
     - seed     — bootstrap hypothesis from the catalog; retire if unconfirmed
                  after 4 reviews. Exception: zero-budget phrase-class seeds
                  (exact strings, e.g. catalog #29) never retire — dormant at
                  most, since their literal Step B sweep costs nothing.
     - active   — confirmed in this book's drafts; checked on every review.
     - dormant  — 1 consecutive reviewed chapter with zero instances.
     - retired  — 2 further consecutive clean chapters (3 total). Move the entry
                  under ## Retired Entries. A rediscovered retired shape
                  reactivates with its history intact.

     IDs are permanent and never reused. Allocate a new id as max(existing id) + 1
     scanned across ALL sections of this file — Active, Seed AND Retired — never
     per-section: retired entries have already spent their numbers, so taking the
     high-water mark from the live sections alone re-issues ids and files two
     different shapes under one id. Review Step B re-checks for duplicate ids
     before every write-back. -->

## Active Entries

### TIC-001: [short name of the construction]
**Discovered**: [CHnn review, YYYY-MM-DD] ([N] instances) | **Seeded from**: [catalog #NN, bootstrap entries only — omit for discovered entries]
**Shape**: [one-line description of the construction]
**Class**: [lexical | phrase | constructional | structural — optional; `phrase` entries with exact strings are checked by literal search (Grep) in review Step B]
**Lang**: [universal | language subtag (`fr`, `de`, …) — optional, defaults to `universal`. Structural/constructional shapes are `universal`; entries whose content is exact strings belong to the language they were written in. Only entries matching the book's language (or `universal`) are swept and counted.]
**Budget**: [N per chapter | N per 1,000 words | 0 = flag on sight. Seeded entries inherit the seed catalog's budget; discovered entries default to 3 per chapter (0.75/1,000 words in chapters over ~4,000 words)]
**From this book**: "[quoted instance from a draft]" ([CHnn])
**Origin does instead**: "[counter-example from the origin prose — how the origin accomplishes the same job]"
**Trend**: [CHnn: N → CHnn: N → …]
**Status**: [seed | active | dormant]
**Waiver**: [constitution §ref if the author sanctioned this pattern — waived entries are reported, never flagged]

## Retired Entries

<!-- Retired entries move here whole, Status: retired. Kept for provenance and
     reactivation. -->
