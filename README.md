![Author Kit Logo](./media/logo.png)

**Write books with structured AI assistance. Chapter by chapter. Draft by draft.**

An open-source toolkit that brings structured, template-driven principles to book writing. Instead of vibe-writing an entire manuscript, Author Kit guides you through a structured workflow: define your concept, outline the structure, then iteratively plan, draft, and review each chapter — with full support for changing direction mid-process.

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
6. **Mid-process flexibility** — Pivot, defer decisions, explore alternatives, and restructure without losing work

This works for **any genre**: literary fiction, thrillers, non-fiction guides, memoirs, technical books, and everything in between.

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

Important for Codex: PATH check and `CODEX_HOME` are different.
- PATH check validates the `codex` executable exists.
- `CODEX_HOME` points Codex to the repo-local `.codex` folder after install.

### 1.1 Book Build/Audio/Stats CLI

Author Kit now provides publishing commands directly in the installer CLI:

```bash
authorkit book build --format docx --format epub
authorkit book audio --merge
authorkit book stats --output json
```

Defaults and behavior:
- Source manuscript: `books/<active-book>/chapters/*/draft.md`
- Output directory: `books/<active-book>/dist/` (audio in `dist/audio/`)
- Metadata source: `books/<active-book>/book.toml` (created by `create-new-book` scripts)
- Built-in style assets:
  - DOCX fallback: `.authorkit/templates/publishing/reference.docx`
  - EPUB fallback: `.authorkit/templates/publishing/epub.css`

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
speaking_rate_wpm = 170

[stats]
reading_wpm = 200
tts_cost_per_1m_chars = 0.0
```

`authorkit book build` format options:
- Repeatable `--format` flag: `docx`, `pdf`, `epub`
- Example: `authorkit book build --format docx --format epub`
- If omitted, formats come from `[build].default_formats`

`authorkit book audio` provider/auth and selection precedence:
- Current provider: OpenAI (`[audio].provider = "openai"`)
- Required auth: `OPENAI_API_KEY` in environment or local `.env`
- Voice selection order: `--voice` CLI flag, then `[audio].voice`, then default `onyx`
- Model selection order: `--model` CLI flag, then `[audio].model`, then default `gpt-4o-mini-tts`

Audio marker behavior (internal speech shaping):
- Markers used: `[DIALOG]` and `[PAUSE]`
- Dialogue-like lines are prefixed with `[DIALOG]`
- Epigraph attribution lines and chapter transitions inject `[PAUSE]`
- Marker-aware instructions are sent to TTS so markers are not read aloud and delivery is adjusted

Future provider support:
- The marker pipeline is provider-agnostic; other TTS providers can map markers to instruction text or SSML equivalents.
- This preserves narration behavior while changing only provider integration/auth.

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

The fastest way is the automated chapter command — it runs the full plan → draft → review cycle for you, looping on draft → review until the chapter passes:

```
/authorkit.chapter          # Auto-detect the next chapter and run the full lifecycle
/authorkit.chapter 3        # Run the full lifecycle for chapter 3 specifically
```

This handles everything: plans the chapter, writes the prose, reviews it, and if the review finds issues, re-drafts and re-reviews (up to 3 cycles). It picks up from wherever the chapter left off — if you already have a plan, it skips to drafting.

Or run each step individually for more control:

```
/authorkit.chapter.plan 1     # Plan chapter 1 (scenes, beats, arc)
/authorkit.chapter.draft 1    # Write the actual prose
/authorkit.chapter.review 1   # Review against plan and constitution
```

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

## The Full Workflow

The diagram below shows the complete Author Kit workflow, including the primary path and all the ways commands interconnect. The key insight: **the workflow is sequential at its core, but every step has escape hatches for mid-process changes.**

```
  ┌─────────────────────────────────────────────────────────────┐
  │                    FOUNDATION PHASE                         │
  │                                                             │
  │   Constitution ──> Conceive ──> Clarify (opt) ──> World     │
  │                                                 Build (opt) │
  └────────────────────────┬────────────────────────────────────┘
                           │
                           v
  ┌─────────────────────────────────────────────────────────────┐
  │                    PLANNING PHASE                           │
  │                                                             │
  │           Outline ──> Chapters (task breakdown)             │
  └────────────────────────┬────────────────────────────────────┘
                           │
                           v
  ┌─────────────────────────────────────────────────────────────┐
  │               CHAPTER ITERATION PHASE                       │
  │                                                             │
  │   For each chapter:                                         │
  │                                                             │
  │     ┌──────┐    ┌──────┐    ┌────────┐                      │
  │     │ Plan │───>│Draft │───>│ Review │──> [X] Approved      │
  │     └──────┘    └──────┘    └────────┘                      │
  │        ^                        │                           │
  │        └── [R] Needs revision ──┘                           │
  │                                                             │
  │   After each chapter:  World Update ──> World Verify        │
  └────────────────────────┬────────────────────────────────────┘
                           │
                           v
  ┌─────────────────────────────────────────────────────────────┐
  │                  QUALITY PHASE                              │
  │                                                             │
  │   Analyze ──> Revise ──> Analyze (repeat until clean)       │
  │                                                             │
  │   Reconcile ──> Fix drift ──> Reconcile                     │
  │                                                             │
  │   World Verify ──> World Build (fix) ──> World Verify       │
  │                                                             │
  │   Checklist ──> Manual review                               │
  └─────────────────────────────────────────────────────────────┘

  ╔═════════════════════════════════════════════════════════════╗
  ║             AVAILABLE AT ANY TIME (steps 5-12)              ║
  ║                                                             ║
  ║   Pivot ─── Change direction across all artifacts           ║
  ║   Retcon ── Change an established fact everywhere           ║
  ║   Park ──── Defer a decision for later                      ║
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
| `authorkit book build` | Build manuscript outputs | Optional `--book`, repeat `--format`, `--force` | `dist/manuscript.md` + rendered docs |
| `authorkit book audio` | Generate chapter audio and optional merged audiobook | Optional `--book`, `--voice`, `--model`, `--merge` | `dist/audio/*.mp3` (+ optional merged file) |
| `authorkit book stats` | Compute chapter/global manuscript metrics | Optional `--book`, `--output`, `--wpm` | Table/JSON/Markdown stats |

### Core Workflow

| Command | Description | Inputs | Outputs |
|---------|-------------|--------|---------|
| `/authorkit.constitution` | Create or update writing principles (voice, tone, style guide) | Style description | `constitution.md` |
| `/authorkit.conceive` | Define book concept from a natural language description | Book idea | `concept.md`, git branch, `checklists/concept-quality.md` |
| `/authorkit.clarify` | Resolve ambiguities in the book concept | Optional focus areas | Updated `concept.md` with clarifications |
| `/authorkit.outline` | Create the full book outline with chapter summaries and arcs | — | `outline.md`, `research.md`, `characters.md` |
| `/authorkit.chapters` | Generate chapter-level task breakdown from the outline | — | `chapters.md` with status markers |

### Chapter-Level Commands

| Command | Description | Inputs | Outputs |
|---------|-------------|--------|---------|
| `/authorkit.chapter` | **Automated** — run the full plan → draft → review cycle, looping until approved | Optional chapter number | `plan.md`, `draft.md`, `review.md`, status → `[X]` |
| `/authorkit.chapter.plan [N]` | Plan a specific chapter in detail (scenes, beats, connections) | Chapter number | `chapters/NN/plan.md`, status → `[P]` |
| `/authorkit.chapter.draft [N]` | Write the actual chapter prose | Chapter number | `chapters/NN/draft.md`, status → `[D]` |
| `/authorkit.chapter.review [N]` | Review a drafted chapter against plan, concept, and constitution | Chapter number | `chapters/NN/review.md`, status → `[X]` or `[R]` |
| `/authorkit.chapter.reorder` | Reorder, split, merge, insert, or remove chapters | Operation description | Renumbered files, updated cross-references |

### World Maintenance

| Command | Description | Inputs | Outputs |
|---------|-------------|--------|---------|
| `/authorkit.world.build` | Build the book's world — establish rules, geography, characters, history, and systems | Optional focus areas | `World/` folder with entity files |
| `/authorkit.world.update [N]` | Extract world-building details from drafted chapters into the `World/` folder | Chapter number(s) | Updated `World/` files, impact report |
| `/authorkit.world.verify` | Verify `World/` files for internal consistency and manuscript alignment | Optional scope | Verification report (read-only) |
| `/authorkit.world.index` | Build or rebuild the `World/_index.md` entity index for fast lookups | Optional: `add-frontmatter` | `World/_index.md`, stats |

### Quality & Analysis

| Command | Description | Inputs | Outputs |
|---------|-------------|--------|---------|
| `/authorkit.analyze` | Cross-chapter consistency and quality analysis (read-only) | Optional context | Analysis report |
| `/authorkit.reconcile` | Check outline, concept, chapters.md, and World/ for drift against drafted chapters | Optional scope | Drift report, optional fixes |
| `/authorkit.revise` | Apply revisions to specific chapters based on feedback | Chapter(s) and issues | Updated drafts, ripple effect report |
| `/authorkit.checklist` | Generate custom quality checklists (craft, continuity, pacing, etc.) | Checklist type | `checklists/[type].md` |

### Mid-Process Changes

| Command | Description | Inputs | Outputs |
|---------|-------------|--------|---------|
| `/authorkit.pivot` | Propagate a direction change across all artifacts with impact analysis | Change description | Updated artifacts, pivot log |
| `/authorkit.retcon` | Retroactively change an established fact across the entire manuscript | Old fact → new fact | Change manifest, updated files, retcon log |
| `/authorkit.park` | Defer a creative decision for later resolution without blocking | Question or "list" or "resolve" | `parked-decisions.md` |
| `/authorkit.snapshot` | Bookmark the current book state with narrative context | Description or "list" or "compare" | `snapshots/` file, git tag |
| `/authorkit.whatif` | Explore an alternative direction on an experimental branch | Hypothesis or "compare" or "merge" or "discard" | `whatif/*` git branch |

---

## Command Interactions

Understanding which commands feed into which helps you navigate the workflow efficiently. Here's how each command relates to the others.

### Foundation Phase (run once, in order)

```
constitution ──> conceive ──> clarify ──> world.build ──> outline ──> chapters
                                (opt)      (opt)
```

- **Constitution** must exist before conceive (it sets the voice rules).
- **Conceive** creates the concept and git branch. Everything else builds on this.
- **Clarify** refines the concept. Run it before outlining if the concept has ambiguities.
- **World Build** is optional but recommended for genres with rich worlds. Can run before or after outline.
- **Outline** requires concept.md. Produces outline.md, research.md, characters.md.
- **Chapters** requires outline.md. Produces the chapter task list.

### Chapter Iteration (repeat per chapter)

Use `/authorkit.chapter` to auto-detect the next step, or run each command individually:

```
chapter.plan N ──> chapter.draft N ──> chapter.review N
                                            │
                           ┌────────────────┤
                           v                v
                     [R] Revise        [X] Approved
                     re-plan/draft     ──> world.update N
                     ──> re-review         ──> next chapter
```

- **Plan** requires the outline and concept. Loads previous chapters for continuity.
- **Draft** requires the plan. Follows the constitution as its style guide.
- **Review** grades the draft against plan, constitution, characters, and World/ files.
  - **PASS** → status becomes `[X]`. Run `world.update` to capture new world details, then move to the next chapter.
  - **NEEDS REVISION** → status becomes `[R]`. Re-plan with feedback, re-draft, re-review.

### Quality Phase (run after several chapters)

```
analyze ──> revise ──> chapter.review ──> analyze (repeat)
   │
   ├──> world.verify ──> world.build (fix) ──> world.verify
   │
   └──> reconcile ──> fix drift ──> reconcile (repeat)
```

- **Analyze** is read-only. It identifies issues across all drafted chapters.
- **Reconcile** is read-first. It checks upstream documents (outline, concept, chapters.md, World/) for drift against drafted chapters, then optionally fixes stale entries.
- **Revise** applies fixes. It may recommend re-reviewing affected chapters.
- **World Verify** is read-only. It checks World/ consistency.
- Run analyze → revise → analyze until critical issues reach zero.

### Mid-Process Commands (available anytime after outlining)

These commands work alongside the main workflow. Here's when to reach for each one:

| Situation | Command | What It Does |
|-----------|---------|-------------|
| "I want to change the ending" | **Pivot** | Scans all artifacts, shows impact, propagates changes top-down |
| "Character X should have been a spy, not a soldier" | **Retcon** | Finds every reference (direct, indirect, derivative), updates consistently |
| "I'm not sure if Marcus should die — I'll decide later" | **Park** | Records the decision with deadline, warns when deadline approaches |
| "I'm about to make a big change and want to be safe" | **Snapshot** | Creates a git tag + narrative bookmark of current state |
| "What if I tried first-person POV for the flashbacks?" | **What-If** | Creates an experimental branch, lets you try it, compare, merge or discard |
| "Chapters 5-7 should come before chapter 3" | **Reorder** | Moves files, renumbers everything, updates all cross-references |

#### How mid-process commands interact with each other

- **Snapshot** is often used *before* a **Pivot** or **What-If** (as a safety net)
- **Pivot** may recommend **Retcon** for specific fact changes within the broader direction change
- **Park** decisions often get resolved via **Pivot** when the author decides
- **What-If** uses **Snapshot** automatically when creating a branch
- **Reorder** may trigger **Pivot** if the structural change affects the narrative direction
- **Retcon** logs are stored in `pivots/` alongside pivot logs for a unified change history

#### How mid-process commands interact with core commands

- After a **Pivot**: run `analyze` to verify consistency, `world.verify` to check world, re-`review` affected chapters
- After a **Retcon**: re-`review` chapters with significant prose changes, run `world.verify`
- **Park** checks deadlines when you run `chapter.plan` or `chapter.draft` — warns if you're approaching a parked decision's deadline
- **Park** decisions appear as findings in `analyze` reports if their deadlines have passed
- After **What-If** merge: run `analyze` to verify the merged content is consistent
- After **Reorder**: run `analyze` and `world.verify` to confirm renumbering didn't break references

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

### Chapter restructuring

If you need to rearrange the chapter order, use `/authorkit.chapter.reorder`:

```
/authorkit.chapter.reorder Move CH05 to after CH02
/authorkit.chapter.reorder Split CH04 into two chapters at the scene break
/authorkit.chapter.reorder Merge CH06 and CH07 into a single chapter
/authorkit.chapter.reorder Insert a new chapter between CH03 and CH04
/authorkit.chapter.reorder Remove CH08
```

This handles all renumbering — file directories, chapters.md entries, outline references, World/ chapter tags, and cross-references in plans. Removed chapters are archived (never deleted).

---

## World Maintenance

Author Kit includes a dedicated world-building system that tracks every detail of your book's world — characters, places, organizations, history, and systems — across the entire manuscript.

### Why?

As your book grows, keeping track of world details becomes harder. Was the tavern called The Iron Flagon or The Iron Flask? Did Elena have green eyes in chapter 2 and blue eyes in chapter 9? World maintenance prevents these consistency problems by maintaining a structured `World/` folder alongside your chapters.

### The World/ Folder

```
World/
├── _index.md           # Auto-generated entity index (Entity Registry, Alias Lookup, Chapter Manifest)
├── Characters/         # One file per major character (identity, appearance, relationships, arc)
├── Organizations/      # Factions, guilds, governments, companies
├── Places/             # Locations with descriptions, significance, geography
├── History/            # Past events, backstory, timeline
├── Systems/            # Magic systems, technology, social structures, frameworks
└── Notes/              # Miscellaneous world notes
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

### Evolution tags

World/ files track how details evolve across the manuscript:

| Tag | Meaning |
|-----|---------|
| `(CONCEPT)` | Established during pre-writing world-building |
| `(CHxx)` | First appeared or was confirmed in chapter xx |
| `(CHxx-rev)` | Updated when chapter xx was revised |
| `(PIVOT-YYYY-MM-DD)` | Changed as part of a direction pivot |
| `(RETCON-YYYY-MM-DD)` | Changed as part of a retroactive fact change |

### Entity index

As a book's world grows, finding the right information becomes increasingly expensive — every World/-touching command would need to scan all files. Author Kit solves this with a **PowerShell-generated central index** at `World/_index.md`, which costs zero LLM tokens to maintain.

Every World/ entity file includes **YAML frontmatter** with structured metadata:

```yaml
---
id: char-elena-voss
type: character
name: Elena Voss
aliases: [Elena, Dr. Voss, the Doctor, Voss]
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

The index (`World/_index.md`) contains three lookup tables:

| Section | Purpose | Example Query |
|---------|---------|---------------|
| **Entity Registry** | All entities with their IDs, names, file paths, and chapter tags | "Where is Elena's file?" |
| **Alias Lookup** | Maps every name variant to its entity (flags ambiguous aliases) | "Who is 'the Doctor'?" |
| **Chapter Manifest** | Inverted index: which entities appear in which chapter | "What World/ files do I need for CH05?" |

**Rebuilding the index:**

```
/authorkit.world.index                  # Full rebuild
/authorkit.world.index add-frontmatter  # Add YAML frontmatter to files that lack it
```

The index is rebuilt automatically by `world.build`, `world.update`, `retcon`, `pivot`, and `chapter.reorder`. You only need to run `world.index` manually if you've edited World/ files by hand.

---

## Mid-Process Changes

Books rarely go exactly according to plan. Author Kit provides structured tools for handling the most common mid-process situations.

### Changing direction: Pivot

When your vision for the book changes — a character needs cutting, a subplot should be added, the ending should be different — use pivot to propagate the change across all artifacts.

```
/authorkit.pivot Cut the romance subplot entirely
/authorkit.pivot Merge characters Marcus and David into a single character
/authorkit.pivot Change the ending so the protagonist fails
```

Pivot performs an **impact analysis** across concept, outline, chapters.md, World/ files, plans, and drafts. It shows you exactly what needs to change, in what order, and the risk level. You approve before any changes are made.

Changes are logged in `pivots/YYYY-MM-DD-[description].md` for traceability.

### Changing established facts: Retcon

When a specific fact needs to change retroactively — a character's age, a place's name, a world rule — retcon finds every reference (direct mentions, indirect implications, and logical consequences) and updates them consistently.

```
/authorkit.retcon Elena was 42 -> Elena is 38
/authorkit.retcon Change Marcus from a soldier to a spy
/authorkit.retcon The magic system costs blood -> The magic system costs memories
```

Retcon generates a **change manifest** showing every occurrence before making changes. It distinguishes between direct references ("she was forty-two"), indirect references ("her two decades of service"), and derivative details ("her commanding officer"). You review and approve the manifest.

### Deferring decisions: Park

Not everything needs to be decided now. Park a decision to keep writing while tracking the uncertainty.

```
/authorkit.park How does the magic system handle time travel?
/authorkit.park Should Marcus die in Act 3?
/authorkit.park list                    # See all parked decisions
/authorkit.park resolve PD-003: Marcus lives
```

Parked decisions have **deadlines** (e.g., "must resolve before CH12"). When you plan or draft a chapter near a deadline, you'll be warned. Overdue decisions appear as findings in `/authorkit.analyze` reports.

### Safety nets: Snapshot

Before making a risky change, bookmark the current state with narrative context.

```
/authorkit.snapshot Before cutting the romance subplot
/authorkit.snapshot Decision point: Marcus lives or dies
/authorkit.snapshot list                    # See all snapshots
/authorkit.snapshot compare with pre-romance-cut
```

A snapshot creates a **git tag** (for the exact file state) and a **narrative file** (what's working, what's uncertain, what's being contemplated). The compare mode shows not just what files changed, but what's narratively different.

### Exploring alternatives: What-If

Try a direction without committing to it. What-If creates an experimental git branch where you can draft, revise, and restructure freely.

```
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
| Change the book's direction | `/authorkit.pivot` |
| Change a specific fact everywhere | `/authorkit.retcon` |
| Decide something later | `/authorkit.park` |
| Save your current state before a big change | `/authorkit.snapshot` |
| Try something without committing | `/authorkit.whatif` |
| Move, split, or merge chapters | `/authorkit.chapter.reorder` |
| Check if outline/concept drifted from drafts | `/authorkit.reconcile` |
| Fix issues found by review or analysis | `/authorkit.revise` |

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
|   |   |-- create-new-book.sh
|   |   |-- setup-outline.sh
|   |   |-- check-prerequisites.sh
|   |   `-- build-world-index.sh
|   `-- powershell/                  # Windows/PowerShell automation
|       |-- common.ps1
|       |-- create-new-book.ps1
|       |-- setup-outline.ps1
|       |-- check-prerequisites.ps1
|       `-- build-world-index.ps1
|-- templates/
|   |-- concept-template.md
|   |-- outline-template.md
|   |-- chapters-template.md
|   |-- chapter-plan-template.md
|   |-- checklist-template.md
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

### Book output files (`books/`)

Created when you run `/authorkit.conceive`:

```text
books/
`-- 001-victorian-mystery/
    |-- concept.md
    |-- outline.md
    |-- research.md
    |-- characters.md
    |-- chapters.md
    |-- parked-decisions.md
    |-- checklists/
    |-- pivots/
    |-- snapshots/
    |-- World/
    |   |-- _index.md
    |   |-- Characters/
    |   |-- Organizations/
    |   |-- Places/
    |   |-- History/
    |   |-- Systems/
    |   `-- Notes/
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
| `AUTHORKIT_BOOK` | Override book detection for non-Git repositories. |
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
- Verify: `authorkit check` should show `pandoc: ok`.

### `authorkit book audio` fails with FFmpeg errors

- Symptom: concat/merge errors mentioning `ffmpeg`.
- Cause: FFmpeg is missing from PATH.
- Fix:
  - Windows: `winget install --id Gyan.FFmpeg -e`
  - macOS: `brew install ffmpeg`
  - Ubuntu/Debian: `sudo apt-get install ffmpeg`
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
  2. `books/<book>/book.toml` (`[audio].voice`, `[audio].model`)
  3. Defaults: `voice = "onyx"`, `model = "gpt-4o-mini-tts"`

### Existing audio files are not overwritten

- Default behavior is interactive prompt per existing chapter file.
- Use `--force` to bypass prompt logic.
- Use `--yes` for non-interactive acceptance (CI-friendly).

### Marker behavior seems absent

- Marker shaping (`[DIALOG]`, `[PAUSE]`) is internal and instruction-driven.
- Markers are not intended to appear in final spoken output.
- If delivery sounds flat, verify the selected voice/model and try regenerating with `--force`.

---

## Editor(s) in Chief

- Mathieu Demarne (`@mdemarne`)

---

## Acknowledgement

The structure of this kit is in part inspired by [spec-kit](https://github.com/github/spec-kit), with a twist for book and novel development.

---

## Support

Need help? Open a [GitHub issue](https://github.com/mazemerize/author-kit/issues). Bug reports, odd behaviors, feature ideas, and questions about using Author kit are all welcome.

---

## Beyond the Code Editor: The Future of Author Kit

Interested in seeing the capacity from Author Kit as a full-fledge book editor experience that does not require being tech-savvy in code editors and AIs? [Contact us](mailto:mazemerize@outlook.com), we would like to hear from you.
