---
description: Write the actual chapter prose based on the chapter plan.
handoffs:
  - label: Review This Chapter
    agent: authorkit.chapter.review
    prompt: Review chapter [N]
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

2. **Parse chapter number** from user input:
   - Accept formats: "1", "01", "CH01", "chapter 1"
   - Normalize to two-digit format: "01", "02", etc.
   - If no chapter number: ERROR "Please specify a chapter number"

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
   - **Optional**: research.md and relevant `research/` topic files (scope `general`, `chapter CHNN`, or topic files directly tied to this chapter's domains)

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
   - If a draft already exists at `chapters/NN/draft.md`: ask user whether to overwrite or skip
   - Load constitution and internalize the voice/style rules
   - Load `STYLE_ANCHOR` and internalize its style constraints
   - Review the chapter plan's opening hook and closing beat

7. **Write the chapter**:

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

8. **Quality self-check** before saving:
   - Does the draft follow the constitution's voice and style rules?
   - Does the draft match `book/style-anchor.md` on POV, tense, narrative distance, cadence, diction, imagery density, and dialogue profile?
   - Does each scene/section achieve its planned purpose?
   - Are the opening hook and closing beat effective?
   - Is the pacing varied and appropriate?
   - Are character voices distinct? (fiction)
   - Is the argument clear and well-supported? (non-fiction)
   - Is the word count in the target range from the chapter plan?

9. **Style match pass**:
   - Compare the full draft against constitution + `book/style-anchor.md`.
   - Correct drift before saving.
   - If new numeric facts were introduced, verify each has rationale. If multiple values were plausible, verify the selected value is context-bounded and not a repetitive default.

10. **Write draft** to `BOOK_DIR/chapters/NN/draft.md`:
   - Include a header: `# Chapter [NN]: [Title]`
   - Use `---` between scenes (fiction) or `##` headings between sections (non-fiction)
   - Do NOT include meta-commentary or notes in the draft - it should be pure prose

11. **Update chapter status**: In chapters.md, change this chapter's status from `[P]` to `[D]`:
   - Find the line matching `- [P] CHNN`
   - Replace `- [P]` with `- [D]`

12. **Report completion**:
    - Path to draft
    - Word count
    - Brief summary of what was written
    - Any deviations from the plan (and why)
    - Suggested next step: `/authorkit.chapter.review [N]` or `/authorkit.chapter.plan [N+1]`

## Writing Rules

- **The draft is prose, not notes.** Write actual book content - full sentences, paragraphs, dialogue, descriptions.
- **Follow the constitution religiously.** The constitution is your style bible. Every sentence should be consistent with its principles.
- **Follow the style anchor religiously.** `book/style-anchor.md` is the continuity anchor across models.
- **The plan is a guide, not a prison.** If a better idea emerges while writing, follow it - but note the deviation.
- **Voice consistency**: If previous chapters exist, match their voice and energy level.
- **No meta-commentary**: The draft file should contain only the book content itself. No "[Author's note]" or "[TODO]" markers.
- **Dialogue formatting**: Use standard conventions for the genre. Fiction typically uses quotation marks and new paragraphs for new speakers.
- **Length**: Aim for the target word count in the chapter plan. It's okay to be 10-15% over or under.

