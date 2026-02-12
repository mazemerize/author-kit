# Author Kit

**Write books with structured AI assistance. Chapter by chapter. Draft by draft.**

An open-source toolkit that brings structured, template-driven principles to book writing. Instead of vibe-writing an entire manuscript, Author Kit guides you through a structured workflow: define your concept, outline the structure, then iteratively plan, draft, and review each chapter.

---

## Table of Contents

- [What is Author Kit?](#what-is-author-kit)
- [Get Started](#get-started)
- [Available Commands](#available-commands)
- [Chapter-Level Iteration](#chapter-level-iteration)
- [World Maintenance](#world-maintenance)
- [Project Structure](#project-structure)
- [Environment Variables](#environment-variables)
- [Prerequisites](#prerequisites)

---

## What is Author Kit?

Traditional AI-assisted writing often means dumping an idea and hoping for a good result. Author Kit takes a different approach:

1. **Concept first** — Define your book's premise, themes, audience, and voice before writing a single word
2. **Outline before prose** — Create a structural outline with chapter summaries, character arcs, and thematic maps
3. **World maintenance** — Build and track your book's world (characters, places, systems, history) as a living reference
4. **Chapter-level iteration** — Each chapter goes through its own plan-draft-review cycle, so quality is built in, not bolted on
5. **Cross-chapter consistency** — Analyze the full manuscript for continuity, pacing, and thematic coherence

This works for **any genre**: literary fiction, thrillers, non-fiction guides, memoirs, technical books, and everything in between.

---

## Get Started

Author Kit works with both **Claude Code** and **GitHub Copilot Chat** (in VS Code). The workflows are identical — use `/authorkit.*` commands to trigger each step.

### 1. Set up the project

Clone or copy Author Kit into your working directory. Open it in Claude Code or VS Code with GitHub Copilot.

### 2. Establish your writing principles

Define the voice, tone, and style rules for your book. This becomes the "style bible" that all chapters are written and reviewed against.

```
/authorkit.constitution First person POV, present tense, literary but accessible prose. Dark humor. Target audience: adult readers of literary fiction. No purple prose. Show don't tell for emotions.
```

### 3. Conceive the book

Describe your book idea. Focus on **what** the book is about and **why** it matters, not the chapter-by-chapter details.

```
/authorkit.conceive A mystery novel set in a crumbling Victorian observatory where an astronomer discovers that the star catalogue compiled by the previous director contains a hidden code. As she deciphers it, she realizes the observatory's history is entangled with a century-old disappearance.
```

This creates a `concept.md` with the premise, genre, themes, characters, voice, and scope.

### 4. Clarify the concept (optional)

Identify and resolve any ambiguities in the concept before outlining.

```
/authorkit.clarify
```

### 5. Build the world (optional)

Establish the rules, geography, characters, history, and systems of your book's world before writing. Especially valuable for fantasy, sci-fi, and historical fiction, but works for any genre.

```
/authorkit.world.build magic system, political structure
```

You can run this multiple times to iteratively deepen specific areas. See [World Maintenance](#world-maintenance) for the full workflow.

### 6. Create the outline

Generate the full book structure: chapter summaries, character arcs, thematic thread maps, and narrative arc.

```
/authorkit.outline
```

This also generates `research.md` (world-building notes) and `characters.md` (character profiles).

### 7. Break into chapters

Convert the outline into a chapter-level task list with status tracking.

```
/authorkit.chapters
```

### 8. Write chapter by chapter

Iterate through each chapter:

```
/authorkit.chapter.plan 1     # Plan chapter 1 (scenes, beats, arc)
/authorkit.chapter.draft 1    # Write the actual prose
/authorkit.chapter.review 1   # Review against plan and constitution
```

If the review passes, move to the next chapter. If it needs revision, re-plan and re-draft.

After drafting a chapter, run `/authorkit.world.update` to extract new world details into the `World/` folder (see [World Maintenance](#world-maintenance)).

### 9. Analyze the full manuscript

After drafting several chapters (or all of them), run a cross-chapter analysis:

```
/authorkit.analyze
```

This checks for continuity errors, plot holes, pacing problems, unresolved threads, and constitution violations across all drafted chapters.

You can also run `/authorkit.world.verify` at any point to check the `World/` folder for internal consistency and alignment with the manuscript.

### 10. Revise as needed

Apply targeted fixes based on analysis findings:

```
/authorkit.revise Fix the timeline contradiction between chapters 3 and 7
```

---

## Available Commands

### Core Workflow

| Command | Description |
|---------|-------------|
| `/authorkit.constitution` | Create or update writing principles (voice, tone, style guide) |
| `/authorkit.conceive` | Define book concept from a natural language description |
| `/authorkit.clarify` | Resolve ambiguities in the book concept |
| `/authorkit.outline` | Create the full book outline with chapter summaries and arcs |
| `/authorkit.chapters` | Generate chapter-level task breakdown from the outline |

### Chapter-Level Commands

| Command | Description |
|---------|-------------|
| `/authorkit.chapter.plan [N]` | Plan a specific chapter in detail (scenes, beats, connections) |
| `/authorkit.chapter.draft [N]` | Write the actual chapter prose |
| `/authorkit.chapter.review [N]` | Review a drafted chapter against plan, concept, and constitution |

### World Maintenance

| Command | Description |
|---------|-------------|
| `/authorkit.world.build` | Build the book's world — establish rules, geography, characters, history, and systems |
| `/authorkit.world.update [N]` | Extract world-building details from drafted chapters into the `World/` folder |
| `/authorkit.world.verify` | Verify `World/` files for internal consistency and manuscript alignment |

### Quality & Analysis

| Command | Description |
|---------|-------------|
| `/authorkit.analyze` | Cross-chapter consistency and quality analysis (read-only) |
| `/authorkit.revise` | Apply revisions to specific chapters based on feedback |
| `/authorkit.checklist` | Generate custom quality checklists (craft, continuity, pacing, etc.) |

---

## Chapter-Level Iteration

The core innovation of Author Kit is **chapter-level iteration**. Instead of writing the whole book and then revising, each chapter goes through its own cycle:

```
                    ┌─────────────────────────┐
                    │                         │
                    v                         │
  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
  │  Plan    │──│  Draft   │──│  Review  │───┘ (if needs revision)
  │ chapter  │  │ chapter  │  │ chapter  │
  └──────────┘  └──────────┘  └──────────┘
                                  │
                                  │ (if passes)
                                  v
                            Next chapter
```

Progress is tracked in `chapters.md` with status markers:

| Marker | Status | Meaning |
|--------|--------|---------|
| `[ ]` | Pending | Chapter not yet started |
| `[P]` | Planned | Chapter plan exists (`chapters/NN/plan.md`) |
| `[D]` | Drafted | First draft written (`chapters/NN/draft.md`) |
| `[R]` | Reviewed | Review completed, needs revision |
| `[X]` | Approved | Chapter passed review, ready for final manuscript |

Example `chapters.md`:

```markdown
## Part 1: The Observatory

- [X] CH01 [Part 1] The Arrival - Elena discovers the abandoned observatory
- [D] CH02 [Part 1] The Catalogue - She finds the star catalogue with odd annotations
- [P] CH03 [Part 1] The Pattern - First hint that the annotations form a code
- [ ] CH04 [Part 1] The Predecessor - Learning about the previous director

## Part 2: The Code

- [ ] CH05 [Part 2] The Cipher - Elena begins decryption
...
```

---

## World Maintenance

Author Kit includes a dedicated world-building system that tracks every detail of your book's world — characters, places, organizations, history, and systems — across the entire manuscript.

### Why?

As your book grows, keeping track of world details becomes harder. Was the tavern called The Iron Flagon or The Iron Flask? Did Elena have green eyes in chapter 2 and blue eyes in chapter 9? World maintenance prevents these consistency problems by maintaining a structured `World/` folder alongside your chapters.

### The World/ Folder

```
World/
├── Characters/     # One file per major character (identity, appearance, relationships, arc)
├── Organizations/  # Factions, guilds, governments, companies
├── Places/         # Locations with descriptions, significance, geography
├── History/        # Past events, backstory, timeline
├── Systems/        # Magic systems, technology, social structures, frameworks
└── Notes/          # Miscellaneous world notes
```

Only relevant categories are created — a contemporary novel won't need a `Systems/` folder for magic.

### Workflow

**1. Build the world** (before or after outlining):

```
/authorkit.world.build                          # Comprehensive world-building
/authorkit.world.build magic system, geography  # Focus on specific areas
```

All entries from initial world-building are tagged `(CONCEPT)` to distinguish them from details that emerge during drafting.

**2. Update after drafting** (after each chapter):

```
/authorkit.world.update 3       # Extract details from chapter 3
/authorkit.world.update 1-5     # Scan a range of chapters
/authorkit.world.update all     # Scan all drafted chapters
```

New details are tagged with their source chapter (e.g., `(CH03)`). If a chapter has been revised and is re-scanned, entries are tagged `(CH03-rev)` and a downstream impact report highlights which other chapters may need attention.

**3. Verify consistency** (anytime):

```
/authorkit.world.verify                  # Verify everything
/authorkit.world.verify Characters/      # Verify just character files
/authorkit.world.verify Systems/ Places/ # Verify specific categories
```

This is a **read-only** diagnostic that checks for:

- **Reciprocal references** — if Elena lists Marcus as her mentor, Marcus's file should reference Elena
- **Cross-entity consistency** — organization members should have character files, places in events should have place files
- **System coherence** — rules within and across systems should not contradict
- **Geographic plausibility** — travel times, climate, and spatial relationships should make sense
- **Timeline consistency** — causes precede effects, ages match historical events
- **Chapter tag integrity** — every `(CHxx)` tag should reference an actual drafted chapter
- **Staleness detection** — entities referenced in chapters but never updated in `World/`

Issues are rated by severity (Critical, High, Medium, Low) with specific file paths and actionable recommendations.

---

## Project Structure

### Toolkit files (`.authorkit/`, `.claude/`, `.github/`)

```
.authorkit/
├── memory/
│   └── constitution.md              # Writing principles template
├── scripts/
│   └── powershell/
│       ├── common.ps1               # Shared functions
│       ├── create-new-book.ps1      # Create book directory + branch
│       ├── setup-outline.ps1        # Initialize outline artifacts
│       └── check-prerequisites.ps1  # Validate required files
└── templates/
    ├── concept-template.md
    ├── outline-template.md
    ├── chapters-template.md
    ├── chapter-plan-template.md
    ├── checklist-template.md
    └── agent-file-template.md

.claude/                                 # Claude Code commands
└── commands/
    ├── authorkit.constitution.md
    ├── authorkit.conceive.md
    ├── authorkit.clarify.md
    ├── authorkit.outline.md
    ├── authorkit.chapters.md
    ├── authorkit.chapter.plan.md
    ├── authorkit.chapter.draft.md
    ├── authorkit.chapter.review.md
    ├── authorkit.analyze.md
    ├── authorkit.revise.md
    ├── authorkit.checklist.md
    ├── authorkit.world.build.md
    ├── authorkit.world.update.md
    └── authorkit.world.verify.md

.github/                                 # GitHub Copilot prompts
├── copilot-instructions.md              # Global Copilot instructions
└── prompts/
    ├── authorkit.constitution.prompt.md
    ├── authorkit.conceive.prompt.md
    ├── authorkit.clarify.prompt.md
    ├── authorkit.outline.prompt.md
    ├── authorkit.chapters.prompt.md
    ├── authorkit.chapter.plan.prompt.md
    ├── authorkit.chapter.draft.prompt.md
    ├── authorkit.chapter.review.prompt.md
    ├── authorkit.analyze.prompt.md
    ├── authorkit.revise.prompt.md
    ├── authorkit.checklist.prompt.md
    ├── authorkit.world.build.prompt.md
    ├── authorkit.world.update.prompt.md
    └── authorkit.world.verify.prompt.md
```

### Book output files (`books/`)

Created when you run `/authorkit.conceive`:

```
books/
└── 001-victorian-mystery/
    ├── concept.md                   # Book concept
    ├── outline.md                   # Full book outline
    ├── research.md                  # Research & world-building notes
    ├── characters.md                # Character profiles
    ├── chapters.md                  # Chapter task breakdown with status
    ├── checklists/                  # Quality checklists
    ├── World/                       # World-building reference files
    │   ├── Characters/             # Character profiles
    │   ├── Organizations/          # Factions, groups, institutions
    │   ├── Places/                 # Locations and geography
    │   ├── History/                # Past events and timeline
    │   ├── Systems/                # Magic, technology, social systems
    │   └── Notes/                  # Miscellaneous world notes
    └── chapters/                    # Individual chapter content
        ├── 01/
        │   ├── plan.md             # Chapter plan
        │   ├── draft.md            # Written prose
        │   └── review.md           # Review notes
        ├── 02/
        │   ├── plan.md
        │   ├── draft.md
        │   └── review.md
        └── ...
```

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `AUTHORKIT_BOOK` | Override book detection for non-Git repositories. Set to the book directory name (e.g., `001-victorian-mystery`) to work on a specific book when not using Git branches. Must be set before using `/authorkit.outline` or follow-up commands. |

---

## Prerequisites

- **Windows** with **PowerShell** (the scripts use `.ps1` files)
- **Git** for branch management and version control
- One of the following AI agents:
  - **[Claude Code](https://www.anthropic.com/claude-code)** — uses `/authorkit.*` commands from `.claude/commands/`
  - **[GitHub Copilot](https://github.com/features/copilot)** in **VS Code** — uses `/authorkit.*` commands from `.github/prompts/` in Copilot Chat (Agent mode recommended)
