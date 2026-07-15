# reflection.md

The surprising software-engineering lesson was that once the Plan–Execute–Summary
loop owned stage boundaries and prompt history, the hard part shifted from
“persuading the model to write code” to “keeping secrets, scoring, and UI state
honest across an API boundary.” Implementing Mastermind feedback with duplicate
digits made that concrete: a browser-only game can cheat or drift, but server-side
validation plus a few focused tests turned iterative AI edits into a product a TA
can restart and trust. The loop didn’t replace engineering judgment — it made
each iteration leave evidence (plan, commit, lessons) so progress compounded
instead of thrashing.
