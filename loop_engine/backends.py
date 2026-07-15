"""
Agent backends — how each PES iteration actually talks to an AI.

Engineer reasoning
------------------
The class tutorial shells out to ``copilot``. Students may use Cursor, Claude
Code, or a chat UI instead. Abstracting the backend lets the *loop logic*
stay identical while the invocation strategy differs.

dry_run is first-class: we can unit-smoke the PES machinery without spending
API credits — critical when iterating on the loop engine itself.
"""

from __future__ import annotations

import shutil
import subprocess
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class AgentResponse:
    output: str
    backend: str
    elapsed_seconds: float
    returncode: int = 0


class AgentBackend(ABC):
    @abstractmethod
    def run(self, prompt: str, config: dict[str, Any]) -> AgentResponse:
        raise NotImplementedError


class DryRunBackend(AgentBackend):
    """
    Simulate an agent turn.

    Emits a structured stub that still exercises completion-promise detection
    and Summary parsing — without calling a real model.
    """

    def run(self, prompt: str, config: dict[str, Any]) -> AgentResponse:
        started = time.time()
        promise = config.get("evolve", {}).get("completion_promise", "DONE")
        # Truncate displayed prompt so dry-run logs stay readable.
        preview = prompt if len(prompt) <= 1200 else prompt[:1200] + "\n…[truncated]…"
        output = (
            "[dry_run] Agent backend did not call an LLM.\n"
            "[dry_run] Rendered prompt preview:\n"
            f"{preview}\n\n"
            "[dry_run] Simulated work unit complete.\n"
            f"<promise>{promise}</promise>\n"
        )
        print(output)
        return AgentResponse(
            output=output,
            backend="dry_run",
            elapsed_seconds=time.time() - started,
            returncode=0,
        )


class EchoBackend(AgentBackend):
    """Write the prompt to a file for manual paste into any AI assistant."""

    def run(self, prompt: str, config: dict[str, Any]) -> AgentResponse:
        started = time.time()
        workspace = Path(config["evolve"]["workspace"])
        workspace.mkdir(parents=True, exist_ok=True)
        out = workspace / "next_prompt.md"
        out.write_text(prompt, encoding="utf-8")
        message = (
            f"[echo] Wrote prompt to {out}\n"
            "[echo] Paste it into your AI assistant, let it work, then re-run "
            "the loop (or mark the stage complete with `python -m loop_engine stage complete …`).\n"
        )
        print(message)
        return AgentResponse(
            output=message,
            backend="echo",
            elapsed_seconds=time.time() - started,
            returncode=0,
        )


class CopilotBackend(AgentBackend):
    """GitHub Copilot CLI — used by the ralph-wiggum class tutorial."""

    def run(self, prompt: str, config: dict[str, Any]) -> AgentResponse:
        if shutil.which("copilot") is None:
            raise RuntimeError(
                "copilot CLI not found on PATH. Install GitHub Copilot CLI "
                "or switch agent.backend to dry_run / echo / cursor."
            )
        started = time.time()
        agent_cfg = config.get("agent", {})
        cmd = ["copilot", "-p", prompt]
        if agent_cfg.get("allow_all_tools", True):
            cmd.insert(1, "--allow-all-tools")
        model = agent_cfg.get("model")
        if model:
            cmd.extend(["--model", model])

        timeout = agent_cfg.get("timeout_seconds") or None
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout if timeout and timeout > 0 else None,
        )
        output = (proc.stdout or "") + (proc.stderr or "")
        print(output)
        return AgentResponse(
            output=output,
            backend="copilot",
            elapsed_seconds=time.time() - started,
            returncode=proc.returncode,
        )


class CursorBackend(AgentBackend):
    """
    Cursor Agent CLI if available.

    Engineer note: in current Cursor CLIs, ``-p`` / ``--print`` means "print to
    stdout for scripting", NOT "prompt follows". The prompt is positional.
    ``--force`` allows tools in non-interactive runs (needed inside our loop).
    """

    def run(self, prompt: str, config: dict[str, Any]) -> AgentResponse:
        started = time.time()
        agent_bin = shutil.which("agent")
        if agent_bin is None and shutil.which("cursor"):
            # Fallback: `cursor agent …` form
            base = ["cursor", "agent"]
        elif agent_bin is not None:
            base = [agent_bin]
        else:
            raise RuntimeError(
                "Cursor agent CLI not found. Install Cursor Agent or use "
                "dry_run / echo backend."
            )

        # Persist prompt to a file so giant templates don't blow ARG_MAX.
        workspace = Path(config["evolve"]["workspace"])
        workspace.mkdir(parents=True, exist_ok=True)
        prompt_path = workspace / "cursor_prompt.md"
        prompt_path.write_text(prompt, encoding="utf-8")

        cmd = [
            *base,
            "--print",
            "--force",
            "--output-format",
            "text",
            prompt,
        ]
        timeout = config.get("agent", {}).get("timeout_seconds") or None
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout if timeout and timeout > 0 else None,
            )
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"Cursor agent invocation failed: {exc}") from exc

        output = (proc.stdout or "") + (proc.stderr or "")
        print(output)
        return AgentResponse(
            output=output,
            backend="cursor",
            elapsed_seconds=time.time() - started,
            returncode=proc.returncode,
        )


def get_backend(name: str) -> AgentBackend:
    mapping: dict[str, type[AgentBackend]] = {
        "dry_run": DryRunBackend,
        "echo": EchoBackend,
        "copilot": CopilotBackend,
        "cursor": CursorBackend,
    }
    if name not in mapping:
        raise ValueError(
            f"Unknown agent backend '{name}'. Choose from: {', '.join(mapping)}"
        )
    return mapping[name]()
