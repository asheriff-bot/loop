# Implementation Plan — Locksmith

## Overall status

- [x] Loop engineering engine (PES)
- [ ] Step 1 — Base system (Locksmith)
- [ ] Step 2 — Extension (daily challenge + leaderboard)

---

## Step 1 — Base system

### Stages

1. [x] specify
2. [x] review
3. [ ] plan *(PES loop)*
4. [ ] build *(PES loop)*

### Build backlog (priority order)

1. [ ] `game/logic.py` — `evaluate_guess(secret, guess)` Mastermind rules + score helper; unit tests for duplicates
2. [ ] `game/db.py` — SQLite schema, create game, add guess, list top scores
3. [ ] `game/app.py` — Flask routes per `specs/01-locksmith-base.md` on port **5055**
4. [ ] `game/static/` + `game/templates/index.html` — playable UI (name, digit pad, history, scores)
5. [ ] `tests/test_game_logic.py` + `tests/test_api.py` — logic + API happy/error paths
6. [ ] `script/server` + update `requirements.txt` (Flask) + `AGENTS.md` run notes
7. [ ] Manual play smoke: win path + lose path + score persists after restart

### Review notes (step1_base)

- Spec OK; enforce multiset exact-then-partial marking; never leak secret while active.

---

## Step 2 — Extension

### Stages

1. [ ] specify
2. [ ] review
3. [ ] plan *(PES loop)*
4. [ ] build *(PES loop)*

### Build backlog

- [ ] TBD after step2 specify
