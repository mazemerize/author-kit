![Author Kit Logo](./media/logo.png)

**Write books with structured AI assistance. Chapter by chapter. Draft by draft. Together.**

An open-source toolkit that brings structured, template-driven principles to book writing. Instead of vibe-writing an entire manuscript, Author Kit guides you through a structured workflow: define your concept, outline the structure, then iteratively plan, draft, and review each chapter — with full support for changing direction mid-process. Outline incrementally as you discover your story, brainstorm interactively, and co-write chapters scene by scene.

---

## Table of Contents

- [What is Author Kit?](#what-is-author-kit)
- [Get Started](#get-started)
- [The Four Commands](#the-four-commands)
- [World Maintenance](#world-maintenance)
- [Book Export, Audiobook and Statistics](#book-export-audiobook-and-statistics)
- [Project Structure](#project-structure)
- [Environment Variables](#environment-variables)
- [Troubleshooting Book CLI](#troubleshooting-book-cli)

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

**Read our articles on Medium**:
- [Why AI Writes the Same Book Every Time](https://medium.com/@mdemarne/why-ai-writes-the-same-book-every-time-0b02323f618a)
- [The World Your AI Forgot to Build](https://medium.com/@mdemarne/the-world-your-ai-forgot-to-build-c7fda0fe71c7)
- [Catching What Drifts in Your Human-Led, AI-Assisted Manuscript](https://medium.com/@mdemarne/catching-what-drifts-in-your-human-led-ai-assisted-manuscript-4d4fb7334a24)
- [Writing with AI: What Works, What Doesn't, and What's Left](https://medium.com/@mdemarne/writing-with-ai-what-works-what-doesnt-and-what-s-left-72d53d95a6da)

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

> **Where to run what:** Commands beginning with `/` (e.g. `/authorkit.discuss`) are typed inside your AI agent's chat — Claude Code, Copilot, or Codex. Commands beginning with `authorkit` (no slash) run in your terminal at the project root.

### 2. Start with a conversation

`/authorkit.discuss` is the entry point for everything that isn't pure manuscript writing. On a fresh repo, it brainstorms with you and produces `concept.md` (premise, audience, voice, themes, scope) plus the `book/` workspace. On an existing repo, it clarifies ambiguities, propagates cross-cutting changes, restructures chapters, updates the constitution, and more — always read-only by default, every write proposed and confirmed first.

```bash
/authorkit.discuss A mystery novel set in a crumbling Victorian observatory where an astronomer discovers that the star catalogue compiled by the previous director contains a hidden code.
```

You can also use it to talk through specific things later:

```bash
/authorkit.discuss the magic system feels vague
/authorkit.discuss should the protagonist succeed or fail at the end?
/authorkit.discuss change Marcus from a soldier to a spy across the manuscript
/authorkit.discuss move CH05 to after CH02
/authorkit.discuss try first person POV for the flashbacks
/authorkit.discuss tighten the voice rules to favor short sentences
/authorkit.discuss park: should the villain survive the third act?
```

The model auto-detects what mode of conversation you're having — brainstorming, clarifying, amending, restructuring, what-if-ing, updating the constitution, parking a decision — and routes any decision you approve to the right file (concept, world entry, outline, characters, parked decisions, etc.). For large changes it presents an impact plan and an auto-snapshot before propagating.

### 3. Write chapters

`/authorkit.write` is the manuscript-generation command. It generates the outline and chapter list if they don't exist yet, plans the requested chapter, drafts it, and reconciles state afterwards — extracting any new world details into `world/`, refreshing the outline summary so it matches the drafted prose, updating `chapters.md` status, and rebuilding the `world/_index.md`.

```bash
/authorkit.write                # Plan + draft the next pending chapter
/authorkit.write 1              # Plan + draft chapter 1
/authorkit.write 7 interactive  # Plan, then write one scene at a time with pauses
/authorkit.write 3 scene 2      # Write just scene 2 of chapter 3
/authorkit.write 5 continue     # Continue chapter 5 from where the draft ends
/authorkit.write 4 from scene 3 # Write from scene 3 through the end
/authorkit.write 8 revise: fix the timeline contradiction with chapter 5
/authorkit.write 6 help improve the opening paragraph
/authorkit.write 6 help I'm stuck on the transition to the next scene
/authorkit.write outline part 1 # Build the structural outline for part 1 only
/authorkit.write outline extend # Extend a partial outline with the next section
```

Progress is tracked in `chapters.md` with status markers:

| Marker | Status | Meaning |
|--------|--------|---------|
| `[ ]` | Pending | Chapter not yet started |
| `[P]` | Planned | Chapter plan exists (`chapters/NN/plan.md`) |
| `[D]` | Drafted | First draft written (`chapters/NN/draft.md`) |
| `[R]` | Reviewed | Review completed, needs revision |
| `[X]` | Approved | Chapter passed review, ready for final manuscript |

For cross-model prose continuity, `/authorkit.write` also maintains `book/style-anchor.md`, derived from the constitution plus the last two approved chapters.

### 4. Review what you wrote

`/authorkit.review` does two jobs depending on scope. Pass a chapter for a craft review (plan adherence, constitution compliance, character/world consistency, continuity, theme integration — produces `chapters/NN/review.md`). Pass nothing (or `all` / `manuscript`) for a manuscript-wide drift sweep (continuity, threads, pacing, voice/style, world-building, overdue parked decisions). Pass a range for both.

```bash
/authorkit.review 1                # Craft review of chapter 1
/authorkit.review                  # Whole-manuscript drift sweep
/authorkit.review 5-10             # Craft reviews + range-scoped drift scan
```

Manuscript drift is read-only by default. If drift between drafts and upstream documents is found, you'll be offered the chance to fix it (`Fix all / Fix high-severity only / Review one by one / Skip`) — and even when approved, fixes only touch concept / outline / chapters.md / world. **Chapter drafts are never modified by `/authorkit.review`.** Use `/authorkit.write [N] revise: ...` for that.

### 5. Research grounding (optional, repeatable)

`/authorkit.research` runs grounded research from web/news/wikipedia/MCP sources and writes reusable notes.

```bash
/authorkit.research Research Victorian observatory architecture for the outline
/authorkit.research For chapter 7, research forensic botany in damp basements
/authorkit.research Research maritime signaling systems in 1890
```

Output goes to `research.md` (index) and `research/**/*.md` (topic files, flat by default, nested when a clear grouping reason exists). When findings are durable and clearly map to a `world/` category, the command **offers** world sync — gated by your approval in the chat. No silent writes to `world/`.

### 6. Export your manuscript

Export is **not** a slash command — it runs through the installer CLI directly:

```bash
authorkit book build --format docx --format epub
authorkit book audio --merge
authorkit book stats --output json
```

Read more in [Book Export](#book-export-audiobook-and-statistics) below.

---

## The Four Commands

Author Kit's slash-command surface is **four commands** that map to authoring activities. Everything that used to be a separate command (clarify, conceive, outline, chapter.plan, chapter.draft, chapter.review, chapter.help, chapter.reorder, world.build, world.sync, amend, park, analyze, revise, snapshot, constitution, whatif, chapters) lives inside one of these four as a mode the model picks based on what you ask for and what already exists on disk.

```
  ┌─────────────────────────────────────────────────────────────────────┐
  │                     /authorkit.discuss                              │
  │                                                                     │
  │   Talk through anything. Read-only by default. On approval, writes  │
  │   land in the right file:                                           │
  │                                                                     │
  │   • Empty repo               ──>  produces concept.md               │
  │   • Open brainstorming       ──>  notes/discuss-*.md (if you save)  │
  │   • Focused clarifications   ──>  concept.md / world/ / outline /   │
  │                                   characters / chapters/NN/plan.md  │
  │   • Cross-cutting changes    ──>  impact plan + auto-snapshot +     │
  │                                   propagation across all artifacts  │
  │   • Park / list / resolve    ──>  parked-decisions.md               │
  │   • Reorder / split / merge  ──>  renumbered files + cross-refs     │
  │   • What-if exploration      ──>  whatif/* git branch + snapshot    │
  │   • Voice / tone updates     ──>  .authorkit/memory/constitution.md │
  │   • Initial world seeding    ──>  world/ entries (CONCEPT-tagged)   │
  └────────────────────────┬────────────────────────────────────────────┘
                           │
                           v
  ┌─────────────────────────────────────────────────────────────────────┐
  │                     /authorkit.write                                │
  │                                                                     │
  │   Produce manuscript prose. Auto-generates the scaffolding it       │
  │   needs and reconciles state after every write:                     │
  │                                                                     │
  │   • No outline yet         ──>  generates outline.md (full/partial) │
  │   • No chapters.md yet     ──>  generates chapter task list         │
  │   • No plan for chapter N  ──>  plans it (scenes/beats/arc/hooks)   │
  │   • Plan exists            ──>  drafts (full / interactive /        │
  │                                  scene N / continue / from scene N) │
  │   • Draft exists + revise  ──>  applies targeted edits              │
  │   • Help with a passage    ──>  scalpel-level refinement            │
  │   • After drafting         ──>  reconcile: extract world deltas,    │
  │                                  refresh outline summary,           │
  │                                  update chapters.md status,         │
  │                                  scan for new ambiguities,          │
  │                                  rebuild world/_index.md            │
  └────────────────────────┬────────────────────────────────────────────┘
                           │
                           v
  ┌─────────────────────────────────────────────────────────────────────┐
  │                     /authorkit.review                               │
  │                                                                     │
  │   Read-only by default. Drafts are NEVER modified — drift fixes,    │
  │   when accepted, only touch concept / outline / chapters / world.   │
  │                                                                     │
  │   • Chapter N    ──>  craft review (plan adherence, constitution,   │
  │                       craft quality, character/world consistency,   │
  │                       continuity, theme integration) →              │
  │                       chapters/NN/review.md                         │
  │   • No scope     ──>  manuscript drift (continuity, threads,        │
  │                       pacing, voice, world, overdue parked          │
  │                       decisions, upstream drift)                    │
  │   • Range N-M    ──>  both                                          │
  └────────────────────────┬────────────────────────────────────────────┘
                           │
                           v
  ┌─────────────────────────────────────────────────────────────────────┐
  │                     /authorkit.research                             │
  │                                                                     │
  │   Grounded research from web / news / wikipedia / MCP. Writes to    │
  │   research.md + research/**/*.md (flat by default, nested for       │
  │   grouped series). Offers world sync when findings are durable and  │
  │   clearly map to a world/ category — gated by chat approval.        │
  └─────────────────────────────────────────────────────────────────────┘
```

### Slash Commands

| Command | Description | Inputs | Outputs |
|---------|-------------|--------|---------|
| `/authorkit.discuss` | Talk through brainstorming, clarification, cross-cutting changes, restructuring, what-if branches, voice/tone updates, parking, and initial world seeding. Read-only by default; every write proposed and confirmed. | Free-form topic, question, change description, or sub-mode keyword | Depends on mode — concept.md, world/, outline.md, characters.md, chapters.md, parked-decisions.md, snapshots/, amendments/, whatif/* branch, constitution, or notes/discuss-*.md |
| `/authorkit.write` | Plan + draft + reconcile manuscript prose. Generates the outline and chapter list when missing. Supports full/interactive/scene/continue/from-scene drafting plus revise and passage help. | Chapter number, range, or `next`; optional sub-mode keyword (`outline`, `interactive`, `scene N`, `continue`, `from scene N`, `revise`, `help`) | `outline.md`, `chapters.md`, `chapters/NN/plan.md`, `chapters/NN/draft.md`, world/ updates, `world/_index.md`, status changes in `chapters.md` |
| `/authorkit.review` | Per-chapter craft review and/or manuscript-wide drift sweep. Drafts are never modified. | Chapter number, range, empty (= manuscript) | `chapters/NN/review.md` for chapter scope; structured drift report for manuscript scope; status changes in `chapters.md` |
| `/authorkit.research` | Grounded research with optional world sync (always gated). | Free-form topic + optional `scope:`, `sources:`, `folder:` overrides | `research.md`, `research/**/*.md`, optional `world/notes/...` after explicit approval |

### Installer CLI Commands (`authorkit`)

| Command | Description | Inputs | Outputs |
|---------|-------------|--------|---------|
| `authorkit init` | Install/update Author Kit assets for selected AI(s). Re-init preserves `constitution.md` and removes files no longer managed by the new selection. | Target dir, `--ai`, `--script`, `--force`, `--here`, `--no-git`, `--ignore-agent-tools` | `.authorkit/`, AI prompt folders, manifest |
| `authorkit check` | Check local tool availability | — | Tool status report (`git`, `claude`, `codex`, `copilot`, `python`, `pandoc`, `ffmpeg`) |
| `authorkit version` | Print CLI and Python versions | — | Version report |
| `authorkit status` | Project health dashboard for the current book | — | Chapter breakdown by status, parked-decision counts, world entity totals, drift warnings |
| `authorkit book build` | Build manuscript outputs | Repeat `--format`, `--force`, `--yes`, `--quiet`, `--output-dir`, `--from-chapter`, `--to-chapter` | `dist/manuscript.md` + rendered docs |
| `authorkit book audio` | Generate chapter audio and optional merged audiobook | `--provider`, `--voice`, `--model`, `--merge`, `--output-dir`, `--from-chapter`, `--to-chapter`, `--force`, `--yes` | `dist/audio/*.mp3` (+ optional merged file) |
| `authorkit book stats` | Compute chapter/global manuscript metrics | `--output`, `--wpm`, `--audio-dir`, `--from-chapter`, `--to-chapter` | Table/JSON/Markdown stats (includes per-chapter estimated audio minutes) |

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

**1. Build the world** (before or after outlining) — via `/authorkit.discuss`:

```bash
/authorkit.discuss build the magic system and political structure
/authorkit.discuss flesh out the world
```

The model enters World Seed mode: it reads `concept.md` (and any `research/` you've grounded), picks the relevant categories for your genre (characters / places / organizations / history / systems / notes), proposes the entries it will write, and on approval seeds `world/` with `(CONCEPT)`-tagged entries plus YAML frontmatter, then rebuilds `world/_index.md`.

**2. Ground details with research** (optional, anytime):

```bash
/authorkit.research Research late-19th-century maritime law for this setting
/authorkit.research For chapter 4, research telegraph relay timing with web and wikipedia sources
/authorkit.research Research Victorian shipboard medical protocols
```

Default behavior writes only research artifacts (`research.md` + topic files in `research/`, flat-first, nested when a grouping reason exists). When findings are durable and clearly map to a `world/` category, the command **offers** world sync inline — gated by your chat approval. Existing note paths are updated in place; no forced migration.

**3. Reconcile after drafting** — automatic on `/authorkit.write`:

Every successful `/authorkit.write [N]` run finishes with a reconcile pass: it extracts new details from the chapter (tagged with the source chapter, e.g., `(CH03)`), refreshes the outline summary so it matches the drafted prose, updates `chapters.md` status, scans for new ambiguities, and rebuilds `world/_index.md`. If a draft contradicts an existing `(CONCEPT)` or `(CHxx)` entry, the contradiction is flagged with a recommendation to run `/authorkit.discuss "<change description>"` so the change is propagated consistently across all artifacts.

For a deeper verification pass (consistency between world/ and the manuscript, drift detection, overdue parked decisions, world rule violations), run:

```bash
/authorkit.review            # Whole-manuscript drift sweep (includes world consistency)
/authorkit.review 5-10       # Range-scoped: craft reviews + drift scan in 5-10
```

Findings are rated by severity (Critical, High, Medium, Low) with specific file paths and actionable recommendations.

### Entity body: Current State + History

Each world/ entity file keeps its body in two parts so it stays legible as the book grows:

- **`## Current State`** — the canonical now-truth (the entity as it stands at the latest drafted chapter), written in concise, untagged statements. Drafting and review read this as authoritative, so they never have to reconstruct the current picture from the full log.
- **`## History`** — the append-only, chapter-tagged provenance log of how the entity evolved. When a later chapter changes a fact, reconcile appends the tagged entry here and supersedes the matching Current State line in place.

This prevents long-running entity files from becoming palimpsests where the current truth is buried under layers of edits. A `/authorkit.review` consolidation pass can refresh a stale Current State and archive long-dead History entries (snapshot-gated).

### Evolution tags

`## History` entries are tagged to show how details evolve across the manuscript:

| Tag | Meaning |
|-----|---------|
| `(CONCEPT)` | Established during pre-writing world-building |
| `(CHxx)` | First appeared or was confirmed in chapter xx |
| `(CHxx-rev)` | Updated when chapter xx was revised |
| `(AMEND-YYYY-MM-DD)` | Changed as part of a direction or fact amendment |

### Entity index

As a book's world grows, finding the right information becomes increasingly expensive — every world/-touching command would need to scan all files. Author Kit solves this with a **script-generated central index** at `world/_index.md` (built by `build-world-index.sh` on Linux/macOS or `build-world-index.ps1` on Windows), which costs zero LLM tokens to maintain.

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

The index is rebuilt automatically by every command that touches `world/` files: `/authorkit.write` (after drafting / reconcile), `/authorkit.discuss` (after cross-cutting amendments, world seeding, or chapter restructuring), and `/authorkit.research` (when an author-approved sync writes to `world/notes/`). You only need to rebuild it manually if you've edited world/ files by hand — and `/authorkit.write` or `/authorkit.discuss` on its next run will rebuild it for you anyway.

Add YAML frontmatter to legacy files (created before frontmatter was standard) by asking `/authorkit.discuss` to "add frontmatter to world files that lack it" — it routes through the same index-rebuild path.

---

## Mid-Process Changes

Books rarely go exactly according to plan. Once `concept.md` exists, everything iterative routes through `/authorkit.discuss`, which auto-detects the right mode from what you say:

| You want to... | Say... |
|----------------|--------|
| Resolve ambiguities in your concept (structured Q&A) | `/authorkit.discuss the X feels vague` |
| Brainstorm ideas | `/authorkit.discuss let's talk about the villain's motivation` |
| Get help on a specific passage while writing | `/authorkit.write [N] help improve the opening paragraph` |
| Ground a topic with sources and keep reusable notes | `/authorkit.research [topic]` |
| Change the book's direction or a specific fact | `/authorkit.discuss change Marcus from a soldier to a spy` |
| Decide something later | `/authorkit.discuss park: <question>` |
| Save your current state before a big change | (auto-snapshots before any cross-cutting amendment or what-if start; you can also say `/authorkit.discuss snapshot now: <description>`) |
| Try something without committing | `/authorkit.discuss try first person POV for the flashbacks` (creates a `whatif/*` branch) |
| Move, split, or merge chapters | `/authorkit.discuss move CH05 to after CH02` |
| Check if outline/concept drifted from drafts | `/authorkit.review` |
| Verify the world/ folder for internal consistency | `/authorkit.review` (world consistency is part of the manuscript drift sweep) |
| Fix issues found by review | `/authorkit.write [N] revise: <issue>` |

A few interactions worth knowing: what-if branching auto-creates a snapshot; cross-cutting amendments log to `amendments/YYYY-MM-DD-*.md` and tag edits `(AMEND-YYYY-MM-DD)`; parked decisions surface in `/authorkit.review` reports and `authorkit status` once their deadline is past.

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
- `authorkit init` seeds repo `.gitignore` with generated artifacts and local secrets (`dist/`, `.env`, `.claude/settings.local.json`, and the local `.codex/` auth/cache/session files) so they are never committed
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
voice = "marin"
instructions = ".authorkit/templates/publishing/audio-instructions.txt"
speaking_rate_wpm = 170

[stats]
reading_wpm = 200
# tts_cost_per_1m_chars = 0.000015   # uncomment and set to enable cost estimates in `authorkit book stats`
```

`authorkit book build` format options:
- Repeatable `--format` flag: `docx`, `epub`
- Example: `authorkit book build --format docx --format epub`
- If omitted, formats come from `[build].default_formats`
- If an output file already exists, `authorkit` prompts before overwrite
- Use `--force` to overwrite existing output files without prompts

`authorkit book audio` provider/auth and selection precedence:
- OpenAI is the only supported audio provider today (`[audio].provider = "openai"`); the knob exists for future providers.
  - [Get started](https://developers.openai.com/api/docs) to create an OpenAI account, enable audio models, and get a key
- Required auth: `OPENAI_API_KEY` in environment or local `.env`
- Voice selection order: `--voice` CLI flag, then `[audio].voice`, then default `marin`
  - You can explore optional voices using [openai.fm](https://github.com/openai/openai-fm)
- Model selection order: `--model` CLI flag, then `[audio].model`, then default `gpt-4o-mini-tts`
  - Read more about [OpenAI audio models](https://developers.openai.com/api/docs/guides/text-to-speech)
- Generated chapter files and merged audiobook output include ID3 metadata tags (title/album/artist/language and chapter tracking)
- OpenAI recommends `marin` or `cedar` voices for best quality. `marin` is the shipped default; switch to `cedar` (or any other supported voice) by setting `[audio].voice` in `book.toml` or passing `--voice`

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
|   |-- authorkit.*.md
|   `-- _shared/                     # Cross-prompt guardrails included by multiple commands
|-- instructions/                    # Canonical instruction templates
|   |-- claude.md.tmpl
|   |-- copilot.md.tmpl
|   `-- codex.md.tmpl
|-- scripts/
|   |-- bash/                        # Linux/macOS shell automation
|   |   |-- common.sh
|   |   |-- setup-book.sh
|   |   |-- setup-outline.sh
|   |   |-- check-prerequisites.sh
|   |   `-- build-world-index.sh
|   `-- powershell/                  # Windows/PowerShell automation
|       |-- common.ps1
|       |-- setup-book.ps1
|       |-- setup-outline.ps1
|       |-- check-prerequisites.ps1
|       `-- build-world-index.ps1
|-- templates/
|   |-- concept-template.md
|   |-- outline-template.md
|   |-- chapters-template.md
|   |-- chapter-plan-template.md
|   |-- research-index-template.md
|   |-- research-topic-template.md
|   |-- world-entity-frontmatter.md
|   |-- style-anchor-template.md
|   |-- parked-decisions-template.md   # /authorkit.discuss (park mode)
|   |-- snapshot-template.md           # /authorkit.discuss (auto-snapshot before risky writes)
|   |-- amendment-template.md          # /authorkit.discuss (cross-cutting change mode)
|   |-- discuss-notes-template.md      # /authorkit.discuss (when notes are saved)
|   `-- publishing/
|       |-- reference.docx
|       |-- epub.css
|       `-- audio-instructions.txt
`-- install-manifest.json            # Written by `authorkit init`

# constitution lives at the toolkit level (not under `book/`) so it can be
# edited via /authorkit.discuss (Constitution mode) and reused across the
# project's lifetime.

Generated by `authorkit init` (based on `--ai`):
- `.claude/commands/` + `CLAUDE.md`
- `.github/prompts/` + `.github/copilot-instructions.md`
- `.codex/prompts/` + `.codex/AGENTS.md`
```

### Book workspace files (`book/`)

Created when you first run `/authorkit.discuss` on an empty repo (or when it enters Conceive mode):

```text
book/
|-- concept.md
|-- style-anchor.md                  # Auto-derived from constitution + last 2 approved chapters; managed by chapter prompts
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
|-- amendments/
|-- snapshots/
|-- notes/
|   `-- discuss-YYYY-MM-DD-HH-MM.md
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
  3. Defaults: `voice = "marin"`, `model = "gpt-4o-mini-tts"`

### Existing audio files are not overwritten

- Default behavior is interactive prompt per existing chapter file.
- Use `--force` to bypass prompt logic.
- Use `--yes` for non-interactive acceptance (CI-friendly).

### Existing manuscript outputs are not overwritten

- Default behavior is interactive prompt per existing format (e.g. `manuscript.docx`).
- Use `authorkit book build --force` to overwrite without prompts.
- Use `authorkit book build --yes` to auto-accept overwrite prompts (CI-friendly).
- Use `--quiet` to suppress per-format status lines.

### Audio metadata tags are missing

- New audio runs write ID3 metadata automatically.
- If older files were created before metadata support, rerun `authorkit book audio` for those chapters.

### Audio delivery sounds flat or unnatural

- Verify the selected voice/model and try regenerating with `--force`.
- Customize the narration instructions template at `.authorkit/templates/publishing/audio-instructions.txt` or provide your own via `[audio].instructions` in `book.toml`.
- OpenAI recommends `marin` (the shipped default) or `cedar` for best quality.

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
