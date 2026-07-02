"""Agent-invocation seam for AutoPilot.

All LLM interaction goes through ``AgentRunner`` so the loop is testable without
a live agent (``FakeRunner``) and portable across AI flavors (``ClaudeRunner``,
``CodexRunner``, ``CopilotRunner``). The real runners shell out to each agent's
headless CLI; their exact invocation/JSON-capture is the one piece that needs
live validation (see docs/autopilot.md "Open questions").

Author:
    mdemarne
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Protocol

from .autopilot_core import Directive, parse_directive
from .book_core import AutopilotConfig, AutopilotOpConfig

# An all-unset config — the default when no book.toml [autopilot] section (or
# no BookConfig at all) is supplied, so no --model/--effort flag is ever added.
_EMPTY_AUTOPILOT_CONFIG = AutopilotConfig(
    planner=AutopilotOpConfig(model=None, effort=None),
    review=AutopilotOpConfig(model=None, effort=None),
    writer=AutopilotOpConfig(model=None, effort=None),
)

# Appended to every worker command AutoPilot dispatches. Workers run headless
# (`claude -p`), so they cannot ask the author and get a reply this turn; this
# directive activates the shared "Unattended Mode" guardrail (grounded elaboration
# writes proceed, optional gated prompts are skipped, and genuine forks are flagged
# for escalation rather than resolved).
UNATTENDED_DIRECTIVE = (
    "[AUTOPILOT-UNATTENDED] This command was dispatched by an autonomous `authorkit autopilot` run; "
    'you cannot ask the author and receive a reply this turn. Follow the "Unattended Mode" rules in the '
    "shared generation guardrails: proceed with writes the concept/outline/research already imply (invent "
    "the specifics, tag entries, rebuild the world index, and report what you wrote); skip optional gated "
    "prompts (use the safe default); and for a genuine fork or contradiction the concept does not settle, "
    "make only the grounded writes and flag the fork in your report instead of inventing a resolution."
)


@dataclass(slots=True)
class RunResult:
    """Outcome of dispatching one worker command in a clean session."""

    ok: bool
    output: str = ""
    error: str = ""


class AgentRunner(Protocol):
    """Runs the planner and dispatches worker commands in clean sessions."""

    def run_planner(
        self, prompt: str, status_json: str, mode_brief: str, context: str = "", guideline: str = ""
    ) -> Directive:
        """Return the planner's single next-action Directive.

        ``context`` is optional read-only material (plot mode passes the concept,
        outline, world index, and research index so the planner can judge what is
        missing; chapters mode leaves it empty and stays status-only).
        ``guideline`` is the operator's ``--guideline`` directive for this run (a
        campaign instruction that takes precedence over the default ladder).
        """
        ...

    def run_command(self, command: str, *, op: str = "writer") -> RunResult:
        """Dispatch one existing command (e.g. ``/authorkit.write 7``).

        ``op`` names the AutoPilot operation bucket this command belongs to —
        ``"review"`` for a dispatched ``/authorkit.review``, ``"writer"`` for
        everything else (``plan``/``draft``/``revise``/``research``) — so the
        runner can apply that bucket's ``[autopilot.*]`` model/effort override,
        if any. The meta-planner call (``run_planner``) is always the
        ``"planner"`` bucket internally; it needs no ``op`` argument.
        """
        ...


def detect_flavor(repo_root: Path) -> str:
    """Read the installed AI flavor from the install manifest (first entry)."""
    manifest = repo_root / ".authorkit" / "install-manifest.json"
    try:
        data = json.loads(manifest.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return "claude"
    ais = data.get("ais") or ([data["ai"]] if isinstance(data.get("ai"), str) else [])
    return ais[0] if ais else "claude"


def _compose_planner_input(
    prompt: str, status_json: str, mode_brief: str, context: str = "", guideline: str = ""
) -> str:
    """Assemble the planner's full input: prompt + mode brief + guideline + optional context + status JSON."""
    parts = [prompt, "", f"## AutoPilot mode\n\n{mode_brief}", ""]
    if guideline:
        # Bare label + operator text; the campaign rules live once, in the
        # planner prompt's '## Author Guidelines (when present)' section.
        parts += [f"## Author Guidelines (high priority)\n\n{guideline}", ""]
    if context:
        parts += [f"## Plan-layer context (read-only)\n\n{context}", ""]
    parts += [
        f"## Current `authorkit status --json`\n\n```json\n{status_json}\n```",
        "",
        "Respond with ONLY the JSON directive described above — no prose, no fences required.",
    ]
    return "\n".join(parts)


class _SubprocessRunner:
    """Shared subprocess plumbing for CLI-backed agent runners."""

    flavor = "claude"

    def __init__(
        self,
        cwd: Path,
        *,
        timeout: int = 3600,
        permission_mode: str | None = None,
        skip_permissions: bool = False,
        models: AutopilotConfig | None = None,
    ):
        self.cwd = cwd
        self.timeout = timeout
        self.permission_mode = permission_mode
        self.skip_permissions = skip_permissions
        # Per-operation model/effort overrides from book.toml [autopilot.*].
        # All-unset by default so no flags are ever injected unless the author
        # opted in.
        self.models = models or _EMPTY_AUTOPILOT_CONFIG

    def _op_config(self, op: str) -> AutopilotOpConfig:
        """Resolve the [autopilot.*] override for a bucket ("planner"/"review"/"writer")."""
        return getattr(self.models, op)

    # Per-flavor command construction — overridden by subclasses.
    def _planner_argv(self, full_prompt: str) -> list[str]:
        raise NotImplementedError

    def _command_argv(self, command: str, op: str = "writer") -> list[str]:
        raise NotImplementedError

    def _extract_text(self, stdout: str) -> str:
        """Pull the assistant's text out of the CLI's stdout envelope."""
        return stdout

    def run_planner(
        self, prompt: str, status_json: str, mode_brief: str, context: str = "", guideline: str = ""
    ) -> Directive:
        full = _compose_planner_input(prompt, status_json, mode_brief, context, guideline)
        proc = subprocess.run(
            self._planner_argv(full),
            cwd=str(self.cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=self.timeout,
        )
        if proc.returncode != 0:
            detail = proc.stderr.strip() or proc.stdout.strip() or "unknown error"
            raise RuntimeError(f"{self.flavor} planner call failed: {detail}")
        return parse_directive(self._extract_text(proc.stdout))

    def run_command(self, command: str, *, op: str = "writer") -> RunResult:
        # Workers run headless — signal unattended mode (see UNATTENDED_DIRECTIVE).
        proc = subprocess.run(
            self._command_argv(f"{command}\n\n{UNATTENDED_DIRECTIVE}", op),
            cwd=str(self.cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=self.timeout,
        )
        ok = proc.returncode == 0
        return RunResult(
            ok=ok,
            output=proc.stdout,
            error="" if ok else (proc.stderr.strip() or proc.stdout.strip() or "unknown error"),
        )


class ClaudeRunner(_SubprocessRunner):
    """Headless Claude Code runner (`claude -p`)."""

    flavor = "claude"

    def _planner_argv(self, full_prompt: str) -> list[str]:
        argv = ["claude", "-p", full_prompt, "--output-format", "json"]
        op = self._op_config("planner")
        if op.model:
            argv += ["--model", op.model]
        if op.effort:
            argv += ["--effort", op.effort]
        return argv

    def _command_argv(self, command: str, op: str = "writer") -> list[str]:
        argv = ["claude", "-p", command]
        # A headless worker must be allowed to use tools (write files, run the
        # setup/world-index scripts) or it makes no progress. Default claude
        # permissions block this; the caller opts into a posture.
        if self.skip_permissions:
            argv.append("--dangerously-skip-permissions")
        elif self.permission_mode:
            argv += ["--permission-mode", self.permission_mode]
        op_config = self._op_config(op)
        if op_config.model:
            argv += ["--model", op_config.model]
        if op_config.effort:
            argv += ["--effort", op_config.effort]
        return argv

    def _extract_text(self, stdout: str) -> str:
        # `claude -p --output-format json` wraps the reply in a JSON envelope
        # with a `result` field. Fall back to raw stdout if that shape changes.
        try:
            envelope = json.loads(stdout)
        except json.JSONDecodeError:
            return stdout
        if isinstance(envelope, dict) and "result" in envelope:
            return str(envelope["result"])
        return stdout


class CodexRunner(_SubprocessRunner):
    """Headless Codex runner. Invocation needs live validation (see docs spike).

    Model/effort injection (only emitted when the author sets a value in
    ``book.toml``): ``-m/--model`` is a dedicated shorthand flag confirmed on
    ``codex exec``. There is no dedicated effort flag — reasoning effort is
    only settable via the generic inline config override,
    ``-c model_reasoning_effort="<level>"`` (valid values: minimal/low/medium/
    high/xhigh). Multiple open Codex CLI GitHub issues report
    ``model_reasoning_effort`` occasionally being ignored — treat this as a
    known-flaky area, not a guaranteed lever.
    """

    flavor = "codex"

    def _planner_argv(self, full_prompt: str) -> list[str]:
        argv = ["codex", "exec", full_prompt]
        op = self._op_config("planner")
        if op.model:
            argv += ["-m", op.model]
        if op.effort:
            argv += ["-c", f'model_reasoning_effort="{op.effort}"']
        return argv

    def _command_argv(self, command: str, op: str = "writer") -> list[str]:
        argv = ["codex", "exec", command]
        op_config = self._op_config(op)
        if op_config.model:
            argv += ["-m", op_config.model]
        if op_config.effort:
            argv += ["-c", f'model_reasoning_effort="{op_config.effort}"']
        return argv


class CopilotRunner(_SubprocessRunner):
    """Headless GitHub Copilot runner. Invocation needs live validation (see docs spike).

    Model/effort injection (only emitted when the author sets a value in
    ``book.toml``): ``--model=<id>`` is confirmed compatible with ``-p``
    (documented example: ``copilot -p "..." --model claude-haiku-4.5``).
    ``--effort=<level>`` (values: low/medium/high/xhigh/max) is a real,
    documented flag, but its compatibility with ``-p`` (non-interactive) mode
    is **unverified** — Copilot's own docs never demonstrate the two paired.
    Spot-check against a live ``copilot`` run before relying on it.
    """

    flavor = "copilot"

    def _planner_argv(self, full_prompt: str) -> list[str]:
        argv = ["copilot", "-p", full_prompt]
        op = self._op_config("planner")
        if op.model:
            argv += ["--model", op.model]
        if op.effort:
            argv += ["--effort", op.effort]
        return argv

    def _command_argv(self, command: str, op: str = "writer") -> list[str]:
        argv = ["copilot", "-p", command]
        op_config = self._op_config(op)
        if op_config.model:
            argv += ["--model", op_config.model]
        if op_config.effort:
            argv += ["--effort", op_config.effort]
        return argv


_RUNNERS: dict[str, type[_SubprocessRunner]] = {
    "claude": ClaudeRunner,
    "codex": CodexRunner,
    "copilot": CopilotRunner,
}


def get_runner(
    repo_root: Path,
    *,
    flavor: str | None = None,
    timeout: int = 3600,
    permission_mode: str | None = None,
    skip_permissions: bool = False,
    models: AutopilotConfig | None = None,
) -> AgentRunner:
    """Construct the AgentRunner for the repo's installed flavor.

    ``models`` is the book's ``[autopilot.*]`` config (from ``BookConfig.autopilot``),
    or ``None`` for an all-unset config — no ``--model``/``--effort`` flags injected.
    """
    resolved = flavor or detect_flavor(repo_root)
    runner_cls = _RUNNERS.get(resolved, ClaudeRunner)
    return runner_cls(
        repo_root,
        timeout=timeout,
        permission_mode=permission_mode,
        skip_permissions=skip_permissions,
        models=models,
    )


class FakeRunner:
    """Scripted runner for tests and dry-runs.

    Returns queued directives in order (falling back to ``done`` when the queue
    empties) and records dispatched commands. An optional ``on_command`` hook
    lets a test mutate the workspace to simulate a real command's effect (e.g.
    flipping a chapter to ``[X]`` in chapters.md) so the loop observes progress.
    """

    def __init__(self, directives: list, *, on_command: Callable[[str], None] | None = None):
        self._directives = list(directives)
        self.dispatched: list[str] = []
        self.dispatched_ops: list[str] = []
        self.planner_calls = 0
        self.planner_inputs: list[dict] = []
        self._on_command = on_command

    def run_planner(
        self, prompt: str, status_json: str, mode_brief: str, context: str = "", guideline: str = ""
    ) -> Directive:
        self.planner_calls += 1
        self.planner_inputs.append(
            {
                "prompt": prompt,
                "status_json": status_json,
                "mode_brief": mode_brief,
                "context": context,
                "guideline": guideline,
            }
        )
        if not self._directives:
            return Directive(action="done", reason="no more scripted directives")
        nxt = self._directives.pop(0)
        return nxt if isinstance(nxt, Directive) else parse_directive(nxt)

    def run_command(self, command: str, *, op: str = "writer") -> RunResult:
        self.dispatched.append(command)
        self.dispatched_ops.append(op)
        if self._on_command is not None:
            self._on_command(command)
        return RunResult(ok=True, output=f"ran {command}")
