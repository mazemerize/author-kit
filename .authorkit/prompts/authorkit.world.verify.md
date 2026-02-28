---
description: Verify world/ files for internal consistency and manuscript alignment.
handoffs:
  - label: Fix World Issues
    agent: authorkit.world.build
    prompt: Fix the world-building issues identified in the verification report
  - label: Re-scan Chapters
    agent: authorkit.world.update
    prompt: Re-scan chapters to update world/ files
  - label: Full Analysis
    agent: authorkit.analyze
    prompt: Run a full cross-chapter analysis including world-building
scripts:
  ps: scripts/powershell/check-prerequisites.ps1 -Json -PathsOnly
---

## User Input

```text
{{USER_INPUT_TOKEN}}
```

You **MUST** consider the user input before proceeding (if not empty). The user input specifies the verification scope (e.g., "all", "characters/", "characters/iria.md", "systems/ places/").

## Goal

Verify that world/ files are internally consistent with each other and (when chapters exist) aligned with the manuscript. This is a **read-only** diagnostic tool that flags issues but never modifies files.

Unlike `/authorkit.analyze` (which requires multiple drafted chapters and covers all aspects of the book), this command focuses exclusively on world-building integrity and can run at any stage — even before a single chapter is written.

## Outline

1. **Setup**: Run `{{SCRIPT_CHECK_PREREQ}}` from repo root and parse BOOK_DIR. All paths must be absolute.

2. **Validate world/ exists**:
   - Check that `BOOK_DIR/world/` directory exists with at least one file
   - If not: ERROR "No world/ folder found. Run `/authorkit.world.build` first."

3. **Parse scope** from user input:
   - **Specific file**: `characters/iria.md`, `world/characters/iria.md` — verify that file plus its cross-references
   - **Category folder**: `characters/`, `organizations/`, `places/`, `history/`, `systems/`, `notes/` — verify all files in that category recursively (including nested descendants)
   - **Multiple targets**: `characters/iria.md systems/magic.md` — verify those files plus cross-references
   - **All** (default): `all`, empty, or no argument — verify the entire world/ folder
   - Normalize all paths relative to `BOOK_DIR/world/`

4. **Determine verification mode**:
   - Check if `BOOK_DIR/chapters/` directory exists and contains any `NN/draft.md` files
   - **World-only mode**: No chapter drafts found. Verify world/ files against each other only.
   - **World+manuscript mode**: Chapter drafts found. Verify world/ files against each other AND against chapter content.
   - Report the mode to the user before proceeding.

5. **Load context**:
   - **If `world/_index.md` exists**: Read it first. Use the Entity Registry for quick entity enumeration, the Alias Lookup for name resolution, and the Chapter Manifest to identify which entities appear in which chapters. This avoids reading every world/ file upfront — load only the files within scope plus their cross-referenced files (identified via Entity Registry file paths).
   - **If no index**: Fall back to loading all world/ files within scope recursively.
   - **Required**: All world/ files within the specified scope
   - **Required**: world/ files outside scope that are cross-referenced by in-scope files (for reciprocal checks)
   - **Optional**: concept.md (for checking CONCEPT entries against the original concept)
   - **Optional**: `/memory/constitution.md` (for naming convention checks)
   - **World+manuscript mode**: All available chapter drafts at `BOOK_DIR/chapters/NN/draft.md`

6. **Execute verification checks**:

   Run the following checks. When scope is limited to specific files or categories, only report issues that involve at least one in-scope file.

   ### A. Reciprocal Reference Integrity

   - For each Character file: verify all relationships reference characters that have their own files
   - For each relationship where Character A's file mentions Character B: verify that B's file reciprocally references A
   - For each Organization's Key Members: verify those characters exist in characters/ and that their Character files reference the Organization
   - For each Organization's Relationships mentioning other organizations: verify reciprocal references
   - For each Place's Control/Inhabitants: verify referenced characters/organizations exist in their respective folders

   ### B. Cross-Entity Consistency

   - Characters listed as Organization members should list that Organization in their profiles
   - Places referenced in history/ events should exist in places/
   - Characters referenced in history/ events should exist in characters/
   - Organizations referenced in history/ events should exist in organizations/
   - System users or practitioners mentioned in systems/ should appear in characters/ (if they are named individuals)
   - Cross-reference links (e.g., "See characters/iria-calder.md") should point to files that actually exist
   - Entity names should be spelled consistently across all files

   ### C. System Coherence

   - Rules within a single System file should not contradict each other
   - Rules across different System files should not contradict (e.g., a magic system saying "only nobles can use magic" vs. a political system saying "commoners have magic-based voting rights")
   - Limitations should not contradict Rules
   - Exceptions should be acknowledged or at least not incompatible with the relevant Rules section
   - Scope definitions should not overlap in contradictory ways

   ### D. Geographic Plausibility

   - Travel times between places should be consistent (if A-to-B takes 3 days and B-to-C takes 2 days, A-to-C should be proportionally plausible unless geography justifies otherwise)
   - Climate/biome descriptions should be plausible for stated geography (a desert next to a rainforest needs explanation)
   - Distances and spatial relationships should not contradict across Place files
   - Place descriptions should be compatible with their stated region/continent

   ### E. Timeline Consistency

   - Events in history/ should be chronologically coherent (causes precede effects)
   - Character ages should be plausible given historical events they participated in
   - Organization founding dates should precede member join dates
   - Sequential events should have plausible time gaps
   - If dates/years are given, they should form a consistent chronology

   ### F. Chapter Tag Integrity (World+manuscript mode only)

   - Every `(CHxx)` tag should reference a chapter that actually exists as `chapters/xx/draft.md`. If `world/_index.md` exists, use the Entity Registry `Chapters` column to enumerate all chapter tags across all entities, then cross-reference against the file system.
   - Every `(CHxx-rev)` tag should reference a chapter that has been revised
   - Identify `(CONCEPT)` entries that are contradicted by later `(CHxx)` entries in the same file — flag as potentially stale CONCEPT
   - Identify entities whose world/ files have no chapter tags despite appearing in drafted chapters (world.update may not have been run)

   ### G. Staleness Detection (World+manuscript mode only)

   - For each world/ entity in scope: scan chapter text for mentions of that entity (by name, title, or key descriptors). If `world/_index.md` exists, use the Alias Lookup to search for all name variants.
   - Flag entities heavily referenced in early chapters but absent from later chapters (potential forgotten threads). If `world/_index.md` exists, use the Chapter Manifest to compare entity presence across early vs. late chapters.
   - Flag entities with only `(CONCEPT)` tags that appear in chapters but whose world/ files were never updated with chapter tags
   - Flag world/ files that have not been updated since the first few chapters despite many subsequent chapters being drafted

7. **Severity assignment**:

   - **CRITICAL**: Direct contradictions (character is both dead and alive, system rule violated by another system), broken cross-references to nonexistent files, chronological impossibilities
   - **HIGH**: Missing reciprocal relationships, organization members not in characters/, chapter tags referencing nonexistent chapters, CONCEPT entries contradicted by chapter content
   - **MEDIUM**: Missing cross-references (entities mentioned but not linked), minor geographic implausibility, stale entries, name spelling inconsistencies
   - **LOW**: Style inconsistencies in world/ files, missing optional sections, suggested improvements

8. **Produce verification report**:

   Output a structured Markdown report to the user (NO file writes):

   ```markdown
   ## World Verification Report

   **Scope**: [what was verified — specific files, category, or "all"]
   **Mode**: [World-only / World+manuscript (N chapters)]
   **Date**: [DATE]
   **world/ Files Checked**: [N]

   ### Summary

   | Check Category | Items Checked | Issues Found | Critical | High | Medium | Low |
   |---------------|--------------|-------------|----------|------|--------|-----|
   | Reciprocal References | [N] | [N] | [N] | [N] | [N] | [N] |
   | Cross-Entity Consistency | [N] | [N] | [N] | [N] | [N] | [N] |
   | System Coherence | [N] | [N] | [N] | [N] | [N] | [N] |
   | Geographic Plausibility | [N] | [N] | [N] | [N] | [N] | [N] |
   | Timeline Consistency | [N] | [N] | [N] | [N] | [N] | [N] |
   | Chapter Tag Integrity | [N] | [N] | [N] | [N] | [N] | [N] |
   | Staleness Detection | [N] | [N] | [N] | [N] | [N] | [N] |

   ### Findings

   | ID | Category | Severity | File(s) | Description | Recommendation |
   |----|----------|----------|---------|-------------|----------------|
   | R1 | Reciprocal | HIGH | characters/iria.md, characters/marcus.md | Iria lists Marcus as "mentor" but Marcus has no reference to Iria | Add Iria to Marcus's Relationships section |
   | C1 | Cross-Entity | MEDIUM | organizations/guild.md, characters/ | Guild lists "Tomas" as member but no characters/tomas.md exists | Create a character file for Tomas or remove from guild roster |

   ### Verification Result

   **Result**: [CLEAN — no issues / N ISSUES FOUND]
   - Critical: [N]
   - High: [N]
   - Medium: [N]
   - Low: [N]
   ```

9. **Suggest next actions**:
   - If reciprocal/cross-entity issues: Recommend `/authorkit.world.build [area]` to add missing entries and fix references
   - If chapter tag integrity issues: Recommend `/authorkit.world.update [chapters]` to re-scan
   - If CONCEPT conflicts: Recommend deciding whether CONCEPT or chapter should be authoritative, then updating
   - If staleness detected: Recommend `/authorkit.world.update` for the chapters that were never scanned
   - If clean: Confirm world/ is consistent, suggest proceeding to next workflow step (outline, draft, or analyze)

## Key Rules

- **STRICTLY READ-ONLY.** Flag issues but never modify world/ files or chapters. The user decides what to fix and how.
- **Scoped checks still load cross-references.** When verifying a single file or category, related files outside scope are loaded for cross-reference checks, but only issues involving at least one in-scope file are reported.
- **Don't duplicate `/authorkit.analyze`.** This command focuses on world/ file consistency — not prose quality, pacing, narrative structure, or other manuscript concerns. Leave those to analyze.
- **Be specific and actionable.** Every finding should cite exact file paths, the specific entry or detail in conflict, and a concrete recommendation for resolution.
- **Limit findings.** Cap at 50 findings total. If more exist, report the count and recommend re-running with narrower scope.
- **Genre-appropriate expectations.** A contemporary romance with 3 world/ files gets lighter verification than an epic fantasy with 40. Don't flag "missing" categories that aren't relevant to the genre.

