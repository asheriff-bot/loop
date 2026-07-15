# REVIEW MODE — critique specs/plan before building

## Goal
{{goal}}

## Context
- Mode: {{mode}}
- Stage: {{stage}}
- Iteration: {{iteration}}

{{memory}}

## Instructions
1. Review `specs/*` and `IMPLEMENTATION_PLAN.md` (if present).
2. Check for: ambiguities, missing acceptance criteria, unrealistic deps,
   underspecified edge cases, and anything disconnected from the stated goal.
3. Ask/answer clarifying questions in the docs themselves (update the specs).
4. Produce a short review note in `IMPLEMENTATION_PLAN.md` under `## Review notes`.
5. Do not implement product code.

When the review is complete and blockers are either resolved or explicitly listed,
output `<promise>{{completion_promise}}</promise>`.
