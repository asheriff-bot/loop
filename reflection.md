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
   pip install — the shell had to prefer the active env’s `python`.
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
   with AI assistance in-session, not by a multi-iteration autonomous
   Copilot CLI agent loop. The loop framed and logged the work; it did not
   fully generate the backend unattended.

## Corrections made

- Wrote and reviewed concrete base/extension specs, then filled
  `IMPLEMENTATION_PLAN.md` from the plan-loop prompt before coding APIs.
- Fixed `loop.sh` empty-array handling and preferred `python` from the active env.
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
drift. Where the toolchain lied (wrong Python binary, occupied port), the fix
was ordinary engineering — read the error, change the script, re-run — then keep
going with the next stage commit instead of abandoning the process.

## Notes from deriving the EvalMetric

I kept putting off “how do we know the loop got better?” until after the game
mostly worked — which is backwards. Without a number, Plan/Execute/Summary is
just a ritual: you feel productive, but you can’t tell a regression from a
refactor. Looking at LoongFlow’s Evaluator idea (score in [0,1] + feedback the
next Plan can actually read) made that concrete for Locksmith.

First instinct was wrong: I almost scored “can you win a daily game?” as a
single boolean. That collapses too much. A green win can hide a secret leak on
GET, a broken hard-mode length, or a flaky pytest. So I split the backend into
independent qualities and *then* weighted them:

```
S = 0.30·L + 0.25·A + 0.15·M + 0.20·T + 0.10·P
```

- **L (logic)** got the heaviest weight because Mastermind duplicates are easy
  to get subtly wrong and everything else sits on top of that.
- **A (API contract)** is next — TA-facing truth is HTTP behavior, especially
  “no secret while active.”
- **T (tests)** is 0.20: I don’t want the metric to be *only* pytest (tests can
  be gamed or skipped), but a dropping pass rate should still hurt S.
- **M (modes)** is smaller but not zero; classic/daily/hard drifting apart is a
  real class of bug we already hit once.
- **P (persistence)** is only 0.10 — rare to break, embarrassing when it does.

Weights summing to 1.0 sounds pedantic until someone edits a YAML knob months
later; asserting that in code saved me from silent “everything looks 80%”
mistakes.

A few practical insights from wiring Eval into the PES loop:

1. **Evaluate after Execute, before Summary.** If you summarize first, the
   memory records “I feel done” before the fitness check contradicts you.
   Putting Evaluate in the middle (Plan → Execute → Evaluate → Summary) means
   lessons include `S=…` and the next Plan starts from evidence.
2. **Don’t stop the loop on a fake DONE.** dry_run always prints
   `<promise>DONE</promise>`. With eval enabled, stop on **target score**, not
   on that string alone — otherwise automation never learns from a red metric.
3. **Reuse the Flask test client, don’t require a live :5055.** Port wars and
   leftover servers made local eval flaky until I stopped depending on the
   long-running process. Same DB-reopen trick proves persistence without
   kill/restart theater.
4. **Skip nested pytest inside unit tests of the evaluator.** The first version
   of `test_evaluator` recursively ran the whole suite and got messy. Separating
   “full S including T” (CLI `./script/eval`) from “fast L/A/M/P checks”
   (`run_pytest=False`) was the boring fix that made CI sane.
5. **S=1.0 is not a trophy; it’s a gate.** On the automate run we hit 1.0000
   on cycle 1 and stopped. That’s correct behavior — the metric is a *brake*,
   not a reason to keep mutating green code. When something regresses later,
   the component breakdown (which term dropped) is more useful than the single
   float.

If I did this earlier, I think Step 2 (hard mode) would have been less “hope
the UI matches the API” and more “S dipped on M → fix ModeConfig / create
shape.” The metric didn’t invent quality; it made the loop *accountable* for
the same things I’d check by hand before asking a TA to play.
