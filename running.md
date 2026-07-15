# running.md — how to run Locksmith

## Prerequisites

- Python 3.11+ (conda env `loop` recommended)
- pip packages from `requirements.txt`

```bash
cd /path/to/Assign-4
conda activate loop          # optional but recommended
pip install -r requirements.txt
```

## Start the game server

```bash
chmod +x script/server loop.sh
./script/server
# equivalent: PYTHONPATH=. python -m game.app
```

Open in a browser:

**http://127.0.0.1:5055/**

You should see the **Locksmith** UI.

## How a TA can play (2 minutes)

1. Enter a player name.
2. Choose **Classic** (or **Daily challenge** / **Hard** after extension).
3. Click **Start game**.
4. Click digits on the pad to fill 4 (or 5 in hard) slots → **Submit guess**.
5. Use Exact / Partial pegs to refine guesses (max 10 classic / 12 hard).
6. On a win, your score appears under **High scores** (SQLite-backed; survives restart).

## Quick API checks

```bash
curl -s http://127.0.0.1:5055/api/health
curl -s -X POST http://127.0.0.1:5055/api/games \
  -H 'Content-Type: application/json' \
  -d '{"player_name":"TA","mode":"classic"}'
```

## Tests

```bash
pip install pytest
PYTHONPATH=. pytest tests/ -q
```

## Loop engineering (process tooling)

```bash
./loop.sh -m plan --backend echo -n 1
python -m loop_engine stage status
```

## EvalMetric (backend automation score)

Composite fitness (LoongFlow-style), each term in `[0, 1]`:

```
S = 0.30·L + 0.25·A + 0.15·M + 0.20·T + 0.10·P
```

| Symbol | Component | What it measures |
|--------|-----------|------------------|
| L | logic_correctness | Mastermind / scoring properties |
| A | api_contract | Flask routes, secret hiding, win path |
| M | mode_coverage | classic / daily / hard shapes |
| T | test_suite | pytest pass rate |
| P | persistence | scores survive “restart” (same DB) |

```bash
./script/eval                 # print S + component breakdown
./loop.sh automate -n 3       # PES build loop gated on target_score (default 1.0)
```

Reports land in `.loop_workspace/evals/`.

Default game port: **5055** (override with `PORT=...`).
