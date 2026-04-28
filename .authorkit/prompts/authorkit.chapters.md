---
description: Generate the chapter-level task breakdown from the book outline.
handoffs:
  - label: Plan First Chapter
    agent: authorkit.chapter.plan
    prompt: Plan chapter 1
  - label: Analyze For Consistency
    agent: authorkit.analyze
    prompt: Run a cross-chapter consistency analysis
scripts:
  sh: scripts/bash/check-prerequisites.sh --json
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
   - **Optional**: research.md and `research/` topic files discovered recursively (world-building and accuracy notes), characters.md (character profiles, topic definitions)

3. **Detect partial outline**:
   - Check outline.md for a "Continuation Notes" section with "Last Outlined Through"
   - If present: the outline is partial — only chapters with full detailed entries should get chapter breakdown entries
   - If absent: the outline is complete — process all chapters

4. **Check for existing chapters.md** (incremental extension):
   - If chapters.md already exists: read it and preserve all existing entries with their current statuses (`[P]`, `[D]`, `[R]`, `[X]`)
   - New entries will be appended for any newly outlined chapters not already in chapters.md
   - Do NOT overwrite or reset existing entries

5. **Execute chapter breakdown workflow**:
   - Load outline.md and extract the chapter list — only chapters with full detailed entries (purpose, summary, key events, connections), not one-line directional notes from the Structural Overview
   - Load concept.md and extract voice, themes, and scope
   - If characters.md exists: map character appearances to chapters
   - If research.md or research/ exists: map research needs and topic files (including nested folders) to relevant chapters by scope and chapter targets
   - Generate the chapter task list organized by parts/acts — for outlined chapters only
   - Create dependency notes showing chapter connections
   - Validate completeness: every fully outlined chapter has an entry; if partial outline, note which chapters are not yet outlined

6. **Generate or update chapters.md**: Use `templates/chapters-template.md` as structure, fill with:
   - Book title from concept.md
   - Chapters organized by parts/acts (from outline.md) — only for chapters with detailed outline entries
   - Each chapter entry: `- [ ] CHNN [Part?] Title - One-line summary`
   - Part checkpoints with verification criteria
   - Drafting strategy recommendation (sequential, key-scene-first, or part-by-part)
   - Dependencies & connections section
   - All entries use the status marker system: `[ ]`, `[P]`, `[D]`, `[R]`, `[X]`
   - If chapters.md already existed: merge new entries after existing ones, preserving existing statuses
   - If the outline is partial: include the "Incremental Outlining" section from the template noting that more chapters will be added after `/authorkit.outline extend`

7. **Report**: Output path to generated chapters.md and summary:
   - Total chapter count (outlined so far)
   - Chapters per part/act
   - Key dependencies identified
   - Recommended drafting order
   - Estimated total word count (from chapter targets for outlined chapters)
   - If partial outline: note how many chapters are outlined vs. estimated total, and remind the author to run `/authorkit.outline extend` after drafting

## Key Rules

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

