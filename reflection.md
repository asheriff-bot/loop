# reflection.md

## How the backend was built

I treated Locksmith as a thin but honest server, not a browser toy. The order
mattered: Mastermind rules first (`game/logic.py`), then SQLite persistence
(`game/db.py`), then Flask routes (`game/app.py`) that only expose public game
state. Secrets live on the server until a game is won or lost; guesses are
validated for length and digit range before scoring. Modes (classic / daily /
hard) ended up as a single `ModeConfig` map so create/guess/score/UI all read
the same numbers instead of drifting. The PES loop stages (specify → review →
plan → build, then the extension pass) forced that sequence into commits and
`prompts.txt`, which is useful when you come back later and need to remember
*why* an endpoint looks the way it does.

## Issues seen

1. **Process ahead of product.** The first `specify` commit mostly captured loop
   scaffolding. Product specs for Locksmith were still thin, so review had to
   absorb real requirements (`specs/01-locksmith-base.md`) before plan/build
   could mean anything.
2. **Loop plumbing bugs while dogfooding.** `loop.sh` blew up on an empty
   `EXTRA` array under `set -u`. Separately, the script preferred system
   `python3` over the conda `loop` env, so `PyYAML` was “missing” even after
   pip install. The Cursor agent backend also treated `-p` as “prompt follows,”
   but in the current CLI `-p` means `--print` — prompts are positional.
3. **Duplicate-digit Mastermind.** Naive exact/partial counting double-counts
   when the secret or guess repeats digits. That is a quiet correctness bug you
   only notice with targeted tests.
4. **Extension creeping into base.** Daily mode helpers and UI radios showed up
   during the base build before the extension spec was closed. Harmless at
   runtime, but it muddied the “base then extend” story until Step 2 formalized
   hard mode + `/api/daily`.
5. **Deterministic tests for hard mode.** Random secrets make win-path API tests
   flaky. Without a patch point on `generate_secret`, you cannot stably assert
   scores.
6. **Local server lifecycle.** Restarting after the extension left port `5055`
   occupied (`Address already in use`) until the old process was killed. Easy to
   mistake for an app bug.
7. **Honest limit on “loop code generation.”** Plan/build stages ran through
   `./loop.sh`, but mostly with `echo` / `dry_run`. The Flask code was written
   by the AI in-session, not by a multi-iteration autonomous `copilot`/`cursor`
   agent loop. The loop framed and logged the work; it did not fully generate
   the backend unattended.

## Corrections made

- Wrote and reviewed concrete base/extension specs, then filled
  `IMPLEMENTATION_PLAN.md` from the plan-loop prompt before coding APIs.
- Fixed `loop.sh` empty-array handling, preferred `python` from the active env,
  and corrected the Cursor backend flags (`--print --force` + positional prompt).
- Implemented exact-first, then multiset partial marking; locked it in with unit
  tests (including duplicate cases) and API tests for create/guess/scores.
- Centralized mode parameters; taught the UI to rebuild pad/slots from
  `code_length` / `digit_min` / `digit_max` returned by `POST /api/games`
  (needed for hard mode).
- Added `GET /api/daily` (date only, never the secret) and mode-filtered
  `/api/scores`.
- Used monkeypatching of `generate_secret` for a deterministic hard-mode win
  test; kept daily wins deterministic via date-seeded SHA secrets.
- Restarted the server cleanly on `5055` after kills; documented
  `./script/server` and TA play steps in `running.md`.

## Takeaway

The valuable SE lesson was not “AI can emit Flask,” but that loop-shaped stages
only help if the backend boundaries are enforced: validate on the server, keep
config in one place, and add tests that fail when duplicates or mode metadata
drift. Where the toolchain lied (wrong Python, wrong CLI flag, occupied port),
the fix was ordinary engineering — read the error, change the script, re-run —
then keep going with the next stage commit instead of abandoning the process.
