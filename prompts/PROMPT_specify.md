# SPECIFY MODE — write/refine specifications

## Goal
{{goal}}

## Context
- Mode: {{mode}}
- Stage: {{stage}}
- Iteration: {{iteration}}

{{memory}}

## Instructions
1. Clarify the product for this assignment step (base system or extension).
2. Author or refine markdown specs under `specs/` with:
   - problem statement & non-goals
   - user-visible behavior
   - API/data shapes if relevant
   - acceptance criteria / test ideas
3. Do not implement application code in this stage.
4. Keep specs specific enough that a later plan/build loop can execute without guesswork.

When the specs for this step are review-ready, output:
`<promise>{{completion_promise}}</promise>`
