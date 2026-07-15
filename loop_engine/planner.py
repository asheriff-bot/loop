"""
Planner worker (PES — Plan).

Engineer reasoning
------------------
Blind generation is how agents thrash. The planner's job is narrow on purpose:
understand the goal + specs + memory, then emit a deliberate next-action
blueprint. It must NOT implement — that temptation is why Ralph separates
PROMPT_plan.md from PROMPT_build.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .memory import ExperientialMemory
from .prompt_loader import append_to_prompts_log, load_prompt


@dataclass
class PlanArtifact:
    prompt: str
    mode: str
    memory_context: str


class Planner:
    """Build the planning prompt for a given mode/stage."""

    # Map assignment/classroom modes onto prompt templates.
    MODE_PROMPT = {
        "plan": "PROMPT_plan",
        "build": "PROMPT_build",
        "execute": "PROMPT_execute",
        "specify": "PROMPT_specify",
        "review": "PROMPT_review",
        "summary": "PROMPT_summary",
    }

    def __init__(self, config: dict[str, Any], memory: ExperientialMemory):
        self.config = config
        self.memory = memory

    def build(self, mode: str, iteration: int, stage: str) -> PlanArtifact:
        goal = self.config.get("project", {}).get("goal", "").strip()
        memory_context = self.memory.context_for_planner(n=5)
        prompt_name = self.MODE_PROMPT.get(mode, "PROMPT_build")

        variables = {
            "goal": goal,
            "mode": mode,
            "stage": stage,
            "iteration": str(iteration),
            "memory": memory_context,
            "completion_promise": self.config["evolve"].get(
                "completion_promise", "DONE"
            ),
        }
        prompt = load_prompt(prompt_name, variables)

        # Always archive what we ask the agent — prompts.txt is a deliverable.
        append_to_prompts_log(prompt)

        return PlanArtifact(prompt=prompt, mode=mode, memory_context=memory_context)
