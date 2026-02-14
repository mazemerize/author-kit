# Author Kit

You are an AI writing assistant working within the Author Kit framework. Author Kit is a structured, template-driven toolkit for writing books chapter by chapter, draft by draft.

## Project Structure

- `.authorkit/memory/constitution.md` — The book's style bible (voice, tone, writing principles)
- `.authorkit/templates/` — Templates for concept, outline, chapters, chapter plans, and checklists
- `.authorkit/scripts/powershell/` — Automation scripts for book setup and prerequisite checking
- `books/` — All book output (one subdirectory per book, named `NNN-short-name`)

## Workflow

The Author Kit workflow is sequential, but supports mid-process pivots at any stage:

1. **Constitution** → Define voice, tone, and style principles
2. **Conceive** → Create the book concept from a natural language description
3. **Clarify** → Resolve ambiguities in the concept (optional)
4. **World Build** → Establish the book's world: rules, geography, characters, history, systems (optional)
5. **Outline** → Generate the full book outline with arcs and themes
6. **Chapters** → Break the outline into a chapter task list
7. **Chapter Plan → Draft → Review** → Iterate each chapter through plan/draft/review
8. **World Update** → Extract world details from drafted chapters into the World/ folder
9. **World Verify** → Check World/ files for internal consistency and manuscript alignment
10. **Analyze** → Cross-chapter consistency analysis
11. **Revise** → Apply targeted fixes
12. **Checklist** → Generate quality checklists

At any point during steps 5-12, mid-process commands can be used to change direction, defer decisions, explore alternatives, or restructure the manuscript.

## Key Conventions

- Chapter status markers: `[ ]` pending, `[P]` planned, `[D]` drafted, `[R]` reviewed, `[X]` approved
- Chapter IDs: `CH01`, `CH02`, etc.
- Book branches: `NNN-short-name` (e.g., `001-victorian-mystery`)
- The constitution is the authoritative style guide — all writing must comply with it
- Use absolute paths when working with files
- PowerShell scripts in `.authorkit/scripts/powershell/` handle book setup and prerequisite validation
- World/ entity files use YAML frontmatter for structured metadata (`id`, `type`, `name`, `aliases`, `chapters`, `relationships`). See `.authorkit/templates/world-entity-frontmatter.md` for the schema.
- `World/_index.md` is a PowerShell-generated index (Entity Registry, Alias Lookup, Chapter Manifest). Rebuild with `/authorkit.world.index` after modifying World/ files.

## Available Commands

Use the slash commands in `.claude/commands/` to trigger structured workflows:

### Core Workflow
- `/authorkit.constitution` — Create/update writing principles
- `/authorkit.conceive` — Define a new book concept
- `/authorkit.clarify` — Resolve concept ambiguities
- `/authorkit.outline` — Create the full book outline
- `/authorkit.chapters` — Generate chapter task breakdown

### Chapter-Level Commands
- `/authorkit.chapter.plan` — Plan a specific chapter
- `/authorkit.chapter.draft` — Write chapter prose
- `/authorkit.chapter.review` — Review a drafted chapter
- `/authorkit.chapter.reorder` — Reorder, split, or merge chapters with automatic renumbering

### World Maintenance
- `/authorkit.world.build` — Build the book's world (rules, geography, characters, history, systems)
- `/authorkit.world.update` — Extract world details from drafted chapters into World/ folder
- `/authorkit.world.verify` — Verify World/ files for consistency and manuscript alignment
- `/authorkit.world.index` — Build/rebuild the World/ entity index (`_index.md`) for fast lookups

### Quality & Analysis
- `/authorkit.analyze` — Cross-chapter analysis (read-only)
- `/authorkit.reconcile` — Check outline, concept, chapters.md, and World/ for drift against drafted chapters
- `/authorkit.revise` — Apply revisions to chapters
- `/authorkit.checklist` — Generate quality checklists

### Mid-Process Changes
- `/authorkit.pivot` — Propagate a direction change across all artifacts with impact analysis
- `/authorkit.retcon` — Retroactively change an established fact across the entire manuscript
- `/authorkit.park` — Defer a creative decision for later resolution
- `/authorkit.snapshot` — Bookmark the current state with narrative context
- `/authorkit.whatif` — Explore an alternative direction on an experimental branch
