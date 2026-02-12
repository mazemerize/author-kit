---
description: Defer a creative decision for later resolution without blocking the writing process.
mode: agent
---

## User Input

```text
${input:parkInput}
```

You **MUST** consider the user input before proceeding (if not empty).

## Goal

Not every creative uncertainty needs to be resolved immediately. This command provides a structured way to flag decisions that can be deferred ("parked") while writing continues, with deadlines and context so they don't get lost.

The command operates in three modes:

- **Park a decision**: Add a new deferred decision with context and deadline
- **List parked decisions**: Show all open decisions with their urgency
- **Resolve a decision**: Mark a decision as resolved and optionally trigger downstream actions

## Outline

1. **Setup**: Run `.authorkit/scripts/powershell/check-prerequisites.ps1 -Json -PathsOnly` from repo root and parse BOOK_DIR. All paths must be absolute.

2. **Determine mode** from user input:

   - **Park mode** (default): User describes a question or uncertainty
   - **List mode**: Input like "list", "show", "status"
   - **Resolve mode**: Input like "resolve: the magic system uses temporal anchors", "resolve PD-003: Marcus lives"

3. **Park Mode** — Add a new deferred decision:

   a. Parse the question/uncertainty from user input.
   b. Ask the user (max 3 questions) for context: where it matters, urgency/deadline, leading options.
   c. Ensure `BOOK_DIR/parked-decisions.md` exists (create with header if not).
   d. Generate sequential ID: `PD-001`, `PD-002`, etc.
   e. Append the decision with: status, date, deadline, urgency, question, context, options, resolution placeholder.
   f. Check deadline proximity against current progress.
   g. Report: Decision parked, ID assigned, deadline noted.

4. **List Mode** — Show all parked decisions:

   a. Read `parked-decisions.md`. Show summary table with ID, title, status, urgency, deadline.
   b. Check current progress (from chapters.md) against deadlines. Flag URGENT and APPROACHING decisions.

5. **Resolve Mode** — Close a parked decision:

   a. Parse decision ID and resolution.
   b. Update entry: change status to RESOLVED, fill resolution section with decision, rationale, and next steps.
   c. Assess downstream impact: recommend `authorkit.pivot` for broad changes, `authorkit.revise` for targeted fixes.
   d. Report: Decision resolved, recommended follow-up actions.

## Integration with Other Commands

- **`authorkit.chapter.plan`** and **`authorkit.chapter.draft`**: Check for deadline proximity before proceeding.
- **`authorkit.analyze`**: Include past-deadline OPEN decisions as HIGH severity findings.

## Key Rules

- **Never block writing.** Parking explicitly permits moving forward with uncertainty.
- **Be specific about deadlines.** "Before CH12" is better than "Eventually."
- **Track options.** Capture what the author is considering, even if vague.
- **Warn proactively.** When deadlines approach, warn loudly.
- **Resolution triggers action.** Always suggest next steps (pivot, revise, world update).
- **Keep the file clean.** Resolved decisions stay for history but are marked RESOLVED.
