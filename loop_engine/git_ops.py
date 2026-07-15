"""
Git helpers for stage-aligned commits.

Engineer reasoning
------------------
loop.pdf: "commit the state of your repository after every stage of every
step" (≥6 commits). Automating the commit *message shape* reduces the chance
we forget a stage boundary. We still won't invent secrets or force-push —
just ``add`` + ``commit`` with a conventional message.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional


ROOT = Path(__file__).resolve().parent.parent


def _run(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=check,
    )


def current_branch() -> str:
    proc = _run(["git", "branch", "--show-current"], check=False)
    return (proc.stdout or "").strip() or "HEAD"


def head_sha() -> Optional[str]:
    proc = _run(["git", "rev-parse", "HEAD"], check=False)
    if proc.returncode != 0:
        return None
    return proc.stdout.strip()


def working_tree_dirty() -> bool:
    proc = _run(["git", "status", "--porcelain"], check=False)
    return bool((proc.stdout or "").strip())


def commit_stage(step_id: str, stage: str, notes: str = "") -> Optional[str]:
    """
    Stage all tracked/untracked changes and commit with a rubric-friendly message.

    Returns the new commit SHA, or None if there was nothing to commit.
    """
    if not working_tree_dirty():
        print(f"[git] Nothing to commit for {step_id}/{stage} (tree clean).")
        return head_sha()

    _run(["git", "add", "-A"])
    message = f"stage({step_id}): {stage}"
    if notes:
        message = f"{message}\n\n{notes}"

    # HEREDOC equivalent via multiple -m keeps hooks happy without a shell.
    proc = _run(["git", "commit", "-m", message], check=False)
    if proc.returncode != 0:
        # Might fail if user.name/email unset — surface stderr clearly.
        raise RuntimeError(
            "git commit failed.\n"
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    sha = head_sha()
    print(f"[git] Committed {step_id}/{stage} → {sha}")
    return sha


def push_current(remote: str = "origin") -> None:
    branch = current_branch()
    proc = _run(["git", "push", remote, branch], check=False)
    if proc.returncode != 0:
        print(f"[git] push failed; attempting upstream create for {branch}…")
        proc2 = _run(["git", "push", "-u", remote, branch], check=False)
        if proc2.returncode != 0:
            raise RuntimeError(
                "git push failed.\n"
                f"stderr:\n{proc2.stderr or proc.stderr}"
            )
    print(f"[git] Pushed {branch} to {remote}")
