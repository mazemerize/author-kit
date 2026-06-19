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


@dataclass(slots=True)
class RunResult:
    """Outcome of dispatching one worker command in a clean session."""

    ok: bool
    output: str = ""
    error: str = ""


class AgentRunner(Protocol):
    """Runs the planner and dispatches worker commands in clean sessions."""

    def run_planner(self, prompt: str, status_json: str, mode_brief: str, context: str = "") -> Directive:
        """Return the planner's single next-action Directive.

        ``context`` is optional read-only material (plot mode passes the concept,
        outline, world index, and research index so the planner can judge what is
        missing; chapters mode leaves it empty and stays status-only).
        """
        ...

    def run_command(self, command: str) -> RunResult:
        """Dispatch one existing command (e.g. ``/authorkit.write 7``)."""
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


def _compose_planner_input(prompt: str, status_json: str, mode_brief: str, context: str = "") -> str:
    """Assemble the planner's full input: prompt + mode brief + optional context + status JSON."""
    parts = [prompt, "", f"## AutoPilot mode\n\n{mode_brief}", ""]
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
        timeout: int = 1800,
        permission_mode: str | None = None,
        skip_permissions: bool = False,
    ):
        self.cwd = cwd
        self.timeout = timeout
        self.permission_mode = permission_mode
        self.skip_permissions = skip_permissions

    # Per-flavor command construction — overridden by subclasses.
    def _planner_argv(self, full_prompt: str) -> list[str]:
        raise NotImplementedError

    def _command_argv(self, command: str) -> list[str]:
        raise NotImplementedError

    def _extract_text(self, stdout: str) -> str:
        """Pull the assistant's text out of the CLI's stdout envelope."""
        return stdout

    def run_planner(self, prompt: str, status_json: str, mode_brief: str, context: str = "") -> Directive:
        full = _compose_planner_input(prompt, status_json, mode_brief, context)
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

    def run_command(self, command: str) -> RunResult:
        proc = subprocess.run(
            self._command_argv(command),
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
        return ["claude", "-p", full_prompt, "--output-format", "json"]

    def _command_argv(self, command: str) -> list[str]:
        argv = ["claude", "-p", command]
        # A headless worker must be allowed to use tools (write files, run the
        # setup/world-index scripts) or it makes no progress. Default claude
        # permissions block this; the caller opts into a posture.
        if self.skip_permissions:
            argv.append("--dangerously-skip-permissions")
        elif self.permission_mode:
            argv += ["--permission-mode", self.permission_mode]
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
    """Headless Codex runner. Invocation needs live validation (see docs spike)."""

    flavor = "codex"

    def _planner_argv(self, full_prompt: str) -> list[str]:
        return ["codex", "exec", full_prompt]

    def _command_argv(self, command: str) -> list[str]:
        return ["codex", "exec", command]


class CopilotRunner(_SubprocessRunner):
    """Headless GitHub Copilot runner. Invocation needs live validation (see docs spike)."""

    flavor = "copilot"

    def _planner_argv(self, full_prompt: str) -> list[str]:
        return ["copilot", "-p", full_prompt]

    def _command_argv(self, command: str) -> list[str]:
        return ["copilot", "-p", command]


_RUNNERS: dict[str, type[_SubprocessRunner]] = {
    "claude": ClaudeRunner,
    "codex": CodexRunner,
    "copilot": CopilotRunner,
}


def get_runner(
    repo_root: Path,
    *,
    flavor: str | None = None,
    timeout: int = 1800,
    permission_mode: str | None = None,
    skip_permissions: bool = False,
) -> AgentRunner:
    """Construct the AgentRunner for the repo's installed flavor."""
    resolved = flavor or detect_flavor(repo_root)
    runner_cls = _RUNNERS.get(resolved, ClaudeRunner)
    return runner_cls(
        repo_root,
        timeout=timeout,
        permission_mode=permission_mode,
        skip_permissions=skip_permissions,
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
        self.planner_calls = 0
        self.planner_inputs: list[dict] = []
        self._on_command = on_command

    def run_planner(self, prompt: str, status_json: str, mode_brief: str, context: str = "") -> Directive:
        self.planner_calls += 1
        self.planner_inputs.append(
            {"prompt": prompt, "status_json": status_json, "mode_brief": mode_brief, "context": context}
        )
        if not self._directives:
            return Directive(action="done", reason="no more scripted directives")
        nxt = self._directives.pop(0)
        return nxt if isinstance(nxt, Directive) else parse_directive(nxt)

    def run_command(self, command: str) -> RunResult:
        self.dispatched.append(command)
        if self._on_command is not None:
            self._on_command(command)
        return RunResult(ok=True, output=f"ran {command}")
