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

Default game port: **5055** (override with `PORT=...`).
