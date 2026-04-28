---
description: Sync the world/ folder with drafted chapters — extract new details, verify consistency, and rebuild the entity index.
handoffs:
  - label: Plan Next Chapter
    agent: authorkit.chapter.plan
    prompt: Plan the chapter following the highest-numbered chapter that was just synced — use updated world context
  - label: Build More World
    agent: authorkit.world.build
    prompt: Deepen world-building in [focus area]
  - label: Amend a Conflict
    agent: authorkit.amend
    prompt: A chapter contradicts an established world entry — propagate the correct version across all artifacts
  - label: Run Analysis
    agent: authorkit.analyze
    prompt: Analyze cross-chapter consistency including world-building
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --include-chapters
  ps: scripts/powershell/check-prerequisites.ps1 -Json -IncludeChapters
---

## User Input

```text
{{USER_INPUT_TOKEN}}
```

You **MUST** consider the user input before proceeding (if not empty). The user input should contain chapter number(s) to sync (e.g., "3", "CH05", "1-5", "all") or a scope for verification (e.g., "verify", "characters/").

## Goal

Keep the `world/` folder in sync with the manuscript. This single command handles three jobs:

1. **Extract** new world-building details from drafted chapters into world/ files
2. **Verify** world/ files for internal consistency and manuscript alignment
3. **Rebuild** the entity index (`world/_index.md`) for fast lookups

Run this after drafting or revising chapters, or anytime you want a consistency check.

## Outline

### Phase 1: Extract World Details from Chapters

*Skip this phase if user input is "verify" or specifies a world/ path (e.g., "characters/").*

1. **Setup**: Run `{{SCRIPT_CHECK_PREREQ}}` from repo root and parse BOOK_DIR and AVAILABLE_DOCS. All paths must be absolute.

2. **Parse chapter input**:
   - Accept formats: "3", "03", "CH03", "chapter 3", "1-5" (range), "all"
   - Normalize to list of two-digit chapter numbers
   - If no chapter specified and no "verify" flag: default to all chapters with `[D]` or `[X]` status that haven't been synced yet (check world/_index.md Chapter Manifest if available)

3. **Determine mode** for each chapter:
   - If `world/_index.md` exists, check Entity Registry for `CHxx` tags for this chapter
   - **No existing tags**: Fresh extraction mode
   - **Existing tags found**: Revision reconciliation mode
   - Report the mode to the user before proceeding

4. **Load context**:
   - **Required**: Chapter draft(s) at `BOOK_DIR/chapters/NN/draft.md`
   - **Required**: Existing world/ folder and all files (if exists)
   - **Optional**: concept.md, constitution

5. **Fresh Extraction** (per chapter):

   a. Read the chapter draft thoroughly.

   b. Identify new or updated details about: Characters, Organizations, Places, History/Events, Systems.

   c. For each detail:
      - Resolve entity via `world/_index.md` Alias Lookup (if index exists), or search world/ files
      - **If entity exists**: Add detail tagged `(CHxx)` to the existing file in place
      - **If new entity**: Create file in appropriate category folder with YAML frontmatter (per `.authorkit/templates/world-entity-frontmatter.md`). Default to category root; only create subfolder when clear grouping reason exists.

   d. Cross-reference: If a detail connects entities, update both files.

6. **Revision Reconciliation** (per chapter):

   a. Catalog existing `(CHxx)` entries in world/ files.
   b. Re-read the revised chapter draft.
   c. For unchanged details: keep as-is. For changed details: update and tag `(CHxx-rev)`. For removed details: check if other chapters reference it — keep with note if yes, deprecate if no.
   d. Scan for new details not previously captured; add tagged `(CHxx-rev)`.
   e. Generate downstream impact report (which other chapters may be affected by changes).

### Phase 2: Verify Consistency

7. **Scope determination**:
   - If user specified a world/ path (e.g., "characters/"): verify only that category
   - If chapters were synced in Phase 1: verify entities touched during sync + their connected entities
   - If "verify" or "all": verify all world/ files

8. **Load world/ files** within scope. If `world/_index.md` exists, use it for targeted loading.

9. **Run verification checks**:

   a. **Reciprocal Reference Integrity**: If entity A lists a relationship to entity B, entity B should reference A back.

   b. **Cross-Entity Consistency**: Organization members should have character files. Places mentioned in events should have place files. Entity relationships should be reciprocal.

   c. **System Coherence**: Rules within and across systems should not contradict each other.

   d. **Geographic Plausibility**: Travel times, distances, spatial relationships should be consistent.

   e. **Timeline Consistency**: Causes precede effects. Ages match historical events. Dates are internally consistent.

   f. **Chapter Tag Integrity**: Every `(CHxx)` tag should reference an actual drafted chapter. No orphaned tags.

   g. **Staleness Detection**: Entities referenced in recent chapters but never updated in world/. Entities with only `(CONCEPT)` tags that have since been mentioned in chapters.

10. **Assign severity**: CRITICAL (breaks the manuscript), HIGH (significant inconsistency requiring revision), MEDIUM (notable issue worth addressing), LOW (minor or cosmetic).

### Phase 3: Rebuild Index

11. **Rebuild `world/_index.md`**: Run `{{SCRIPT_BUILD_WORLD_INDEX}}` from repo root. This regenerates:
    - Entity Registry (all entities with IDs, names, paths, chapter tags)
    - Alias Lookup (name variants → entity, flagging ambiguous aliases)
    - Chapter Manifest (which entities appear in which chapter)

12. **Add-frontmatter mode**: If user input includes "add-frontmatter", run the build-world-index script with the frontmatter flag from repo root (this is the canonical implementation — do not regenerate frontmatter manually):
    - PowerShell: `.authorkit/scripts/powershell/build-world-index.ps1 -AddFrontmatter`
    - Bash: `.authorkit/scripts/bash/build-world-index.sh --add-frontmatter`

    The script derives `id` from the file path, extracts `name` from the H1, scans the body for chapter tags, and writes the frontmatter block in place. It then rebuilds `world/_index.md` in the same pass, so step 11 can be skipped when this mode runs.

### Phase 4: Report

13. **Produce a unified sync report**:

   ```markdown
   ## World Sync Report

   **Date**: [DATE]
   **Chapters synced**: [list or "verify"]

   ### Extraction Summary (if applicable)
   - World files created: [N] (list paths)
   - World files updated: [N] (list paths)
   - New entities discovered: [N]
   - Details added to existing entities: [N]

   ### Revision Impact (if applicable)
   | World File | Detail | Old Value | New Value | Downstream |
   |-----------|--------|-----------|-----------|------------|

   ### Verification Findings
   | ID | Category | Severity | Location | Summary | Recommendation |
   |----|----------|----------|----------|---------|----------------|

   **Issues by severity**: [N] Critical, [N] High, [N] Medium, [N] Low

   ### Index Stats
   - Entities indexed: [N]
   - Aliases registered: [N]
   - Chapters covered: [N]
   - Files without frontmatter: [N]
   ```

14. **Suggest next steps**:
    - If critical verification issues: address before continuing
    - If downstream impacts from revisions: list affected chapters
    - If clean: continue with `/authorkit.chapter.plan [N+1]` or `/authorkit.analyze`

## Key Rules

- **Reference format, not narrative.** World entries should be factual and concise.
- **Every detail MUST be chapter-tagged.** `(CHxx)` for fresh, `(CHxx-rev)` for revisions, `(CONCEPT)` for pre-writing.
- **Don't speculate.** Only record what is explicitly in the chapter text.
- **Update incrementally.** Add to existing files rather than rewriting them.
- **Preserve file layout.** Keep human-organized subfolder structures in place.
- **Cross-reference generously.** When a detail connects entities, update both files.
- **Respect (CONCEPT) entries.** If a chapter contradicts a `(CONCEPT)` entry, flag and update with the chapter tag. If the contradiction is substantive (a world rule, not just a minor detail), suggest `/authorkit.amend` to ensure the change is propagated consistently across all artifacts.
- **Flag, don't fix.** Downstream impacts are reported, not auto-fixed.
- **Verification is read-only.** Phase 2 flags issues but does not modify files (except those already modified in Phase 1).
- **Frontmatter is optional for read-only files.** Files without YAML frontmatter are included in verification but won't appear in the index. Use "add-frontmatter" to add it.
- **Cap verification at 50 findings** to keep reports actionable.
