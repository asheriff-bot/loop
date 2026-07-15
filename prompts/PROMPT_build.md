# BUILD / EXECUTE MODE — implement one valuable increment

You are running inside a Plan–Execute–Summary loop engineering system.

## Goal
{{goal}}

## Context
- Mode: {{mode}}
- Assignment stage: {{stage}}
- Iteration: {{iteration}}

{{memory}}

## Instructions
0. Study `specs/*` and `IMPLEMENTATION_PLAN.md`.
1. Pick the **highest-priority unfinished** item. Search the codebase before coding.
2. Implement it fully — no stubs, placeholders, or "TODO later" exits.
3. Run the relevant tests for the unit you changed. Fix failures you cause (and any
   unrelated broken tests you touch).
4. Update `IMPLEMENTATION_PLAN.md` (mark done / add discoveries).
5. If you learn a new run command, update `AGENTS.md` briefly (operational only).
6. `git add` + `git commit` with a clear message describing *why*.

## Hard constraints
- Single sources of truth; avoid adapters/migrations unless the spec requires them.
- Keep progress out of `AGENTS.md`.
- Record durable learnings so the next loop iteration does not rediscover them.

## Lessons
After your work, write a short `## Lessons` section with 1–5 bullets about what
worked or failed (the Summary step stores these in experiential memory).

## When fully done
When **all** plan items for the current step are implemented and validated, output:
`<promise>{{completion_promise}}</promise>`
