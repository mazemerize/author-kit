---
description: Build the book's world before writing - establish rules, geography, characters, history, and systems.
handoffs:
  - label: Discuss World Ideas
    agent: authorkit.discuss
    prompt: Brainstorm world-building ideas before committing
  - label: Build Outline
    agent: authorkit.outline
    prompt: Create the book outline using the established world
  - label: Deepen World
    agent: authorkit.world.build
    prompt: Expand world-building in the area of...
  - label: Sync World
    agent: authorkit.world.sync
    prompt: Verify the world files for internal consistency
  - label: Amend Existing Chapters
    agent: authorkit.amend
    prompt: New world rules conflict with already-drafted chapters — propagate the correct version
  - label: Research A Topic
    agent: authorkit.research
    prompt: Research a world-building topic before adding it to world files
scripts:
  ps: scripts/powershell/check-prerequisites.ps1 -Json -PathsOnly
---

## User Input

```text
{{USER_INPUT_TOKEN}}
```

You **MUST** consider the user input before proceeding (if not empty). The user input may specify focus areas (e.g., "magic system", "political structure", "geography") or be blank for comprehensive world-building.

## Goal

Establish the rules, geography, characters, history, and systems of the book's world **before** outlining or drafting. This is proactive world-building: the author defines the world first, then writes within it.

This command can be run multiple times to iteratively deepen specific areas.

## Outline

1. **Setup**: Run `{{SCRIPT_CHECK_PREREQ}}` from repo root and parse BOOK_DIR. All paths must be absolute.

2. **Load context**:
   - **Required**: concept.md (premise, genre, themes, characters, setting)
   - **Optional**: `/memory/constitution.md` (voice, tone — informs world-building style)
   - **Optional**: Existing `world/` folder (if running iteratively to deepen)
   - **Optional**: `research.md` and relevant `research/` topic files discovered recursively (use these grounded findings as inputs when they match requested focus areas)

3. **Assess genre and determine relevant categories**:

   Not all books need all categories. Select based on genre:

   | Category | Fantasy/Sci-fi | Historical | Contemporary | Non-fiction |
   |----------|---------------|-----------|-------------|------------|
   | characters/ | Yes | Yes | Yes | Rarely |
   | organizations/ | Yes | Often | Sometimes | Sometimes |
   | places/ | Yes | Yes | Sometimes | Rarely |
   | history/ | Yes | Yes | Rarely | Sometimes |
   | systems/ | Yes (magic, tech) | Sometimes (social) | Rarely | Often (frameworks) |
   | notes/ | Always | Always | Always | Always |

   If user specified focus areas, only work on those categories. Otherwise, work through all relevant categories.

4. **For each relevant category**, either:

   a. **If user input specifies details**: Accept them directly, organize into the appropriate format.

   b. **If concept.md is rich enough**: Extract and expand details from the concept. If `research/` contains relevant grounded findings (including nested folders), prefer those over unsupported assumptions.

   c. **If details are sparse**: Ask the user targeted questions. Limit to the most impactful questions per category (max 3 questions per category to avoid overwhelming).

   **Genre-specific question areas**:

   - **Fantasy/Sci-fi**: Magic systems (rules, costs, limitations, who can use it), technology level, races/species and their cultures, cosmology (gods, creation myths, planes of existence), geography (continents, climate, biomes, travel times), political structure (nations, empires, city-states), economy (trade, resources, currency), religions and philosophies, languages and naming conventions, key historical events that shaped the current world
   - **Historical fiction**: Time period and specific year(s), what is historically accurate vs fictional, cultural norms and daily life, available technology, social hierarchy and class structure, key historical events as backdrop, real historical figures included
   - **Contemporary**: Geographic setting (city, region, country), social/cultural milieu, key institutions (schools, companies, government), technology and communication norms, socioeconomic context
   - **Non-fiction**: Conceptual framework and taxonomy, key terminology with precise definitions, domain structure and relationships, prerequisite knowledge the reader needs, competing theories or approaches

5. **Create the world/ folder structure**:

   Only create folders for categories that have content to put in them. Use the genre relevance table in step 3 to guide this — if a category is "Rarely" or "Sometimes" for this genre and neither the concept nor user input mentions anything for it, **skip that folder entirely**. Do not create empty placeholder folders.

   For example, a contemporary romance might only need `characters/` and `notes/`. An epic fantasy might need all six. A non-fiction book might only need `systems/` and `notes/`.

   ```
   BOOK_DIR/world/
   ├── characters/      (if needed)
   ├── organizations/   (if needed)
   ├── places/          (if needed)
   ├── history/         (if needed)
   ├── systems/         (if needed)
   └── notes/           (if needed)
   ```

6. **Decide file placement per entity before writing**:
   - If an entity already exists (resolve via `world/_index.md` by `id`/aliases, or by recursive world/ scan if no index), update that existing file in place.
   - Never relocate or normalize existing files; preserve human-organized folder layouts.
   - For new entities, default to category root (`characters/`, `places/`, etc.).
   - Create/use a category subfolder only when there is a clear grouping reason:
     - an appropriate grouping subfolder already exists, or
     - this run creates 3+ new entities sharing one clear grouping label (region/faction/era/domain).
   - Auto-created nesting depth is one level under the category root. Deeper human-created nesting remains valid and should be preserved.

7. **Create initial files** in each category using the chapter-tagged format:

   All pre-writing entries are tagged `(CONCEPT)` to indicate they were established before any chapter was written. This distinguishes them from details that emerge during drafting (which will be tagged `(CHxx)` by `/authorkit.world.sync`).

   **characters/** — One file per major character (see `.authorkit/templates/world-entity-frontmatter.md` for full schema):
   ```markdown
   ---
   id: char-[kebab-name]
   type: character
   name: [Character Name]
   aliases: [short name, title, nickname, etc.]
   chapters: [CONCEPT]
   first_appearance: CONCEPT
   relationships:
     - target: [related-entity-id]
       type: [relationship-type]
       since: CONCEPT
   tags: [role tags]
   last_updated: [YYYY-MM-DD]
   ---
   # [Character Name]

   ## Identity
   - **Full name**: [Name] (CONCEPT)
   - **Title/Role**: [Title] (CONCEPT)
   - **Age**: [Age or range] (CONCEPT)

   ## Appearance
   - **Build**: [Description] (CONCEPT)
   - **Hair**: [Description] (CONCEPT)
   - **Eyes**: [Description] (CONCEPT)
   - **Distinguishing features**: [Description] (CONCEPT)

   ## Personality
   - [Trait 1] (CONCEPT)
   - [Trait 2] (CONCEPT)

   ## Relationships
   - **[Other Character]**: [Nature of relationship] (CONCEPT)

   ## Background
   - [Key background detail] (CONCEPT)

   ## Arc
   - CONCEPT: [Planned character arc summary]
   ```

   **places/** — One file per significant location:
   ```markdown
   ---
   id: place-[kebab-name]
   type: place
   name: [Place Name]
   aliases: [short name, alternate names]
   chapters: [CONCEPT]
   first_appearance: CONCEPT
   relationships:
     - target: [related-entity-id]
       type: [relationship-type]
       since: CONCEPT
   tags: [location tags]
   last_updated: [YYYY-MM-DD]
   ---
   # [Place Name]

   ## Description
   - [Physical description] (CONCEPT)

   ## Significance
   - [Why this place matters to the story] (CONCEPT)

   ## Key Features
   - [Notable feature] (CONCEPT)

   ## Control/Inhabitants
   - [Who lives here or controls it] (CONCEPT)

   ## First Appearance: (planned)
   ```

   **organizations/** — One file per faction/group:
   ```markdown
   ---
   id: org-[kebab-name]
   type: organization
   name: [Organization Name]
   aliases: [short name, alternate names]
   chapters: [CONCEPT]
   first_appearance: CONCEPT
   relationships:
     - target: [related-entity-id]
       type: [relationship-type]
       since: CONCEPT
   tags: [faction tags]
   last_updated: [YYYY-MM-DD]
   ---
   # [Organization Name]

   ## Purpose
   - [What this group exists to do] (CONCEPT)

   ## Key Members
   - [Member]: [Role] (CONCEPT)

   ## Structure
   - [How the organization is structured] (CONCEPT)

   ## Relationships
   - **[Other Org]**: [Nature of relationship] (CONCEPT)

   ## First Appearance: (planned)
   ```

   **history/** — One file per significant past event:
   ```markdown
   ---
   id: event-[kebab-name]
   type: event
   name: [Event Name]
   aliases: [short name, alternate names]
   chapters: [CONCEPT]
   first_appearance: CONCEPT
   relationships:
     - target: [related-entity-id]
       type: [relationship-type]
       since: CONCEPT
   tags: [event tags]
   last_updated: [YYYY-MM-DD]
   ---
   # [Event Name]

   ## When
   - [Time period or date] (CONCEPT)

   ## Who
   - [Key participants] (CONCEPT)

   ## What Happened
   - [Description of the event] (CONCEPT)

   ## Significance
   - [How this event shapes the current story] (CONCEPT)
   ```

   **systems/** — One file per system (magic, technology, politics, economy, etc.):
   ```markdown
   ---
   id: sys-[kebab-name]
   type: system
   name: [System Name]
   aliases: [short name, alternate names]
   chapters: [CONCEPT]
   first_appearance: CONCEPT
   relationships:
     - target: [related-entity-id]
       type: [relationship-type]
       since: CONCEPT
   tags: [system tags]
   last_updated: [YYYY-MM-DD]
   ---
   # [System Name]

   ## Rules
   - [Rule 1] (CONCEPT)
   - [Rule 2] (CONCEPT)

   ## Limitations/Costs
   - [Limitation 1] (CONCEPT)

   ## Scope
   - [Who can use it / where it applies / how widespread] (CONCEPT)

   ## Manifestations
   - [How this system shows up in the story] (CONCEPT)

   ## Exceptions
   - [Any known exceptions to the rules] (CONCEPT)
   ```

   **notes/** — For general world-building notes that don't fit elsewhere:
   ```markdown
   ---
   id: note-[kebab-name]
   type: note
   name: [Topic]
   aliases: []
   chapters: [CONCEPT]
   first_appearance: CONCEPT
   relationships: []
   tags: [reference tags]
   last_updated: [YYYY-MM-DD]
   ---
   # [Topic]

   - [Note] (CONCEPT)
   ```

8. **Build the world/ index**: Run `.authorkit/scripts/powershell/build-world-index.ps1 -Json` from the repo root to generate `world/_index.md`. This creates the Entity Registry, Alias Lookup, and Chapter Manifest for fast lookups across all commands.

9. **Internal consistency validation**:
   - Check that character relationships are reciprocal (if A is B's enemy, B should know about A)
   - Check that systems don't contradict each other
   - Check that geography is plausible (travel times, climate zones, resource distribution)
   - Check that history is internally consistent (cause precedes effect)
   - Flag any contradictions or gaps for the user

10. **Report completion**:
   - Summary of world/ files created, organized by category
   - Count of entries per category
   - Any consistency warnings or gaps flagged
   - Areas that could benefit from more depth
   - Suggested next step: `/authorkit.research [topic]` for additional grounding, `/authorkit.world.build [specific area]` to deepen, `/authorkit.world.sync` to check internal consistency, or `/authorkit.outline` to proceed to outlining

## Key Rules

- **This is reference material, not prose.** world/ files should read like an encyclopedia, not a novel.
- **Be specific, not vague.** "A large city" is bad. "A port city of ~200,000 on the western coast, built on steep hills overlooking a natural harbor" is good.
- **Tag everything (CONCEPT).** This tag is critical for the evolution tracking system. When chapters are drafted and `/authorkit.world.sync` runs, new details will be tagged with chapter numbers.
- **YAML frontmatter is recommended but optional.** New files created by this command include full frontmatter (`id`, `type`, `name`, `aliases`, `chapters`, `first_appearance`, `relationships`, `tags`, `last_updated` — see `.authorkit/templates/world-entity-frontmatter.md`). However, files the author creates or edits by hand do not need frontmatter — `/authorkit.world.sync` can read them without it and can add frontmatter later via its `add-frontmatter` mode.
- **Don't over-build.** Only create entries for things that will actually matter to the story. A magic system with 50 rules that only appears once is wasted effort. Focus on what the reader will encounter.
- **Cross-reference.** Use relative paths to link related entries (e.g., "See characters/iria-calder.md" or "Related: history/the-great-war.md").
- **Iterative by design.** This command can be run multiple times. Each run should deepen or add, not replace. If world/ already has entries, read them first and build on them.
- **Preserve human structure.** If files are manually moved into logical subfolders, keep updating them in place.
- **Genre-appropriate depth.** An epic fantasy might need 30+ world/ files. A contemporary romance might need 5. Scale to the book's needs.

