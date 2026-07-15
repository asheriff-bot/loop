# Spec: loop.pdf assignment rubric (meta)

This is not the product spec — it is the **process contract** we must satisfy.

## Requirements

1. Use an AI assistant **and** loop engineering code (this repo's PES loop).
2. Build something nontrivial (e.g. small website with interactive backend).
   Not an exact clone of an existing demo.
3. Use version control (public GitHub, or grant instructor/TA access).
4. Build in **two steps**: base system, then extension.
5. Each step has **≥3 stages** (we use specify → review → plan → build).
6. **Use a loop for at least one stage** (we use the PES loop for plan + build).
7. **Commit after every stage of every step** (≥6 commits).
8. Include deliverable files:
   - `prompts.txt` — every prompt/command given to an agent
   - `running.md` — how a TA runs the product
   - `reflection.md` — one paragraph of SE learning

## How this repo maps to the rubric

| Rubric item | Mechanism |
|-------------|-----------|
| Loop engineering code | `loop_engine/` + `loop.sh` (PES, LoongFlow-inspired) |
| Stages | `python -m loop_engine stage …` + `config.yaml` assignment block |
| Stage commits | `stage complete` → `git commit` |
| Loop on a stage | `./loop.sh -m plan` / `./loop.sh -m build` |
| prompts.txt | Auto-appended each Planner.build() |
| running.md / reflection.md | Authored as assignment artifacts |
