---
description: Write chapter prose — full chapter, scene by scene, or continue a partial draft. Supports collaborative writing with mixed authorship.
handoffs:
  - label: Review This Chapter
    agent: authorkit.chapter.review
    prompt: Review chapter [N]
  - label: Help With Passage
    agent: authorkit.chapter.help
    prompt: Help with chapter [N]
  - label: Plan Next Chapter
    agent: authorkit.chapter.plan
    prompt: Plan chapter [N+1]
scripts:
  ps: scripts/powershell/check-prerequisites.ps1 -Json -IncludeChapters
---

## User Input

```text
{{USER_INPUT_TOKEN}}
```

You **MUST** consider the user input before proceeding (if not empty). The user input should contain the chapter number.

## Outline

1. **Setup**: Run `{{SCRIPT_CHECK_PREREQ}}` from repo root and parse BOOK_DIR, STYLE_ANCHOR, and AVAILABLE_DOCS. All paths must be absolute.

2. **Parse chapter number and drafting mode** from user input:

   **Chapter number** (required):
   - Accept formats: "1", "01", "CH01", "chapter 1"
   - Normalize to two-digit format: "01", "02", etc.
   - If no chapter number: ERROR "Please specify a chapter number"

   **Drafting mode** (auto-detected from remaining input):
   - **"full"** or no mode keyword → **Full mode**: Write the entire chapter in one pass (default, preserves existing behavior)
   - **"interactive"** or **"section by section"** → **Interactive mode**: Write one scene/section at a time, pausing for author input between each
   - **"scene N"** or **"section N"** → **Scene mode**: Write only the specified scene/section from the plan
   - **"continue"** or **"next"** → **Continue mode**: Find where the current partial draft ends and write the next scene/section
   - **"from scene N"** → **From-scene mode**: Write from scene N through the end of the chapter

3. **Verify chapter plan exists**:
   - Check that `BOOK_DIR/chapters/NN/plan.md` exists
   - If not: ERROR "Chapter plan not found. Run `/authorkit.chapter.plan [N]` first."
   - Check chapters.md status is at least `[P]` (planned)

4. **Load all context** for writing:
   - **Required**: `chapters/NN/plan.md` (the scene/section breakdown, beats, arc)
   - **Required**: concept.md (voice, tone, overall themes)
   - **Required**: `/memory/constitution.md` (writing principles - this is your style guide)
   - **Required**: `STYLE_ANCHOR` at `BOOK_DIR/style-anchor.md` (refresh before drafting)
   - **Recommended**: characters.md (character voices, speech patterns, physical descriptions)
   - **Recommended**: `world/` folder files for characters and locations appearing in this chapter (ensures setting/character detail consistency with established world). **If `world/_index.md` exists**: Read it. Use the Chapter Manifest to find entities from the previous chapter. Resolve character/location names from the chapter plan via the Alias Lookup. Load only the world/ files identified by these lookups, rather than all world/ files.
   - **Recommended**: Previous chapter draft `chapters/NN-1/draft.md` (for continuity of voice, scene transitions, and ongoing threads)
   - **Optional**: outline.md (overall structure context)
   - **Optional**: research.md and relevant `research/` topic files discovered recursively (scope `general`, `chapter CHNN`, or topic files directly tied to this chapter's domains)

5. **Build or refresh style anchor** at `STYLE_ANCHOR` before drafting:
   - Source style from constitution + the last two approved chapters (`[X]`) before this chapter number.
   - Fallbacks:
     - If one approved chapter exists: use constitution + that chapter.
     - If none exist: use constitution only.
   - Write the style anchor using this fixed schema:
     - `## Non-Negotiables (POV, Tense, Narrative Distance)`
     - `## Cadence Profile (Sentence and Paragraph Rhythm)`
     - `## Dialogue Profile`
     - `## Diction and Register`
     - `## Imagery Density and Taboo Patterns`
     - `## Drift Red Flags`
     - `## Provenance`

6. **Pre-flight checks**:
   - Load constitution and internalize the voice/style rules
   - Load `STYLE_ANCHOR` and internalize its style constraints
   - Review the chapter plan's scene/section breakdown, opening hook, and closing beat

   **Draft state detection**:
   - Check if `chapters/NN/draft.md` already exists
   - If it exists, check for a partial draft marker: `<!-- PARTIAL DRAFT: Scenes X-Y of Z complete -->`
   - **Full mode + complete draft exists**: Ask user whether to overwrite or skip
   - **Full mode + partial draft exists**: Ask user whether to overwrite, continue from where it left off, or skip
   - **Interactive/Scene/Continue/From-scene mode + draft exists**: Read the existing draft content (it may contain author-written or AI-written content — treat all as canonical)
   - **Any mode + no draft exists**: Proceed normally

   **Mixed authorship awareness**: The existing draft may contain content the author wrote directly. Do not assume all existing content was AI-generated. Match the voice and style of what's already on the page (via style-anchor + the existing prose itself).

7. **Write the chapter** (behavior depends on mode):

   ### Full Mode (default)

   Follow the scene/section breakdown from the chapter plan. For each scene/section:

   a. **Set the stage**: Establish setting/context using sensory details (fiction) or clear framing (non-fiction)

   b. **Execute the beats**: Write through each key beat in order, ensuring:
      - Each beat advances the story/argument
      - Transitions between beats feel natural
      - The emotional/intellectual progression follows the planned arc

   c. **Character voice** (fiction): Ensure each character speaks distinctly per their profile in characters.md

   d. **Pacing**: Vary sentence length and paragraph size. Use short sentences for tension, longer ones for reflection. Break for dialogue. Use white space intentionally.

   e. **Show don't tell** (unless constitution says otherwise): Demonstrate emotions through action and dialogue rather than stating them

   f. **Scene transitions**: Use clear but not heavy-handed transitions between scenes/sections

   g. **Opening**: Start strong with the planned opening hook. The first paragraph should compel the reader to continue.

   h. **Closing**: End with the planned closing beat. Leave the reader wanting to turn the page.

   ### Interactive Mode

   Write **one scene/section at a time**, pausing after each for author input:

   1. Identify the first unwritten scene from the plan (or the first scene if starting fresh)
   2. Write that scene following the same quality rules as Full mode
   3. Add or update the progress marker at the top of draft.md: `<!-- PARTIAL DRAFT: Scenes 1-N of TOTAL complete -->`
   4. Report what was written (scene summary, word count) and ask:
      - "Continue to scene [N+1]?"
      - "Review or adjust what we have?"
      - "Would you like to write the next scene yourself?"
   5. Wait for author input before writing the next scene
   6. If the author writes content between sessions (e.g., they wrote scene 3 themselves), detect it when continuing and skip to the next unwritten scene

   ### Scene Mode

   Write **only the specified scene/section**:
   1. Identify the target scene from the plan
   2. If a partial draft exists, read it for voice continuity
   3. Write the target scene
   4. If inserting into an existing draft: place the scene in its correct position relative to existing content
   5. Update the progress marker
   6. Report what was written and suggest next steps

   ### Continue Mode

   Pick up **where the draft currently ends**:
   1. Read the existing draft (may contain author-written and AI-written content)
   2. Determine which scenes/sections are already covered by comparing draft content against the plan's scene breakdown
   3. Identify the next unwritten scene
   4. Match the voice and style of the existing content
   5. Write the next scene, appending to the draft
   6. Update the progress marker
   7. Report and ask whether to continue or pause

   ### From-Scene Mode

   Write **from the specified scene through the end**:
   1. Identify the starting scene
   2. If earlier scenes exist in the draft, read them for continuity
   3. Write from the starting scene through the final scene, including the closing beat
   4. Update the progress marker (or remove it if all scenes are now complete)

   ### Progress Tracking for Non-Full Modes

   - Maintain a progress marker at the top of draft.md: `<!-- PARTIAL DRAFT: Scenes 1-3 of 5 complete -->`
   - Do NOT update chapters.md status to `[D]` until ALL scenes are written
   - When the final scene is written, remove the progress marker and update status to `[D]`
   - If the author wrote a scene that deviates from the plan, follow the author's lead — the draft content is canonical over the plan

8. **Quality self-check** before saving (apply to all newly written content):
   - Does the new content follow the constitution's voice and style rules?
   - Does it match `book/style-anchor.md` on POV, tense, narrative distance, cadence, diction, imagery density, and dialogue profile?
   - Does each scene/section achieve its planned purpose?
   - If this completes the chapter: Are the opening hook and closing beat effective?
   - Is the pacing varied and appropriate?
   - Are character voices distinct? (fiction)
   - Is the argument clear and well-supported? (non-fiction)
   - For full mode: Is the word count in the target range from the chapter plan?

9. **Style match pass**:
   - Compare newly written content against constitution + `book/style-anchor.md`.
   - Also check that new content is consistent in voice with any existing author-written content in the draft.
   - Correct drift before saving.
   - If new numeric facts were introduced, verify each has rationale. If multiple values were plausible, verify the selected value is context-bounded and not a repetitive default.

10. **Write draft** to `BOOK_DIR/chapters/NN/draft.md`:
   - Include a header: `# Chapter [NN]: [Title]`
   - Use `---` between scenes (fiction) or `##` headings between sections (non-fiction)
   - Do NOT include meta-commentary or notes in the draft - it should be pure prose
   - For non-full modes: preserve existing content and append/insert new content in the correct position
   - For non-full modes with incomplete scenes: add or update `<!-- PARTIAL DRAFT: Scenes X-Y of Z complete -->` at the top

11. **Update chapter status** (mode-dependent):
   - **Full mode** or **all scenes now complete**: Change status from `[P]` to `[D]`
   - **Partial (not all scenes written yet)**: Do NOT change status — leave at `[P]` until the chapter is complete

12. **Report completion**:
    - Path to draft
    - Word count (total draft and newly written content)
    - Brief summary of what was written
    - Any deviations from the plan (and why)
    - **Full mode / chapter complete**: Suggested next step: `/authorkit.chapter.review [N]` or `/authorkit.chapter.plan [N+1]`
    - **Partial (interactive/scene/continue)**: Report progress (e.g., "Scenes 1-3 of 5 complete") and suggest: "Continue with `/authorkit.chapter.draft [N] continue`", "Write the next scene yourself", or "Get help with `/authorkit.chapter.help [N]`"

## Writing Rules

- **The draft is prose, not notes.** Write actual book content - full sentences, paragraphs, dialogue, descriptions.
- **Follow the constitution religiously.** The constitution is your style bible. Every sentence should be consistent with its principles.
- **Follow the style anchor religiously.** `book/style-anchor.md` is the continuity anchor across models.
- **The plan is a guide, not a prison.** If a better idea emerges while writing, follow it - but note the deviation.
- **Voice consistency**: If previous chapters exist, match their voice and energy level. If the current draft contains author-written content, match the author's voice.
- **No meta-commentary**: The draft file should contain only the book content itself. No "[Author's note]" or "[TODO]" markers. The only exception is the `<!-- PARTIAL DRAFT: ... -->` progress marker for non-full modes.
- **Dialogue formatting**: Use standard conventions for the genre. Fiction typically uses quotation marks and new paragraphs for new speakers.
- **Length**: In full mode, aim for the target word count in the chapter plan (10-15% variance okay). In scene/interactive mode, aim for proportional length per scene.
- **Mixed authorship**: The draft may contain content written by the author and content written by AI. Treat all existing content as canonical. Match the voice and style of what's on the page. If author-written content deviates from the plan, follow the author's lead.
- **Seamless transitions**: When continuing or inserting scenes into an existing draft, ensure the transition from existing content to new content is seamless. Re-read the last few paragraphs before the insertion point and the first few after (if any) to ensure continuity.

