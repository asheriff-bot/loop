"""
Assignment stage tracker (loop.pdf workflow).

Engineer reasoning
------------------
The product can look done while the *process* still fails the rubric.
Tracking stages in JSON makes "did we commit after specify for step 2?" a
deterministic check instead of scrolling git log by hand at 2am.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from . import git_ops
from .models import StageState, utc_now_iso


class StageTracker:
    def __init__(self, path: str | Path, assignment_cfg: dict[str, Any]):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.assignment_cfg = assignment_cfg
        self.stages: list[StageState] = []
        self._init_or_load()

    def _init_or_load(self) -> None:
        if self.path.exists():
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            self.stages = [StageState.from_dict(s) for s in raw.get("stages", [])]
            return

        # Seed from config so the rubric map exists before any work starts.
        for step in self.assignment_cfg.get("steps", []):
            for stage in step.get("stages", []):
                self.stages.append(
                    StageState(step_id=step["id"], stage=stage, status="pending")
                )
        self.save()

    def save(self) -> None:
        payload = {
            "stages": [s.to_dict() for s in self.stages],
            "updated_at": utc_now_iso(),
        }
        self.path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def find(self, step_id: str, stage: str) -> StageState:
        for s in self.stages:
            if s.step_id == step_id and s.stage == stage:
                return s
        raise KeyError(f"Unknown stage {step_id}/{stage}")

    def start(self, step_id: str, stage: str) -> StageState:
        state = self.find(step_id, stage)
        state.status = "in_progress"
        state.started_at = utc_now_iso()
        self.save()
        print(f"[stage] START {step_id}/{stage}")
        return state

    def complete(
        self,
        step_id: str,
        stage: str,
        notes: str = "",
        commit: bool = True,
    ) -> StageState:
        state = self.find(step_id, stage)
        state.status = "completed"
        state.completed_at = utc_now_iso()
        state.notes = notes
        if commit:
            sha = git_ops.commit_stage(step_id, stage, notes=notes)
            state.commit_sha = sha
        self.save()
        print(f"[stage] COMPLETE {step_id}/{stage}")
        return state

    def status_report(self) -> str:
        lines = ["# Assignment stage status", ""]
        completed = sum(1 for s in self.stages if s.status == "completed")
        lines.append(f"Progress: {completed}/{len(self.stages)} stages completed")
        lines.append("")
        for s in self.stages:
            mark = {
                "pending": "·",
                "in_progress": "…",
                "completed": "✓",
            }.get(s.status, "?")
            sha = f" ({s.commit_sha[:7]})" if s.commit_sha else ""
            lines.append(f"- [{mark}] {s.step_id}/{s.stage}{sha}")
        # Rubric floor: 2 steps × 3 stages ⇒ 6 commits minimum.
        if completed < 6:
            lines.append("")
            lines.append(
                f"Note: loop.pdf expects ≥6 stage commits; currently {completed}."
            )
        return "\n".join(lines)

    def next_pending(self) -> Optional[StageState]:
        for s in self.stages:
            if s.status != "completed":
                return s
        return None

    def stages_using_loop(self) -> list[StageState]:
        """
        loop.pdf: must use a loop for at least one stage.
        By convention we use the PES loop for plan + build (like the class demo).
        """
        return [s for s in self.stages if s.stage in {"plan", "build"}]
