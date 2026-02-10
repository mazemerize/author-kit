---
description: Build the book's world before writing - establish rules, geography, characters, history, and systems.
mode: agent
---

## User Input

```text
${input:focusAreas}
```

You **MUST** consider the user input before proceeding (if not empty). The user input may specify focus areas (e.g., "magic system", "political structure", "geography") or be blank for comprehensive world-building.

## Goal

Establish the rules, geography, characters, history, and systems of the book's world **before** outlining or drafting. This is proactive world-building: the author defines the world first, then writes within it.

This command can be run multiple times to iteratively deepen specific areas.

## Outline

1. **Setup**: Run `.authorkit/scripts/powershell/check-prerequisites.ps1 -Json -PathsOnly` from repo root and parse BOOK_DIR. All paths must be absolute.

2. **Load context**:
   - **Required**: concept.md (premise, genre, themes, characters, setting)
   - **Optional**: `.authorkit/memory/constitution.md` (voice, tone — informs world-building style)
   - **Optional**: Existing `World/` folder (if running iteratively to deepen)

3. **Assess genre and determine relevant categories**:

   Not all books need all categories. Select based on genre:

   | Category | Fantasy/Sci-fi | Historical | Contemporary | Non-fiction |
   |----------|---------------|-----------|-------------|------------|
   | Characters/ | Yes | Yes | Yes | Rarely |
   | Organizations/ | Yes | Often | Sometimes | Sometimes |
   | Places/ | Yes | Yes | Sometimes | Rarely |
   | History/ | Yes | Yes | Rarely | Sometimes |
   | Systems/ | Yes (magic, tech) | Sometimes (social) | Rarely | Often (frameworks) |
   | Notes/ | Always | Always | Always | Always |

   If user specified focus areas, only work on those categories. Otherwise, work through all relevant categories.

4. **For each relevant category**, either:

   a. **If user input specifies details**: Accept them directly, organize into the appropriate format.

   b. **If concept.md is rich enough**: Extract and expand details from the concept. Make informed decisions based on genre conventions.

   c. **If details are sparse**: Ask the user targeted questions. Limit to the most impactful questions per category (max 3 questions per category to avoid overwhelming).

   **Genre-specific question areas**:

   - **Fantasy/Sci-fi**: Magic systems (rules, costs, limitations, who can use it), technology level, races/species and their cultures, cosmology (gods, creation myths, planes of existence), geography (continents, climate, biomes, travel times), political structure (nations, empires, city-states), economy (trade, resources, currency), religions and philosophies, languages and naming conventions, key historical events that shaped the current world
   - **Historical fiction**: Time period and specific year(s), what is historically accurate vs fictional, cultural norms and daily life, available technology, social hierarchy and class structure, key historical events as backdrop, real historical figures included
   - **Contemporary**: Geographic setting (city, region, country), social/cultural milieu, key institutions (schools, companies, government), technology and communication norms, socioeconomic context
   - **Non-fiction**: Conceptual framework and taxonomy, key terminology with precise definitions, domain structure and relationships, prerequisite knowledge the reader needs, competing theories or approaches

5. **Create the World/ folder structure**:

   ```
   BOOK_DIR/World/
   ├── Characters/
   ├── Organizations/
   ├── Places/
   ├── History/
   ├── Systems/
   └── Notes/
   ```

   Only create folders for categories relevant to this book.

6. **Create initial files** in each category using the chapter-tagged format:

   All pre-writing entries are tagged `(CONCEPT)` to indicate they were established before any chapter was written. This distinguishes them from details that emerge during drafting (which will be tagged `(CHxx)` by `authorkit.world.update`).

   **Characters/** — One file per major character:
   ```markdown
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

   **Places/** — One file per significant location:
   ```markdown
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

   **Organizations/** — One file per faction/group:
   ```markdown
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

   **History/** — One file per significant past event:
   ```markdown
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

   **Systems/** — One file per system (magic, technology, politics, economy, etc.):
   ```markdown
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

   **Notes/** — For general world-building notes that don't fit elsewhere:
   ```markdown
   # [Topic]

   - [Note] (CONCEPT)
   ```

7. **Internal consistency validation**:
   - Check that character relationships are reciprocal (if A is B's enemy, B should know about A)
   - Check that systems don't contradict each other
   - Check that geography is plausible (travel times, climate zones, resource distribution)
   - Check that history is internally consistent (cause precedes effect)
   - Flag any contradictions or gaps for the user

8. **Report completion**:
   - Summary of World/ files created, organized by category
   - Count of entries per category
   - Any consistency warnings or gaps flagged
   - Areas that could benefit from more depth
   - Suggested next step: `authorkit.world.build [specific area]` to deepen, or `authorkit.outline` to proceed to outlining

## Key Rules

- **This is reference material, not prose.** World/ files should read like an encyclopedia, not a novel.
- **Be specific, not vague.** "A large city" is bad. "A port city of ~200,000 on the western coast, built on steep hills overlooking a natural harbor" is good.
- **Tag everything (CONCEPT).** This tag is critical for the evolution tracking system. When chapters are drafted and `authorkit.world.update` runs, new details will be tagged with chapter numbers.
- **Don't over-build.** Only create entries for things that will actually matter to the story. A magic system with 50 rules that only appears once is wasted effort. Focus on what the reader will encounter.
- **Cross-reference.** Use relative paths to link related entries (e.g., "See Characters/elena-voss.md" or "Related: History/the-great-war.md").
- **Iterative by design.** This command can be run multiple times. Each run should deepen or add, not replace. If World/ already has entries, read them first and build on them.
- **Genre-appropriate depth.** An epic fantasy might need 30+ World/ files. A contemporary romance might need 5. Scale to the book's needs.
