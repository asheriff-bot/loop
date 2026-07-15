"""
Smoke tests for the PES loop engine.

Engineer reasoning
------------------
If the loop itself is buggy, every product iteration sits on sand. These tests
stay offline (dry_run backend) so CI/homework can run without API keys.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from loop_engine.agent import PESAgent
from loop_engine.config import load_config
from loop_engine.memory import ExperientialMemory
from loop_engine.models import Experience
from loop_engine.prompt_loader import load_prompt
from loop_engine.stages import StageTracker


@pytest.fixture()
def tmp_config(tmp_path: Path) -> dict:
    cfg = load_config()
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    cfg["evolve"]["workspace"] = str(workspace)
    cfg["evolve"]["memory_file"] = str(workspace / "memory.json")
    cfg["evolve"]["stage_log"] = str(workspace / "stages.json")
    cfg["evolve"]["max_iterations"] = 2
    cfg["evolve"]["checkpoint_interval"] = 1
    cfg["agent"]["backend"] = "dry_run"
    cfg["git"]["commit_on_stage"] = False
    cfg["git"]["push_on_iteration"] = False
    return cfg


def test_prompt_substitution():
    text = load_prompt(
        "PROMPT_plan",
        {
            "goal": "Ship a demo",
            "mode": "plan",
            "stage": "plan",
            "iteration": "1",
            "memory": "No memory",
            "completion_promise": "DONE",
        },
    )
    assert "Ship a demo" in text
    assert "{{goal}}" not in text
    assert "<promise>DONE</promise>" in text


def test_memory_roundtrip(tmp_path: Path):
    path = tmp_path / "mem.json"
    mem = ExperientialMemory(path)
    mem.add(
        Experience(
            iteration=1,
            stage="build",
            plan_summary="plan",
            execution_summary="exec",
            reflection="ok",
            success=True,
            lessons=["write tests first"],
        )
    )
    mem2 = ExperientialMemory(path)
    assert mem2.size == 1
    assert "write tests first" in mem2.context_for_planner()


def test_pes_loop_dry_run_stops_on_promise(tmp_config: dict):
    agent = PESAgent(tmp_config)
    results = agent.run_loop(mode="build", stage="build", max_iterations=5)
    # dry_run always emits the completion promise → one cycle should suffice
    assert len(results) == 1
    assert results[0].done is True
    assert agent.memory.size >= 1
    # checkpoint_interval=1 → a checkpoint directory should exist
    ck = Path(tmp_config["evolve"]["workspace"]) / "checkpoints"
    assert ck.exists()
    assert any(ck.iterdir())


def test_stage_tracker_progress(tmp_config: dict):
    tracker = StageTracker(
        tmp_config["evolve"]["stage_log"], tmp_config["assignment"]
    )
    assert len(tracker.stages) >= 6  # 2 steps × ≥3 stages
    first = tracker.next_pending()
    assert first is not None
    tracker.start(first.step_id, first.stage)
    tracker.complete(first.step_id, first.stage, notes="test", commit=False)
    raw = json.loads(Path(tmp_config["evolve"]["stage_log"]).read_text())
    assert raw["stages"][0]["status"] == "completed"
