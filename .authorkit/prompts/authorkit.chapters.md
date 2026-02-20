---
description: Generate the chapter-level task breakdown from the book outline.
handoffs:
  - label: Plan First Chapter
    agent: authorkit.chapter.plan
    prompt: Plan chapter 1
    send: true
  - label: Analyze For Consistency
    agent: authorkit.analyze
    prompt: Run a cross-chapter consistency analysis
    send: true
scripts:
  ps: scripts/powershell/check-prerequisites.ps1 -Json
---

## User Input

```text
{{USER_INPUT_TOKEN}}
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

1. **Setup**: Run `{{SCRIPT_CHECK_PREREQ}}` from repo root and parse BOOK_DIR and AVAILABLE_DOCS list. All paths must be absolute.

2. **Load design documents**: Read from BOOK_DIR:
   - **Required**: outline.md (chapter structure, arcs, themes), concept.md (premise, audience, voice)
   - **Optional**: research.md and `research/` topic files (world-building and accuracy notes), characters.md (character profiles, topic definitions)

3. **Execute chapter breakdown workflow**:
   - Load outline.md and extract chapter list with their parts/acts
   - Load concept.md and extract voice, themes, and scope
   - If characters.md exists: map character appearances to chapters
   - If research.md or research/ exists: map research needs and topic files to relevant chapters by scope and chapter targets
   - Generate the chapter task list organized by parts/acts
   - Create dependency notes showing chapter connections
   - Validate completeness (every outline chapter has an entry, every theme is covered)

4. **Generate chapters.md**: Use `templates/chapters-template.md` as structure, fill with:
   - Book title from concept.md
   - Chapters organized by parts/acts (from outline.md)
   - Each chapter entry: `- [ ] CHNN [Part?] Title - One-line summary`
   - Part checkpoints with verification criteria
   - Drafting strategy recommendation (sequential, key-scene-first, or part-by-part)
   - Dependencies & connections section
   - All entries use the status marker system: `[ ]`, `[P]`, `[D]`, `[R]`, `[X]`

5. **Report**: Output path to generated chapters.md and summary:
   - Total chapter count
   - Chapters per part/act
   - Key dependencies identified
   - Recommended drafting order
   - Estimated total word count (from chapter targets)

## Chapter Entry Rules

**CRITICAL**: Each chapter entry must be concise but informative enough to plan from.

### Format (REQUIRED)

```text
- [ ] CHNN [Part?] Title - Brief summary
```

**Format Components**:

1. **Status marker**: ALWAYS start with `- [ ]` (pending)
2. **Chapter ID**: Sequential (CH01, CH02, CH03...)
3. **[Part] label**: Include if book has parts/acts (e.g., [Part 1], [Act II])
4. **Title**: The chapter title from the outline
5. **Summary**: One-line description of what happens/is covered

**Examples**:

- `- [ ] CH01 [Part 1] The Arrival - Iria discovers the abandoned estate and its hidden library`
- `- [ ] CH05 [Part 2] Breaking Point - The alliance fractures when secrets surface`
- `- [ ] CH01 Introduction - Overview of distributed systems and why they matter`
- `- [ ] CH08 Advanced Patterns - Saga pattern, event sourcing, and CQRS in practice`

### Organization

1. Group chapters by parts/acts (if applicable)
2. Include part purpose and checkpoint criteria
3. Note key dependencies between chapters
4. Track cross-chapter elements (recurring motifs, evolving relationships, building arguments)

Context for chapter generation: {ARGS}

