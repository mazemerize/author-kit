---
description: Explore an alternative direction on an experimental branch without committing to it.
handoffs:
  - label: Compare Branches
    agent: authorkit.whatif
    prompt: Compare the what-if branch with the source branch
  - label: Merge What-If
    agent: authorkit.whatif
    prompt: Merge this what-if branch back to the source branch
  - label: Discard What-If
    agent: authorkit.whatif
    prompt: Discard this what-if branch and return to the source branch
scripts:
  ps: scripts/powershell/check-prerequisites.ps1 -Json -IncludeChapters
---

## User Input

```text
{{USER_INPUT_TOKEN}}
```

You **MUST** consider the user input before proceeding (if not empty).

## Goal

Sometimes you want to **try** a creative direction without committing to it. This command creates a safe experimental branch where you can draft, plan, or revise freely, then compare the results against the original before deciding whether to keep, merge, or discard the experiment.

The command operates in four modes:

- **Start**: Create an experimental branch
- **Compare**: Summarize narrative differences between the experiment and the original
- **Merge**: Accept the experiment and merge it back
- **Discard**: Abandon the experiment and return to the original

## Outline

1. **Setup**: Run `{{SCRIPT_CHECK_PREREQ}}` from repo root and parse BOOK_DIR and AVAILABLE_DOCS. All paths must be absolute.

2. **Determine mode** from user input:

   - **Start mode** (default): User describes what they want to explore
     - Input like: "What if Marcus dies in chapter 5?", "Try first person POV for the flashbacks", "Explore cutting Act 2 entirely"
   - **Compare mode**: User wants to see what changed
     - Input like: "compare", "what changed?", "show differences"
   - **Merge mode**: User wants to keep the experiment
     - Input like: "merge", "keep this", "accept"
   - **Discard mode**: User wants to abandon the experiment
     - Input like: "discard", "abandon", "go back", "nevermind"

3. **Start Mode** — Create an experimental branch:

   a. Determine the current branch name (the "source branch").

   b. Generate a what-if branch name: `whatif/[slug]` (e.g., `whatif/marcus-dies-ch5`, `whatif/first-person-flashbacks`).

   c. **Create a snapshot** of the current state automatically (see `/authorkit.snapshot`):
      - Create snapshot file at `BOOK_DIR/snapshots/YYYY-MM-DD-pre-whatif-[slug].md`
      - Create git tag: `snapshot/YYYY-MM-DD-pre-whatif-[slug]`
      - Record the source branch name in the snapshot

   d. **Create and switch to the what-if branch**:
      ```
      git checkout -b whatif/[slug]
      ```

   e. **Create experiment record** at `BOOK_DIR/whatif-active.md`:

      ```markdown
      # Active What-If Experiment

      **Branch**: whatif/[slug]
      **Source Branch**: [original branch name]
      **Started**: [DATE]
      **Snapshot**: snapshot/YYYY-MM-DD-pre-whatif-[slug]

      ## Hypothesis

      [What the author wants to explore — from user input]

      ## Changes to Try

      - [Specific changes to make on this branch]

      ## Success Criteria

      - [How to evaluate whether this direction is better — user-provided or inferred]
      ```

   f. Report: Branch created, snapshot taken, instructions for what to do next (use normal commands like `/authorkit.chapter.plan`, `/authorkit.chapter.draft`, `/authorkit.revise`, `/authorkit.pivot` to make experimental changes).

4. **Compare Mode** — Summarize narrative differences:

   a. Verify we're on a `whatif/*` branch. If not, check for `whatif-active.md` to identify the experiment.

   b. Read `whatif-active.md` for the source branch name and hypothesis.

   c. **Generate narrative comparison** (not just git diff):

      ```markdown
      ## What-If Comparison: [EXPERIMENT NAME]

      **Experiment Branch**: whatif/[slug]
      **Source Branch**: [source]
      **Duration**: [days since start]

      ### Hypothesis

      [Original hypothesis from whatif-active.md]

      ### Changes Made on This Branch

      | Artifact | Change Summary |
      |----------|---------------|
      | [file] | [what changed] |

      ### Narrative Differences

      #### Plot
      - **Source**: [what happens in the original]
      - **What-if**: [what happens in the experiment]

      #### Characters
      - [Character differences]

      #### Pacing / Structure
      - [Structural differences]

      #### Voice / Tone
      - [Any voice changes]

      ### Word Count Comparison

      | Metric | Source | What-If | Delta |
      |--------|--------|---------|-------|
      | Total drafted words | [N] | [N] | [+/-N] |
      | Chapters modified | - | [N] | - |

      ### Assessment

      **Strengths of the what-if direction**:
      - [What works better]

      **Weaknesses of the what-if direction**:
      - [What works worse or is lost]

      **Recommendation**: [Keep / Discard / Partial merge]
      ```

   d. To generate this comparison:
      - Read the current (what-if) versions of modified files
      - Use `git show [source-branch]:[file]` to read the original versions
      - Compare narratively (not just textually)

   e. Report the comparison.

5. **Merge Mode** — Accept the experiment:

   a. Verify we're on a `whatif/*` branch.
   b. Read `whatif-active.md` for the source branch.
   c. Warn the user: "This will merge all experimental changes into [source branch]. This cannot be easily undone. Proceed?"
   d. On approval:
      - Switch to the source branch: `git checkout [source-branch]`
      - Merge: `git merge whatif/[slug] --no-ff -m "Merge what-if: [description]"`
      - Delete the what-if branch: `git branch -d whatif/[slug]`
      - Remove `whatif-active.md`
      - Update the snapshot file to note the experiment was accepted
   e. Report: Merge complete, recommend running `/authorkit.analyze` to verify consistency.

6. **Discard Mode** — Abandon the experiment:

   a. Verify we're on a `whatif/*` branch.
   b. Read `whatif-active.md` for the source branch.
   c. Warn the user: "This will switch back to [source branch] and delete the experimental branch. All changes on the what-if branch will be lost (but recoverable via git reflog). Proceed?"
   d. On approval:
      - Switch to the source branch: `git checkout [source-branch]`
      - Delete the what-if branch: `git branch -D whatif/[slug]`
      - Remove `whatif-active.md`
      - Update the snapshot file to note the experiment was discarded
   e. Report: Experiment discarded, back on source branch.

## Key Rules

- **One experiment at a time.** If `whatif-active.md` already exists, warn the user they have an active experiment. They must merge or discard it before starting a new one.
- **Auto-snapshot on start.** Every what-if branch automatically creates a pre-experiment snapshot. No additional manual step needed.
- **Normal workflow on the branch.** All standard commands (`/authorkit.chapter.plan`, `/authorkit.chapter.draft`, `/authorkit.revise`, etc.) work normally on the what-if branch. The experiment is just a git branch with extra metadata.
- **Narrative comparison, not just diff.** The compare mode should tell the author *what's different about the story*, not just which files changed.
- **Clean up after yourself.** Merge and discard both remove `whatif-active.md` and clean up branches.
- **Git safety.** Use `--no-ff` for merges to preserve the experiment history. Use `-D` (force) for discards since the branch hasn't been merged.
- **Recoverable.** Even after discard, the branch is recoverable via `git reflog` for a limited time. Mention this to the user.

