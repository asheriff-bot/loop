"""
Executor worker (PES — Execute).

Engineer reasoning
------------------
Execution is where the agent touches the repo: implement, test, commit a unit
of work. In LoongFlow this is a registered Executor worker with an evaluator.
Here, execution *is* invoking the coding-agent backend with the planner's
prompt. Keeping this class thin makes the orchestration graph obvious.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .backends import AgentBackend, AgentResponse
from .planner import PlanArtifact


@dataclass
class ExecutionArtifact:
    response: AgentResponse
    plan: PlanArtifact


class Executor:
    def __init__(self, config: dict[str, Any], backend: AgentBackend):
        self.config = config
        self.backend = backend

    def run(self, plan: PlanArtifact) -> ExecutionArtifact:
        print(
            f"[executor] Invoking backend={self.backend.__class__.__name__} "
            f"mode={plan.mode}"
        )
        response = self.backend.run(plan.prompt, self.config)
        return ExecutionArtifact(response=response, plan=plan)
