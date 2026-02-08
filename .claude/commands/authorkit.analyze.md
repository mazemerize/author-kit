---
description: Perform a read-only cross-chapter consistency and quality analysis across the entire book.
scripts:
  ps: scripts/powershell/check-prerequisites.ps1 -Json -RequireChapters -IncludeChapters
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Goal

Identify inconsistencies, continuity errors, pacing problems, and unresolved threads across all drafted chapters. This command MUST run only after at least several chapters have been drafted.

## Operating Constraints

**STRICTLY READ-ONLY**: Do **not** modify any files. Output a structured analysis report. Offer an optional remediation plan (user must explicitly approve before any edits).

**Constitution Authority**: The book constitution (`/memory/constitution.md`) is the authoritative style guide. Constitution violations are automatically CRITICAL.

## Execution Steps

### 1. Initialize Analysis Context

Run `{SCRIPT}` once from repo root and parse JSON for BOOK_DIR and AVAILABLE_DOCS. Derive absolute paths.

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

### 4. Severity Assignment

- **CRITICAL**: Constitution violation, major plot hole, timeline contradiction, character inconsistency that breaks immersion
- **HIGH**: Unresolved subplot, significant pacing issue, theme dropped, important foreshadowing unfulfilled
- **MEDIUM**: Minor continuity error, slight voice drift, pacing could be improved, minor character inconsistency
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
- Provide specific `/authorkit.revise` suggestions for top issues
- If mostly clean: Suggest continuing with next chapter or moving to final polish
