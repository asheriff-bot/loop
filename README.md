# Assign-4 — Locksmith + Loop Engineering (PES)

**Play the game:** `./script/server` → [http://127.0.0.1:5055/](http://127.0.0.1:5055/)

Mastermind-style **Locksmith** (Flask + SQLite) built with from-scratch
**Plan–Execute–Summary** loop engineering code for CMU DevOps `loop.pdf`,
inspired by [LoongFlow](https://github.com/baidu-baige/LoongFlow) and the
classroom [Ralph Wiggum tutorial](https://github.com/gwincr11/ralph-wiggum-tutorial).

## Why this shape?

| Source | Idea we kept |
|--------|----------------|
| **loop.pdf** | AI + loop → nontrivial product; 2 steps × ≥3 stages; loop ≥1 stage; stage commits; `prompts.txt` / `running.md` / `reflection.md` |
| **Ralph loop** | `./loop.sh -m plan\|build`, prompt files, stop on completion promise |
| **LoongFlow PES** | Explicit Plan → Execute → Summary + experiential memory (simplified, coursework-sized) |

Expert performance comes from better **thinking**, not denser retries.

```
┌──────────────────────────────────────────────┐
│                 PESAgent.run_loop            │
│                                              │
│   ┌────────┐   ┌──────────┐   ┌──────────┐   │
│   │  Plan  │──▶│ Execute  │──▶│ Summary  │   │
│   │ prompt │   │  agent   │   │ memory   │   │
│   └────────┘   └──────────┘   └────┬─────┘   │
│        ▲                           │         │
│        └───────── next iter ───────┘         │
│              until <promise>DONE</promise>   │
└──────────────────────────────────────────────┘
```

## Quick start

```bash
conda activate loop   # optional
pip install -r requirements.txt pytest
chmod +x loop.sh

# Offline smoke test (no LLM)
./loop.sh -m build --backend dry_run -n 1
pytest tests/ -q
python -m loop_engine stage status
```

## Layout

```
loop.sh                 # thin CLI (ralph-compatible flags)
config.yaml             # project goal, stages, backends
loop_engine/            # PES implementation + reasoning comments
prompts/                # mode prompt templates
specs/                  # product + rubric specs
tests/                  # offline unit tests
prompts.txt             # auto-appended agent prompt history
running.md              # how a TA runs things
reflection.md           # SE reflection paragraph
IMPLEMENTATION_PLAN.md  # living plan the loop updates
AGENTS.md               # operational agent notes
```

## Assignment workflow

See `specs/00-assignment-rubric.md` and `running.md`. Short version:

1. `stage start/complete` around **specify → review → plan → build** for `step1_base`
2. Use `./loop.sh -m plan` / `./loop.sh -m build` for the looped stages
3. Repeat for `step2_extension`
4. Keep `prompts.txt`, `running.md`, `reflection.md` current

## Agent backends

| Backend | Use when |
|---------|----------|
| `dry_run` | Testing the loop itself (default) |
| `echo` | Write prompt to `.loop_workspace/next_prompt.md` for manual paste |
| `copilot` | GitHub Copilot CLI (class tutorial) |
| `cursor` | Cursor Agent CLI if available |

```bash
./loop.sh -m plan --backend echo -n 1
./loop.sh -m build --backend copilot
```

## License / provenance

Original coursework code. Concepts referenced from LoongFlow (Apache-2.0) and
the Ralph Wiggum loop pattern; this tree is **not** a fork of either repo.
