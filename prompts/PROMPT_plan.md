# PLAN MODE — analysis only (do not implement)

You are running inside a Plan–Execute–Summary loop engineering system.

## Goal
{{goal}}

## Context
- Mode: {{mode}}
- Assignment stage: {{stage}}
- Iteration: {{iteration}}

{{memory}}

## Instructions
0. Study `specs/*` and `IMPLEMENTATION_PLAN.md` (create the plan file if missing).
1. Study the existing codebase. Do **not** assume features are missing — search first.
2. Compare code vs specs. Look for TODOs, stubs, skipped tests, and inconsistencies.
3. Update `IMPLEMENTATION_PLAN.md` as a prioritized bullet list of remaining work.
4. If a required capability is truly absent, author/extend a spec under `specs/`.

## Hard constraints
- **Plan only. Do NOT implement code changes** (docs/plan updates are OK).
- Prefer consolidating shared utilities over copy-paste.
- Keep `AGENTS.md` operational (commands/ports/patterns). Progress notes belong in `IMPLEMENTATION_PLAN.md`.

## When finished
Summarize remaining work and confidence. Output `<promise>{{completion_promise}}</promise>` only if the plan is complete and implementation-ready (no further planning iterations needed).
