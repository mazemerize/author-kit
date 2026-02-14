---
description: Extract and organize world-building details from drafted chapters into the World/ folder.
mode: agent
---

## User Input

```text
${input:chapterNumbers}
```

You **MUST** consider the user input before proceeding (if not empty). The user input should contain chapter number(s) to scan (e.g., "3", "CH05", "1-5", "all") or specify that this is a post-revision update.

## Goal

After drafting or revising chapters, extract new world-building details and organize them into the `World/` folder. This command operates in two modes:

- **Fresh extraction** (after drafting a new chapter): Scan the chapter for new world details and create/update World/ entries.
- **Revision reconciliation** (after revising an existing chapter): Re-scan the revised chapter, update/remove changed entries, and flag downstream impacts.

## Outline

1. **Setup**: Run `.authorkit/scripts/powershell/check-prerequisites.ps1 -Json -IncludeChapters` from repo root and parse BOOK_DIR and AVAILABLE_DOCS. All paths must be absolute.

2. **Parse chapter input**:
   - Accept formats: "3", "03", "CH03", "chapter 3", "1-5" (range), "all"
   - Normalize to list of two-digit chapter numbers
   - If no chapter specified: ERROR "Please specify chapter number(s) (e.g., authorkit.world.update 3)"

3. **Determine mode** for each chapter:
   - If `World/_index.md` exists, read it. Check the Entity Registry `Chapters` column for `CHxx` matching this chapter number — this tells you which entities already have tags for this chapter without scanning every file.
   - If `_index.md` does not exist, fall back to scanning World/ files for `(CHxx)` tags.
   - **If no existing tags for this chapter**: Fresh extraction mode
   - **If existing tags found**: Revision reconciliation mode
   - Report the mode to the user before proceeding

4. **Load context**:
   - **Required**: The specified chapter draft(s) at `BOOK_DIR/chapters/NN/draft.md`
   - **Required**: Existing World/ folder and all files within (if exists)
   - **Optional**: concept.md (for understanding the world's baseline)
   - **Optional**: `.authorkit/memory/constitution.md` (for understanding naming/style conventions)

5. **For each chapter — Fresh Extraction Mode**:

   a. Read the chapter draft thoroughly.

   b. Identify new or updated details about:
      - **Characters**: New introductions, physical descriptions, personality reveals, relationship changes, backstory reveals, speech patterns
      - **Organizations**: New factions, membership reveals, hierarchy details, alliances/conflicts
      - **Places**: New locations, descriptions of existing places, geographic relationships, atmosphere details
      - **History/Events**: Past events mentioned, historical context, backstory events
      - **Systems**: Rules revealed, limitations discovered, new applications, exceptions

   c. For each detail found:
      - Check if a World/ file already exists for this entity. If `World/_index.md` exists, use the Alias Lookup table to resolve the entity name (handles variants like "Dr. Voss" → `char-elena-voss`), then get the file path from the Entity Registry. If no index, search World/ files directly.
      - **If exists**: Add the new detail to the appropriate section, tagged `(CHxx)`
      - **If new entity**: Create a new file in the appropriate category folder, with all details tagged `(CHxx)`. Include YAML frontmatter following the schema in `.authorkit/templates/world-entity-frontmatter.md`.

   d. Follow the file format established by `authorkit.world.build`:
      - Characters: Identity, Appearance, Personality, Relationships, Background, Arc
      - Places: Description, Significance, Key Features, Control/Inhabitants
      - Organizations: Purpose, Key Members, Structure, Relationships
      - History: When, Who, What Happened, Significance
      - Systems: Rules, Limitations, Scope, Manifestations, Exceptions

   e. **Cross-reference**: If a new detail connects to an existing entity, add a cross-reference in both files.

6. **For each chapter — Revision Reconciliation Mode**:

   a. **Catalog existing entries**: Find all details in World/ files tagged with `(CHxx)` where `xx` is the revised chapter.

   b. Re-read the revised chapter draft.

   c. **For each existing tagged entry**:
      - If the detail **still exists unchanged** in the revised chapter: Keep as-is
      - If the detail was **changed** (e.g., eye color, name, location): Update the entry with the new value, tag it `(CHxx-rev)`
      - If the detail was **removed** from the chapter entirely:
        - Check if other chapters also reference this detail
        - If yes: Keep the entry but note `(removed from CHxx)` and flag for attention
        - If no: Remove the entry or mark it as deprecated

   d. Scan the revised chapter for any **new** details not previously captured. Add them tagged `(CHxx-rev)`.

   e. **Generate downstream impact report**:

      ```markdown
      ## World Update Report: Chapter [NN] Revision

      ### Changed Entries
      | World File | Detail | Old Value | New Value | Downstream References |
      |-----------|--------|-----------|-----------|----------------------|
      | [file] | [what changed] | [old] | [new] | [other chapters referencing this] |

      ### Removed Entries
      | World File | Detail | Removed From | Still Referenced In |
      |-----------|--------|-------------|-------------------|
      | [file] | [what was removed] | [chapter] | [other chapters] |

      ### New Entries
      | World File | Detail | Chapter |
      |-----------|--------|---------|
      | [file] | [new detail] | [chapter] |

      ### Chapters Needing Attention
      - [CHxx]: [why this chapter may need revision due to the change]
      ```

7. **Consistency check** (both modes):
   - After updating World/ files, do a quick scan for internal contradictions
   - Flag if any details from this chapter conflict with details from other chapters
   - These are not automatically fixed — just flagged for the user

8. **Update frontmatter and rebuild index**:
   - For every World/ file that was created or modified, update its YAML frontmatter: add the new chapter tag to `chapters`, update `last_updated`, add any new `relationships` or `aliases` discovered.
   - Run `.authorkit/scripts/powershell/build-world-index.ps1 -Json` from the repo root to rebuild `World/_index.md`.

9. **Report completion**:
   - Mode used (fresh extraction or revision reconciliation)
   - World/ files created or updated (list with paths)
   - New entities discovered
   - Details added to existing entities
   - Any consistency warnings
   - Downstream impact report (if revision mode)
   - Suggested next step:
     - After fresh extraction: `authorkit.world.verify` to check consistency, `authorkit.chapter.plan [N+1]` to continue, or `authorkit.analyze` for full analysis
     - After revision: `authorkit.world.verify` to check consistency of updated entries, address flagged chapters, then `authorkit.analyze`

## Key Rules

- **Reference format, not narrative.** World/ entries should be factual and concise.
- **Every detail MUST be chapter-tagged.** This is the core mechanism for tracking evolution. Use `(CHxx)` for fresh extraction, `(CHxx-rev)` for revision updates, `(CONCEPT)` entries from world.build are left as-is unless contradicted.
- **Don't speculate.** Only record what is explicitly established in the chapter text. If a character's eye color isn't mentioned, don't infer it.
- **Update incrementally.** Add to existing files rather than rewriting them. Preserve all existing entries from other chapters.
- **Cross-reference generously.** When a detail connects entities (e.g., "Elena visited the Iron Quarter"), update both files.
- **Respect (CONCEPT) entries.** Details tagged `(CONCEPT)` from pre-writing world-building should not be removed. If a chapter contradicts a `(CONCEPT)` entry, flag the conflict but update the entry to reflect what's actually in the text, tagging the new value with the chapter number.
- **Flag, don't fix.** When revision reconciliation reveals downstream impacts, flag them clearly in the report but do NOT automatically edit other chapters. The user decides how to handle ripple effects.
