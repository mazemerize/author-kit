---
description: Resolve ambiguities in the book concept through structured Q&A. Records accepted answers directly into concept.md.
handoffs:
  - label: Discuss Ideas
    agent: authorkit.discuss
    prompt: Brainstorm ideas now that the concept is clearer
  - label: Update Constitution
    agent: authorkit.constitution
    prompt: Refresh voice/tone rules based on the clarified concept
  - label: Build World
    agent: authorkit.world.build
    prompt: Build the world from the clarified concept
  - label: Create Outline
    agent: authorkit.outline
    prompt: Create an outline using the clarified concept
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --paths-only
  ps: scripts/powershell/check-prerequisites.ps1 -Json -PathsOnly
---

## User Input

```text
{{USER_INPUT_TOKEN}}
```

You **MUST** consider the user input before proceeding (if not empty). The user input may target a specific area to clarify (e.g., "the magic system", "the audience"). If empty, scan the whole concept for the highest-impact ambiguities.

## Goal

Identify and resolve underspecified areas in the book concept *before* outlining. Unlike `/authorkit.discuss`, this command **writes to `concept.md`** as answers are accepted — that is the point of the command, and the user is opting into it by invoking `clarify`.

This is a focused, structured Q&A — not an open-ended conversation. For brainstorming or open exploration, use `/authorkit.discuss` instead.

## Outline

1. **Setup**: Run `{{SCRIPT_CHECK_PREREQ}}` from repo root and parse BOOK_DIR. All paths must be absolute.

2. **Load context** (read whatever exists):
   - **Required**: `concept.md` — if missing, ERROR "No concept found. Run `/authorkit.conceive` first."
   - **Optional**: `.authorkit/memory/constitution.md` (voice, tone, writing principles)
   - **Optional**: `outline.md`, `chapters.md`, `world/`, `characters.md` (to spot ambiguities that have already been resolved downstream)

3. **Identify ambiguities** in concept.md across these areas:
   - Premise & Scope
   - Genre & Audience
   - Characters/Subjects
   - Voice & Tone
   - Themes
   - Structure & Pacing
   - Setting/world
   - Research Requirements

   If the user provided a specific focus (e.g., "clarify the magic system"), restrict to that area.

4. **Prioritize** the most impactful ambiguities. Order: premise > audience > structure > voice > details. Cap at **5 questions per session** to keep the Q&A focused.

5. **Run structured Q&A** — one question at a time:
   - Present ONE clarification question per turn, answerable with a short answer or multiple-choice.
   - For each question, provide a **recommended answer** with reasoning grounded in genre conventions and existing concept context.
   - Wait for the author's reply.

6. **Record each accepted answer** directly into `concept.md`:
   - Ensure a `## Clarifications` section exists (create if missing, place near the top of the file).
   - Under a `### Session YYYY-MM-DD` subheading, append: `- Q: <question> -> A: <answer>`.
   - Apply the answer to the relevant concept section (update Premise, Audience, Voice, etc., as appropriate). Keep edits minimal — surgical updates, not rewrites.
   - Confirm to the author after each save: "Recorded under Clarifications and updated [Section X]."

7. **Continue** until ambiguities are resolved, the author says "done", or 5 questions have been asked.

8. **Report completion**:
   - Count of clarifications recorded
   - Sections of `concept.md` updated
   - Suggested next step:
     - If voice/tone changed materially: `/authorkit.constitution` to refresh the style rules
     - Otherwise: `/authorkit.outline` to outline from the clarified concept

## Key Rules

- **Concept.md is the only file written.** Do not edit outline, world/, chapters, or anything else. If the clarification implies downstream changes, mention them and recommend `/authorkit.amend` — don't propagate them here.
- **One question at a time.** Walls of questions overwhelm the author and get answered shallowly.
- **Recommend, don't dictate.** Always offer a suggested answer with reasoning. The author can accept, modify, or reject.
- **The author's instinct wins.** If they push back on a recommendation, support their choice — don't argue for the "correct" one.
- **No brainstorming.** If the conversation drifts into open exploration, suggest handing off to `/authorkit.discuss` and stop.
- **Stop at 5 questions** even if more ambiguities remain. Suggest re-running `/authorkit.clarify` later for a fresh batch.
