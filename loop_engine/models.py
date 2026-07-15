"""
Shared datatypes for the loop.

Engineer reasoning
------------------
I want every stage boundary to produce something we can serialize, commit, and
re-read later. Plain dicts work until the third iteration, then you forget
which keys exist. Small dataclasses keep the contract visible.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from datetime import datetime, timezone
from typing import Any, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Experience:
    """
    One distilled lesson from a PES cycle.

    LoongFlow stores richer evolutionary memory (islands, MAP-Elites). For this
    assignment we keep a lightweight "what worked / what failed / what next"
    record — enough to stop the agent from repeating the same mistake.
    """

    iteration: int
    stage: str
    plan_summary: str
    execution_summary: str
    reflection: str
    success: bool
    lessons: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now_iso)
    # EvalMetric composite score S ∈ [0,1] from LocksmithEvaluator (optional).
    eval_score: Optional[float] = None
    eval_feedback: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Experience":
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass
class CycleResult:
    """Outcome of one Plan → Execute → Summary cycle."""

    iteration: int
    mode: str
    plan_text: str
    execute_text: str
    summary_text: str
    done: bool
    experience: Optional[Experience] = None
    raw_agent_output: str = ""
    eval_score: Optional[float] = None
    eval_met_target: Optional[bool] = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        return payload


@dataclass
class StageState:
    """
    Tracks assignment stage progress for loop.pdf compliance.

    Rubric interpretation: 2 steps × ≥3 stages, commit after every stage.
    We record timestamps so the TA can see the process, not just the product.
    """

    step_id: str
    stage: str
    status: str = "pending"  # pending | in_progress | completed
    commit_sha: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StageState":
        return cls(**data)
