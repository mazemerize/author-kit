---
description: Retroactively change an established fact across all chapters, plans, and world files.
handoffs:
  - label: Review Affected Chapters
    agent: authorkit.chapter.review
    prompt: Review chapters modified by the retcon
  - label: Verify World Consistency
    agent: authorkit.world.verify
    prompt: Verify world consistency after retcon changes
  - label: Run Full Analysis
    agent: authorkit.analyze
    prompt: Run cross-chapter analysis after retcon
scripts:
  ps: scripts/powershell/check-prerequisites.ps1 -Json -IncludeChapters
---

## User Input

```text
{{USER_INPUT_TOKEN}}
```

You **MUST** consider the user input before proceeding (if not empty). The user input should specify what fact is changing, in the format: "[old fact] -> [new fact]" or a natural language description of the change.

## Goal

When a mid-story discovery or creative decision requires changing an **established fact** across previously written chapters — a character's backstory, a place's description, a timeline detail, a world rule — find every reference and update it consistently while preserving each chapter's voice and style.

This is more specific than `/authorkit.pivot` (which handles broad direction changes) and more systematic than `/authorkit.revise` (which targets specific issues). Retcon handles the **search-and-replace-with-intelligence** problem: finding every occurrence of a fact across the manuscript and updating it consistently.

## Outline

1. **Setup**: Run `{{SCRIPT_CHECK_PREREQ}}` from repo root and parse BOOK_DIR and AVAILABLE_DOCS. All paths must be absolute.

2. **Parse the retcon** from user input:
   - If empty: ERROR "Please specify the fact change (e.g., /authorkit.retcon Character X was a soldier -> Character X was a spy)"
   - Extract:
     - **Old fact**: What is currently established
     - **New fact**: What it should become
     - **Scope** (optional): Limit to specific chapters or files
   - Accept formats:
     - Explicit: "Transit from the harbor to the citadel takes 40 minutes -> Transit takes 75 minutes (distance remeasured after route audit)"
     - Natural language: "Change Marcus from a soldier to a spy"
     - Complex: "The magic system costs blood -> The magic system costs memories"

3. **Comprehensive search** across all artifacts:

   - **If `world/_index.md` exists**: Read it first. Use the Alias Lookup table to find ALL name variants for the entity being retconned. Use the Entity Registry `Chapters` column to identify exactly which chapter files reference this entity — search only those files instead of all chapters. Read the entity's frontmatter `relationships` field to identify connected entities for indirect reference searching.
   - **If no index**: Fall back to searching all world/ files and chapters by name.

   For the old fact, search for:
   - **Direct references**: Exact mentions of the old fact
   - **Indirect references**: Implications, consequences, or reactions based on the old fact
   - **Derivative details**: Things that logically follow from the old fact (e.g., if changing travel time from 40 to 75 minutes, update any arrival windows, alibis, or timetable constraints that depended on 40)

   Search these files:
   a. **concept.md**: Check premise, characters, themes
   b. **outline.md**: Check chapter summaries, character arcs
   c. **characters.md**: Check profiles, relationships
   d. **world/ files**: Check ALL categories — characters/, places/, organizations/, history/, systems/, notes/
   e. **Chapter plans** (`chapters/NN/plan.md`): Check all existing plans
   f. **Chapter drafts** (`chapters/NN/draft.md`): Check all drafted chapters — this is where the most nuanced changes live
   g. **chapters.md**: Check chapter summaries

4. **Generate a change manifest**:

   ```markdown
   ## Retcon Manifest: [OLD FACT] -> [NEW FACT]

   **Date**: [DATE]

   ### Direct References (exact mentions)

   | File | Location | Current Text | Proposed Change |
   |------|----------|-------------|-----------------|
   | chapters/03/draft.md | Para 7 | "...her twenty years in the army..." | "...her years in the intelligence service..." |
   | world/characters/iria.md | Background | "Military service (CONCEPT)" | "Intelligence service (RETCON)" |

   ### Indirect References (implications and consequences)

   | File | Location | Current Text | Why It's Affected | Proposed Change |
   |------|----------|-------------|-------------------|-----------------|
   | chapters/05/draft.md | Scene 2 | "She drew her sword instinctively" | Soldiers draw swords; spies might not | "She reached for the concealed blade" |

   ### Derivative Details (logical consequences)

   | File | Location | Current Detail | Logical Issue | Proposed Change |
   |------|----------|---------------|---------------|-----------------|
   | chapters/07/draft.md | Para 12 | "Her commanding officer had warned her" | Spies don't have commanding officers in same way | "Her handler had warned her" |

   ### Unchanged (references that work with both old and new facts)

   | File | Location | Text | Why It's Fine |
   |------|----------|------|--------------|
   | chapters/02/draft.md | Para 3 | "She moved with discipline" | Applies to both soldiers and spies |

   ### Summary

   - Direct references: [N]
   - Indirect references: [N]
   - Derivative details: [N]
   - Total files affected: [N]
   - Total changes proposed: [N]
   ```

5. **Present manifest to user** for review:
   - User may approve all changes
   - User may modify specific proposed changes
   - User may exclude certain files or chapters
   - User may abandon the retcon

6. **Apply approved changes**:

   a. For each file in dependency order (upstream first):

      - **world/ files**: Update entries. Tag changes with `(RETCON-[DATE])` to track.
      - **concept.md / outline.md / characters.md**: Update references directly.
      - **Chapter plans**: Update affected scene descriptions and notes.
      - **Chapter drafts**: Apply changes while **preserving the chapter's existing voice and style**:
        - Direct references: Replace with new text
        - Indirect references: Rewrite the surrounding context to fit naturally
        - Derivative details: Adjust logical consequences
        - Every edit must be indistinguishable in style from the surrounding prose

   b. For each modified chapter draft:
      - Reset status to `[D]` (to trigger re-review)
      - Do NOT reset to `[P]` unless the chapter's structure changed

   c. Update chapters.md with new statuses.

   d. After modifying world/ files, update their YAML frontmatter: add `RETCON-YYYY-MM-DD` to the `chapters` field, update any changed `aliases` or `relationships`, update `last_updated`. Run `.authorkit/scripts/powershell/build-world-index.ps1 -Json` to rebuild the index.

7. **Post-retcon consistency check**:

   After all changes are applied, perform a quick scan:
   - Do any remaining references to the old fact exist? (might be in files not initially found)
   - Do the changes introduce any new contradictions?
   - Are there any chapters where the new fact conflicts with the chapter's plot logic?
   - Report any issues found

8. **Write retcon log** to `BOOK_DIR/pivots/YYYY-MM-DD-retcon-[short-description].md`:

   ```markdown
   # Retcon: [OLD FACT] -> [NEW FACT]

   **Date**: [DATE]
   **Files Modified**: [N]
   **Changes Applied**: [N]

   ## Change Summary

   | File | Changes |
   |------|---------|
   | [path] | [summary of changes] |

   ## Post-Retcon Check

   - Remaining old references: [N — should be 0]
   - New contradictions found: [N]
   - Chapters needing re-review: [list]
   ```

9. **Report completion**:
   - Total changes applied across N files
   - Chapters with reset statuses
   - Any residual issues found in post-retcon check
   - Suggested next steps:
     - `/authorkit.chapter.review [N]` for chapters with significant prose changes
     - `/authorkit.world.verify` to check world consistency
     - `/authorkit.analyze` for a full consistency sweep

## Retcon Principles

- **Find everything.** The most dangerous retcon is a partial one. Search thoroughly — direct references, indirect implications, and logical consequences.
- **Preserve voice.** Every change to a chapter draft must be stylistically indistinguishable from the surrounding prose. Match sentence rhythm, vocabulary level, and narrative distance.
- **Show the manifest first.** Never apply changes without user review. The manifest is the contract.
- **Track changes.** Use `(RETCON-[DATE])` tags in world/ files. Store full retcon logs in `pivots/`.
- **Check your work.** The post-retcon consistency scan catches what the initial search missed.
- **Indirect > direct.** Direct references are easy. The hard part is finding implications and derivative details. Spend extra effort here.
- **Don't over-correct.** If a reference works equally well with the old and new facts, leave it alone. Document it in the "Unchanged" section.

