---
description: Create a full or partial book outline with chapter breakdowns, character arcs, and thematic mapping. Supports incremental outlining — outline part of the book now, extend later.
handoffs:
  - label: Create Chapter Breakdown
    agent: authorkit.chapters
    prompt: Break the outline into chapter tasks
    send: true
  - label: Extend Outline
    agent: authorkit.outline
    prompt: Extend the outline with the next section
  - label: Run Research
    agent: authorkit.research
    prompt: Research grounding for this outline
  - label: Build World First
    agent: authorkit.world.build
    prompt: Build the world before outlining
  - label: Discuss Ideas
    agent: authorkit.discuss
    prompt: Brainstorm ideas before outlining
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

2. **Load context**: Read BOOK_CONCEPT and `/memory/constitution.md`. Load OUTLINE template (already copied by script). If `research.md` exists, load it. If `research/` exists, load relevant topic files recursively (scope `general`, `outline`, and any chapter-targeted files that influence structure).

3. **Determine scope** from user input:

   Parse the user input for scope indicators:
   - **No scope** (empty input, or "full"): Full outline — generate all chapters. This is the default and preserves existing behavior.
   - **Partial scope** ("part 1", "act I", "chapters 1-8", "first 5 chapters"): Generate the structural overview for the ENTIRE book, but only create detailed chapter entries for the requested range.
   - **Extend** ("extend", "continue", "next part", "next section"): Extend an existing partial outline with the next section of chapters. Requires an existing outline.md with a Continuation Notes section.

   If extend mode is requested but no outline.md exists: ERROR "No outline to extend. Run `/authorkit.outline` or `/authorkit.outline [scope]` first."

   If extend mode is requested and outline.md exists but has no "Continuation Notes" section: treat as a full outline that's already complete. Warn the user and ask if they want to add more chapters beyond the current outline.

4. **Execute outline workflow**: Follow the structure in the outline template to:
   - Fill Structural Overview (determine structure type, chapter count, parts/acts) — **always for the full book**, even in partial mode
   - Fill Constitution Check (validate voice/tone/audience alignment)
   - Generate chapter breakdowns — **for the requested scope only** (all chapters in full mode, selected range in partial mode, next section in extend mode)
   - Map character arcs / concept progression — for outlined chapters, with notes on expected direction for un-outlined portions
   - Map thematic threads — for outlined chapters, with notes on expected continuation

5. **Phases**:

### Phase 0: Research & World-Building

**Check if research artifacts already exist**:

- If `research.md` and/or `research/` exists (typically produced by `/authorkit.research`), treat them as primary research context, including nested topic folders.
- Do **not** auto-run external research in this command. Use existing artifacts and internal reasoning only.

**Check if world/ folder already exists** (created by `/authorkit.world.build`):

**If world/ exists** (world.build was run before outlining):
1. Read all existing world/ files as primary context (characters/, places/, organizations/, history/, systems/, notes/)
2. Refresh `research.md` as needed as a supplementary summary for research that doesn't fit the world/ structure. If `research/` topic files already exist anywhere under `research/`, fold their conclusions into this summary index.
3. Generate `characters.md` as a summary index pointing to the detailed `world/characters/` files, plus any characters not yet in world/
4. Validate world/ entries against concept.md — flag any inconsistencies
5. If world/ feels incomplete for the story's needs, suggest running `/authorkit.world.build` again to deepen specific areas

**If world/ does NOT exist** (world.build was skipped):
1. **Identify research needs** from the concept:
   - For each setting detail -> research task
   - For each historical/technical claim -> accuracy check
   - For each character background -> consistency check
2. **Generate or refresh research notes** in `research.md` (using existing `research/` topic files discovered recursively when present):
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

1. **Determine structure** (always for the full book):
   - Based on genre, concept, and themes
   - Decide: linear vs non-linear, number of parts/acts, POV rotation pattern
   - Map the narrative arc or argument flow across chapters
   - This structural overview is generated regardless of scope — even partial outlines need the full picture at a high level

2. **Create chapter entries** (scope-dependent):

   **Full mode**: Create detailed entries for ALL chapters.

   **Partial mode**: Create detailed entries only for the requested range (e.g., Part 1 chapters). For parts/chapters outside the scope, include only a one-line directional note in the Structural Overview table — do not create full chapter entries.

   **Extend mode**:
   - Read the existing outline.md, including its Continuation Notes section
   - Read any chapters drafted since the last outline session (check chapters.md for `[D]` or `[X]` statuses)
   - Use the Continuation Notes (open threads, character positions, thematic state) plus drafted chapter content as context
   - Generate detailed chapter entries for the next logical section (next part/act, or a reasonable batch of 3-8 chapters)
   - Append these entries to the existing Chapter Breakdown — do NOT replace existing entries

   For all modes:
   - For each chapter in scope: title, purpose, summary, key events/points, characters/concepts, closing beat, connections
   - Ensure each chapter has a clear reason to exist
   - Verify pacing: mix of high-tension and breathing-room chapters

3. **Map arcs and threads** (scope-aware):
   - Track each character's development across outlined chapters
   - Map each theme's progression across outlined chapters
   - Identify foreshadowing opportunities and payoff locations within scope
   - For partial/extend mode: note expected arc directions and thematic continuation beyond the outlined section

4. **Generate Continuation Notes** (partial and extend mode only):

   If the outline does not cover all chapters, populate the "Continuation Notes" section of the template:
   - **Last Outlined Through**: The last chapter/part with detailed entries
   - **Open Plot Threads**: Every unresolved plot thread at the end of the outlined section, with its current state and expected direction
   - **Character Arc Positions**: Where each major character stands at the end of the outlined section and where they're heading
   - **Thematic Threads In Progress**: Which themes have been introduced/developed but not resolved
   - **Notes for Next Outlining Session**: Anything the next `/authorkit.outline extend` should know — upcoming tone shifts, planned reveals, structural considerations

   For **full mode**: Remove the Continuation Notes section from the template entirely (or leave it empty with a note that the outline is complete).

**Output**: Completed outline.md — full or partial with Continuation Notes

### Phase 2: Validation

1. **Constitution Check**: Re-verify against book constitution
2. **Completeness Check**: Every outlined chapter has purpose, summary, key events, and connections
3. **Arc Check** (scope-aware):
   - **Full mode**: Every major character has a complete arc; every theme is introduced and resolved
   - **Partial/Extend mode**: Every arc within the outlined section has a clear trajectory; arcs extending beyond the section are documented in Continuation Notes
4. **Pacing Check**: No section of the outlined chapters has too many slow or too many intense chapters in a row

5. **Stop and report**: Command ends after validation. Report:
   - OUTLINE path
   - Generated artifacts (research.md, characters.md)
   - Whether research/ topics (including nested folders) were consumed
   - **Scope**: Whether this is a full or partial outline, and which chapters are covered
   - **If partial**: Remind the author they can run `/authorkit.outline extend` after drafting the outlined chapters to continue

## Key Rules

- Use absolute paths
- Each chapter entry must be detailed enough to plan independently
- The outline should make it possible to draft any chapter without needing to draft preceding ones first (though reading them helps)
- Genre conventions should inform but not constrain the structure

