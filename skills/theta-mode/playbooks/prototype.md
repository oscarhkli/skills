# Prototype playbook

A prototype is throwaway code that answers a question reading cannot. It verifies a decision or its alternatives and gathers references.

## When

- A design choice depends on timing, ordering, rendering or concurrency.
- Two reports contradict and the code does not decide.
- The human asks "would X work?" or "did you verify it?".
- The design phase has an open question that is hard to judge.

Skip it when reading the code settles the question.

## Who

- One fresh `theta-agent` per prototype, focused on ONE topic. Do not expand the scope. A new question found on the way goes into the report as a follow-up and is not built.
- At most 3 hypotheses per prototype by default.
- The coordinator writes the hypotheses in plain words in the brief, each with the result that would disprove it.

## Where

- Use the `create-worktree` skill. Parent directory `<repo>-worktrees` (sibling of the repo), worktree name `proto-<topic>` or `proto-<topic>-<approach>`, branch `proto/<topic>[-<approach>]`. The name always starts with `proto-`.
- The skill branches from local main, which can be stale. Run `git fetch origin` first. After the skill creates the worktree, run `git reset --hard origin/main` inside it. The branch is new and throwaway, so nothing is lost.
- Never use the scratchpad or the main checkout.
- Keep a control worktree `proto-main-check` on clean `origin/main` for any claim that a bug already exists today. A prototype cannot tell its own faults from existing ones.

## Build

- Follow `principle-lazy-senior-dev`: smallest change, speed over polish, ignore code quality.
- The prototype must still build and run the real code path the hypothesis is about. A hypothesis is never PASS from a build that did not run that path.
- Old tests that break show the blast radius. List them by name and cause. Fix a broken test only when the hypothesis run needs it to compile or run.
- Instrument freely: logs, timelines, a rough browser script.

## Several approaches

- One fresh subagent and one worktree per approach, the same hypotheses for each.
- The report compares them in one table: approach x hypothesis (PASS, FAIL or PARTIAL; observed or inferred) x size x pros and cons.
- The coordinator recommends one, or a hybrid built in a new worktree from the winner. Name the part taken from another approach.

## Size

Report production, test and doc changes, and the layers touched, separately. Never call a change small from the production diff alone.

## Report

Only what the decision needs, no fixed length:

- The result of each hypothesis, with the path of its evidence.
- What failed and what it means for the design.
- Tradeoffs and a recommendation.
- The references found: file and symbol, or quoted doc text.
- What was not tested.

If the decision is still open, say what is open and offer the human the next options. Do not decide for them.

## After the report

- The coordinator opens the evidence behind the result that drives the decision.
- A conflict between two reports is settled by the cheapest experiment, not by reading.
- Record the findings and worktree paths in the plan notes.
- Worktrees stay until the human says to remove them.
