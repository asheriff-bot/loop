# Implementation Plan

> Living document. The PES **plan** mode updates this; **build** mode picks the
> top unfinished item. Clear completed items periodically so the file stays lean.

## Overall status

- [x] Loop engineering engine (PES) scaffolded from scratch
- [ ] Step 1 — Base system (nontrivial interactive app)
- [ ] Step 2 — Extension

---

## Step 0 — Loop infrastructure (this repo bootstrap)

- [x] `loop_engine` PES package (plan / execute / summary + memory)
- [x] `loop.sh` CLI wrapper mirroring class tutorial UX
- [x] Prompt templates for specify / review / plan / build / summary
- [x] Stage tracker aligned with loop.pdf (2 steps × stages + commits)
- [x] Offline dry_run backend + unit tests
- [ ] Choose concrete product idea for Step 1 (must be nontrivial, not a clone)

---

## Step 1 — Base system

### Stages (commit after each)

1. **specify** — write `specs/` for the base product
2. **review** — critique specs; fix holes
3. **plan** — fill this section with prioritized build tasks *(use PES loop)*
4. **build** — implement via PES loop until `<promise>DONE</promise>`

### Build backlog (fill during plan stage)

- [ ] TBD after specify/review

---

## Step 2 — Extension

### Stages (commit after each)

1. **specify**
2. **review**
3. **plan** *(use PES loop)*
4. **build** *(use PES loop)*

### Build backlog

- [ ] TBD

---

## Review notes (step1_base / review)

Reviewed `specs/01-locksmith-base.md`:

- **Feasible**: Flask + SQLite + vanilla JS is appropriate for a TA-runnable localhost demo.
- **Gaps fixed during review**: clarified score formula, secret reveal only after finish, digit domain 1–6, port **5055**.
- **Risk**: Mastermind partial-count with duplicates — must use multiset marking (exact first, then partial). Tests required.
- **Not disconnected**: `/api/scores` feeds the UI sidebar; create → guess → finish path is end-to-end.
- **Ready for plan/build**: yes.
