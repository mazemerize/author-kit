---
description: Run grounded, multi-source research for a specific topic and record reusable research artifacts.
handoffs:
  - label: Build Outline
    agent: authorkit.outline
    prompt: Build or update the outline using the latest research artifacts
  - label: Build World
    agent: authorkit.world.build
    prompt: Expand world-building with the latest research findings
  - label: Rebuild World Index
    agent: authorkit.world.index
    prompt: Rebuild world index after research sync
  - label: Plan Chapter
    agent: authorkit.chapter.plan
    prompt: Plan chapter [N] with updated research context
scripts:
  ps: scripts/powershell/check-prerequisites.ps1 -Json -PathsOnly
---

## User Input

```text
{{USER_INPUT_TOKEN}}
```

You **MUST** consider the user input before proceeding (if not empty). The user input should include a research topic and may include directives:

- `scope: clarify|world|outline|chapter N|general` (default: `general`)
- `sources: auto|web|news|wikipedia|mcp` (default: `auto`)
- `action: suggest|sync-world` (default: `suggest`)

Prefer free-form interpretation first. Treat explicit directives as optional overrides.

## Goal

Perform grounded research from available sources, then store results as reusable artifacts:

- `BOOK_DIR/research.md` (index + summary)
- `BOOK_DIR/research/*.md` (topic-level notes)

By default, this command is **suggest-only** and does not modify `world/` files. World updates happen only when `action: sync-world` is explicitly requested.

## Outline

1. **Setup**: Run `{{SCRIPT_CHECK_PREREQ}} -Json -PathsOnly` from repo root and parse `BOOK_DIR` and `BOOK_CONCEPT`. All paths must be absolute.

2. **Parse user intent and optional directives**:
   - Infer topic, scope, source preferences, and sync intent from free-form text first.
   - Extract explicit `scope:`, `sources:`, and `action:` directives if present.
   - Explicit directives override inferred values.
   - If topic is empty after parsing: ERROR "Please provide a research topic (for example: `/authorkit.research Research forensic botany for chapter 7`)."
   - If inference is unclear, normalize defaults:
     - `scope = general`
     - `sources = auto`
     - `action = suggest`

3. **Resolve scope details**:
   - `chapter N` from either free-form text or `scope: chapter N` should normalize to `CHNN` and include chapter targets in the topic file.
   - Other scopes map directly: `clarify`, `world`, `outline`, `general`.

4. **Load context**:
   - **Required**: `concept.md`
   - **Optional**: `outline.md`
   - **Optional**: `chapters/NN/plan.md` and `chapters/NN/draft.md` for chapter scope
   - **Optional**: `world/_index.md` and relevant world/ files
   - **Optional**: existing `research.md` and existing files in `research/`

5. **Determine source strategy**:
   - If sources resolve to `auto`, use all available source families: web/news/Wikipedia/MCP.
   - If a subset is requested or overridden, use only that subset.
   - If one source family is unavailable, continue with available sources and log it under "Source Availability Notes".

6. **Run research and synthesize findings**:
   - Collect facts, constraints, and tradeoffs relevant to the topic and scope.
   - Track claims with citations and confidence.
   - Surface contradictions between sources or with existing book artifacts.
   - Explicitly separate:
     - grounded findings
     - interpretation/inference
     - unresolved questions

7. **Write research artifacts**:

   a. Ensure `BOOK_DIR/research/` exists.

   b. Create or update a topic file:
   - Path: `BOOK_DIR/research/<id>-<slug>.md`
   - Use `.authorkit/templates/research-topic-template.md`
   - Required frontmatter fields:
     - `id`, `topic`, `scope`, `chapter_targets`, `sources_used`, `created_at`, `updated_at`, `status`, `world_sync_status`
   - Required claims table columns:
     - `Claim ID`, `Claim`, `Source Type`, `Source Title`, `Locator`, `Accessed`, `Confidence`
   - `Locator` must be URL or MCP URI.

   c. Create or update `BOOK_DIR/research.md`:
   - Use `.authorkit/templates/research-index-template.md`
   - Add/update row for this topic with status and world sync state.
   - Keep an "Open follow-ups" section for unresolved questions.

8. **Optional world sync** (only when action resolves to `sync-world`):
   - Create/update `BOOK_DIR/world/notes/research-<slug>.md`.
   - Convert durable findings to world notes tagged with `(CONCEPT)` or `(CHxx)` based on scope.
   - Update frontmatter fields in the world note according to `.authorkit/templates/world-entity-frontmatter.md`.
   - Rebuild world index by running `{{SCRIPT_BUILD_WORLD_INDEX}}` from repo root.
   - Update topic frontmatter `world_sync_status` to `synced`.

9. **Report completion**:
   - Topic researched and scope used
   - Source families requested vs used
   - Paths written (`research.md`, topic file, optional world note)
   - Key findings with confidence
   - Contradictions/risks
   - Follow-up questions
   - Suggested next step:
     - clarify/world scope -> `/authorkit.world.build` or `/authorkit.outline`
     - chapter scope -> `/authorkit.chapter.plan [N]`
     - sync-world mode -> `/authorkit.world.verify`

## Key Rules

- **Grounding first**: Prefer verifiable sources over speculation.
- **Suggest-only by default**: Do not modify `world/` unless `action: sync-world` is explicit.
- **Preserve compatibility**: `research.md` remains the top-level index for downstream commands.
- **Structured output required**: always maintain both `research.md` and at least one topic file in `research/`.
- **Use absolute paths** when reading or writing files.
