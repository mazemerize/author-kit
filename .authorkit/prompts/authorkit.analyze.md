---
description: Perform a read-only cross-chapter consistency and quality analysis across the entire book, including upstream document drift detection.
handoffs:
  - label: Sync World
    agent: authorkit.world.sync
    prompt: Sync and verify world files
  - label: Revise Chapter
    agent: authorkit.revise
    prompt: Address the critical issues from the analysis
  - label: Amend A Fact
    agent: authorkit.amend
    prompt: Change an established fact across the manuscript
scripts:
  ps: scripts/powershell/check-prerequisites.ps1 -Json -RequireChapters -IncludeChapters
---

## User Input

```text
{{USER_INPUT_TOKEN}}
```

You **MUST** consider the user input before proceeding (if not empty).

## Goal

Identify inconsistencies, continuity errors, pacing problems, and unresolved threads across all drafted chapters. This command MUST run only after at least several chapters have been drafted.

## Operating Constraints

**STRICTLY READ-ONLY**: Do **not** modify any files. Output a structured analysis report. Offer an optional remediation plan (user must explicitly approve before any edits).

**Constitution Authority**: The book constitution (`/memory/constitution.md`) is the authoritative style guide. Constitution violations are automatically CRITICAL.
**Style Continuity Anchor**: `book/style-anchor.md` is the continuity baseline across model switches. Style-anchor drift is at least MEDIUM severity.

## Execution Steps

### 1. Initialize Analysis Context

Run `{{SCRIPT_CHECK_PREREQ}}` once from repo root and parse JSON for BOOK_DIR, STYLE_ANCHOR, and AVAILABLE_DOCS. Derive absolute paths.

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

**From world/ folder (if exists):**
- **If `world/_index.md` exists**: Read it first. Use the Chapter Manifest to load entity files per chapter (targeted loading) rather than all files at once. Use the Alias Lookup for name resolution when cross-referencing chapter text against world/ entities.
- If no index: load all entity files (characters/, places/, organizations/, history/, systems/, notes/)
- Pay attention to chapter tags `(CHxx)` and `(CONCEPT)` for evolution tracking

**From all drafted chapters (chapters/NN/draft.md):**
- Full prose for consistency checking

**From constitution:**
- All writing principles

**From style anchor (if exists):**
- `book/style-anchor.md` cadence, diction/register, imagery density, dialogue profile, and drift flags

### 3. Upstream Drift Detection (Reconciliation)

Before analyzing cross-chapter quality, check whether upstream planning documents have drifted from what was actually drafted. Drafted chapters are the canonical source of truth — everything else may be stale.

**Scope**: All drafted chapters (or user-specified range from input).

#### 3a. Outline Drift (outline.md)

For each chapter entry in outline.md that corresponds to a drafted chapter:
- Read the outline's Summary, Key Events, Characters Present, Ends With, and Connections fields.
- For each factual claim, grep the corresponding `chapters/NN/draft.md` for verification.
- Flag claims that don't match the draft.
- Common drift: characters acting differently, events playing out differently, endings that don't match.

For not-yet-drafted chapters: check if their claims about already-drafted chapters are accurate.

#### 3b. Concept Drift (concept.md)

- Focus on Synopsis, Characters, and Clarifications sections.
- Identify claims about specific events, character behaviors, or plot mechanics that have been concretized differently in drafts.

#### 3c. Chapters.md Drift

- Check each chapter's summary text against the draft. Key details should match.

#### 3d. World Drift (world/ files)

- For world/ files tagged `(CHxx)`: verify tagged claims against the actual draft.
- For `(CONCEPT)` entries: check if drafts now cover that topic differently.

**Drift severity**:
- **High**: A future chapter plan referencing this claim would produce a continuity error.
- **Medium**: The claim is inaccurate but unlikely to cause downstream errors.
- **Low**: Technically compatible but could be more precise.

**Offer drift fixes**: After presenting drift findings, ask the user: "Fix all / Fix high-severity only / Review one by one / Skip?" If fixing, update upstream documents to match drafts (never modify drafts).

### 4. Detection Passes

Focus on high-signal findings. Limit to 50 findings total (excluding drift findings from step 3).

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
- Drift from `book/style-anchor.md` profile

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

If a `world/` folder exists in BOOK_DIR, perform these checks by cross-referencing world/ files against all drafted chapters:

- **Setting detail drift**: Locations described differently across chapters (e.g., building changes floors, distances change, weather contradictions)
- **Character detail contradictions**: Physical descriptions, ages, backgrounds that conflict between chapters or with world/ files
- **Organization continuity**: Membership, hierarchy, or purpose changes without narrative justification
- **Timeline/history contradictions**: Past events described differently, contradictory dates or sequences
- **System rule violations**: Magic/technology/political systems behaving inconsistently with established rules in world/systems/
- **Geography contradictions**: Travel times, distances, spatial relationships that don't add up
- **Cultural inconsistencies**: Customs, language, social norms that change without explanation
- **(CONCEPT) vs chapter conflicts**: Details tagged `(CONCEPT)` in world/ files that are contradicted by what's actually written in chapters

Each finding should cite the specific world/ file and the chapter(s) where the contradiction occurs.

### 5. Severity Assignment

- **CRITICAL**: Constitution violation, major plot hole, timeline contradiction, character inconsistency that breaks immersion, world rule violation that breaks established system logic, major geography/timeline contradiction
- **HIGH**: Unresolved subplot, significant pacing issue, theme dropped, important foreshadowing unfulfilled, character detail contradiction across chapters, significant setting drift
- **MEDIUM**: Minor continuity error, slight voice drift, pacing could be improved, minor character inconsistency, minor world detail inconsistency, cultural detail mismatch
- **LOW**: Style nitpick, optional improvement, very minor detail mismatch

### 6. Produce Analysis Report

Output a Markdown report (no file writes):

```markdown
## Book Analysis Report: [TITLE]

**Chapters Analyzed**: [N] of [Total]
**Analysis Date**: [DATE]

### Upstream Drift (Reconciliation)

| Source | Claim | Draft Reality | Severity | Fixed? |
|--------|-------|---------------|----------|--------|
| outline.md CH03 | [claim] | [reality] | High | [Yes/No/Skipped] |

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
| [Style Anchor] | [PASS/FAIL] | [chapters] |

### World Consistency (if world/ exists)

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

### 7. Next Actions

- If drift was found and fixed: note what upstream documents were updated
- If drift was found but skipped: recommend running `/authorkit.analyze` again after fixing
- If CRITICAL issues exist: Recommend resolving before drafting more chapters
- Provide specific `/authorkit.revise` suggestions for top issues
- If world-building issues dominate: Recommend `/authorkit.world.sync verify only` for deeper world-specific analysis
- If mostly clean: Suggest continuing with next chapter or moving to final polish

