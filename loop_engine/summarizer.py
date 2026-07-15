"""
Summary worker (PES — Summary / Reflect).

Engineer reasoning
------------------
This is the step most DIY agent loops skip — and then wonder why iteration N+1
repeats iteration N's mistake. We parse the agent output for signals of done /
failure, distill lessons into ExperientialMemory, and optionally write a short
human-readable note under ``.loop_workspace/reflections/``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .executor import ExecutionArtifact
from .memory import ExperientialMemory
from .models import Experience, utc_now_iso


@dataclass
class SummaryArtifact:
    experience: Experience
    done: bool
    text: str


class Summarizer:
    def __init__(self, config: dict[str, Any], memory: ExperientialMemory):
        self.config = config
        self.memory = memory
        self.promise = config["evolve"].get("completion_promise", "DONE")

    def summarize(
        self,
        iteration: int,
        stage: str,
        execution: ExecutionArtifact,
    ) -> SummaryArtifact:
        output = execution.response.output or ""
        done = self._detect_done(output)
        success = execution.response.returncode == 0 and not self._detect_hard_failure(
            output
        )

        lessons = self._extract_lessons(output)
        # Always record at least one operational lesson so memory never stays empty.
        if not lessons:
            lessons = [
                (
                    "Completed a cycle; review IMPLEMENTATION_PLAN.md before the next "
                    "iteration to avoid re-planning finished work."
                )
            ]

        plan_summary = (
            f"Mode={execution.plan.mode}; prompt length={len(execution.plan.prompt)} chars"
        )
        execution_summary = (
            f"backend={execution.response.backend}; "
            f"elapsed={execution.response.elapsed_seconds:.2f}s; "
            f"returncode={execution.response.returncode}; "
            f"output_chars={len(output)}"
        )
        reflection = (
            f"Completion promise detected={done}. "
            f"Treating cycle as {'success' if success else 'needs-follow-up'}."
        )

        experience = Experience(
            iteration=iteration,
            stage=stage,
            plan_summary=plan_summary,
            execution_summary=execution_summary,
            reflection=reflection,
            success=success,
            lessons=lessons,
        )
        self.memory.add(experience)
        self._write_reflection_file(iteration, stage, experience, output)

        text = (
            f"[summary] iteration={iteration} done={done} success={success}\n"
            f"[summary] lessons:\n"
            + "\n".join(f"  - {x}" for x in lessons)
        )
        print(text)
        return SummaryArtifact(experience=experience, done=done, text=text)

    def _detect_done(self, output: str) -> bool:
        """
        Ralph stops on a completion promise string; we also accept the XML form
        ``<promise>DONE</promise>`` used in PROMPT_build.md.
        """
        if not self.promise:
            return False
        if re.search(
            rf"<promise>\s*{re.escape(self.promise)}\s*</promise>",
            output,
            flags=re.IGNORECASE,
        ):
            return True
        return self.promise in output

    def _detect_hard_failure(self, output: str) -> bool:
        markers = [
            "Traceback (most recent call last)",
            "FATAL:",
            "Error: Prompt file not found",
        ]
        return any(m in output for m in markers)

    def _extract_lessons(self, output: str) -> list[str]:
        """
        Pull bullet lines under a 'Lessons' heading if the agent followed the
        summary prompt. Fall back to empty and let the caller add a default.
        """
        lessons: list[str] = []
        in_block = False
        for line in output.splitlines():
            if re.search(r"^\s*#{1,3}\s*lessons?\b", line, re.IGNORECASE) or re.search(
                r"^\s*lessons?\s*:\s*$", line, re.IGNORECASE
            ):
                in_block = True
                continue
            if in_block:
                if re.match(r"^\s*#{1,3}\s+\S", line):
                    break
                m = re.match(r"^\s*[-*]\s+(.+)$", line)
                if m:
                    lessons.append(m.group(1).strip())
        return lessons[:8]

    def _write_reflection_file(
        self,
        iteration: int,
        stage: str,
        experience: Experience,
        raw_output: str,
    ) -> None:
        workspace = Path(self.config["evolve"]["workspace"])
        reflections = workspace / "reflections"
        reflections.mkdir(parents=True, exist_ok=True)
        path = reflections / f"iter-{iteration:04d}-{stage}.md"
        body = (
            f"# Reflection — iteration {iteration} ({stage})\n\n"
            f"- Created: {utc_now_iso()}\n"
            f"- Success: {experience.success}\n\n"
            f"## Plan\n{experience.plan_summary}\n\n"
            f"## Execution\n{experience.execution_summary}\n\n"
            f"## Reflection\n{experience.reflection}\n\n"
            f"## Lessons\n"
            + "\n".join(f"- {x}" for x in experience.lessons)
            + "\n\n## Raw agent output (truncated)\n```\n"
            + (raw_output[:4000] + ("…" if len(raw_output) > 4000 else ""))
            + "\n```\n"
        )
        path.write_text(body, encoding="utf-8")
