---
description: Create the full book outline with chapter breakdowns, character arcs, and thematic mapping.
handoffs:
  - label: Create Chapter Breakdown
    agent: authorkit.chapters
    prompt: Break the outline into chapter tasks
    send: true
  - label: Run Research
    agent: authorkit.research
    prompt: Research grounding for this outline
  - label: Build World First
    agent: authorkit.world.build
    prompt: Build the world before outlining
  - label: Create Checklist
    agent: authorkit.checklist
    prompt: Create a checklist for...
scripts:
  ps: scripts/powershell/setup-outline.ps1 -Json
---

## User Input

```text
{{USER_INPUT_TOKEN}}
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

1. **Setup**: Run `{{SCRIPT_SETUP_OUTLINE}}` from repo root and parse JSON for BOOK_CONCEPT, OUTLINE, BOOK_DIR, CHAPTERS_DIR.

2. **Load context**: Read BOOK_CONCEPT and `/memory/constitution.md`. Load OUTLINE template (already copied by script). If `research.md` exists, load it. If `research/` exists, load relevant topic files (scope `general`, `outline`, and any chapter-targeted files that influence structure).

3. **Execute outline workflow**: Follow the structure in the outline template to:
   - Fill Structural Overview (determine structure type, chapter count, parts/acts)
   - Fill Constitution Check (validate voice/tone/audience alignment)
   - Generate the complete chapter breakdown
   - Map character arcs / concept progression across chapters
   - Map thematic threads across the book

4. **Phases**:

### Phase 0: Research & World-Building

**Check if research artifacts already exist**:

- If `research.md` and/or `research/` exists (typically produced by `/authorkit.research`), treat them as primary research context.
- Do **not** auto-run external research in this command. Use existing artifacts and internal reasoning only.

**Check if world/ folder already exists** (created by `/authorkit.world.build`):

**If world/ exists** (world.build was run before outlining):
1. Read all existing world/ files as primary context (characters/, places/, organizations/, history/, systems/, notes/)
2. Refresh `research.md` as needed as a supplementary summary for research that doesn't fit the world/ structure. If `research/` topic files already exist, fold their conclusions into this summary index.
3. Generate `characters.md` as a summary index pointing to the detailed `world/characters/` files, plus any characters not yet in world/
4. Validate world/ entries against concept.md — flag any inconsistencies
5. If world/ feels incomplete for the story's needs, suggest running `/authorkit.world.build` again to deepen specific areas

**If world/ does NOT exist** (world.build was skipped):
1. **Identify research needs** from the concept:
   - For each setting detail -> research task
   - For each historical/technical claim -> accuracy check
   - For each character background -> consistency check
2. **Generate or refresh research notes** in `research.md` (using existing `research/` topic files when present):
   - Decision: [what was determined]
   - Rationale: [why this choice]
   - Sources: [reference materials or reasoning]
3. **Generate character/subject profiles** in `characters.md`:
   - For fiction: Full character profiles (background, motivation, voice, arc, relationships)
   - For non-fiction: Key concept definitions, relationships between topics, prerequisite knowledge
4. **Note**: For complex books with extensive world-building needs (fantasy, sci-fi, historical), suggest running `/authorkit.world.build` before proceeding to structural design.

**Output**: research.md, characters.md (+ validated world/ if it exists, plus existing research/ topic files if present)

### Phase 1: Structural Design

**Prerequisites**: research.md and characters.md complete (and world/ validated if it exists)

1. **Determine structure**:
   - Based on genre, concept, and themes
   - Decide: linear vs non-linear, number of parts/acts, POV rotation pattern
   - Map the narrative arc or argument flow across chapters

2. **Create chapter entries**:
   - For each chapter: title, purpose, summary, key events/points, characters/concepts, closing beat, connections
   - Ensure each chapter has a clear reason to exist
   - Verify pacing: mix of high-tension and breathing-room chapters

3. **Map arcs and threads**:
   - Track each character's development chapter by chapter
   - Map each theme's introduction, development, and resolution
   - Identify foreshadowing opportunities and payoff locations

**Output**: Completed outline.md with all sections filled

### Phase 2: Validation

1. **Constitution Check**: Re-verify against book constitution
2. **Completeness Check**: Every chapter has purpose, summary, key events, and connections
3. **Arc Check**: Every major character has a complete arc; every theme is introduced and resolved
4. **Pacing Check**: No section of the book has too many slow or too many intense chapters in a row

5. **Stop and report**: Command ends after validation. Report OUTLINE path, generated artifacts (research.md, characters.md), and whether research/ topics were consumed.

## Key Rules

- Use absolute paths
- Each chapter entry must be detailed enough to plan independently
- The outline should make it possible to draft any chapter without needing to draft preceding ones first (though reading them helps)
- Genre conventions should inform but not constrain the structure

