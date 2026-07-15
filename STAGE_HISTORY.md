# Stage history map (for graders / TAs)

This file maps each **required stage commit** on `main` to the artifacts it
delivered. Use it together with:

```bash
git log --oneline --grep='stage('
```

Repo: https://github.com/asheriff-bot/loop  
Branch: `main`

Assignment shape: **2 steps × 4 stages** (specify → review → plan → build),  
which exceeds the minimum of 3 stages per step (and therefore ≥6 commits).

---

## Quick index

| Step | Stage | Commit | What landed in *this* commit |
|------|-------|--------|------------------------------|
| 1 Base | specify | [`36dd9ab`](https://github.com/asheriff-bot/loop/commit/36dd9ab) | Loop engineering scaffold (`loop_engine/`, `loop.sh`, prompts, rubric meta-spec) |
| 1 Base | review | [`0609056`](https://github.com/asheriff-bot/loop/commit/0609056) | **Base product spec** `specs/01-locksmith-base.md` + review notes in plan |
| 1 Base | plan | [`181d375`](https://github.com/asheriff-bot/loop/commit/181d375) | Prioritized `IMPLEMENTATION_PLAN.md` backlog; `game/` package init |
| 1 Base | build | [`032eed4`](https://github.com/asheriff-bot/loop/commit/032eed4) | **Playable Locksmith base**: Flask API, SQLite, UI, tests, `script/server` |
| 2 Extension | specify | [`42caaf3`](https://github.com/asheriff-bot/loop/commit/42caaf3) | Stage boundary + extension prompts logged in `prompts.txt` |
| 2 Extension | review | [`4087ee7`](https://github.com/asheriff-bot/loop/commit/4087ee7) | Extension review notes in `IMPLEMENTATION_PLAN.md` |
| 2 Extension | plan | [`0d3ddc4`](https://github.com/asheriff-bot/loop/commit/0d3ddc4) | **Hard mode + ModeConfig** (main extension code) + tests/UI updates |
| 2 Extension | build | [`494b986`](https://github.com/asheriff-bot/loop/commit/494b986) | Build-stage prompt/lesson capture completing the stage gate |

There are **8** `stage(...)` commits (≥6 required).

---

## Step 1 — Base system

### `36dd9ab` — `stage(step1_base): specify`

**Intent:** define the loop process and project contract.

**Primary artifacts:**
- `loop_engine/*` — Plan / Execute / Summary loop (later Evaluate)
- `loop.sh`, `config.yaml`, `prompts/PROMPT_*.md`
- `specs/00-assignment-rubric.md`
- initial `prompts.txt`, `running.md`, `reflection.md`, `AGENTS.md`

### `0609056` — `stage(step1_base): review`

**Intent:** critique and lock the *product* spec for the base game.

**Primary artifacts:**
- `specs/01-locksmith-base.md` (Locksmith rules, API, acceptance)
- Review notes written into `IMPLEMENTATION_PLAN.md`
- Prompt history updates in `prompts.txt`

### `181d375` — `stage(step1_base): plan`

**Intent:** PES **plan** stage — backlog only, minimal code.

**Primary artifacts:**
- Prioritized build backlog in `IMPLEMENTATION_PLAN.md`
- `game/__init__.py` package placeholder
- Plan-loop entries appended to `prompts.txt`

### `032eed4` — `stage(step1_base): build`

**Intent:** PES **build** stage — ship a runnable base product.

**Primary artifacts (the base system a TA plays):**
- `game/app.py`, `game/logic.py`, `game/db.py`
- `game/templates/index.html`, `game/static/*`
- `game/daily.py` (daily helper used by API; also supports later extension surface)
- `tests/test_api.py`, `tests/test_game_logic.py`
- `script/server`, Flask dep in `requirements.txt`, updated `running.md`

**Note for graders (timing honesty):**  
`specs/02-locksmith-extension.md` was *authored early* in this same commit
(extension requirements drafted while finishing base). The **implementation** of
hard mode still lands in Step 2 below (`0d3ddc4`).

**How to verify base after this commit (conceptually):**
- Classic create/guess API + browser UI
- Scores in SQLite
- Port `5055` via `./script/server`

---

## Step 2 — Extension

### `42caaf3` — `stage(step2_extension): specify`

**Intent:** open the extension step and record specify-stage agent prompts.

**Primary artifacts in *this* commit:**
- `prompts.txt` — Step 2 specify prompt log

**Where the written extension spec lives:**  
`specs/02-locksmith-extension.md` (Hard mode + daily board; file created earlier
in `032eed4` as noted above). Step 2 specify uses that document as the contract;
this commit marks the formal stage boundary + prompt capture.

### `4087ee7` — `stage(step2_extension): review`

**Intent:** review extension plan before coding hard mode.

**Primary artifacts:**
- Extension review notes in `IMPLEMENTATION_PLAN.md`  
  (UI must honor `code_length` / digit range from create API)

### `0d3ddc4` — `stage(step2_extension): plan`

**Intent:** turn extension review into an executable plan **and** land the
extension implementation that the plan described (hard mode).

**Primary artifacts (this is the main Step 2 product delta):**
- `game/logic.py` — `ModeConfig` + `classic` / `daily` / `hard`
- `game/app.py` — hard create/guess path, `/api/daily`
- `game/static/game.js`, `game/templates/index.html`, CSS — Hard radio + dynamic pad
- `tests/test_api.py`, `tests/test_game_logic.py` — hard + daily endpoint coverage
- Plan/prompt updates in `IMPLEMENTATION_PLAN.md` / `prompts.txt`

**Note for graders (stage naming honesty):**  
Ideal textbook flow would put this code under `stage(...): build`. In this repo
the **hard-mode code ships in the Step 2 plan commit** (`0d3ddc4`), and the
following build commit closes the stage with process logging. Functionally the
extension is complete at HEAD; this map exists so the commit graph is unambiguous.

### `494b986` — `stage(step2_extension): build`

**Intent:** close the Step 2 build stage gate after validation.

**Primary artifacts in *this* commit:**
- `prompts.txt` — build-stage execution / lessons / completion promise capture

**Product code already present from `0d3ddc4`.** At HEAD, classic + daily + hard
are all playable; EvalMetric reports `S = 1.0`.

---

## How a TA can spot-check the graph

```bash
# All stage commits
git log --oneline --grep='stage('

# Base product introduction
git show --stat 032eed4

# Extension (hard mode) introduction
git show --stat 0d3ddc4

# Run today (HEAD)
./script/server          # http://127.0.0.1:5055/
./script/eval            # EvalMetric breakdown
PYTHONPATH=. pytest -q
```

---

## Post-stage follow-ups (not stage gates)

These commits are **after** the required 8 stage commits; they refine docs/metrics
and do not replace stage evidence:

| Commit | Purpose |
|--------|---------|
| `b8740ed` | EvalMetric / PES Evaluate automation |
| `53d43b2` | Expanded `reflection.md` learnings |
| `8c083fd` | Architecture diagram (loop vs game) in README |
| others | Cursor-ref cleanup, README polish, etc. |

---

## Summary for the rubric

| Rubric item | Satisfied by |
|-------------|--------------|
| 2 steps | Step 1 base + Step 2 extension |
| ≥3 stages/step | 4 stages each (8 total) |
| Stage commits ≥6 | 8 `stage(...)` commits listed above |
| Loop on ≥1 stage | Plan/build PES loops (+ later `automate`/`eval`) |
| Nontrivial interactive backend | Locksmith on `:5055` |
| `prompts.txt` / `running.md` / `reflection.md` | Present and maintained |
