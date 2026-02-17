---
description: Identify underspecified areas in the book concept by asking targeted clarification questions and encoding answers back into the concept.
handoffs:
  - label: Create Book Outline
    agent: authorkit.outline
    prompt: Create an outline for this book concept.
  - label: Research A Topic
    agent: authorkit.research
    prompt: Research an ambiguity that needs external grounding
scripts:
  ps: scripts/powershell/check-prerequisites.ps1 -Json -PathsOnly
---

## User Input

```text
{{USER_INPUT_TOKEN}}
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

Goal: Detect and reduce ambiguity or missing decision points in the active book concept and record the clarifications directly in the concept file.

Note: This clarification workflow is expected to run BEFORE invoking `/authorkit.outline`. If the user explicitly states they are skipping clarification, you may proceed, but must warn that downstream rework risk increases.

Execution steps:

1. Run `{{SCRIPT_CHECK_PREREQ}}` from repo root **once**. Parse JSON payload for `BOOK_DIR` and `BOOK_CONCEPT`. If JSON parsing fails, abort and instruct user to re-run `/authorkit.conceive`.

2. Load the current concept file. If `research.md` or `research/` exists, load relevant research artifacts first and use them to resolve or narrow accuracy-sensitive ambiguities. Then perform a structured ambiguity & coverage scan using this taxonomy. For each category, mark status: Clear / Partial / Missing.

   Premise & Scope:
   - Core conflict/thesis clarity
   - Explicit scope boundaries
   - Target length and structure

   Genre & Audience:
   - Genre conventions acknowledged
   - Target reader specificity
   - Comparable titles relevance

   Characters / Subjects:
   - Protagonist/main subject depth
   - Supporting cast/topics sufficiency
   - Character motivations / topic relationships

   Voice & Tone:
   - POV consistency
   - Tense choice rationale
   - Tone specificity (beyond vague adjectives)

   Themes:
   - Theme distinctness
   - Theme-to-narrative mapping
   - Potential theme conflicts

   Structure & Pacing:
   - Structural approach clarity
   - Pacing expectations
   - Part/act division rationale

   World / Setting / Context:
   - Setting specificity
   - World-building requirements (fiction)
   - Context/background needs (non-fiction)

   Research Requirements:
   - Accuracy domains identified
   - Sensitivity areas flagged
   - Expert consultation needs

3. Generate a prioritized queue of candidate clarification questions (maximum 5):
    - Each question must be answerable with EITHER:
       - A short multiple-choice selection (2-5 distinct options), OR
       - A short-phrase answer (<=5 words)
    - Only include questions whose answers materially impact outline, chapter planning, or writing quality.
    - Prioritize: premise clarity > audience > structure > voice > details

4. Sequential questioning loop (interactive):
    - Present EXACTLY ONE question at a time.
    - For multiple-choice questions:
       - Analyze all options and determine the **most suitable option** based on genre best practices and the concept context.
       - Present your **recommended option prominently** with clear reasoning.
       - Format as: `**Recommended:** Option [X] - <reasoning>`
       - Then render all options as a Markdown table.
       - After the table: `You can reply with the option letter, accept the recommendation by saying "yes", or provide your own answer.`
    - After the user answers:
       - If "yes" or "recommended", use your stated recommendation.
       - Validate the answer, then record it.
    - Stop when: all critical ambiguities resolved, user signals "done", or 5 questions asked.

5. Integration after EACH accepted answer:
    - Ensure a `## Clarifications` section exists in the concept (create if missing).
    - Under it, create a `### Session YYYY-MM-DD` subheading for today.
    - Append: `- Q: <question> -> A: <final answer>`.
    - Apply the clarification to the most appropriate section of the concept.
    - Save the concept file AFTER each integration.

6. Validation after each write:
   - Clarifications section contains one bullet per accepted answer.
   - Updated sections contain no lingering vague placeholders the answer was meant to resolve.
   - Markdown structure valid.

7. Write the updated concept back to `BOOK_CONCEPT`.

8. Report completion:
   - Number of questions asked & answered.
   - Path to updated concept.
   - Sections touched.
   - Coverage summary table.
   - Suggested next command (`/authorkit.outline`) or `/authorkit.research` for unresolved accuracy/sensitivity domains.

Behavior rules:
- If no meaningful ambiguities found, respond: "No critical ambiguities detected." and suggest proceeding to outline.
- If concept file missing, instruct user to run `/authorkit.conceive` first.
- Never exceed 5 total questions.
- Respect user early termination ("stop", "done", "proceed").

