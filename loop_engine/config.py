"""
Configuration loading.

Engineer reasoning
------------------
YAML over argparse-only: instructors (and future-me) can diff a config change
in git. CLI flags still override for one-off experiments — see ``cli.py``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = ROOT / "config.yaml"


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """Load YAML config and ensure required sections exist with sane defaults."""
    config_path = Path(path) if path else DEFAULT_CONFIG_PATH
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}

    # Defensive defaults — a missing section shouldn't crash mid-loop.
    data.setdefault("project", {})
    data.setdefault("assignment", {"steps": []})
    data.setdefault(
        "evolve",
        {
            "max_iterations": 10,
            "completion_promise": "DONE",
            "checkpoint_interval": 2,
            "workspace": ".loop_workspace",
            "memory_file": ".loop_workspace/experiential_memory.json",
            "stage_log": ".loop_workspace/stage_log.json",
        },
    )
    data.setdefault(
        "agent",
        {
            "backend": "dry_run",
            "model": "claude-opus-4.8",
            "allow_all_tools": True,
            "timeout_seconds": 0,
        },
    )
    data.setdefault(
        "git",
        {
            "commit_on_stage": True,
            "push_on_iteration": False,
            "remote": "origin",
        },
    )

    # Resolve workspace paths relative to repo root so cwd doesn't matter.
    evolve = data["evolve"]
    for key in ("workspace", "memory_file", "stage_log"):
        p = Path(evolve[key])
        if not p.is_absolute():
            evolve[key] = str((ROOT / p).resolve())

    data["_root"] = str(ROOT)
    data["_config_path"] = str(config_path.resolve())
    return data
