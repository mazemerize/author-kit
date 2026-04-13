---
description: Change an established fact or direction across all book artifacts — handles both broad pivots and surgical fact changes with impact analysis.
handoffs:
  - label: Revise Affected Chapters
    agent: authorkit.revise
    prompt: Address the changes identified in the amendment
  - label: Re-Outline
    agent: authorkit.outline
    prompt: Regenerate the outline to reflect the change
  - label: Sync World After Change
    agent: authorkit.world.sync
    prompt: Sync world files after the amendment
  - label: Run Full Analysis
    agent: authorkit.analyze
    prompt: Run cross-chapter analysis after the amendment
  - label: Snapshot Before Change
    agent: authorkit.snapshot
    prompt: Create a snapshot before applying the change
scripts:
  ps: scripts/powershell/check-prerequisites.ps1 -Json -IncludeChapters
---

## User Input

```text
{{USER_INPUT_TOKEN}}
```

You **MUST** consider the user input before proceeding (if not empty). The user input describes the change in natural language.

## Goal

When the author wants to change something about their book — whether it's a broad direction change (new ending, cut a subplot, merge characters) or a specific fact change (character's backstory, a place's name, a world rule) — find every reference across all artifacts, show the impact, and apply the change consistently.

This command replaces both "pivot" (broad direction changes) and "retcon" (surgical fact changes). The author doesn't need to decide which type of change they're making — describe the change, and this command handles it.

## Outline

1. **Setup**: Run `{{SCRIPT_CHECK_PREREQ}}` from repo root and parse BOOK_DIR and AVAILABLE_DOCS. All paths must be absolute.

2. **Parse the change request** from user input:
   - If empty: ERROR "Please describe the change (e.g., `/authorkit.amend Change Marcus from a soldier to a spy`)"
   - Classify the change scope:
     - **Fact change**: A specific detail changes (name, backstory, world rule, timeline detail). These need search-and-replace-with-intelligence across all mentions.
     - **Direction change**: A broad creative shift (cut subplot, change ending, merge characters, change setting). These need top-down propagation across all artifacts.
     - **Mixed**: Some changes are both (e.g., "Change Marcus from a soldier to a spy" is a fact change AND a direction change that affects his scenes, motivations, and relationships).
   - Extract:
     - What is changing (old state → new state, or description of the shift)
     - Scope (optional): limit to specific chapters or files

3. **Comprehensive search** — scan ALL existing artifacts for references to the changing elements:

   - **If `world/_index.md` exists**: Use the Alias Lookup to find all name variants for affected entities. Use the Entity Registry `Chapters` column to target specific files. Read frontmatter `relationships` to identify connected entities for indirect reference searching.
   - **If no index**: Search all world/ files and chapters.

   For each artifact, search for:
   - **Direct references**: Exact mentions of the changing element
   - **Indirect references**: Implications, consequences, or reactions based on the old state
   - **Derivative details**: Things that logically follow (e.g., if changing travel time from 40 to 75 minutes, update arrival windows, alibis, timetable constraints)

   Search these files:
   a. **concept.md**: Premise, characters, themes
   b. **outline.md**: Chapter summaries, character arcs, thematic maps
   c. **chapters.md**: Chapter summaries
   d. **characters.md**: Profiles, relationships
   e. **world/ files**: All relevant categories (characters/, places/, organizations/, history/, systems/, notes/)
   f. **Chapter plans** (`chapters/NN/plan.md`)
   g. **Chapter drafts** (`chapters/NN/draft.md`) — the most nuanced changes live here
   h. **constitution**: Check for conflicts with writing principles

   For each hit, record: file path, what specifically needs to change, whether it's minor (wording) or major (structural), and dependencies.

4. **Present the change plan** to the user:

   ```markdown
   ## Amendment Plan: [SHORT DESCRIPTION]

   **Type**: [Fact Change / Direction Change / Mixed]
   **Date**: [DATE]
   **Description**: [User's stated change]

   ### Impact Summary

   | Artifact | Impact Level | Changes Needed |
   |----------|-------------|----------------|
   | concept.md | [None/Minor/Major] | [What needs to change] |
   | outline.md | [None/Minor/Major] | [What needs to change] |
   | chapters.md | [None/Minor/Major] | [What needs to change] |
   | characters.md | [None/Minor/Major] | [What needs to change] |
   | world/ | [None/Minor/Major] | [N files affected: list] |
   | Chapter plans | [None/Minor/Major] | [N plans affected: list] |
   | Chapter drafts | [None/Minor/Major] | [N drafts affected: list] |
   | Constitution | [None/Conflict] | [Any conflicts] |

   ### Change Details

   **Direct references** (exact mentions):
   | File | Location | Current Text | Proposed Change |
   |------|----------|-------------|-----------------|

   **Indirect references** (implications and consequences):
   | File | Location | Current Text | Why Affected | Proposed Change |
   |------|----------|-------------|--------------|-----------------|

   **Derivative details** (logical consequences):
   | File | Location | Current Detail | Issue | Proposed Change |
   |------|----------|---------------|-------|-----------------|

   **Unchanged** (references that work with both old and new states):
   | File | Location | Text | Why It's Fine |
   |------|----------|------|--------------|

   ### Execution Order

   1. [First artifact] — [why first]
   2. [Second artifact] — [depends on first because...]

   ### Risk Assessment

   - **Cascade risk**: [Low/Medium/High]
   - **Consistency risk**: [Low/Medium/High]
   - **Effort estimate**: [N artifacts to update, M chapters to revise]

   ### Recommendation

   [Suggest snapshotting first for large changes (5+ artifacts). Flag any concerns.]
   ```

5. **Wait for user approval** before making any changes. The user may:
   - Approve the full plan
   - Modify specific proposed changes
   - Exclude certain files or chapters
   - Abandon the change
   - Request a snapshot first

6. **Execute the change** in dependency order (upstream first, downstream last):

   a. **world/ files**: Update entries. Tag changes with `(AMEND-[DATE])`. After modifying, update YAML frontmatter: add `AMEND-YYYY-MM-DD` to `chapters` field, update changed `aliases` or `relationships`, update `last_updated`. Rebuild index via `build-world-index.ps1 -Json`.

   b. **concept.md / outline.md / characters.md / chapters.md**: Update references directly.

   c. **Chapter plans**: Update affected scene descriptions and notes. If a plan changed significantly, reset chapter status to `[P]`.

   d. **Chapter drafts**: Apply changes while **preserving each chapter's existing voice and style**:
      - Direct references: Replace with new text
      - Indirect references: Rewrite surrounding context to fit naturally
      - Derivative details: Adjust logical consequences
      - Every edit must be stylistically indistinguishable from surrounding prose
      - For minor edits: reset status to `[D]` (re-review needed)
      - For major structural changes: reset status to `[P]` (re-plan and re-draft needed)

   e. Update chapters.md with new statuses.

7. **Post-change consistency check**:
   - Scan for remaining references to the old state
   - Check for new contradictions introduced by the changes
   - Report any issues found

8. **Write change log** to `BOOK_DIR/pivots/YYYY-MM-DD-[short-description].md`:

   ```markdown
   # Amendment: [SHORT DESCRIPTION]

   **Date**: [DATE]
   **Type**: [Fact Change / Direction Change / Mixed]
   **Files Modified**: [N]
   **Changes Applied**: [N]

   ## Change Description

   [User's original description]

   ## Artifacts Modified

   | File | Change Summary |
   |------|---------------|
   | [path] | [what was changed] |

   ## Chapter Status Changes

   | Chapter | Before | After | Reason |
   |---------|--------|-------|--------|
   | CH03 | [X] | [D] | Direct fact change in prose |

   ## Post-Change Check

   - Remaining old references: [N]
   - New contradictions found: [N]
   - Chapters needing re-review: [list]
   ```

9. **Report completion**:
   - Summary of all changes made
   - Files modified (with paths)
   - Chapter statuses reset
   - Any residual issues from consistency check
   - Suggested next steps:
     - `/authorkit.chapter.review [N]` for chapters with significant prose changes
     - `/authorkit.world.sync` to verify world consistency
     - `/authorkit.analyze` for a full consistency sweep

## Key Principles

- **Top-down propagation**: Update upstream artifacts (concept, outline) before downstream ones (plans, drafts). This prevents cascading inconsistencies.
- **Find everything**: Direct references are easy. The hard part is finding indirect implications and derivative details. Spend extra effort here.
- **Show the plan first**: Never apply changes without user review. The change plan is the contract.
- **Preserve voice**: Every change to a chapter draft must be stylistically indistinguishable from surrounding prose.
- **Snapshot first for large changes**: If 5+ artifacts are affected, recommend creating a snapshot before proceeding.
- **Don't over-correct**: If a reference works equally well with the old and new states, leave it unchanged. Document it in the "Unchanged" section.
- **Tag changes**: Use `(AMEND-YYYY-MM-DD)` tags in world/ files. Store logs in `pivots/`.
- **Flag, don't force**: For chapters with approved `[X]` status, flag them for user attention rather than silently resetting.
- **Check your work**: The post-change consistency scan catches what the initial search missed.
