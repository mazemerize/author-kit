---
description: Create the book concept from a natural language book idea description.
handoffs:
  - label: Build World
    agent: authorkit.world.build
    prompt: Build the world for this book concept
  - label: Create Book Outline
    agent: authorkit.outline
    prompt: Create an outline for this book concept.
  - label: Clarify Book Concept
    agent: authorkit.clarify
    prompt: Clarify the book concept requirements
    send: true
scripts:
  ps: scripts/powershell/create-new-book.ps1 -Json "{ARGS}"
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

The text the user typed after `/authorkit.conceive` in the triggering message **is** the book description. Assume you always have it available in this conversation even if `{ARGS}` appears literally below. Do not ask the user to repeat it unless they provided an empty command.

Given that book description, do this:

1. **Generate a concise short name** (2-4 words) for the branch:
   - Analyze the book description and extract the most meaningful keywords
   - Create a 2-4 word short name that captures the essence of the book
   - Examples:
     - "A mystery novel set in Victorian London" -> "victorian-mystery"
     - "Technical guide to distributed systems" -> "distributed-systems-guide"
     - "Coming of age story about a young musician" -> "young-musician-story"

2. **Check for existing branches before creating new one**:

   a. First, fetch all remote branches to ensure we have the latest information:

      ```powershell
      git fetch --all --prune
      ```

   b. Find the highest book number across all sources for the short-name:
      - Remote branches: `git ls-remote --heads origin`
      - Local branches: `git branch`
      - Books directories: Check for directories matching `books/[0-9]+-<short-name>`

   c. Determine the next available number:
      - Extract all numbers from all three sources
      - Find the highest number N
      - Use N+1 for the new branch number

   d. Run the script `{SCRIPT}` with the calculated number and short-name:
      - Pass `-Number N+1` and `-ShortName "your-short-name"` along with the book description
      - Example: `{SCRIPT} -Number 1 -ShortName "victorian-mystery" "A mystery novel set in Victorian London"`

   **IMPORTANT**:
   - Check all three sources (remote branches, local branches, books directories) to find the highest number
   - You must only ever run this script once per book
   - The JSON output will contain BRANCH_NAME and CONCEPT_FILE paths

3. Load `templates/concept-template.md` to understand required sections.

4. Follow this execution flow:

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

5. Write the concept to CONCEPT_FILE using the template structure, replacing placeholders with concrete details derived from the book description while preserving section order and headings.

6. **Concept Quality Validation**: After writing the initial concept, validate it:

   a. **Create Concept Quality Checklist**: Generate a checklist file at `BOOK_DIR/checklists/concept-quality.md`:

      ```markdown
      # Concept Quality Checklist: [BOOK TITLE]

      **Purpose**: Validate concept completeness and quality before outlining
      **Created**: [DATE]
      **Book**: [Link to concept.md]

      ## Content Quality

      - [ ] Premise is compelling and clear in one sentence
      - [ ] Genre and audience are well-defined
      - [ ] Themes are distinct and relevant to the premise
      - [ ] Characters/subjects have clear roles and motivations
      - [ ] Voice and tone are specific and consistent with genre

      ## Completeness

      - [ ] No [NEEDS CLARIFICATION] markers remain
      - [ ] Success criteria are measurable
      - [ ] Scope is realistic for the genre
      - [ ] All mandatory sections completed
      - [ ] Comparable titles are relevant and well-chosen

      ## Readiness

      - [ ] Concept is specific enough to outline from
      - [ ] No contradictions between sections
      - [ ] Tone description could guide consistent writing

      ## Notes

      - Items marked incomplete require concept updates before `/authorkit.clarify` or `/authorkit.outline`
      ```

   b. **Run Validation Check**: Review the concept against each checklist item.

   c. **Handle Validation Results**:

      - **If all items pass**: Mark checklist complete and proceed to reporting.

      - **If [NEEDS CLARIFICATION] markers remain** (max 3):
        Present each as a question with options, wait for user answers, then update the concept.

7. Report completion with branch name, concept file path, checklist results, and readiness for the next phase (`/authorkit.clarify` or `/authorkit.outline`).

**NOTE:** The script creates and checks out the new branch and initializes the concept file before writing.

## General Guidelines

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
