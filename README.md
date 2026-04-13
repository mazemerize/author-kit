![Author Kit Logo](./media/logo.png)

**Write books with structured AI assistance. Chapter by chapter. Draft by draft. Together.**

An open-source toolkit that brings structured, template-driven principles to book writing. Instead of vibe-writing an entire manuscript, Author Kit guides you through a structured workflow: define your concept, outline the structure, then iteratively plan, draft, and review each chapter — with full support for changing direction mid-process. Outline incrementally as you discover your story, brainstorm interactively, and co-write chapters scene by scene.

---

## Table of Contents

- [What is Author Kit?](#what-is-author-kit)
- [Get Started](#get-started)
- [The Full Workflow](#the-full-workflow)
- [Available Commands](#available-commands)
- [Command Interactions](#command-interactions)
- [Chapter-Level Iteration](#chapter-level-iteration)
- [World Maintenance](#world-maintenance)
- [Mid-Process Changes](#mid-process-changes)
- [Book Export, Audiobook and Statistics](#book-export-audiobook-and-statistics)
- [Project Structure](#project-structure)
- [Environment Variables](#environment-variables)
- [Prerequisites](#prerequisites)

---

## What is Author Kit?

Traditional AI-assisted writing often means dumping an idea and hoping for a good result. Author Kit takes a different approach:

1. **Concept first** — Define your book's premise, themes, audience, and voice before writing a single word
2. **Incremental discovery** — Outline part of the book, draft those chapters, then extend the outline based on what emerged. Brainstorm ideas interactively before committing
3. **Outline before prose** — Create a structural outline with chapter summaries, character arcs, and thematic maps — all at once or part by part
4. **World maintenance** — Build and track your book's world (characters, places, systems, history) as a living reference
5. **Collaborative chapter writing** — Write chapters together: draft scene by scene, get help on specific paragraphs, or let the AI continue where you left off
6. **Chapter-level iteration** — Each chapter goes through its own plan-draft-review cycle, so quality is built in, not bolted on
7. **Cross-chapter consistency** — Analyze the full manuscript for continuity, pacing, and thematic coherence
8. **Mid-process flexibility** — Amend direction or facts, defer decisions, explore alternatives, and restructure without losing work
9. **Manuscript generation** — Export the fully generated content as a word or epub document
10. **Audiobook export** — Use AI to generate an audio version of your manuscript

This works for **any genre**: literary fiction, thrillers, non-fiction guides, memoirs, technical books, and everything in between.

### Read and Learn More about Author Kit 💡

Before getting started, read more about Author Kit, its benefits and drawbacks, and how it operates.

**Read our articles on Medium** (written for an earlier version of Author Kit — the specific commands have evolved, but the core philosophy and approach remain the same):
- [Why AI Writes the Same Book Every Time](https://medium.com/@mdemarne/why-ai-writes-the-same-book-every-time-0b02323f618a)
- [The World Your AI Forgot to Build](https://medium.com/@mdemarne/the-world-your-ai-forgot-to-build-c7fda0fe71c7)
- [Catching What Drifts in Your Human-Led, AI-Assisted Manuscript](https://medium.com/@mdemarne/catching-what-drifts-in-your-human-led-ai-assisted-manuscript-4d4fb7334a24)
- [Writing with AI: What Works, What Doesn’t, and What’s Left](https://medium.com/@mdemarne/writing-with-ai-what-works-what-doesnt-and-what-s-left-72d53d95a6da)

---

## Get Started

Author Kit uses an installer CLI and supports **Claude Code**, **GitHub Copilot**, and **Codex**.

### Prerequisites

- **Python 3.11+**
- **uv** (`uvx` and `uv tool install`)
- **Git**
- **Linux/macOS or Windows**
- One of the following AI agents:
  - **[Claude Code](https://www.anthropic.com/claude-code)**
  - **[GitHub Copilot](https://github.com/features/copilot)**
  - **[Codex CLI](https://github.com/openai/codex)**

### 1. Set up the project

One-shot install (always latest):

```bash
uvx --from git+https://github.com/mazemerize/author-kit.git authorkit init . --ai claude --script sh
```

Persistent PATH install:

```bash
uv tool install authorkit-cli --from git+https://github.com/mazemerize/author-kit.git
authorkit init . --ai copilot --script sh
authorkit init . --ai codex --script sh
authorkit init . --ai claude --script ps
```

Update an existing repo in-place:

```bash
authorkit init --here --force --ai codex --script sh
```

For Codex, set `CODEX_HOME` to `<repo>/.codex` after install.

### Agent tool checks

By default, `authorkit init` checks for required CLI tools for selected AI flavors:

- `claude` requires `claude` on PATH
- `codex` requires `codex` on PATH
- `copilot` does not require a dedicated binary for prompt installation

If you prefer to install prompts/files without tool checks, use `--ignore-agent-tools`:

```bash
authorkit init . --ai claude,copilot,codex --script sh --ignore-agent-tools
```

**Notes**:

- For Codex: PATH check and `CODEX_HOME` are different
  - PATH check validates the `codex` executable exists.
  - `CODEX_HOME` points Codex to the repo-local `.codex` folder after install.
- Choose `sh` (Bash) for MacOS and Linux or `ps` (PowerShell) for Windows.

### 2. Establish your writing principles

Define the voice, tone, and style rules for your book. This becomes the "style bible" that all chapters are written and reviewed against.

```bash
/authorkit.constitution First person POV, present tense, literary but accessible prose. Dark humor. Target audience: adult readers of literary fiction. No purple prose. Show don't tell for emotions.
```

### 3. Conceive the book

Describe your book idea. Focus on **what** the book is about and **why** it matters, not the chapter-by-chapter details.

```bash
/authorkit.conceive A mystery novel set in a crumbling Victorian observatory where an astronomer discovers that the star catalogue compiled by the previous director contains a hidden code. As she deciphers it, she realizes the observatory's history is entangled with a century-old disappearance.
```

This creates a `concept.md` with the premise, genre, themes, characters, voice, and scope.

### 4. Clarify the concept (optional)

Identify and resolve any ambiguities in the concept before outlining. Use the discuss command in clarify mode — it walks through structured questions and records answers directly into concept.md.

```bash
/authorkit.discuss clarify
/authorkit.discuss clarify the magic system's rules and limitations
```

### 5. Research grounding (optional, repeatable)

Run targeted research before outlining, during world-building, or while drafting chapters.

```bash
/authorkit.research Research Victorian observatory architecture for the outline
/authorkit.research For chapter 7, research forensic botany in damp basements
/authorkit.research Research maritime signaling systems in 1890 and sync durable findings to world notes (action:sync-world)
```

This writes a top-level `research.md` summary plus topic files in `research/` (flat by default for simple topics, nested when grouping is useful).
With `sync-world` enabled (for example via `action:sync-world`), grounded findings are also synced into `world/notes/` while preserving any existing note path.

### 6. Build the world (optional)

Establish the rules, geography, characters, history, and systems of your book's world before writing. Especially valuable for fantasy, sci-fi, and historical fiction, but works for any genre.

```bash
/authorkit.world.build magic system, political structure
```

You can run this multiple times to iteratively deepen specific areas. See [World Maintenance](#world-maintenance) for the full workflow.

### 6b. Discuss ideas (optional, repeatable)

Brainstorm world-building, character arcs, plot directions, or themes interactively before committing to an outline.

```bash
/authorkit.discuss the magic system and its limitations
/authorkit.discuss should the protagonist succeed or fail at the end?
/authorkit.discuss I'm not sure about the villain's motivation
```

This is a conversation — no files are created unless you say "save" or "note this". When you're ready, follow the suggested handoff to apply decisions via `/authorkit.world.build`, `/authorkit.outline`, etc.

### 7. Create the outline

Generate the book structure: chapter summaries, character arcs, thematic thread maps, and narrative arc. You can outline everything at once, or incrementally — part by part.

```bash
/authorkit.outline                 # Full outline (all chapters at once)
/authorkit.outline part 1          # Outline just Part 1
/authorkit.outline chapters 1-8    # Outline a specific range
/authorkit.outline extend          # Extend with the next section after drafting
```

Partial outlines include "Continuation Notes" that capture open threads, character positions, and thematic state — providing context when you return to extend the outline later.

This also generates `research.md` (world-building notes) and `characters.md` (character profiles), and uses existing `research/` topic files recursively if present.

### 8. Break into chapters

Convert the outline into a chapter-level task list with status tracking.

```bash
/authorkit.chapters
```

### 9. Write chapter by chapter

Each chapter goes through a plan → draft → review cycle:

```bash
/authorkit.chapter.plan 1     # Plan chapter 1 (scenes, beats, arc)
/authorkit.chapter.draft 1    # Write the actual prose
/authorkit.chapter.review 1   # Review against plan and constitution
```

For more collaborative writing, draft scene by scene:

```bash
/authorkit.chapter.draft 1 interactive   # Write one scene at a time with pauses for your input
/authorkit.chapter.draft 1 scene 3       # Write just scene 3 (you handle the others)
/authorkit.chapter.draft 1 continue      # Continue from where you (or the AI) left off
```

Or get targeted help on specific passages while you write:

```bash
/authorkit.chapter.help chapter 1 improve the opening paragraph
/authorkit.chapter.help chapter 3 alternatives for the dialogue between X and Y
/authorkit.chapter.help chapter 5 I'm stuck on the transition to the next scene
```

After drafting a chapter, run `/authorkit.world.sync` to extract new world details into the `world/` folder (see [World Maintenance](#world-maintenance)).

### 10. Analyze the full manuscript

After drafting several chapters (or all of them), run a cross-chapter analysis:

```bash
/authorkit.analyze
```

This checks for continuity errors, plot holes, pacing problems, unresolved threads, and constitution violations across all drafted chapters.

You can also run `/authorkit.world.sync verify` at any point to check the `world/` folder for internal consistency and alignment with the manuscript.

### 11. Revise as needed

Apply targeted fixes based on analysis findings:

```bash
/authorkit.revise Fix the timeline contradiction between chapters 3 and 7
```

### 12. Export your manuscript

Author Kit provides publishing commands directly in the installer CLI:

```bash
authorkit book build --format docx --format epub
authorkit book audio --merge
authorkit book stats --output json
```

Read me in [Book Export](#book-export-audiobook-and-statistics) below.

---

## The Full Workflow

The diagram below shows the complete Author Kit workflow, including the primary path and all the ways commands interconnect.
The key insight: **the workflow is sequential at its core, but every step has escape hatches for mid-process changes.**

```
  ┌─────────────────────────────────────────────────────────────┐
  │                       FOUNDATION PHASE                      │
  │                                                             │
  │   Constitution ──> Conceive ──────────────────────────────  │
  │                       │                                     │
  │                       ├──> Discuss (opt, repeatable)        │
  │                       │    (clarify concept or brainstorm)  │
  │                       │                                     │
  │                       ├──> Research (opt, repeatable)       │
  │                       │                                     │
  │                       └──> World Build (opt)                │
  │                                                             │
  └────────────────────────┬────────────────────────────────────┘
                           │
                           v
  ┌─────────────────────────────────────────────────────────────┐
  │              PLANNING PHASE (full or incremental)           │
  │                                                             │
  │   Outline (full) ──> Chapters (task breakdown)              │
  │         or                                                  │
  │   Outline (part 1) ──> Chapters ──> Draft ──> Outline       │
  │                                     (extend) ──> Chapters   │
  └────────────────────────┬────────────────────────────────────┘
                           │
                           v
  ┌─────────────────────────────────────────────────────────────┐
  │               CHAPTER ITERATION PHASE                       │
  │                                                             │
  │   For each chapter:                                         │
  │                                                             │
  │     ┌──────┐    ┌──────────────┐    ┌────────┐              │
  │     │ Plan │───>│    Draft     │───>│ Review │──> [X]       │
  │     └──────┘    │ (full, scene │    └────────┘              │
  │        ^        │  by scene,   │        │                   │
  │        │        │  or continue)│        │                   │
  │        │        └──────────────┘        │                   │
  │        └── [R] Needs revision ──────────┘                   │
  │                                                             │
  │   During drafting:  Chapter Help (targeted passage help)    │
  │   After each chapter:  World Sync                           │
  └────────────────────────┬────────────────────────────────────┘
                           │
                           v
  ┌─────────────────────────────────────────────────────────────┐
  │                  QUALITY PHASE                              │
  │                                                             │
  │   Analyze ──> Revise ──> Analyze (repeat until clean)       │
  │   (includes drift reconciliation as first phase)            │
  │                                                             │
  │   World Sync (verify) ──> World Build (fix) ──> World Sync  │
  └─────────────────────────────────────────────────────────────┘

  ╔═════════════════════════════════════════════════════════════╗
  ║             AVAILABLE AT ANY TIME (steps 5-12)              ║
  ║                                                             ║
  ║   Discuss ── Brainstorm ideas interactively                 ║
  ║   Amend ──── Change direction or facts across artifacts     ║
  ║   Research ─ Ground details from web/news/wikipedia/MCP     ║
  ║   Park ───── Defer a decision for later                     ║
  ║   Snapshot ─ Bookmark state before a risky change           ║
  ║   What-If ── Explore alternatives on a branch               ║
  ║   Reorder ── Move, split, merge, or insert chapters         ║
  ╚═════════════════════════════════════════════════════════════╝
```

---

## Available Commands

### Installer CLI Commands (`authorkit`)

| Command | Description | Inputs | Outputs |
|---------|-------------|--------|---------|
| `authorkit init` | Install/update Author Kit assets for selected AI(s) | Target dir, `--ai`, `--script` | `.authorkit/`, AI prompt folders, manifest |
| `authorkit check` | Check local tool availability | — | Tool status report (`git`, `claude`, `codex`, `copilot`, `pandoc`, `ffmpeg`) |
| `authorkit version` | Print CLI and Python versions | — | Version report |
| `authorkit book build` | Build manuscript outputs | Repeat `--format`, `--force` | `dist/manuscript.md` + rendered docs |
| `authorkit book audio` | Generate chapter audio and optional merged audiobook | `--voice`, `--model`, `--merge` | `dist/audio/*.mp3` (+ optional merged file) |
| `authorkit book stats` | Compute chapter/global manuscript metrics | `--output`, `--wpm` | Table/JSON/Markdown stats (includes per-chapter estimated audio minutes) |

### Core Workflow

| Command | Description | Inputs | Outputs |
|---------|-------------|--------|---------|
| `/authorkit.constitution` | Create or update writing principles (voice, tone, style guide) | Style description | `constitution.md` |
| `/authorkit.conceive` | Define book concept from a natural language description | Book idea | `concept.md`, `book.toml` |
| `/authorkit.research` | Ground a topic using available sources (web/news/wikipedia/MCP) and store reusable notes | Free-form topic/request + optional `scope:`, `sources:`, `action:`, `folder:` overrides | `research.md`, `research/**/*.md` (flat or nested), optional `world/notes/research-*.md` or `world/notes/research/*.md` |
| `/authorkit.discuss` | Brainstorm ideas interactively, or clarify the concept with structured Q&A | Topic to discuss, or "clarify" | Optional `notes/discuss-*.md`, or updated `concept.md` in clarify mode |
| `/authorkit.outline` | Create a full or partial book outline with chapter summaries and arcs. Supports incremental outlining | Optional scope (e.g., "part 1", "extend") | `outline.md`, `research.md`, `characters.md` |
| `/authorkit.chapters` | Generate chapter-level task breakdown from the outline (works with partial outlines) | — | `chapters.md` with status markers |

### Chapter-Level Commands

| Command | Description | Inputs | Outputs |
|---------|-------------|--------|---------|
| `/authorkit.chapter.plan [N]` | Plan a specific chapter in detail (scenes, beats, connections) | Chapter number | `chapters/NN/plan.md`, status → `[P]` |
| `/authorkit.chapter.draft [N]` | Write chapter prose — full chapter, scene by scene, or continue a partial draft | Chapter number + optional mode | `chapters/NN/draft.md`, status → `[D]` |
| `/authorkit.chapter.help [N]` | Get targeted writing help on a specific passage, scene, or paragraph | Chapter + passage description | Updated `draft.md` |
| `/authorkit.chapter.review [N]` | Review a drafted chapter against plan, concept, and constitution | Chapter number | `chapters/NN/review.md`, status → `[X]` or `[R]` |
| `/authorkit.chapter.reorder` | Reorder, split, merge, insert, or remove chapters | Operation description | Renumbered files, updated cross-references |

### World Maintenance

| Command | Description | Inputs | Outputs |
|---------|-------------|--------|---------|
| `/authorkit.world.build` | Build the book's world — establish rules, geography, characters, history, and systems | Optional focus areas | `world/` folder with entity files |
| `/authorkit.world.sync` | Extract, verify, and index world details — handles chapter extraction, consistency checks, and index rebuilding in one command | Chapter number(s), "verify", or "add-frontmatter" | Updated `world/` files, `world/_index.md`, verification report |

### Quality & Analysis

| Command | Description | Inputs | Outputs |
|---------|-------------|--------|---------|
| `/authorkit.analyze` | Cross-chapter consistency, quality analysis, and upstream drift reconciliation | Optional context | Analysis report with drift findings |
| `/authorkit.revise` | Apply revisions to specific chapters based on feedback | Chapter(s) and issues | Updated drafts, ripple effect report |

### Mid-Process Changes

| Command | Description | Inputs | Outputs |
|---------|-------------|--------|---------|
| `/authorkit.amend` | Change direction or retroactively change facts across all artifacts | Change description | Updated artifacts, amendment log |
| `/authorkit.park` | Defer a creative decision for later resolution without blocking | Question or "list" or "resolve" | `parked-decisions.md` |
| `/authorkit.snapshot` | Bookmark the current book state with narrative context | Description or "list" or "compare" | `snapshots/` file, git tag |
| `/authorkit.whatif` | Explore an alternative direction on an experimental branch | Hypothesis or "compare" or "merge" or "discard" | `whatif/*` git branch |

---

## Command Interactions

Understanding which commands feed into which helps you navigate the workflow efficiently. Here's how each command relates to the others.

### Foundation Phase (run once, in order)

```
constitution ──> conceive ──> discuss ──> research ──> world.build ──> outline ──> chapters
                    │          (clarify,   (opt)       (opt)            (full
                    │           brainstorm)                            or partial)
                    └── discuss (opt, repeatable) ─────────────────────────┘
```

- **Constitution** must exist before conceive (it sets the voice rules).
- **Conceive** initializes `book/` and creates/updates the concept. Everything else builds on this.
- **Discuss** is optional and repeatable. Use it to brainstorm world-building, character arcs, plot directions, or themes before committing to artifacts.
- **Discuss** (clarify mode) refines the concept. Use it before outlining if the concept has ambiguities. Regular discuss mode is for open-ended brainstorming.
- **Research** is optional and repeatable. Run it before outline, during world-building, or during chapter work to ground details.
- **World Build** is optional but recommended for genres with rich worlds. Can run before or after outline.
- **Outline** requires concept.md. Produces outline.md, research.md, characters.md. Can outline all chapters at once or incrementally (part by part). Consumes existing `research/` topic files recursively when available.
- **Chapters** requires outline.md. Produces the chapter task list. Works with partial outlines — run again after extending.

### Chapter Iteration (repeat per chapter)

```
chapter.plan N ──> chapter.draft N ──> chapter.review N
                   (full, scene by       │
                    scene, continue)      │
                        │           ┌─────┤
                   chapter.help N   v     v
                   (as needed)  [R] Rev  [X] Approved
                                re-draft  ──> world.sync N
                                ──> review    ──> next chapter
```

- **Plan** requires the outline and concept. Loads previous chapters for continuity.
- **Draft** requires the plan. Write the full chapter at once, or collaboratively: scene by scene, continue from where you left off, or target specific scenes. Follows the constitution as its style guide. Supports mixed authorship — you write some parts, the AI writes others.
- **Help** provides targeted assistance on specific passages during drafting — alternatives, improvements, continuations, dialogue polish, etc. Use it as needed without disrupting the plan-draft-review flow.
- **Review** grades the draft against plan, constitution, characters, and world/ files.
- **Research** can be run before planning or revising a chapter to ground domain-specific details.
- **PASS** → status becomes `[X]`. Run `world.sync` to capture new world details, then move to the next chapter.
- **NEEDS REVISION** → status becomes `[R]`. Re-plan with feedback, re-draft, re-review.

### Quality Phase (run after several chapters)

```
analyze ──> revise ──> chapter.review ──> analyze (repeat)
   │
   └──> world.sync (verify) ──> world.build (fix) ──> world.sync
```

- **Analyze** identifies issues across all drafted chapters and includes upstream drift reconciliation (checking outline, concept, chapters.md, and world/ for drift).
- **Revise** applies fixes. It may recommend re-reviewing affected chapters.
- **World Sync** (verify mode) checks world/ consistency.
- Run analyze → revise → analyze until critical issues reach zero.

### Mid-Process Commands (available anytime once `concept.md` exists)

These commands work alongside the main workflow. Here's when to reach for each one:

| Situation | Command | What It Does |
|-----------|---------|-------------|
| "I need grounded facts before I outline or draft this" | **Research** | Collects source-backed findings into `research.md` and `research/` topic files (flat or nested), with optional sync to `world/notes/` |
| "I want to change the ending" | **Amend** | Scans all artifacts, shows impact, propagates changes top-down |
| "Character X should have been a spy, not a soldier" | **Amend** | Finds every reference (direct, indirect, derivative), updates consistently |
| "I'm not sure if Marcus should die — I'll decide later" | **Park** | Records the decision with deadline, warns when deadline approaches |
| "I'm about to make a big change and want to be safe" | **Snapshot** | Creates a git tag + narrative bookmark of current state |
| "What if I tried first-person POV for the flashbacks?" | **What-If** | Creates an experimental branch, lets you try it, compare, merge or discard |
| "Chapters 5-7 should come before chapter 3" | **Reorder** | Moves files, renumbers everything, updates all cross-references |

#### How mid-process commands interact with each other

- **Snapshot** is often used *before* an **Amend** or **What-If** (as a safety net)
- **Amend** handles both direction changes and fact changes in a single command
- **Park** decisions often get resolved via **Amend** when the author decides
- **What-If** uses **Snapshot** automatically when creating a branch
- **Reorder** may trigger **Amend** if the structural change affects the narrative direction
- Amendment logs are stored in `pivots/` for a unified change history

#### How mid-process commands interact with core commands

- After an **Amend**: run `analyze` to verify consistency, `world.sync` to check world, re-`review` affected chapters
- **Park** checks deadlines when you run `chapter.plan` or `chapter.draft` — warns if you're approaching a parked decision's deadline
- **Park** decisions appear as findings in `analyze` reports if their deadlines have passed
- After **What-If** merge: run `analyze` to verify the merged content is consistent
- After **Reorder**: run `analyze` and `world.sync` to confirm renumbering didn't break references

---

## Chapter-Level Iteration

The core innovation of Author Kit is **chapter-level iteration**. Instead of writing the whole book and then revising, each chapter goes through its own cycle:

```
                    ┌─────────────────────────┐
                    │                         │
                    v                         │
  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
  │  Plan    │──│  Draft   │──│  Review  │───-┘ (if needs revision)
  │ chapter  │  │ chapter  │  │ chapter  │
  └──────────┘  └──────────┘  └──────────┘
                                  │
                                  │ (if passes)
                                  v
                            Next chapter
```

**Collaborative writing**: Instead of the AI drafting the full chapter, you can work together. Use `/authorkit.chapter.draft N interactive` to write scene by scene with pauses for your input, write parts yourself and use `/authorkit.chapter.draft N continue` to have the AI pick up where you left off, or use `/authorkit.chapter.help` for targeted assistance on specific passages. The AI matches your voice via the style anchor regardless of who wrote what.

Progress is tracked in `chapters.md` with status markers:

| Marker | Status | Meaning |
|--------|--------|---------|
| `[ ]` | Pending | Chapter not yet started |
| `[P]` | Planned | Chapter plan exists (`chapters/NN/plan.md`) |
| `[D]` | Drafted | First draft written (`chapters/NN/draft.md`) |
| `[R]` | Reviewed | Review completed, needs revision |
| `[X]` | Approved | Chapter passed review, ready for final manuscript |

For cross-model prose continuity, chapter workflows also maintain `book/style-anchor.md`, derived from the constitution plus the last two approved chapters when available.

Example `chapters.md`:

```markdown
## Part 1: The Observatory

- [X] CH01 [Part 1] The Arrival - Iria discovers the abandoned observatory
- [D] CH02 [Part 1] The Catalogue - She finds the star catalogue with odd annotations
- [P] CH03 [Part 1] The Pattern - First hint that the annotations form a code
- [ ] CH04 [Part 1] The Predecessor - Learning about the previous director

## Part 2: The Code

- [ ] CH05 [Part 2] The Cipher - Iria begins decryption
...
```

### Chapter restructuring

If you need to rearrange the chapter order, use `/authorkit.chapter.reorder`:

```bash
/authorkit.chapter.reorder Move CH05 to after CH02
/authorkit.chapter.reorder Split CH04 into two chapters at the scene break
/authorkit.chapter.reorder Merge CH06 and CH07 into a single chapter
/authorkit.chapter.reorder Insert a new chapter between CH03 and CH04
/authorkit.chapter.reorder Remove CH08
```

This handles all renumbering — file directories, chapters.md entries, outline references, world/ chapter tags, and cross-references in plans. Removed chapters are archived (never deleted).

---

## World Maintenance

Author Kit includes a dedicated world-building system that tracks every detail of your book's world — characters, places, organizations, history, and systems — across the entire manuscript.

### Why?

As your book grows, keeping track of world details becomes harder. Was the tavern called The Iron Flagon or The Iron Flask? Did Iria have green eyes in chapter 2 and blue eyes in chapter 9? World maintenance prevents these consistency problems by maintaining a structured `world/` folder alongside your chapters.

### The `world/` Folder

```
world/
├── _index.md           # Auto-generated entity index (Entity Registry, Alias Lookup, Chapter Manifest)
├── characters/         # One file per major character (identity, appearance, relationships, arc)
├── organizations/      # Factions, guilds, governments, companies
├── places/             # Locations with descriptions, significance, geography
├── history/            # Past events, backstory, timeline
├── systems/            # Magic systems, technology, social structures, frameworks
└── notes/              # Miscellaneous world notes
```

Only relevant categories are created — a contemporary novel won't need a `systems/` folder for magic.

### Workflow

**1. Build the world** (before or after outlining):

```bash
/authorkit.world.build                          # Comprehensive world-building
/authorkit.world.build magic system, geography  # Focus on specific areas
```

All entries from initial world-building are tagged `(CONCEPT)` to distinguish them from details that emerge during drafting.

**2. Ground details with research** (optional, anytime):

```bash
/authorkit.research Research late-19th-century maritime law for this setting
/authorkit.research For chapter 4, research telegraph relay timing with web and wikipedia sources
/authorkit.research Research Victorian shipboard medical protocols and sync durable facts to world notes (action:sync-world)
```

Default mode is suggest-only (`research.md` + topic files under `research/`).
Placement is adaptive: simple one-off topics stay flat, while grouped series can be placed in logical subfolders.
Use `sync-world` (for example `action:sync-world`) to write durable findings into `world/notes/` and rebuild `world/_index.md`.
When both flat and nested note layouts are possible, Author Kit updates existing note paths in place and avoids forced migration.

**3. Sync after drafting** (after each chapter):

```bash
/authorkit.world.sync 3         # Extract details from chapter 3
/authorkit.world.sync 1-5       # Scan a range of chapters
/authorkit.world.sync all       # Scan all drafted chapters
/authorkit.world.sync verify    # Verify-only mode (read-only diagnostic)
```

World sync handles everything in one command: extracts new details from chapters (tagged with source chapter, e.g., `(CH03)`), verifies internal consistency (reciprocal references, system coherence, timeline, chapter tag integrity), and rebuilds the `world/_index.md` entity index.

Issues are rated by severity (Critical, High, Medium, Low) with specific file paths and actionable recommendations.

### Evolution tags

world/ files track how details evolve across the manuscript:

| Tag | Meaning |
|-----|---------|
| `(CONCEPT)` | Established during pre-writing world-building |
| `(CHxx)` | First appeared or was confirmed in chapter xx |
| `(CHxx-rev)` | Updated when chapter xx was revised |
| `(AMEND-YYYY-MM-DD)` | Changed as part of a direction or fact amendment |

### Entity index

As a book's world grows, finding the right information becomes increasingly expensive — every world/-touching command would need to scan all files. Author Kit solves this with a **PowerShell-generated central index** at `world/_index.md`, which costs zero LLM tokens to maintain.

world/ entity files can include **YAML frontmatter** with structured metadata (recommended but optional — files without frontmatter are still readable by all commands):

```yaml
---
id: char-vadek-dellhar
type: character
name: Vadek D'Ellhar
aliases: [Vadek, Dr. Ellhar, the Doctor, Ellhar]
chapters: [CONCEPT, CH01, CH03, CH05]
first_appearance: CH01
relationships:
  - target: char-marcus-reid
    type: mentor-of
    since: CONCEPT
tags: [protagonist, magic-user]
last_updated: 2025-02-14
---
```

The index (`world/_index.md`) contains three lookup tables:

| Section | Purpose | Example Query |
|---------|---------|---------------|
| **Entity Registry** | All entities with their IDs, names, file paths, and chapter tags | "Where is Iria's file?" |
| **Alias Lookup** | Maps every name variant to its entity (flags ambiguous aliases) | "Who is 'the Doctor'?" |
| **Chapter Manifest** | Inverted index: which entities appear in which chapter | "What world/ files do I need for CH05?" |

**Rebuilding the index:**

```bash
/authorkit.world.sync                    # Full sync including index rebuild
/authorkit.world.sync add-frontmatter    # Add YAML frontmatter to files that lack it
```

The index is rebuilt automatically by `world.build`, `world.sync`, `amend`, and `chapter.reorder`. You only need to run `world.sync` manually if you've edited world/ files by hand.

---

## Mid-Process Changes

Books rarely go exactly according to plan. Author Kit provides structured tools for handling the most common mid-process situations.

### Changing direction or facts: Amend

When your vision for the book changes or a specific fact needs to change — use amend to propagate the change across all artifacts. It auto-classifies whether the change is a direction change, a fact change, or both.

```bash
/authorkit.amend Cut the romance subplot entirely
/authorkit.amend Change the ending so the protagonist fails
/authorkit.amend Transit from the harbor to the citadel takes 40 minutes -> Transit takes 75 minutes
/authorkit.amend Change Marcus from a soldier to a spy
```

Amend performs an **impact analysis** across concept, outline, chapters.md, world/ files, plans, and drafts. It shows you exactly what needs to change, in what order, and the risk level. You approve before any changes are made. For fact changes, it generates a **change manifest** showing every occurrence — direct references, indirect implications, and derivative details.

Changes are logged in `pivots/YYYY-MM-DD-[description].md` with `(AMEND-YYYY-MM-DD)` tags for traceability.

### Deferring decisions: Park

Not everything needs to be decided now. Park a decision to keep writing while tracking the uncertainty.

```bash
/authorkit.park How does the magic system handle time travel?
/authorkit.park Should Marcus die in Act 3?
/authorkit.park list                    # See all parked decisions
/authorkit.park resolve PD-003: Marcus lives
```

Parked decisions have **deadlines** (e.g., "must resolve before CH12"). When you plan or draft a chapter near a deadline, you'll be warned. Overdue decisions appear as findings in `/authorkit.analyze` reports.

### Safety nets: Snapshot

Before making a risky change, bookmark the current state with narrative context.

```bash
/authorkit.snapshot Before cutting the romance subplot
/authorkit.snapshot Decision point: Marcus lives or dies
/authorkit.snapshot list                    # See all snapshots
/authorkit.snapshot compare with pre-romance-cut
```

A snapshot creates a **git tag** (for the exact file state) and a **narrative file** (what's working, what's uncertain, what's being contemplated). The compare mode shows not just what files changed, but what's narratively different.

### Exploring alternatives: What-If

Try a direction without committing to it. What-If creates an experimental git branch where you can draft, revise, and restructure freely.

```bash
/authorkit.whatif What if Marcus dies in chapter 5?
/authorkit.whatif Try first person POV for the flashbacks

# ... make experimental changes using normal commands ...

/authorkit.whatif compare       # See narrative differences
/authorkit.whatif merge         # Keep the experiment
/authorkit.whatif discard       # Abandon and go back
```

What-If automatically creates a snapshot before branching. Only one experiment can be active at a time. The compare mode provides a **narrative summary**, not just a file diff — it tells you what's different about the story, not just which lines changed.

### Choosing the right tool

| You want to... | Use... |
|----------------|--------|
| Brainstorm ideas before committing | `/authorkit.discuss` |
| Get help on a specific passage while writing | `/authorkit.chapter.help` |
| Ground a topic with sources and keep reusable notes | `/authorkit.research` |
| Change the book's direction or a specific fact | `/authorkit.amend` |
| Decide something later | `/authorkit.park` |
| Save your current state before a big change | `/authorkit.snapshot` |
| Try something without committing | `/authorkit.whatif` |
| Move, split, or merge chapters | `/authorkit.chapter.reorder` |
| Check if outline/concept drifted from drafts | `/authorkit.analyze` |
| Fix issues found by review or analysis | `/authorkit.revise` |

## Book Export, Audiobook and Statistics

Author Kit provides publishing commands directly in the installer CLI to export your work:

```bash
authorkit book build --format docx  # Export as Word (docx) or ebook (epub)
authorkit book audio --merge        # Generate an audio file per chapter or a single, final one
authorkit book stats --output json  # Compute statistics about the current book
```

Defaults and behavior:
- Source manuscript: `book/chapters/*/draft.md`
- Output directory: `book/dist/` (audio in `dist/audio/`)
- `authorkit init` seeds repo `.gitignore` with `dist/` so generated artifacts are not committed
- Metadata source: `book/book.toml` (created by `setup-book` scripts)
- Python dependencies for book audio/stats (`openai`, `python-dotenv`, `mutagen`) are installed with `authorkit-cli`
- Built-in style assets:
  - DOCX fallback: `.authorkit/templates/publishing/reference.docx`
  - EPUB fallback: `.authorkit/templates/publishing/epub.css`
  - Audio narration instructions: `.authorkit/templates/publishing/audio-instructions.txt`

`book.toml` baseline (created automatically):

```toml
[book]
title = "..."
author = "..."
language = "en-US"
subtitle = ""

[build]
default_formats = ["docx"]
reference_docx = ".authorkit/templates/publishing/reference.docx"
epub_css = ".authorkit/templates/publishing/epub.css"

[audio]
provider = "openai"
model = "gpt-4o-mini-tts"
voice = "onyx"
instructions = ".authorkit/templates/publishing/audio-instructions.txt"
speaking_rate_wpm = 170

[stats]
reading_wpm = 200
tts_cost_per_1m_chars = 0.0
```

`authorkit book build` format options:
- Repeatable `--format` flag: `docx`, `epub`
- Example: `authorkit book build --format docx --format epub`
- If omitted, formats come from `[build].default_formats`
- If an output file already exists, `authorkit` prompts before overwrite
- Use `--force` to overwrite existing output files without prompts

`authorkit book audio` provider/auth and selection precedence:
- Current provider: OpenAI (`[audio].provider = "openai"`)
  - [Get started](https://developers.openai.com/api/docs) to create an openAI account, enable audio models, and get a key
- Required auth: `OPENAI_API_KEY` in environment or local `.env`
- Voice selection order: `--voice` CLI flag, then `[audio].voice`, then default `onyx`
  - You can explore optional voices using [openai.fm](https://github.com/openai/openai-fm)
- Model selection order: `--model` CLI flag, then `[audio].model`, then default `gpt-4o-mini-tts`
  - Read more about [OpenAI audio models](https://developers.openai.com/api/docs/guides/text-to-speech)
- Generated chapter files and merged audiobook output include ID3 metadata tags (title/album/artist/language and chapter tracking)
- OpenAI recommends `marin` or `cedar` voices for best quality; `onyx` remains the default

Audio narration instructions:
- A template file controls narrator style sent to the TTS model via the `instructions` parameter
- Default template: `.authorkit/templates/publishing/audio-instructions.txt`
- Override with a custom file: set `instructions` in `[audio]` to your own path (absolute, relative to `book/`, or relative to repo root)
- Instructions selection order: `[audio].instructions` config path, then default template, then built-in fallback
- The default template follows openai.fm-style guidance covering voice, punctuation, delivery, phrasing, tone, pauses, and markdown handling

---

## Project Structure

### Toolkit files

```text
.authorkit/
|-- memory/
|   `-- constitution.md
|-- prompts/                         # Canonical source for all authorkit prompts
|   `-- authorkit.*.md
|-- instructions/                    # Canonical instruction templates
|   |-- claude.md.tmpl
|   |-- copilot.md.tmpl
|   `-- codex.md.tmpl
|-- scripts/
|   |-- bash/                        # Linux/macOS shell automation
|   |   |-- common.sh
|   |   |-- setup-book.sh
|   |   |-- create-new-book.sh          # Deprecated shim to setup-book.sh
|   |   |-- setup-outline.sh
|   |   |-- check-prerequisites.sh
|   |   `-- build-world-index.sh
|   `-- powershell/                  # Windows/PowerShell automation
|       |-- common.ps1
|       |-- setup-book.ps1
|       |-- create-new-book.ps1         # Deprecated shim to setup-book.ps1
|       |-- setup-outline.ps1
|       |-- check-prerequisites.ps1
|       `-- build-world-index.ps1
|-- templates/
|   |-- concept-template.md
|   |-- outline-template.md
|   |-- research-index-template.md
|   |-- research-topic-template.md
|   |-- chapters-template.md
|   |-- chapter-plan-template.md
|   |-- agent-file-template.md
|   |-- publishing/
|   |   |-- reference.docx
|   |   `-- epub.css
|   `-- world-entity-frontmatter.md
`-- install-manifest.json            # Written by `authorkit init`

Generated by `authorkit init` (based on `--ai`):
- `.claude/commands/` + `CLAUDE.md`
- `.github/prompts/` + `.github/copilot-instructions.md`
- `.codex/prompts/` + `.codex/AGENTS.md`
```

### Book workspace files (`book/`)

Created when you run `/authorkit.conceive`:

```text
book/
|-- concept.md
|-- style-anchor.md
|-- outline.md
|-- research.md
|-- research/
|   |-- 20260217-victorian-observatory-architecture.md
|   `-- chapters/
|       `-- CH07/
|           `-- 20260218-forensic-botany-basements.md
|-- characters.md
|-- chapters.md
|-- book.toml
|-- parked-decisions.md
|-- pivots/
|-- snapshots/
|-- world/
|   |-- _index.md
|   |-- characters/
|   |-- organizations/
|   |-- places/
|   |-- history/
|   |-- systems/
|   `-- notes/
|       `-- research/
|           `-- victorian-signaling.md
`-- chapters/
    |-- 01/
    |   |-- plan.md
    |   |-- draft.md
    |   `-- review.md
    `-- ...
```

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `CODEX_HOME` | For Codex usage, set to `<repo>/.codex`. |
| `OPENAI_API_KEY` | Required for `authorkit book audio` when using OpenAI TTS provider. |

---

## Troubleshooting Book CLI

### `authorkit book build` fails with Pandoc errors

- Symptom: missing binary or conversion failure mentioning `pandoc`.
- Cause: Pandoc is not installed or not on PATH.
- Fix:
  - Windows: `winget install --id JohnMacFarlane.Pandoc -e`
  - macOS: `brew install pandoc`
  - Ubuntu/Debian: `sudo apt-get install pandoc`
- After install, close and reopen your terminal so PATH is refreshed.
- Verify: `authorkit check` should show `pandoc: ok`.

### `authorkit book audio` fails with FFmpeg errors

- Symptom: concat/merge errors mentioning `ffmpeg`.
- Cause: FFmpeg is missing from PATH.
- Fix:
  - Windows: `winget install --id Gyan.FFmpeg -e`
  - macOS: `brew install ffmpeg`
  - Ubuntu/Debian: `sudo apt-get install ffmpeg`
- After install, close and reopen your terminal so PATH is refreshed.
- Verify: `authorkit check` should show `ffmpeg: ok`.

### `authorkit book audio` fails with authentication errors

- Symptom: error about missing API key or failed OpenAI auth.
- Cause: `OPENAI_API_KEY` is not set (or invalid/expired).
- Fix:
  - Set env var for current shell/session, or
  - Store it in a local `.env` file (do not commit).
- Verify in shell:
  - PowerShell: `echo $env:OPENAI_API_KEY`
  - bash/zsh: `echo $OPENAI_API_KEY`

### Audio voice/model are not what you expect

- Selection precedence:
  1. CLI flags: `--voice`, `--model`
  2. `book/book.toml` (`[audio].voice`, `[audio].model`)
  3. Defaults: `voice = "onyx"`, `model = "gpt-4o-mini-tts"`

### Existing audio files are not overwritten

- Default behavior is interactive prompt per existing chapter file.
- Use `--force` to bypass prompt logic.
- Use `--yes` for non-interactive acceptance (CI-friendly).

### Audio metadata tags are missing

- New audio runs write ID3 metadata automatically.
- If older files were created before metadata support, rerun `authorkit book audio` for those chapters.

### Audio delivery sounds flat or unnatural

- Verify the selected voice/model and try regenerating with `--force`.
- Customize the narration instructions template at `.authorkit/templates/publishing/audio-instructions.txt` or provide your own via `[audio].instructions` in `book.toml`.
- OpenAI recommends `marin` or `cedar` voices for best quality.

---

## Editor(s) in Chief

- Mathieu Demarne (`@mdemarne`)

---

## Acknowledgement

The structure of this kit is in part inspired by [spec-kit](https://github.com/github/spec-kit), with a twist for book and novel development.

---

## Support

Need help? Open a [GitHub issue](https://github.com/mazemerize/author-kit/issues). Bug reports, odd behaviors, feature ideas, and questions about using Author Kit are all welcome.

---

## Beyond the Code Editor: The Future of Author Kit

Interested in seeing the capacity from Author Kit as a full-fledged book editor experience that does not require being tech-savvy in code editors and AIs? [Contact us](mailto:mazemerize@outlook.com), we would like to hear from you.
