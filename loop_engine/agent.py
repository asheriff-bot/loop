"""
PESAgent — Plan → Execute → Evaluate → Summary orchestrator.

Engineer reasoning
------------------
LoongFlow inserts evaluation between execution and summarization so the loop
optimizes a measurable fitness, not vibes. We keep that shape:

    while not done and iteration < max:
        plan    = Planner.build(mode, memory)
        result  = Executor.run(plan)
        score   = LocksmithEvaluator.evaluate()   # EvalMetric S
        summary = Summarizer.summarize(result, score)
        stop if promise OR S >= target_score
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from . import git_ops
from .backends import get_backend
from .evaluator import LocksmithEvaluator, save_eval_report
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

        evolve = config["evolve"]
        self.max_iterations = int(evolve.get("max_iterations") or 10)
        self.checkpoint_interval = int(evolve.get("checkpoint_interval") or 0)
        self.target_score = float(evolve.get("target_score", 1.0))
        self.eval_enabled = bool(evolve.get("eval_enabled", True))
        self.eval_run_pytest = bool(evolve.get("eval_run_pytest", True))
        self.evaluator = LocksmithEvaluator(
            target_score=self.target_score,
            run_pytest=self.eval_run_pytest,
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
        """One Plan → Execute → Evaluate → Summary cycle."""
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"PES cycle  mode={mode}  iteration={iteration}  stage={stage}")
        print(f"memory size={self.memory.size}  backend={self.backend.__class__.__name__}")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        plan = self.planner.build(mode=mode, iteration=iteration, stage=stage)
        print("[pes] ▶ PLAN complete (prompt rendered + logged to prompts.txt)")

        execution = self.executor.run(plan)
        print("[pes] ▶ EXECUTE complete")

        evaluation = None
        if self.eval_enabled:
            evaluation = self.evaluator.evaluate()
            report_path = Path(self.config["evolve"]["workspace"]) / "evals" / (
                f"iter-{iteration:04d}.json"
            )
            save_eval_report(evaluation, report_path)
            print(evaluation.render())
            print(f"[pes] ▶ EVALUATE complete → {report_path}")

        summary = self.summarizer.summarize(
            iteration=iteration,
            stage=stage,
            execution=execution,
            evaluation=evaluation,
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
                print(f"[pes] push skipped: {exc}")

        # Done if agent promised completion *or* eval met the target (automation stop).
        done = summary.done
        if evaluation is not None and evaluation.met_target:
            done = True

        return CycleResult(
            iteration=iteration,
            mode=mode,
            plan_text=plan.prompt,
            execute_text=execution.response.output,
            summary_text=summary.text,
            done=done,
            experience=summary.experience,
            raw_agent_output=execution.response.output,
            eval_score=evaluation.score if evaluation else None,
            eval_met_target=evaluation.met_target if evaluation else None,
        )

    def run_loop(
        self,
        mode: str,
        stage: str,
        max_iterations: Optional[int] = None,
        stop_on_promise: bool = True,
        stop_on_target_score: bool = True,
    ) -> list[CycleResult]:
        """
        Outer loop: repeat PES cycles until completion promise, max iterations,
        or EvalMetric reaches target_score.
        """
        limit = max_iterations if max_iterations is not None else self.max_iterations
        unlimited = limit == 0
        results: list[CycleResult] = []
        iteration = 1

        while True:
            if not unlimited and iteration > limit:
                print(f"[pes] Reached max iterations: {limit}")
                break

            result = self.run_cycle(mode=mode, iteration=iteration, stage=stage)
            results.append(result)

            if stop_on_target_score and result.eval_met_target:
                print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                print(
                    f"✓ EvalMetric target met: S={result.eval_score:.4f} "
                    f">= {self.target_score:.2f}"
                )
                print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                break

            if stop_on_promise and result.done and result.eval_met_target is not False:
                # When eval is enabled and target missed, keep looping even if
                # dry_run emitted DONE — fitness drives automation.
                if not self.eval_enabled or result.eval_met_target:
                    promise = self.config["evolve"].get("completion_promise", "DONE")
                    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                    print(f"✓ Completion promise found: '{promise}'")
                    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                    break

            iteration += 1
            print(f"\n\n======================== LOOP {iteration} ========================\n")

        return results

    def run_eval_only(self):
        """Standalone EvalMetric without an agent turn."""
        result = self.evaluator.evaluate()
        report_path = Path(self.config["evolve"]["workspace"]) / "evals" / "manual.json"
        save_eval_report(result, report_path)
        print(result.render())
        print(f"[eval] report → {report_path}")
        return result
