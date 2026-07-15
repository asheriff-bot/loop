"""
Structured experiential memory.

Engineer reasoning
------------------
Without memory, a loop is just "retry harder". LoongFlow's insight is that the
Summary step should *persist* reusable lessons. We don't need island-model
evolution for homework — we need: retrieve recent lessons → inject into Plan →
write new lessons after Summary.

Storage is a JSON file in ``.loop_workspace/``. File-based beats Redis here:
zero infra, easy for a TA to open and grade the process.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from .models import Experience, utc_now_iso


class ExperientialMemory:
    """Append-only experience log with a short retrieval API for planners."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._experiences: list[Experience] = []
        self._meta: dict[str, Any] = {
            "created_at": utc_now_iso(),
            "updated_at": utc_now_iso(),
            "iteration_count": 0,
        }
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            return
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        self._meta = raw.get("meta", self._meta)
        self._experiences = [
            Experience.from_dict(item) for item in raw.get("experiences", [])
        ]

    def save(self) -> None:
        self._meta["updated_at"] = utc_now_iso()
        payload = {
            "meta": self._meta,
            "experiences": [e.to_dict() for e in self._experiences],
        }
        self.path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def add(self, experience: Experience) -> None:
        self._experiences.append(experience)
        self._meta["iteration_count"] = max(
            self._meta.get("iteration_count", 0), experience.iteration
        )
        self.save()

    def recent(self, n: int = 5) -> list[Experience]:
        return self._experiences[-n:]

    def failures(self, n: int = 5) -> list[Experience]:
        failed = [e for e in self._experiences if not e.success]
        return failed[-n:]

    def successes(self, n: int = 5) -> list[Experience]:
        ok = [e for e in self._experiences if e.success]
        return ok[-n:]

    def context_for_planner(self, n: int = 5) -> str:
        """
        Render memory as prompt-ready text.

        Design choice: prose beats JSON inside LLM prompts — models follow
        narrative lessons more reliably than nested schemas.
        """
        recent = self.recent(n)
        if not recent:
            return (
                "No prior experiential memory yet. This is the first iteration — "
                "explore carefully and record lessons in Summary."
            )

        lines = ["## Retrieved experiential memory (most recent first)"]
        for exp in reversed(recent):
            status = "SUCCESS" if exp.success else "FAILURE"
            lines.append(
                f"\n### Iteration {exp.iteration} [{status}] stage={exp.stage}"
            )
            lines.append(f"- Plan: {exp.plan_summary}")
            lines.append(f"- Execution: {exp.execution_summary}")
            lines.append(f"- Reflection: {exp.reflection}")
            if exp.lessons:
                lines.append("- Lessons:")
                for lesson in exp.lessons:
                    lines.append(f"  - {lesson}")
        return "\n".join(lines)

    def checkpoint(self, checkpoint_dir: str | Path, name: str) -> Path:
        """
        Snapshot memory — LoongFlow uses checkpoint-iter-{id}-{count}.
        We keep a similar naming convention so resume tooling feels familiar.
        """
        dest_dir = Path(checkpoint_dir) / name
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / "experiential_memory.json"
        dest.write_text(self.path.read_text(encoding="utf-8"), encoding="utf-8")
        return dest

    @property
    def size(self) -> int:
        return len(self._experiences)

    def best_guess_done(self) -> Optional[Experience]:
        """Last successful experience, if any — useful for status reports."""
        for exp in reversed(self._experiences):
            if exp.success:
                return exp
        return None
