"""
CLI for the loop engineering engine.

Engineer reasoning
------------------
Two entry shapes matter for this class:

1. ``./loop.sh -m plan -n 5``  — familiar to anyone who saw the ralph tutorial
2. ``python -m loop_engine …`` — better for tests, staging commands, status

This module owns (2); ``loop.sh`` is a thin wrapper that calls into here so we
don't maintain two divergent parsers.
"""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from .agent import PESAgent
from .config import load_config
from .stages import StageTracker


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="loop_engine",
        description=(
            "Loop Engineering CLI — Plan-Execute-Summary agent loop "
            "(LoongFlow-inspired, coursework-sized)."
        ),
    )
    parser.add_argument(
        "-c",
        "--config",
        default=None,
        help="Path to config.yaml (default: ./config.yaml)",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # --- run: the PES loop itself ---
    run_p = sub.add_parser("run", help="Run the PES loop for a mode/stage")
    run_p.add_argument(
        "-m",
        "--mode",
        default="build",
        choices=["plan", "build", "execute", "specify", "review", "summary"],
        help="Which prompt/mode to run (default: build)",
    )
    run_p.add_argument(
        "-n",
        "--max",
        type=int,
        default=None,
        help="Max iterations; 0 = unlimited; default from config",
    )
    run_p.add_argument(
        "--stage",
        default=None,
        help="Assignment stage label (default: same as mode)",
    )
    run_p.add_argument(
        "--backend",
        default=None,
        choices=["dry_run", "echo", "copilot"],
        help="Override agent.backend from config",
    )
    run_p.add_argument(
        "--no-stop",
        action="store_true",
        help="Do not stop when the completion promise appears",
    )

    # --- stage: assignment rubric helpers ---
    stage_p = sub.add_parser("stage", help="Manage assignment stages / commits")
    stage_sub = stage_p.add_subparsers(dest="stage_cmd", required=True)

    stage_sub.add_parser("status", help="Show stage completion status")

    start_p = stage_sub.add_parser("start", help="Mark a stage in_progress")
    start_p.add_argument("step_id")
    start_p.add_argument("stage")

    complete_p = stage_sub.add_parser(
        "complete", help="Mark stage complete and git-commit"
    )
    complete_p.add_argument("step_id")
    complete_p.add_argument("stage")
    complete_p.add_argument("--notes", default="")
    complete_p.add_argument(
        "--no-commit",
        action="store_true",
        help="Update tracker without creating a git commit",
    )

    next_p = stage_sub.add_parser("next", help="Show the next pending stage")
    # argparse needs the parser object even if unused — keeps API parallel.
    _ = next_p

    # --- memory ---
    mem_p = sub.add_parser("memory", help="Inspect experiential memory")
    mem_p.add_argument(
        "--recent", type=int, default=5, help="How many experiences to show"
    )

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = load_config(args.config)

    if args.command == "run":
        if args.backend:
            config["agent"]["backend"] = args.backend
        stage = args.stage or args.mode
        agent = PESAgent(config)
        agent.run_loop(
            mode=args.mode,
            stage=stage,
            max_iterations=args.max,
            stop_on_promise=not args.no_stop,
        )
        return 0

    tracker = StageTracker(config["evolve"]["stage_log"], config["assignment"])

    if args.command == "stage":
        if args.stage_cmd == "status":
            print(tracker.status_report())
            return 0
        if args.stage_cmd == "start":
            tracker.start(args.step_id, args.stage)
            return 0
        if args.stage_cmd == "complete":
            commit = (not args.no_commit) and config.get("git", {}).get(
                "commit_on_stage", True
            )
            tracker.complete(
                args.step_id,
                args.stage,
                notes=args.notes,
                commit=commit,
            )
            print(tracker.status_report())
            return 0
        if args.stage_cmd == "next":
            nxt = tracker.next_pending()
            if not nxt:
                print("All stages completed.")
            else:
                print(f"Next: {nxt.step_id}/{nxt.stage} (status={nxt.status})")
            return 0

    if args.command == "memory":
        agent = PESAgent(config)
        print(agent.memory.context_for_planner(n=args.recent))
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
