# Author Kit

**Write books with structured AI assistance. Chapter by chapter. Draft by draft.**

An open-source toolkit that brings structured, template-driven principles to book writing. Instead of vibe-writing an entire manuscript, Author Kit guides you through a structured workflow: define your concept, outline the structure, then iteratively plan, draft, and review each chapter.

---

## Table of Contents

- [What is Author Kit?](#what-is-author-kit)
- [Get Started](#get-started)
- [Available Commands](#available-commands)
- [Chapter-Level Iteration](#chapter-level-iteration)
- [Project Structure](#project-structure)
- [Environment Variables](#environment-variables)
- [Prerequisites](#prerequisites)

---

## What is Author Kit?

Traditional AI-assisted writing often means dumping an idea and hoping for a good result. Author Kit takes a different approach:

1. **Concept first** - Define your book's premise, themes, audience, and voice before writing a single word
2. **Outline before prose** - Create a structural outline with chapter summaries, character arcs, and thematic maps
3. **Chapter-level iteration** - Each chapter goes through its own plan-draft-review cycle, so quality is built in, not bolted on
4. **Cross-chapter consistency** - Analyze the full manuscript for continuity, pacing, and thematic coherence

This works for **any genre**: literary fiction, thrillers, non-fiction guides, memoirs, technical books, and everything in between.

---

## Get Started

Author Kit works with both **Claude Code** and **GitHub Copilot Chat** (in VS Code). The workflows are identical — only how you invoke them differs.

### 1. Set up the project

Clone or copy Author Kit into your working directory.

**Claude Code**: Open Claude Code in the project folder. You'll see the `/authorkit.*` commands available.

**GitHub Copilot**: Open the project in VS Code. The prompt files in `.github/prompts/` are available in Copilot Chat — type `#` and select the `authorkit.*` prompt you want to use.

### 2. Establish your writing principles

Define the voice, tone, and style rules for your book. This becomes the "style bible" that all chapters are written and reviewed against.

**Claude Code**:
```
/authorkit.constitution First person POV, present tense, literary but accessible prose. Dark humor. Target audience: adult readers of literary fiction. No purple prose. Show don't tell for emotions.
```

**GitHub Copilot**: Open Copilot Chat, attach the `authorkit.constitution` prompt, and provide your writing principles as input.

### 3. Conceive the book

Describe your book idea. Focus on **what** the book is about and **why** it matters, not the chapter-by-chapter details.

**Claude Code**:
```
/authorkit.conceive A mystery novel set in a crumbling Victorian observatory where an astronomer discovers that the star catalogue compiled by the previous director contains a hidden code. As she deciphers it, she realizes the observatory's history is entangled with a century-old disappearance.
```

**GitHub Copilot**: Attach the `authorkit.conceive` prompt and provide your book description as input.

This creates a `concept.md` with the premise, genre, themes, characters, voice, and scope.

### 4. Clarify the concept (optional)

Identify and resolve any ambiguities in the concept before outlining.

**Claude Code**: `/authorkit.clarify`

**GitHub Copilot**: Attach the `authorkit.clarify` prompt.

### 5. Create the outline

Generate the full book structure: chapter summaries, character arcs, thematic thread maps, and narrative arc.

**Claude Code**: `/authorkit.outline`

**GitHub Copilot**: Attach the `authorkit.outline` prompt.

This also generates `research.md` (world-building notes) and `characters.md` (character profiles).

### 6. Break into chapters

Convert the outline into a chapter-level task list with status tracking.

**Claude Code**: `/authorkit.chapters`

**GitHub Copilot**: Attach the `authorkit.chapters` prompt.

### 7. Write chapter by chapter

Iterate through each chapter:

**Claude Code**:
```
/authorkit.chapter.plan 1     # Plan chapter 1 (scenes, beats, arc)
/authorkit.chapter.draft 1    # Write the actual prose
/authorkit.chapter.review 1   # Review against plan and constitution
```

**GitHub Copilot**: Attach the `authorkit.chapter.plan`, `authorkit.chapter.draft`, or `authorkit.chapter.review` prompt and provide the chapter number as input.

If the review passes, move to the next chapter. If it needs revision, re-plan and re-draft.

### 8. Analyze the full manuscript

After drafting several chapters (or all of them), run a cross-chapter analysis:

**Claude Code**: `/authorkit.analyze`

**GitHub Copilot**: Attach the `authorkit.analyze` prompt.

This checks for continuity errors, plot holes, pacing problems, unresolved threads, and constitution violations across all drafted chapters.

### 9. Revise as needed

Apply targeted fixes based on analysis findings:

**Claude Code**:
```
/authorkit.revise Fix the timeline contradiction between chapters 3 and 7
```

**GitHub Copilot**: Attach the `authorkit.revise` prompt and describe the revision needed as input.

---

## Available Commands

Author Kit provides the same workflows for both Claude Code (slash commands) and GitHub Copilot (prompt files).

### Core Workflow

| Claude Code | Copilot Prompt | Description |
|-------------|---------------|-------------|
| `/authorkit.constitution` | `authorkit.constitution` | Create or update writing principles (voice, tone, style guide) |
| `/authorkit.conceive` | `authorkit.conceive` | Define book concept from a natural language description |
| `/authorkit.clarify` | `authorkit.clarify` | Resolve ambiguities in the book concept |
| `/authorkit.outline` | `authorkit.outline` | Create the full book outline with chapter summaries and arcs |
| `/authorkit.chapters` | `authorkit.chapters` | Generate chapter-level task breakdown from the outline |

### Chapter-Level Commands

| Claude Code | Copilot Prompt | Description |
|-------------|---------------|-------------|
| `/authorkit.chapter.plan [N]` | `authorkit.chapter.plan` | Plan a specific chapter in detail (scenes, beats, connections) |
| `/authorkit.chapter.draft [N]` | `authorkit.chapter.draft` | Write the actual chapter prose |
| `/authorkit.chapter.review [N]` | `authorkit.chapter.review` | Review a drafted chapter against plan, concept, and constitution |

### Quality & Analysis

| Claude Code | Copilot Prompt | Description |
|-------------|---------------|-------------|
| `/authorkit.analyze` | `authorkit.analyze` | Cross-chapter consistency and quality analysis (read-only) |
| `/authorkit.revise` | `authorkit.revise` | Apply revisions to specific chapters based on feedback |
| `/authorkit.checklist` | `authorkit.checklist` | Generate custom quality checklists (craft, continuity, pacing, etc.) |

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
    └── authorkit.checklist.md

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
    └── authorkit.checklist.prompt.md
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
  - **[Claude Code](https://www.anthropic.com/claude-code)** — uses `/authorkit.*` slash commands from `.claude/commands/`
  - **[GitHub Copilot](https://github.com/features/copilot)** in **VS Code** — uses prompt files from `.github/prompts/` in Copilot Chat (Agent mode recommended)
