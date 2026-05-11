---
description: Run grounded, multi-source research for a specific topic and record reusable research artifacts. Offers world sync when findings warrant it.
handoffs:
  - label: Discuss Findings
    agent: authorkit.discuss
    prompt: Talk through what the research surfaced before committing to artifacts
  - label: Write Next Chapter With Findings
    agent: authorkit.write
    prompt: Plan chapter [N] using the latest research
  - label: Review Manuscript For Drift
    agent: authorkit.review
    prompt: Sweep the manuscript after research updates landed in world/
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --paths-only
  ps: scripts/powershell/check-prerequisites.ps1 -Json -PathsOnly
---

## User Input

```text
{{USER_INPUT_TOKEN}}
```

You **MUST** consider the user input before proceeding (if not empty). The input must include a research topic and may include optional directives:

- `scope: clarify|world|outline|chapter N|general` (default: `general`)
- `sources: auto|web|news|wikipedia|mcp` (default: `auto`)
- `folder: <relative-path-under-research>` (optional explicit placement override)

Free-form text is interpreted first; explicit directives override inferred values.

## Goal

Perform grounded research from available sources, then store results as reusable artifacts:

- `BOOK_DIR/research.md` (index + summary)
- `BOOK_DIR/research/**/*.md` (topic-level notes; flat or nested)

By default this command writes only research artifacts. **World sync is offered automatically when findings are durable and clearly belong in `world/`** — but a world write never happens without explicit author approval in the chat.

## Outline

1. **Setup**: Run `{{SCRIPT_CHECK_PREREQ}}` from repo root (the `scripts:` frontmatter selects the right shell-flavor flags). Parse `BOOK_DIR` and `BOOK_CONCEPT`. All paths must be absolute.

2. **Parse user intent and optional directives**:
   - Infer topic, scope, and source preferences from free-form text first.
   - Extract explicit `scope:`, `sources:`, and `folder:` directives if present. Explicit directives override inferred values.
   - If the topic is empty after parsing: ERROR *"Please provide a research topic (for example: `/authorkit.research Research forensic botany for chapter 7`)."*
   - If `folder:` is provided, validate it is a safe relative path under `research/` (no absolute paths, no traversal like `..`). If invalid: ERROR with correction guidance.
   - Unclear inference normalizes to defaults: `scope = general`, `sources = auto`.

3. **Resolve scope details**:
   - `chapter N` from either free-form text or `scope: chapter N` normalizes to `CHNN` and the chapter target is recorded on the topic file.
   - Other scopes map directly: `clarify`, `world`, `outline`, `general`.

4. **Resolve topic file path**:

   **Precedence (highest wins)**:
   1. Existing topic file (matched by frontmatter `id` anywhere under `BOOK_DIR/research/`) — always update in place; no relocation.
   2. Explicit `folder:` directive — write to `BOOK_DIR/research/<folder>/<id>-<slug>.md`.
   3. `scope:`-based folder map (when nested placement is warranted; see below).
   4. Adaptive flat-first placement at `BOOK_DIR/research/<id>-<slug>.md`.

   - Ensure `BOOK_DIR/research/` exists.
   - First, search recursively under `BOOK_DIR/research/` for an existing topic file with matching frontmatter `id`. If found, update that file in place.
   - Otherwise, if `folder:` is provided, write to `BOOK_DIR/research/<folder>/<id>-<slug>.md`.
   - Otherwise use adaptive flat-first placement:
     - Default to `BOOK_DIR/research/<id>-<slug>.md`.
     - Route to a nested scope folder only when there is a clear grouping reason:
       - matching scope folder already exists, or
       - there are already 3 or more topic files in that scope cluster, or
       - user intent clearly requests grouped/series organization.
   - Scope folder map when nested placement is warranted:
     - `clarify` -> `research/clarify/`
     - `world` -> `research/world/`
     - `outline` -> `research/outline/`
     - `general` -> `research/general/`
     - `chapter N` -> `research/chapters/CHNN/`
   - For simple one-off topics with no grouping signal, keep flat placement.

5. **Load context**:
   - **Required**: `concept.md`
   - **Optional**: `outline.md`
   - **Optional**: `chapters/NN/plan.md` and `chapters/NN/draft.md` for chapter scope
   - **Optional**: `world/_index.md` and relevant `world/` files
   - **Optional**: existing `research.md` and existing files under `research/` (recursive)

6. **Determine source strategy**:
   - If `sources` resolves to `auto`, use all available source families: web/news/Wikipedia/MCP.
   - If a subset is requested or overridden, use only that subset.
   - If one source family is unavailable, continue with available sources and log it under "Source Availability Notes".

7. **Run research and synthesize findings**:
   - Collect facts, constraints, and tradeoffs relevant to the topic and scope.
   - Track claims with citations and confidence.
   - Surface contradictions between sources or with existing book artifacts.
   - Explicitly separate:
     - grounded findings
     - interpretation/inference
     - unresolved questions

8. **Write research artifacts**:

   a. Create or update the topic file at the resolved path from step 4 using `.authorkit/templates/research-topic-template.md`. Required frontmatter fields:
      - `id`, `topic`, `scope`, `chapter_targets`, `sources_used`, `created_at`, `updated_at`, `status`, `world_sync_status`
      Required claims table columns:
      - `Claim ID`, `Claim`, `Source Type`, `Source Title`, `Locator`, `Accessed`, `Confidence`
      `Locator` must be a URL or MCP URI.

   b. Create or update `BOOK_DIR/research.md` using `.authorkit/templates/research-index-template.md`. Add/update the row for this topic with status and world sync state. Maintain an "Open follow-ups" section for unresolved questions.

9. **Decide whether to offer world sync**:

   Assess the findings against these criteria. Offer world sync only when **all** of these are true:
   - The scope is `world`, `chapter N`, or `general` (not `clarify` — clarify routes through `/authorkit.discuss`).
   - At least one finding is **durable** (a stable fact about the book's setting / system / character / organization / history), not transient context or interpretation.
   - The durable finding maps to a recognizable world category (places, organizations, history, systems, characters, notes).
   - The finding either creates a new entry or adds a non-conflicting detail to an existing entry. If it **conflicts** with an existing `(CONCEPT)` or `(CHxx)` entry, do NOT offer auto-sync — recommend `/authorkit.discuss "<change description>"` to route it through Cross-cutting change.

   If world sync is warranted, **propose it**: name the world file(s) you would write, name the tag (`(CONCEPT)` if scope is general / world / outline; `(CHxx)` if scope is `chapter N`), and ask: *"Sync these findings to world/? (yes / no)"*. Wait for explicit approval.

10. **World sync (only on author approval)**:

    - Resolve world note path using this order:
      - If an existing note for this slug is found at either `BOOK_DIR/world/notes/research-<slug>.md` or `BOOK_DIR/world/notes/research/<slug>.md`, update that path in place.
      - Else if the resolved research topic path from step 4 is nested OR `BOOK_DIR/world/notes/research/` already exists, write to `BOOK_DIR/world/notes/research/<slug>.md`.
      - Else write to `BOOK_DIR/world/notes/research-<slug>.md`.
    - Convert durable findings to world notes tagged appropriately.
    - Update frontmatter fields on the world note according to `.authorkit/templates/world-entity-frontmatter.md`.
    - Rebuild the world index with `{{SCRIPT_BUILD_WORLD_INDEX}}` from repo root.
    - Update the topic file's frontmatter `world_sync_status` to `synced`.

11. **Report completion**:
    - Topic researched and scope used
    - Source families requested vs used
    - Paths written (`research.md`, topic file, optional world note)
    - Key findings with confidence
    - Contradictions/risks
    - Follow-up questions
    - Suggested next step:
      - `clarify` / `world` / `outline` scope → `/authorkit.discuss <focus>` (World Seed or Clarify mode)
      - `chapter N` scope → `/authorkit.write [N]`
      - World sync just ran → `/authorkit.review` to surface any new drift surfaced by the new world details

## Key Rules

- **Grounding first**: prefer verifiable sources over speculation.
- **Suggest-only by default**: world writes happen only after explicit chat-level approval.
- **Preserve compatibility**: `research.md` remains the top-level index for downstream commands.
- **Structured output required**: always maintain both `research.md` and at least one topic file in `research/` (flat or nested).
- **Preserve human layout**: if a topic already exists in a human-organized folder, update it there; do not auto-migrate files.
- **Use absolute paths** when reading or writing files.
- **Flag conflicts; don't auto-resolve.** If a finding conflicts with an existing world entry, route through `/authorkit.discuss` rather than silently overwriting.
