# AGENTS.md — operational reference for coding agents

Keep this file **short and operational**. Progress/status belongs in `IMPLEMENTATION_PLAN.md`.

## Project

- Loop engine package: `loop_engine/`
- Config: `config.yaml`
- Prompt templates: `prompts/`
- Specs for the product under construction: `specs/`
- Runtime state: `.loop_workspace/` (gitignored)

## Commands

```bash
# Setup
conda activate loop          # or: python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install pytest           # for tests

# Smoke-test the loop without an LLM
./loop.sh -m build --backend dry_run -n 1
python -m loop_engine run -m plan --backend dry_run -n 1

# Assignment stage tracker
python -m loop_engine stage status
python -m loop_engine stage start step1_base specify
python -m loop_engine stage complete step1_base specify --notes "specs draft v1"

# Real agent backends (when installed + authenticated)
./loop.sh -m plan --backend copilot -n 3
./loop.sh -m build --backend cursor

# Inspect memory
python -m loop_engine memory --recent 5

# Unit tests (offline)
pytest tests/ -q
```

## Modes ↔ prompts

| Mode | Prompt | Intent |
|------|--------|--------|
| specify | `prompts/PROMPT_specify.md` | Write specs only |
| review | `prompts/PROMPT_review.md` | Critique specs/plan |
| plan | `prompts/PROMPT_plan.md` | Update IMPLEMENTATION_PLAN only |
| build / execute | `prompts/PROMPT_build.md` / `PROMPT_execute.md` | Implement + test + commit |
| summary | `prompts/PROMPT_summary.md` | Reflect + lessons |

## Completion promise

Default stop token: `DONE` (also accepted as `<promise>DONE</promise>`).

## Ports / product app (Locksmith)

- Start: `./script/server` or `PYTHONPATH=. python -m game.app`
- URL: `http://127.0.0.1:5055/`
- DB: `game/data/locksmith.db` (gitignored; auto-created)
- Package: `game/` (`logic.py`, `db.py`, `app.py`, `daily.py`, `static/`, `templates/`)
- Tests: `PYTHONPATH=. pytest tests/ -q`
