---
description: Assess chapter progress and route to the next step in the chapter lifecycle.
handoffs:
  - label: Plan Chapter
    agent: authorkit.chapter.plan
    prompt: Plan chapter [N]
  - label: Draft Chapter
    agent: authorkit.chapter.draft
    prompt: Draft chapter [N]
  - label: Review Chapter
    agent: authorkit.chapter.review
    prompt: Review chapter [N]
  - label: Revise Chapter
    agent: authorkit.revise
    prompt: Revise chapter [N] based on review feedback
  - label: Update World
    agent: authorkit.world.update
    prompt: Update world files for chapter [N]
scripts:
  ps: scripts/powershell/check-prerequisites.ps1 -Json -IncludeChapters
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty). The user input may contain a chapter number (e.g., "3", "CH05") or be empty for auto-detection.

## Goal

Assess the current state of the book's chapters and route to the next step in the chapter lifecycle. This is a **read-only orchestrator** — it never modifies files, only reads state and recommends the next action.

## Operating Constraints

**STRICTLY READ-ONLY**: Do **not** modify any files. Assess state and present handoff options only.

## Outline

1. **Setup**: Run `{SCRIPT}` from repo root and parse BOOK_DIR and AVAILABLE_DOCS. All paths must be absolute.

2. **Load chapters.md**: Read `BOOK_DIR/chapters.md` and parse all chapter entries.
   - Extract chapter numbers, titles, and status markers: `[ ]` pending, `[P]` planned, `[D]` drafted, `[R]` reviewed/needs revision, `[X]` approved
   - If chapters.md doesn't exist: ERROR "No chapters.md found. Run `/authorkit.chapters` first to generate the chapter task list."

3. **Determine target chapter**:

   **If user specified a chapter number:**
   - Accept formats: "1", "01", "CH01", "chapter 1"
   - Normalize to two-digit format
   - Verify the chapter exists in chapters.md

   **If no chapter specified — find the frontier:**
   - Scan chapters.md for the first chapter that is NOT `[X]` (approved)
   - If all chapters are `[X]`: report book is complete (see step 6)
   - The frontier chapter is the target

4. **Assess target chapter state**:

   Based on the status marker, check for the existence of supporting files and determine the next action:

   | Status | Meaning | Check | Next Action |
   |--------|---------|-------|-------------|
   | `[ ]` | Pending | — | `/authorkit.chapter.plan [N]` |
   | `[P]` | Planned | Verify `chapters/NN/plan.md` exists | `/authorkit.chapter.draft [N]` |
   | `[D]` | Drafted | Verify `chapters/NN/draft.md` exists | `/authorkit.chapter.review [N]` |
   | `[R]` | Needs revision | Read `chapters/NN/review.md` for issues | `/authorkit.revise [N]` |
   | `[X]` | Approved | Check if World/ update needed | `/authorkit.world.update [N]` or next chapter |

   **Special handling for `[R]` (needs revision):**
   - Read `chapters/NN/review.md` if it exists
   - Extract the critical and important issues
   - Present a brief summary of what needs fixing before recommending revision

   **Special handling for `[X]` (approved) when user explicitly requested this chapter:**
   - Check if `World/` folder exists
   - Check if any World/ file contains `(CHxx)` tags for this chapter
   - If World/ exists but no tags for this chapter: recommend `/authorkit.world.update [N]`
   - If World/ is up to date (or doesn't exist): report chapter is done, suggest next unfinished chapter

5. **Report progress summary**:

   Present a compact overview:

   ```
   ## Chapter Progress

   **Target**: Chapter [NN] — [Title]
   **Status**: [Status description]

   ### Book Overview
   - Approved: [count] of [total] chapters
   - In progress: Chapter [NN] ([status])
   - Remaining: [count] chapters

   ### Progress
   [X] CH01 - Title
   [X] CH02 - Title
   [D] CH03 - Title  ← current
   [ ] CH04 - Title
   [ ] CH05 - Title

   ### Recommended Next Step
   [Description of what to do and why]
   ```

6. **Handle edge cases**:

   - **All chapters `[X]`**: Congratulate completion. Recommend `/authorkit.analyze` for cross-chapter analysis, or `/authorkit.world.verify` if World/ exists.
   - **No chapters at all**: chapters.md exists but is empty or has no entries. ERROR with guidance.
   - **Multiple chapters in `[R]`**: Note all chapters needing revision and let the user choose which to tackle.
   - **Non-sequential progress**: If chapters are being written out of order (e.g., CH01 `[X]`, CH02 `[ ]`, CH03 `[D]`), report this and let the user decide which to continue.

## Key Rules

- **Never modify files.** This is purely a state assessment and routing command.
- **Be concise.** The user wants to know what to do next, not a lengthy analysis. Keep the progress report compact.
- **Trust the status markers.** The status in chapters.md is authoritative. Don't second-guess it.
- **Verify file existence.** A chapter marked `[P]` should have a plan.md — if it doesn't, note the discrepancy and still recommend planning.
- **Surface review feedback.** When the next step is revision, summarize what needs fixing so the user has context before clicking the handoff.
