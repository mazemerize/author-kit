---
description: Create or refresh the book concept from a natural language book idea description.
handoffs:
  - label: Discuss Ideas First
    agent: authorkit.discuss
    prompt: Brainstorm and explore ideas before committing
  - label: Build World
    agent: authorkit.world.build
    prompt: Build the world for this book concept
  - label: Create Book Outline
    agent: authorkit.outline
    prompt: Create an outline for this book concept.
  - label: Clarify Book Concept
    agent: authorkit.clarify
    prompt: Clarify the book concept — resolve ambiguities
    send: true
  - label: Update Constitution
    agent: authorkit.constitution
    prompt: Refine voice, tone, and style rules to match this concept
scripts:
  sh: scripts/bash/setup-book.sh --json
  ps: scripts/powershell/setup-book.ps1 -Json
---

## User Input

```text
{{USER_INPUT_TOKEN}}
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

The text the user typed after `/authorkit.conceive` in the triggering message **is** the book description. Use the `## User Input` block above as the source. Do not ask the user to repeat it unless they provided an empty command.

Given that book description, do this:

1. **Initialize single-book workspace**:
   - Run `{{SCRIPT_SETUP_BOOK}}` from repo root.
   - Parse JSON output keys: `BOOK_DIR`, `CONCEPT_FILE`, `STYLE_ANCHOR`, `BOOK_TOML`, `HAS_GIT`.
   - Do not create or rename git branches in this command.

2. Load `templates/concept-template.md` to understand required sections.

3. Follow this execution flow:

    1. Parse user description from Input
       If empty: ERROR "No book description provided"
    2. Extract key concepts from description
       Identify: genre, characters/subjects, setting, themes, tone, conflict/thesis
    3. For unclear aspects:
       - Make informed guesses based on genre conventions and context
       - Only mark with [NEEDS CLARIFICATION: specific question] if:
         - The choice significantly impacts the book's direction
         - Multiple reasonable interpretations exist with different implications
         - No reasonable default exists
       - **LIMIT: Maximum 3 [NEEDS CLARIFICATION] markers total**
       - Prioritize clarifications by impact: premise > audience > structure > style details
    4. Fill Premise section
       If no clear premise: ERROR "Cannot determine book premise"
    5. Determine Genre & Audience
       Use genre conventions to fill reasonable defaults
    6. Identify Themes
       Extract from description; infer from genre if not explicit
    7. Define Characters/Subjects
       For fiction: main characters with motivations and arcs
       For non-fiction: key topics and their relationships
    8. Establish Tone & Voice
       Infer from genre and description; use reasonable defaults
    9. Define Scope
       Estimate based on genre conventions (e.g., literary fiction 70-90k words, thriller 80-100k)
    10. Set Success Criteria
        Create book-specific, measurable quality outcomes
    11. Return: SUCCESS (concept ready for outlining)

4. Write the concept to CONCEPT_FILE using the template structure, replacing placeholders with concrete details derived from the book description while preserving section order and headings.

5. **Concept Quality Validation**: After writing the initial concept, validate it inline against these criteria — do **not** create a separate checklist file:

   **Content quality**
   - Premise is compelling and clear in one sentence
   - Genre and audience are well-defined
   - Themes are distinct and relevant to the premise
   - Characters/subjects have clear roles and motivations
   - Voice and tone are specific and consistent with genre

   **Completeness**
   - No `[NEEDS CLARIFICATION]` markers remain (or, if present, ≤ 3 and high-impact only)
   - Success criteria are measurable
   - Scope is realistic for the genre
   - All mandatory sections completed
   - Comparable titles are relevant and well-chosen

   **Readiness**
   - Concept is specific enough to outline from
   - No contradictions between sections
   - Tone description could guide consistent writing

   **Handling results**:
   - If all criteria pass: proceed to reporting.
   - If `[NEEDS CLARIFICATION]` markers remain (max 3): present each as a question with options, wait for user answers, then update the concept.

6. Report completion with the concept path, which validation criteria passed/failed, and readiness for the next phase (`/authorkit.clarify` to resolve concept ambiguities, `/authorkit.discuss` to brainstorm openly, or `/authorkit.outline`).

## Key Rules

### Quick Guidelines

- Focus on **WHAT** the book is about and **WHY** it matters to readers.
- Avoid implementation details (specific chapter content, exact plot points).
- Written to capture the essence and direction of the book.
- DO NOT create any checklists embedded in the concept.

### Section Requirements

- **Mandatory sections**: Must be completed for every book
- **Optional sections**: Include only when relevant
- When a section doesn't apply, remove it entirely (don't leave as "N/A")

### For AI Generation

When creating this concept from a user prompt:

1. **Make informed guesses**: Use genre conventions and common patterns to fill gaps
2. **Document assumptions**: Record reasonable defaults in the Assumptions section
3. **Limit clarifications**: Maximum 3 [NEEDS CLARIFICATION] markers
4. **Think like a reader**: Every vague aspect should be specific enough to generate an outline

**Examples of reasonable defaults** (don't ask about these):
- Chapter count: Genre-standard ranges (literary fiction ~20-25, thriller ~30-40, non-fiction ~12-20)
- Word count: Genre-standard ranges
- POV: Most common for the genre (thriller = third limited, literary = flexible, memoir = first person)
- Tense: Past tense unless genre strongly suggests present
- Structure: Linear unless concept implies otherwise
