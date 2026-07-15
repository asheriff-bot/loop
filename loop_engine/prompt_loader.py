"""
Prompt file loading and variable substitution.

Engineer reasoning
------------------
Ralph's loop concatenates a whole markdown prompt file into the agent CLI.
That works. We keep the same idea, but add ``{{variable}}`` slots for goal,
memory, stage, and iteration — so one prompt template stays accurate as the
run progresses without editing markdown by hand every loop.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Mapping

ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = ROOT / "prompts"

_VAR_RE = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")


def load_prompt(name: str, variables: Mapping[str, str] | None = None) -> str:
    """
    Load ``prompts/<name>.md`` (or an absolute/relative path) and substitute
    ``{{vars}}``. Unknown variables are left untouched so a missing key doesn't
    silently delete instruction text.
    """
    path = Path(name)
    if not path.suffix:
        path = PROMPTS_DIR / f"{name}.md"
    elif not path.is_absolute() and not path.exists():
        candidate = PROMPTS_DIR / path.name
        if candidate.exists():
            path = candidate

    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")

    text = path.read_text(encoding="utf-8")
    if not variables:
        return text

    def repl(match: re.Match[str]) -> str:
        key = match.group(1)
        return variables.get(key, match.group(0))

    return _VAR_RE.sub(repl, text)


def append_to_prompts_log(prompt_text: str, log_path: Path | None = None) -> None:
    """
    loop.pdf requires ``prompts.txt`` containing every command/prompt given to
    an agent. Append rather than overwrite so the artifact is the full history.
    """
    log = log_path or (ROOT / "prompts.txt")
    separator = "\n" + ("=" * 72) + "\n"
    header = f"# Prompt captured at loop iteration\n"
    with log.open("a", encoding="utf-8") as fh:
        fh.write(separator)
        fh.write(header)
        fh.write(prompt_text.rstrip() + "\n")
