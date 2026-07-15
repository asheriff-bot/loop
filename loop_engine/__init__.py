"""
Loop Engineering Engine
=======================

Why this package exists
-----------------------
loop.pdf asks us to use "some loop engineering code" with an AI assistant to
build something nontrivial in staged commits. The class prototype used the
Ralph Wiggum loop; LoongFlow shows a stronger thinking pattern:
Plan → Execute → Summary (PES), with memory so later iterations improve.

This package is a from-scratch, coursework-sized PES loop:
  - structured enough to meet the assignment (stages, prompts, commits)
  - small enough to read, reason about, and modify without a research stack

Public entry points live in ``loop_engine.cli`` and ``loop.sh``.
"""

from .agent import PESAgent
from .config import load_config
from .models import CycleResult, Experience, StageState

__all__ = [
    "PESAgent",
    "load_config",
    "CycleResult",
    "Experience",
    "StageState",
]

__version__ = "0.1.0"
