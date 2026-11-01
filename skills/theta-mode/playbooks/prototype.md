# Prototype playbook

A prototype is throwaway code that answers a question reading cannot. It verifies a decision or its alternatives and gathers references.

## When

- A design choice depends on timing, ordering, rendering or concurrency.
- Two reports contradict and the code does not decide.
- The human asks "would X work?" or "did you verify it?".
- The design phase has an open question that is hard to judge.

Test: could one grep, one file read or one command answer it with evidence? If yes, run that and skip the prototype.

- Skip when all hold: reading code, docs or one command settles it; it does not depend on timing, ordering, concurrency or rendering; being wrong costs a one-line, reversible fix.
- Build one when any holds: the answer depends on runtime behaviour you cannot read (timing, ordering, concurrency, rendering); two sources or reports contradict; being wrong costs a rewrite across layers or a PR; the human asked "did you verify it?".

## Who

- One fresh `theta-agent` per prototype, focused on ONE topic. Do not expand the scope. A new question found on the way goes into the report as a follow-up and is not built.
- One open question gets at most 3 prototypes by default, one per candidate answer, each built by its own fresh subagent. Each prototype checks only the few assumptions behind its own candidate.
- The coordinator writes the candidate and its assumptions in plain words in the brief, each assumption with the result that would disprove it.

## Where

- Use the `create-worktree` skill. Parent directory `<repo>-worktrees` (sibling of the repo), worktree name `proto-<topic>` or `proto-<topic>-<approach>`, branch `proto/<topic>[-<approach>]`. The name always starts with `proto-`.
- The skill branches from local main, which can be stale. Run `git fetch origin` first. After the skill creates the worktree, run `git reset --hard origin/main` inside it. The branch is new and throwaway, so nothing is lost.
- Never use the scratchpad or the main checkout.
- Never push a `proto/` branch or open a PR for it. Prototypes are local and throwaway.
- Keep a control worktree `proto-main-check` on clean `origin/main` for any claim that a bug already exists today. A prototype cannot tell its own faults from existing ones.

## Build

- Follow `principle-lazy-senior-dev`: smallest change, speed over polish, ignore code quality.
- The prototype must still build and run the real code path the assumption is about. An assumption is never PASS from a build that did not run that path.
- Old tests that break show the blast radius. List them by name and cause. Fix a broken test only when the prototype run needs it to compile or run.
- Instrument freely: logs, timelines, a rough browser script.

## Several approaches

- One fresh subagent and one worktree per candidate answer.
- The coordinator compares the reports in one table: candidate x assumption (PASS, FAIL or PARTIAL; observed or inferred) x size x pros and cons.
- The coordinator recommends one, or a hybrid built in a new worktree from the winner. Name the part taken from another approach.

## Size

Report production, test and doc changes, and the layers touched, separately. Never call a change small from the production diff alone.

## Report

Only what the decision needs, no fixed length:

- The result of each candidate, with the path of its evidence.
- What failed and what it means for the design.
- Tradeoffs and a recommendation.
- The references found: file and symbol, or quoted doc text.
- What was not tested.

Each prototype leaves a `PROTOTYPE.md` at the root of its worktree, never committed (the branch is not pushed). It holds the same text the subagent reports in chat: each candidate's result with the path of its evidence, the recommendation, the references found and what was not tested.

If the decision is still open, say what is open and offer the human the next options. Do not decide for them.

## After the report

- The coordinator opens the evidence behind the result that drives the decision.
- A conflict between two reports is settled by the cheapest experiment, not by reading.
- Record the findings, worktree paths and each `PROTOTYPE.md` path in the plan notes.
- When the approach is adopted, put the prototype's conclusion in the PR's Tradeoffs section (see `create-pr.md`). When it is abandoned, keep it in the plan notes. `PROTOTYPE.md` is a working file, not the archive.
- Worktrees stay until the human says to remove them.
