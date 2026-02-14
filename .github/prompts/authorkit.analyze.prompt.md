---
description: Perform a read-only cross-chapter consistency and quality analysis across the entire book.
mode: agent
---

## User Input

```text
${input:analysisScope}
```

You **MUST** consider the user input before proceeding (if not empty).

## Goal

Identify inconsistencies, continuity errors, pacing problems, and unresolved threads across all drafted chapters. This command MUST run only after at least several chapters have been drafted.

## Operating Constraints

**STRICTLY READ-ONLY**: Do **not** modify any files. Output a structured analysis report. Offer an optional remediation plan (user must explicitly approve before any edits).

**Constitution Authority**: The book constitution (`.authorkit/memory/constitution.md`) is the authoritative style guide. Constitution violations are automatically CRITICAL.

## Execution Steps

### 1. Initialize Analysis Context

Run `.authorkit/scripts/powershell/check-prerequisites.ps1 -Json -RequireChapters -IncludeChapters` once from repo root and parse JSON for BOOK_DIR and AVAILABLE_DOCS. Derive absolute paths.

Abort with an error message if required files are missing.

### 2. Load Artifacts

**From concept.md:**
- Premise, themes, characters/subjects, voice & tone, scope

**From outline.md:**
- Chapter structure, character arcs, thematic thread map, narrative arc

**From chapters.md:**
- Chapter statuses, dependencies

**From characters.md (if exists):**
- Character profiles, speech patterns, relationships

**From World/ folder (if exists):**
- **If `World/_index.md` exists**: Read it first. Use the Chapter Manifest to load entity files per chapter (targeted loading) rather than all files at once. Use the Alias Lookup for name resolution when cross-referencing chapter text against World/ entities.
- If no index: load all entity files (Characters/, Places/, Organizations/, History/, Systems/, Notes/)
- Pay attention to chapter tags `(CHxx)` and `(CONCEPT)` for evolution tracking

**From all drafted chapters (chapters/NN/draft.md):**
- Full prose for consistency checking

**From constitution:**
- All writing principles

### 3. Detection Passes

Focus on high-signal findings. Limit to 50 findings total.

#### A. Continuity & Timeline
- Events referenced in later chapters that weren't established in earlier ones
- Timeline contradictions (character in two places at once, seasonal inconsistencies)
- Character knowledge inconsistencies (knowing something before it was revealed)
- Setting details that change between chapters (eye color, building location, etc.)

#### B. Character Consistency (Fiction)
- Voice/speech pattern drift across chapters
- Motivation changes without justification
- Relationship dynamics that shift without cause
- Characters acting out of established character

#### C. Theme & Motif Tracking
- Themes introduced but never developed or resolved
- Themes that appear inconsistently
- Motifs that drift in meaning
- Foreshadowing that is never paid off

#### D. Pacing Analysis
- Consecutive chapters with similar energy levels
- Chapters that are significantly longer/shorter than average without justification
- Action/reflection balance across parts/acts
- Tension curve compared to intended narrative arc

#### E. Voice & Style Consistency
- POV breaks or inconsistencies
- Tense shifts (unless intentional)
- Prose style drift (e.g., becoming more/less literary)
- Constitution principle violations

#### F. Argument Coherence (Non-Fiction)
- Claims made without support
- Contradictory statements across chapters
- Prerequisites explained after they're needed
- Conclusions that don't follow from presented evidence

#### G. Plot Thread Tracking (Fiction)
- Subplots opened but not closed
- Chekhov's guns that never fire
- Mysteries raised but never resolved
- Character relationships that stall

#### H. World-Building Consistency

If a `World/` folder exists in BOOK_DIR, perform these checks by cross-referencing World/ files against all drafted chapters:

- **Setting detail drift**: Locations described differently across chapters (e.g., building changes floors, distances change, weather contradictions)
- **Character detail contradictions**: Physical descriptions, ages, backgrounds that conflict between chapters or with World/ files
- **Organization continuity**: Membership, hierarchy, or purpose changes without narrative justification
- **Timeline/history contradictions**: Past events described differently, contradictory dates or sequences
- **System rule violations**: Magic/technology/political systems behaving inconsistently with established rules in World/Systems/
- **Geography contradictions**: Travel times, distances, spatial relationships that don't add up
- **Cultural inconsistencies**: Customs, language, social norms that change without explanation
- **(CONCEPT) vs chapter conflicts**: Details tagged `(CONCEPT)` in World/ files that are contradicted by what's actually written in chapters

Each finding should cite the specific World/ file and the chapter(s) where the contradiction occurs.

### 4. Severity Assignment

- **CRITICAL**: Constitution violation, major plot hole, timeline contradiction, character inconsistency that breaks immersion, world rule violation that breaks established system logic, major geography/timeline contradiction
- **HIGH**: Unresolved subplot, significant pacing issue, theme dropped, important foreshadowing unfulfilled, character detail contradiction across chapters, significant setting drift
- **MEDIUM**: Minor continuity error, slight voice drift, pacing could be improved, minor character inconsistency, minor world detail inconsistency, cultural detail mismatch
- **LOW**: Style nitpick, optional improvement, very minor detail mismatch

### 5. Produce Analysis Report

Output a Markdown report (no file writes):

```markdown
## Book Analysis Report: [TITLE]

**Chapters Analyzed**: [N] of [Total]
**Analysis Date**: [DATE]

### Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| C1 | Continuity | HIGH | CH03, CH07 | Character's eye color changes | Standardize to blue (CH03 version) |

### Thread Tracking

| Thread | Introduced | Developed | Resolved | Status |
|--------|-----------|-----------|----------|--------|
| [Thread name] | CH01 | CH03, CH07 | CH12 | Complete |
| [Thread name] | CH02 | CH05 | - | OPEN |

### Pacing Map

| Chapter | Word Count | Energy Level | Type |
|---------|-----------|-------------|------|
| CH01 | 3,200 | Medium | Setup |
| CH02 | 4,100 | High | Action |

### Constitution Compliance

| Principle | Status | Chapters with Issues |
|-----------|--------|---------------------|
| [Voice] | PASS | - |
| [Tense] | FAIL | CH04, CH09 |

### World Consistency (if World/ exists)

| Category | Entries Checked | Conflicts Found | Details |
|----------|----------------|-----------------|---------|
| Characters | [N] | [N] | [Brief summary] |
| Places | [N] | [N] | [Brief summary] |
| Organizations | [N] | [N] | [Brief summary] |
| Systems | [N] | [N] | [Brief summary] |
| (CONCEPT) Conflicts | [N] | [N] | [Pre-writing details contradicted by chapters] |

### Metrics

- Total chapters drafted: [N]
- Total word count: [N]
- Average chapter length: [N] words
- Critical issues: [N]
- Open threads: [N]
- Constitution violations: [N]
```

### 6. Next Actions

- If CRITICAL issues exist: Recommend resolving before drafting more chapters
- Provide specific revision suggestions for top issues using the `authorkit.revise` prompt
- If world-building issues dominate: Recommend `authorkit.world.verify` for deeper world-specific analysis
- If mostly clean: Suggest continuing with next chapter or moving to final polish
