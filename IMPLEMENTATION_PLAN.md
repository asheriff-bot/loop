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

## Review notes

_None yet — run `./loop.sh -m review` after specs exist._
