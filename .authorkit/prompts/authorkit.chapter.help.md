---
description: Get targeted writing help on a specific passage, scene, or paragraph — suggestions, alternatives, and collaborative refinement.
handoffs:
  - label: Continue Drafting
    agent: authorkit.chapter.draft
    prompt: Draft chapter [N]
  - label: Continue From Where Draft Ends
    agent: authorkit.chapter.draft
    prompt: Continue chapter [N] from where the draft ends
  - label: Write Specific Scene
    agent: authorkit.chapter.draft
    prompt: Draft chapter [N] scene [M]
  - label: Review This Chapter
    agent: authorkit.chapter.review
    prompt: Review chapter [N]
  - label: Discuss Ideas
    agent: authorkit.discuss
    prompt: Discuss ideas for chapter [N]
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --include-chapters
  ps: scripts/powershell/check-prerequisites.ps1 -Json -IncludeChapters
---

## User Input

```text
{{USER_INPUT_TOKEN}}
```

You **MUST** consider the user input before proceeding (if not empty). The user input should contain a chapter reference and a description of what they need help with.

## Goal

Provide targeted, collaborative writing assistance on a specific passage, scene, paragraph, or writing problem within a chapter. The author is actively writing — either they've written content and want help improving it, or they're stuck and need a hand. This is a **scalpel**, not a bulldozer: help with the specific thing requested, don't rewrite the whole chapter.

This command supports **mixed authorship** — the draft may contain parts the author wrote and parts the AI wrote. Treat all existing content as canonical regardless of who wrote it.

**Scope boundary**: `chapter.help` is for *passage-level* refinement (alternatives, polish, sensory detail, dialogue, trim, voice check, brief continuation). For writing whole scenes or continuing from where the draft ends, hand off to `chapter.draft` (which has dedicated `scene N`, `continue`, and `from scene N` modes).

## Outline

1. **Setup**: Run `{{SCRIPT_CHECK_PREREQ}}` from repo root and parse BOOK_DIR, STYLE_ANCHOR, and AVAILABLE_DOCS. All paths must be absolute.

2. **Parse user input** to extract:

   **Chapter number** (required):
   - Accept formats: "chapter 5 scene 2", "ch3 the opening", "5 dialogue between X and Y"
   - Normalize to two-digit format: "01", "02", etc.
   - If no chapter number found: ERROR "Please specify a chapter (e.g., `/authorkit.chapter.help chapter 3 improve the opening`)"

   **Target passage** (what to help with):
   - A scene reference: "scene 2", "the tavern scene", "opening", "closing"
   - A text reference: "the paragraph about the door", "the dialogue between Iria and Marcus"
   - A line or passage the author pastes directly in their message
   - A general area: "the transition between scene 1 and 2", "the description of the city"

   **Help mode** (auto-detected from keywords in user input):
   - **"alternatives" / "options"**: Generate 2-3 alternative versions
   - **"improve" / "strengthen" / "better"**: Analyze and suggest specific improvements
   - **"stuck" / "continue" / "what comes next"**: Suggest a brief continuation (2-3 paragraphs) to unblock the author. For writing the next full scene, hand off to `/authorkit.chapter.draft [N] continue` instead.
   - **"dialogue"**: Focus on making dialogue more natural and character-distinctive
   - **"describe" / "show" / "sensory"**: Enhance sensory detail, convert telling to showing
   - **"trim" / "tighten" / "cut"**: Suggest cuts and compressions
   - **"check" / "voice" / "style"**: Check passage against constitution and style-anchor for drift
   - **"write scene N" / "write the [scene]"**: NOT handled here — redirect to `/authorkit.chapter.draft [N] scene N` (scene-level writing belongs to `chapter.draft`)
   - **Default** (no mode keyword): Read the passage, assess what kind of help would be most useful, and suggest it before proceeding

3. **Load context**:
   - **Required**: `.authorkit/memory/constitution.md` (writing principles — the style guide)
   - **Required**: `STYLE_ANCHOR` at `BOOK_DIR/style-anchor.md` (prose continuity)
   - **Required**: `chapters/NN/draft.md` (the current draft — may be partial or complete)
   - **Recommended**: `chapters/NN/plan.md` (scene breakdown, beats, purpose)
   - **Recommended**: concept.md (voice, tone, themes)
   - **Recommended**: characters.md (character voices, speech patterns)
   - **Recommended**: `world/` files relevant to the passage (use `world/_index.md` alias lookup if available)
   - **Optional**: Previous chapter draft `chapters/NN-1/draft.md` (for continuity)
   - **Optional**: research.md and relevant `research/` topic files

   If no draft exists yet for this chapter: that's fine. The author may be working on it outside the tool and hasn't saved yet, or they want help planning what to write. Adapt accordingly.

4. **Locate the target passage** in the draft:
   - If the author referenced a scene number: map it to the plan's scene breakdown, then find the corresponding section in the draft
   - If the author referenced specific text: search the draft for it
   - If the author pasted content: use the pasted content as the target (it may or may not be in the draft yet)
   - If "opening": the first 1-3 paragraphs
   - If "closing": the last 1-3 paragraphs
   - If the passage can't be found: ask the author to clarify what they mean

5. **Deliver help based on mode**:

   ### "alternatives" / "options"

   Present the original passage (quoted), then 2-3 alternative versions:
   ```
   **Original:**
   > [quoted passage]

   **Option A** — [one-line rationale]:
   [rewritten passage]

   **Option B** — [one-line rationale]:
   [rewritten passage]

   **Option C** — [one-line rationale]:
   [rewritten passage]
   ```
   Each option should take a meaningfully different approach (not just word swaps). Explain what each option prioritizes.

   ### "improve" / "strengthen"

   Analyze the passage for:
   - Clarity and impact
   - Voice consistency (against constitution + style-anchor)
   - Show vs. tell balance
   - Pacing and rhythm
   - Character voice distinctiveness (if dialogue)

   Present specific, actionable suggestions — not vague advice. Show the exact text and the suggested replacement.

   ### "stuck" / "continue"

   Read the draft up to where it ends (or where the author indicates they're stuck). Then:
   - Summarize what the plan expects to happen next (if a plan exists)
   - Write 2-3 paragraphs of suggested continuation to unblock the author
   - Match the voice and style of what's already on the page
   - Offer: "Does this direction feel right? I can adjust the tone or try a different approach. To continue writing the full next scene, run `/authorkit.chapter.draft [N] continue`."

   ### "write scene N" / "write the [scene]"

   This is **out of scope for `chapter.help`** — scene-level writing belongs to `chapter.draft`. Reply:

   > Writing a full scene is `chapter.draft`'s job. Run `/authorkit.chapter.draft [N] scene [M]` to write a specific scene, or `/authorkit.chapter.draft [N] continue` to pick up where the draft ends. I can still help with passage-level refinement once the scene exists.

   Do not write the scene here.

   ### "dialogue"

   Focus specifically on dialogue quality:
   - Check each character speaks distinctly (per characters.md profiles)
   - Ensure dialogue serves a purpose (reveals character, advances plot, creates tension)
   - Suggest more natural phrasing where dialogue feels stiff
   - Check dialogue tags and action beats

   ### "describe" / "show"

   Enhance sensory and experiential detail:
   - Identify "telling" passages and suggest "showing" alternatives
   - Add sensory details (sight, sound, smell, touch, taste) where appropriate
   - Ground abstract emotions in physical sensation and action
   - Check against the constitution's imagery density preferences

   ### "trim" / "tighten"

   Suggest cuts while preserving essential content:
   - Identify redundant phrases, over-explanation, unnecessary adverbs
   - Suggest tighter alternatives
   - Show word count savings
   - Flag anything that seems load-bearing before cutting

   ### "check" / "voice" / "style"

   Compare the passage against constitution + style-anchor:
   - POV consistency
   - Tense consistency
   - Narrative distance
   - Cadence and rhythm
   - Diction and register
   - Flag any drift with specific examples

   ### Default (no mode keyword)

   Read the passage, then:
   - Briefly assess its strengths
   - Identify the most impactful area for improvement
   - Suggest which help mode would be most useful
   - Ask: "Would you like me to [suggested mode], or did you have something else in mind?"

6. **After presenting help**:

   Always end with an interactive prompt:
   - "Would you like me to apply [option/suggestion], try a different approach, or help with another passage?"
   - If the author says "apply" or picks an option: edit `chapters/NN/draft.md` at the target location
   - If the author wants to try another approach: adjust and re-present
   - If the author wants help elsewhere: repeat from step 4 with the new target

7. **When applying changes**:
   - Edit `draft.md` at the specific location — do not rewrite surrounding content
   - Do NOT change the chapter status in chapters.md (this is a micro-edit, not a full re-draft)
   - Do NOT update the partial draft progress marker (if one exists)
   - Confirm: "Applied to `chapters/NN/draft.md`. [Brief description of what changed.]"

## Key Rules

- **Minimal footprint.** Only change what was asked about. Do not "while I'm at it" fix other parts of the draft.
- **Respect the author's voice.** The author may have a style that differs from the constitution. When helping with author-written passages, match *their* voice, not an idealized version.
- **The draft is canonical.** If the draft contradicts the plan, the draft wins. Note the deviation but follow the draft.
- **Constitution + style-anchor for AI-written passages.** When writing new content (the brief stuck/continue continuation), follow the constitution and style-anchor to maintain consistency.
- **No meta-commentary in edits.** When applying changes to draft.md, write only prose. No [NOTE], [TODO], or [AUTHOR] markers.
- **Repeat as needed.** This command is designed for multiple rounds of help within a single chapter. The author should be able to ask for help on 5 different passages in one session.
