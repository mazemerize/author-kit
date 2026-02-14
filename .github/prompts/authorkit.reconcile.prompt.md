---
description: Check upstream documents (outline, concept, chapters.md, World/) for drift against drafted chapters.
mode: agent
---

## User Input

```text
${input:scope}
```

You **MUST** consider the user input before proceeding (if not empty). The user input may contain:
- A scope: "all", "act1", "act2", "act3", or a chapter range like "1-6", "CH07-CH12"
- If empty: default to all drafted chapters

## Goal

Scan all upstream planning documents — outline.md, concept.md, chapters.md, and World/ files — for factual claims that have been **superseded by drafted chapters**. Drafted chapters are the canonical source of truth. Everything else may be stale. This command produces a drift report and optionally fixes the discrepancies.

This is a **read-then-fix** command: it reads everything, reports what's stale, and asks the user whether to apply corrections.

## Why This Exists

The outline is written before chapters are drafted. During drafting, creative choices diverge from the outline — characters act differently, events unfold differently, details shift. These are good changes (the draft is always better-informed than the plan). But the outline, concept, chapters.md summaries, and World/ files don't update themselves. When the next chapter is planned using a stale outline, the stale details propagate into new drafts as continuity errors.

## Outline

### Phase 1: Identify Drafted Chapters

1. **Setup**: Run `.authorkit/scripts/powershell/check-prerequisites.ps1 -Json -RequireChapters -IncludeChapters` from repo root and parse BOOK_DIR and AVAILABLE_DOCS. All paths must be absolute.

2. **Determine scope** from user input:
   - "all" or empty: all chapters with status `[D]`, `[R]`, or `[X]` in chapters.md
   - "act1", "act2", "act3": chapters within that act's range
   - "1-6", "CH07-CH12": specific chapter range
   - A single chapter: "7", "CH07"

3. **Load all drafted chapters** within scope. Read each `chapters/NN/draft.md`.

### Phase 2: Scan Upstream Documents

For each upstream document, extract every factual claim about events in drafted chapters and verify against the actual draft text.

#### 2a. Outline (outline.md)

For each chapter entry in outline.md that corresponds to a **drafted** chapter:
- Read the outline's Summary, Key Events, Characters Present, Ends With, and Connections fields.
- For each factual claim (who did what, who said what, what happened, who was present, what the chapter ends with):
  - Grep the corresponding `chapters/NN/draft.md` for verification.
  - Flag any claim that doesn't match the draft.

For each chapter entry that corresponds to a **not-yet-drafted** chapter:
- Read its Summary, Key Events, and Connections.
- Identify any claims about events from **already-drafted** chapters (e.g., "after the argument in CH03", "building on Copy #7's departure in CH06").
- Grep the referenced draft to verify.
- Flag mismatches.

**Common drift patterns to watch for**:
- "Character X told Character Y to..." — but the draft shows Y acted independently
- "After the [event] in CH[N]..." — but the event played out differently
- Character motivations described in outline that the draft contradicts
- Ending descriptions that don't match the draft's actual closing
- Character presence ("Characters Present") that doesn't match who actually appears in the draft

#### 2b. Concept (concept.md)

- Focus on the Synopsis, Characters, and Clarifications sections.
- Identify claims about specific events, character behaviours, or plot mechanics that have been concretized differently in drafts.
- Concept drift is usually less granular than outline drift, but can include things like character descriptions, relationship dynamics, or timeline assumptions.

#### 2c. Chapters.md

- Check each chapter's summary text (after the title) against the draft.
- These summaries are brief, but key details (who does what, what happens) should match.

#### 2d. World/ Files

- **If `World/_index.md` exists**: Read it. Use the Entity Registry `Chapters` column to identify entities tagged with `(CONCEPT)` that may need drift checks — these are the entities whose pre-writing assumptions may have been superseded by drafted chapters. Use the Chapter Manifest to find entities tagged for the in-scope chapters. Only read those specific World/ files, rather than all World/ files.
- For each World/ file that references events from drafted chapters (tagged with `(CHxx)`):
  - Verify the tagged claim against the draft.
- For each World/ file that references events from concept/outline only (tagged `(CONCEPT)`):
  - Check if a draft now covers that event. If so, verify the `(CONCEPT)` claim still holds, or flag it as needing a source upgrade to `(CHxx)`.

### Phase 3: Generate Drift Report

Output a structured report:

```markdown
# Reconciliation Report

**Book**: [title]
**Scope**: [scope]
**Drafted chapters scanned**: [list]
**Date**: [date]

## Summary

- **Total discrepancies found**: [N]
- **Outline drift**: [N] issues
- **Concept drift**: [N] issues
- **Chapters.md drift**: [N] issues
- **World/ drift**: [N] issues

## Outline Drift

### CH[NN] — [Title]

| Outline Claim | Draft Reality | Severity |
|---------------|---------------|----------|
| [what the outline says] | [what the draft actually says] | [High/Medium/Low] |

[Repeat per chapter with drift]

## Concept Drift

| Concept Claim | Draft Reality | Location | Severity |
|---------------|---------------|----------|----------|
| [claim] | [what actually happened] | [section in concept.md] | [severity] |

## Chapters.md Drift

| Chapter | Summary Claim | Draft Reality | Severity |
|---------|---------------|---------------|----------|
| CH[NN] | [claim] | [reality] | [severity] |

## World/ Drift

| File | Claim | Draft Reality | Severity |
|------|-------|---------------|----------|
| [path] | [tagged claim] | [reality] | [severity] |
```

**Severity levels**:
- **High**: A future chapter plan that references this claim would produce a continuity error. (e.g., "Control Elliot instructed him to..." when the draft shows he acted independently)
- **Medium**: The claim is inaccurate but unlikely to cause downstream errors. (e.g., a slightly different wording of an ending)
- **Low**: The claim is vague enough to be technically compatible but could be more precise. (e.g., outline says "briefly" but draft gives it a full scene)

### Phase 4: Offer Fixes

After presenting the report:

1. Ask the user: "Found [N] discrepancies. Fix all / Fix high-severity only / Review one by one / Skip?"

2. **If fixing**:
   - For each discrepancy, edit the upstream document to match the draft.
   - For outline entries: rewrite the specific claim to match the draft's version.
   - For concept entries: update or add a clarification note.
   - For chapters.md: update the summary text.
   - For World/ files: update the tagged entry and change the source tag from `(CONCEPT)` to `(CHxx)` where applicable.

3. **Report fixes applied**: List each file modified and what changed.

## Key Rules

- **This command is read-first, fix-second.** Always show the report before modifying anything.
- **Drafted chapters are never modified.** Only upstream documents are corrected.
- **The outline is a living document.** It was correct when written; it may not be correct now. That's normal and expected.
- **Don't flag creative improvements as drift.** If the draft expanded on the outline in a way that's richer but compatible (e.g., added a scene the outline didn't mention), that's not a discrepancy — it's growth. Only flag actual contradictions.
- **Severity matters.** High-severity issues are the ones that will cause problems in future chapters. Focus there.
- **Run this at act checkpoints.** The best time to reconcile is after completing an act's worth of chapters, before planning the next act.

## When to Use This Command

- After completing an act (e.g., all Act I chapters drafted → reconcile before starting Act II)
- Before planning a chapter that depends heavily on prior chapters
- When you suspect the outline may have drifted (e.g., a chapter made a significant creative departure during drafting)
- As a periodic hygiene check during long drafting sessions
