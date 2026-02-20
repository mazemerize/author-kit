---
description: Create or update the book constitution - voice, tone, style guide, and writing principles.
handoffs:
  - label: Conceive Book
    agent: authorkit.conceive
    prompt: Define the book concept. The book is about...
---

## User Input

```text
{{USER_INPUT_TOKEN}}
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

You are updating the book constitution at `/memory/constitution.md`. This file is a TEMPLATE containing placeholder tokens in square brackets (e.g. `[BOOK_TITLE]`, `[PRINCIPLE_1_NAME]`). Your job is to (a) collect/derive concrete values, (b) fill the template precisely, and (c) ensure all writing guidelines are clear and actionable.

Follow this execution flow:

1. Load the existing constitution template at `/memory/constitution.md`.
   - Identify every placeholder token of the form `[ALL_CAPS_IDENTIFIER]`.
   **IMPORTANT**: The user might require fewer or more principles than the template provides. Adjust accordingly.

2. Collect/derive values for placeholders:
   - If user input supplies a value, use it.
   - Otherwise infer from existing book context (concept.md, outline.md, prior constitution versions).
   - For governance dates: `RATIFICATION_DATE` is the original adoption date, `LAST_AMENDED_DATE` is today if changes are made.
   - `CONSTITUTION_VERSION` must increment according to semantic versioning:
     - MAJOR: Fundamental voice/style change.
     - MINOR: New principle added or materially expanded.
     - PATCH: Clarifications, wording refinements.

3. Draft the updated constitution:
   - Replace every placeholder with concrete text.
   - Ensure each principle is actionable and testable during chapter review.
   - Voice & Style principles should be specific enough that two different writers would produce similar prose.
   - Include examples where helpful (e.g., "DO: 'The door creaked open.' DON'T: 'The ancient, weathered door slowly and painfully creaked open.'").

4. Key areas to cover (adapt based on genre):
   - **Voice**: POV, tense, narrative distance, formality level
   - **Tone**: Emotional register, humor policy, darkness/lightness balance
   - **Audience**: Target reader, assumed knowledge, accessibility requirements
   - **Prose Standards**: Show vs tell policy, dialogue rules, description density, sentence rhythm
   - **Naming & Numbers**: Naming originality requirements and numeric-specificity policy (rationale-first numbers, uncertainty handling when precision is unsupported)
   - **Content Boundaries**: Sensitivity guidelines, research accuracy requirements, content warnings
   - **Structural Rules**: Chapter length targets, scene transition style, cliffhanger policy

5. Validation before final output:
   - No remaining unexplained bracket tokens.
   - Principles are declarative and testable.
   - Dates in ISO format YYYY-MM-DD.
   - Each principle could be used as a review criterion.

6. Write the completed constitution back to `/memory/constitution.md` (overwrite).

7. Output a final summary to the user with:
   - New version and bump rationale.
   - Key principles established.
   - Suggested next step: `/authorkit.conceive` to define the book concept.

