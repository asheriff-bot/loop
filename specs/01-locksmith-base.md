# Spec: Locksmith — Base System

## Problem

Build a small browser game, **Locksmith**, where the player cracks a secret
numeric lock code. Feedback follows Mastermind rules. Game logic and scoring
live on a **Python Flask backend** with SQLite persistence — not only in the
browser.

This is intentionally **not** a Space Invaders clone (class demo).

## Non-goals (base)

- Real-time multiplayer / websockets
- Accounts / OAuth
- Mobile-native apps
- Sound effects / sprite assets

## Gameplay

- Secret code: length **4**, each digit in **1–6** (repeats allowed).
- Player has **10 guesses**.
- After each guess the server returns:
  - `exact`: correct digit in correct position
  - `partial`: correct digit in wrong position (Mastermind “white peg” rules)
- Win: all 4 exact before guesses run out.
- Lose: 10 incorrect/incomplete guesses.
- Score (wins only): `max(0, (10 - guesses_used) * 100 + exact_bonus)` where
  `exact_bonus` is unused for v1 simplicity → score = `(11 - guesses_used) * 100`
  so a win in 1 guess = 1000, in 10 guesses = 100.

## Backend API

Base URL: `http://127.0.0.1:5055`

| Method | Path | Body | Result |
|--------|------|------|--------|
| GET | `/` | — | Serve interactive game UI |
| GET | `/api/health` | — | `{ "ok": true }` |
| POST | `/api/games` | `{ "player_name": str }` | Create game; `{ game_id, max_guesses, code_length }` |
| GET | `/api/games/<id>` | — | Public state (never the secret): status, guesses, feedback |
| POST | `/api/games/<id>/guess` | `{ "guess": [d,d,d,d] }` | Feedback + updated status; on win include `score` |
| GET | `/api/scores` | — | Top scores `{ scores: [...] }` (best 10) |

### Rules the server must enforce

- Reject guesses with wrong length or digits outside 1–6 (HTTP 400).
- Reject guesses on finished games (HTTP 409).
- **Never** return the secret code until the game is won or lost (then may include `secret` for learning).

## Data

SQLite file: `game/data/locksmith.db`

Tables:

- `games(id, player_name, secret, status, guesses_used, score, created_at, finished_at)`
- `guesses(id, game_id, guess_json, exact, partial, created_at)`

## Frontend

Single page served by Flask:

- Enter player name → Start
- Click/tap 4 digits (palette 1–6) → Submit guess
- History of prior guesses with exact/partial badges
- Remaining guesses + win/lose banner
- Sidebar/panel: recent high scores from `/api/scores`
- Works on desktop browsers without a build step (vanilla JS + CSS)

## Acceptance criteria

1. `python -m game.app` (or `./script/server`) serves on **port 5055**.
2. A TA can play a full win and a full loss in the browser.
3. High scores persist across server restarts.
4. Unit tests cover Mastermind feedback + API create/guess happy paths.
5. Secret is not leaked in `GET /api/games/<id>` while `status == "active"`.
