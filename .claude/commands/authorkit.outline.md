---
description: Create the full book outline with chapter breakdowns, character arcs, and thematic mapping.
handoffs:
  - label: Create Chapter Breakdown
    agent: authorkit.chapters
    prompt: Break the outline into chapter tasks
    send: true
  - label: Create Checklist
    agent: authorkit.checklist
    prompt: Create a checklist for...
scripts:
  ps: scripts/powershell/setup-outline.ps1 -Json
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

1. **Setup**: Run `{SCRIPT}` from repo root and parse JSON for BOOK_CONCEPT, OUTLINE, BOOK_DIR, CHAPTERS_DIR, BRANCH.

2. **Load context**: Read BOOK_CONCEPT and `/memory/constitution.md`. Load OUTLINE template (already copied by script).

3. **Execute outline workflow**: Follow the structure in the outline template to:
   - Fill Structural Overview (determine structure type, chapter count, parts/acts)
   - Fill Constitution Check (validate voice/tone/audience alignment)
   - Generate the complete chapter breakdown
   - Map character arcs / concept progression across chapters
   - Map thematic threads across the book

4. **Phases**:

### Phase 0: Research & World-Building

1. **Identify research needs** from the concept:
   - For each setting detail -> research task
   - For each historical/technical claim -> accuracy check
   - For each character background -> consistency check

2. **Generate research notes** in `research.md`:
   - Decision: [what was determined]
   - Rationale: [why this choice]
   - Sources: [reference materials or reasoning]

3. **Generate character/subject profiles** in `characters.md`:
   - For fiction: Full character profiles (background, motivation, voice, arc, relationships)
   - For non-fiction: Key concept definitions, relationships between topics, prerequisite knowledge

**Output**: research.md, characters.md

### Phase 1: Structural Design

**Prerequisites**: research.md and characters.md complete

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

5. **Stop and report**: Command ends after validation. Report branch, OUTLINE path, and generated artifacts (research.md, characters.md).

## Key Rules

- Use absolute paths
- Each chapter entry must be detailed enough to plan independently
- The outline should make it possible to draft any chapter without needing to draft preceding ones first (though reading them helps)
- Genre conventions should inform but not constrain the structure
