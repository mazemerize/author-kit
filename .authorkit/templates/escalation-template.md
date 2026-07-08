<!-- Canonical schema for AutoPilot escalation records in book/escalations/.
     AutoPilot writes one OPEN record per stop point; the author resolves it
     (usually via /authorkit.discuss), which fills the Resolution block and sets
     Status to RESOLVED, unblocking the loop. Same OPEN/RESOLVED shape as
     parked-decisions; escalations differ only in that they BLOCK the loop.
     AutoPilot renders records from this schema — do not hand-author this file. -->

# [ESC-ID]: [SHORT_TITLE]

**Status**: OPEN
**Raised**: [YYYY-MM-DD] by [RAISED_BY]
**Type**: [story-fork | contradiction | outline-exhausted | quality-stall | structural | parked-overdue | grounding-gap | loop-health]
**Trigger**: [What tripped the escalation, with citations]
**Context**: [Relevant artifacts / chapters]
**Decision needed**: [The specific question for the author]
**Options**: [Option A; Option B; ... — optional, with a recommendation]
**Recommended command**: [/authorkit.discuss "resolve [ESC-ID]: <decision>" — or /authorkit.write N revise: / /authorkit.research]

## Resolution

**Resolved**: [YYYY-MM-DD]
**Decision**: [What was decided]
**Files changed**: [Paths touched while resolving]
**Amendment / Snapshot**: [amendment or snapshot id, if the resolution was cross-cutting]
