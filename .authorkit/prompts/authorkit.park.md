---
description: Defer a creative decision for later resolution without blocking the writing process.
handoffs:
  - label: Resolve a Parked Decision
    agent: authorkit.park
    prompt: Resolve the parked decision about...
  - label: Pivot Based on Decision
    agent: authorkit.pivot
    prompt: Apply the resolved decision as a pivot
scripts:
  ps: scripts/powershell/check-prerequisites.ps1 -Json -PathsOnly
---

## User Input

```text
{{USER_INPUT_TOKEN}}
```

You **MUST** consider the user input before proceeding (if not empty).

## Goal

Not every creative uncertainty needs to be resolved immediately. This command provides a structured way to flag decisions that can be deferred ("parked") while writing continues, with deadlines and context so they don't get lost.

The command operates in three modes:

- **Park a decision**: Add a new deferred decision with context and deadline
- **List parked decisions**: Show all open decisions with their urgency
- **Resolve a decision**: Mark a decision as resolved and optionally trigger downstream actions

## Outline

1. **Setup**: Run `{{SCRIPT_CHECK_PREREQ}}` from repo root and parse BOOK_DIR. All paths must be absolute.

2. **Determine mode** from user input:

   - **Park mode** (default — user describes a question or uncertainty):
     - Input like: "How does the magic system handle time travel?", "Should Marcus die in Act 3?", "park: whether to use first or third person for flashbacks"
   - **List mode** (user asks to see parked decisions):
     - Input like: "list", "show", "status", "what's parked?"
   - **Resolve mode** (user wants to close a parked decision):
     - Input like: "resolve: the magic system uses temporal anchors", "resolve PD-003: Marcus lives"

3. **Park Mode** — Add a new deferred decision:

   a. Parse the question/uncertainty from user input.

   b. Ask the user (max 3 questions) to establish context:
      - Where does this decision matter? (which chapters, which artifacts)
      - How urgent is it? When must it be resolved? (e.g., "before CH12", "before Act 3", "anytime")
      - Any leading options? (e.g., "Option A: he dies. Option B: he's captured.")
      If the user input already provides this context, skip questions.

   c. Ensure `BOOK_DIR/parked-decisions.md` exists. If not, create it with header:

      ```markdown
      # Parked Decisions

      Deferred creative decisions that need resolution before the book is complete.
      Use `/authorkit.park` to add, list, or resolve decisions.

      ---
      ```

   d. Generate a sequential ID: `PD-001`, `PD-002`, etc. (based on existing entries).

   e. Append the new decision:

      ```markdown
      ## PD-NNN: [SHORT TITLE]

      **Status**: OPEN
      **Parked**: [DATE]
      **Deadline**: [Before CHNN / Before Part N / Before final draft / No deadline]
      **Urgency**: [Blocking (must resolve before next chapter) / Soon (within 3-5 chapters) / Eventually (before manuscript complete)]

      ### Question

      [The decision that needs to be made]

      ### Context

      - **Affects**: [List of artifacts — chapters, characters, world files, outline sections]
      - **Background**: [Why this is uncertain — what led to the question]

      ### Options Considered

      - **Option A**: [Description] — [Pros/cons if known]
      - **Option B**: [Description] — [Pros/cons if known]
      - **Option C**: [If applicable]

      ### Resolution

      *Unresolved*

      ---
      ```

   f. **Check existing chapter plans for deadline proximity**: If any chapter currently being planned or drafted is near the deadline, warn the user immediately.

   g. Report: Decision parked, ID assigned, deadline noted, current count of open decisions.

4. **List Mode** — Show all parked decisions:

   a. Read `BOOK_DIR/parked-decisions.md`. If it doesn't exist: "No parked decisions. Use `/authorkit.park [question]` to park a decision."

   b. Present a summary table:

      ```markdown
      ## Parked Decisions Summary

      | ID | Title | Status | Urgency | Deadline | Parked Date |
      |----|-------|--------|---------|----------|-------------|
      | PD-001 | Magic and time travel | OPEN | Soon | Before CH12 | 2026-02-01 |
      | PD-002 | Marcus's fate | OPEN | Eventually | Before Act 3 | 2026-02-05 |
      | PD-003 | Flashback POV | RESOLVED | - | - | 2026-01-28 |
      ```

   c. **Deadline warnings**: Check the current book progress (from chapters.md status markers). For each OPEN decision:
      - If deadline chapter is currently being planned/drafted: **URGENT — deadline reached**
      - If deadline chapter is 1-2 chapters away: **APPROACHING**
      - Otherwise: on track

   d. Report summary with any urgency warnings.

5. **Resolve Mode** — Close a parked decision:

   a. Parse the decision ID and resolution from user input.

   b. Find the decision in `parked-decisions.md`.

   c. Update the entry:
      - Change **Status** to `RESOLVED`
      - Fill in the **Resolution** section with:
        ```markdown
        ### Resolution

        **Decided**: [DATE]
        **Decision**: [What was decided]
        **Rationale**: [Why this option was chosen]
        **Next Steps**: [Any actions needed — pivot, revise, update world, etc.]
        ```

   d. **Assess downstream impact**:
      - Does the resolution require changes to existing artifacts?
      - If yes: recommend `/authorkit.pivot` for broad changes or `/authorkit.revise` for targeted fixes
      - If the resolution introduces new world-building elements: recommend `/authorkit.world.build` to establish them

   e. Report: Decision resolved, any recommended follow-up actions.

## Integration with Other Commands

The following commands check `parked-decisions.md` for deadline proximity:

- **`/authorkit.chapter.plan`**: Before planning a chapter, check if any parked decisions have a deadline at or before this chapter. If so, warn: "Parked decision PD-NNN has a deadline before this chapter. Consider resolving it first."
- **`/authorkit.chapter.draft`**: Same check before drafting.
- **`/authorkit.analyze`**: Include parked decisions in the analysis report — list OPEN decisions that have passed their deadlines as HIGH severity findings.

## Key Rules

- **Never block writing.** The whole point is to keep momentum. Parking a decision explicitly permits moving forward with uncertainty.
- **Be specific about deadlines.** "Eventually" is acceptable, but "Before CH12" is better. The earlier a deadline is known, the better.
- **Track options.** Even vague options help future resolution. Capture what the author is considering.
- **Warn proactively.** When deadlines approach, warn loudly — but don't force resolution.
- **Resolution is action.** Resolving a parked decision often triggers downstream work (pivot, revise, world update). Always suggest next steps.
- **Keep the file clean.** Resolved decisions stay in the file (for historical reference) but are clearly marked RESOLVED.

