"""
PESAgent — Plan → Execute → Summary orchestrator.

Engineer reasoning
------------------
LoongFlow's PESAgent runs concurrent evolutionary islands with evaluators and
checkpoints. For assignment loop engineering we want the *same thinking shape*
without the research-platform weight:

    while not done and iteration < max:
        plan    = Planner.build(mode, memory)
        result  = Executor.run(plan)          # coding agent does the work
        summary = Summarizer.summarize(result)
        memory.add(summary.experience)
        maybe checkpoint / push

That loop *is* the product we're shipping for loop.pdf's "use a loop" clause.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from . import git_ops
from .backends import get_backend
from .executor import Executor
from .memory import ExperientialMemory
from .models import CycleResult
from .planner import Planner
from .summarizer import Summarizer


class PESAgent:
    def __init__(self, config: dict[str, Any]):
        self.config = config
        workspace = Path(config["evolve"]["workspace"])
        workspace.mkdir(parents=True, exist_ok=True)

        self.memory = ExperientialMemory(config["evolve"]["memory_file"])
        backend_name = config.get("agent", {}).get("backend", "dry_run")
        self.backend = get_backend(backend_name)
        self.planner = Planner(config, self.memory)
        self.executor = Executor(config, self.backend)
        self.summarizer = Summarizer(config, self.memory)

        self.max_iterations = int(config["evolve"].get("max_iterations") or 10)
        self.checkpoint_interval = int(
            config["evolve"].get("checkpoint_interval") or 0
        )
        self.push_on_iteration = bool(
            config.get("git", {}).get("push_on_iteration", False)
        )
        self.remote = config.get("git", {}).get("remote", "origin")
        self._completed_cycles = 0

    def run_cycle(
        self,
        mode: str,
        iteration: int,
        stage: str,
    ) -> CycleResult:
        """One PES cycle. Keep side effects (memory, files) inside summarizer."""
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"PES cycle  mode={mode}  iteration={iteration}  stage={stage}")
        print(f"memory size={self.memory.size}  backend={self.backend.__class__.__name__}")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        plan = self.planner.build(mode=mode, iteration=iteration, stage=stage)
        # Explicit phase labels make logs greppable when a run goes sideways.
        print("[pes] ▶ PLAN complete (prompt rendered + logged to prompts.txt)")

        execution = self.executor.run(plan)
        print("[pes] ▶ EXECUTE complete")

        summary = self.summarizer.summarize(
            iteration=iteration, stage=stage, execution=execution
        )
        print("[pes] ▶ SUMMARY complete (memory updated)")

        self._completed_cycles += 1
        if (
            self.checkpoint_interval > 0
            and self._completed_cycles % self.checkpoint_interval == 0
        ):
            ck_root = Path(self.config["evolve"]["workspace"]) / "checkpoints"
            name = f"checkpoint-iter-{iteration}-{self._completed_cycles}"
            path = self.memory.checkpoint(ck_root, name)
            print(f"[pes] checkpoint saved → {path}")

        if self.push_on_iteration:
            try:
                git_ops.push_current(self.remote)
            except RuntimeError as exc:
                # Don't kill a good local cycle because remotes are flaky.
                print(f"[pes] push skipped: {exc}")

        return CycleResult(
            iteration=iteration,
            mode=mode,
            plan_text=plan.prompt,
            execute_text=execution.response.output,
            summary_text=summary.text,
            done=summary.done,
            experience=summary.experience,
            raw_agent_output=execution.response.output,
        )

    def run_loop(
        self,
        mode: str,
        stage: str,
        max_iterations: Optional[int] = None,
        stop_on_promise: bool = True,
    ) -> list[CycleResult]:
        """
        Ralph-style outer loop: repeat PES cycles until completion promise or
        max iterations. This is what ``loop.sh`` / ``python -m loop_engine`` call.
        """
        limit = max_iterations if max_iterations is not None else self.max_iterations
        # 0 means unlimited — mirror loop.sh semantics from the class tutorial.
        unlimited = limit == 0
        results: list[CycleResult] = []
        iteration = 1

        while True:
            if not unlimited and iteration > limit:
                print(f"[pes] Reached max iterations: {limit}")
                break

            result = self.run_cycle(mode=mode, iteration=iteration, stage=stage)
            results.append(result)

            if stop_on_promise and result.done:
                promise = self.config["evolve"].get("completion_promise", "DONE")
                print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                print(f"✓ Completion promise found: '{promise}'")
                print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                break

            iteration += 1
            print(f"\n\n======================== LOOP {iteration} ========================\n")

        return results
