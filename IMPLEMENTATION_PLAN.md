# Implementation Plan — Locksmith

## Overall status

- [x] Loop engineering engine (PES)
- [x] Step 1 — Base system (Locksmith classic + UI + SQLite)
- [x] Step 2 — Extension (daily endpoint + hard mode) — in build

---

## Step 1 — Base system — DONE

Build backlog all completed (logic, db, Flask API, UI, tests, server script).

---

## Step 2 — Extension

### Stages

1. [x] specify
2. [x] review
3. [ ] plan *(PES loop)*
4. [ ] build *(PES loop)*

### Build backlog

1. [ ] ModeConfig for classic/daily/hard in `game/logic.py`
2. [ ] `GET /api/daily` (date only, no secret)
3. [ ] Hard create/guess scoring path in `game/app.py`
4. [ ] UI: Hard radio + dynamic pad/slots from API metadata
5. [ ] Tests for hard win + daily endpoint
6. [ ] Update running.md / AGENTS.md

### Review notes (step2_extension / review)

- Hard mode params are clear and testable.
- UI must rebuild digit pad from `code_length` / digit max returned by create.
- Daily endpoint must not leak secret.
