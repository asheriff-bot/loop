# Spec: Locksmith — Extension (Hard Mode + Daily board)

## Problem

Extend the base Locksmith game with:

1. **Daily challenge** already wired in base UI — keep and document as part of extension surface: deterministic UTC-date code + mode-filtered scores.
2. **Hard mode**: longer code, wider digit alphabet, more guesses; separate scoreboard filter.

## Hard mode rules

| Param | Classic | Hard |
|-------|---------|------|
| Code length | 4 | 5 |
| Digits | 1–6 | 1–8 |
| Max guesses | 10 | 12 |
| Score (win) | `(11 - guesses) * 100` | `(13 - guesses) * 120` |

API: `POST /api/games` with `"mode": "hard"`.

UI: add a third radio **Hard**. Digit pad grows to 1–8; current guess shows 5 slots when mode is hard (read `code_length` from create response).

## Daily info endpoint

`GET /api/daily` → `{ "date": "YYYY-MM-DD", "mode": "daily" }` (does **not** reveal secret).

## Acceptance

1. Hard game playable end-to-end in browser.
2. `/api/scores?mode=hard` only lists hard wins.
3. `/api/daily` returns today's UTC date.
4. Tests cover hard create + win + daily endpoint.
