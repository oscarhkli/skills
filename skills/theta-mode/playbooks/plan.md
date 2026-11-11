# Plan playbook

A plan is a document a fresh `theta-agent` can execute without this conversation. Its shape follows the plan-mode artifact: why, approach, critical files, reuse, verification. Plan mode itself is not required. This file covers one plan for one PR. For work spanning several PRs, read `slice.md` first.

## Before drafting

- Read `../interview/SKILL.md` (relative to `theta-mode`'s base directory) and follow it, unless the request already settles scope and constraints.
- Read the repo's existing plan docs, such as `docs/plans/`, and match their shape. Use the structure below where they are silent.
- If a design question is open, read `prototype.md` and run it before choosing.
- Write to the directory the human names, else the repo's plan directory, else the project's directory in project brain.

## Structure

- Start here: repo, base branch, the files to read first and the terms the plan uses, each defined in plain words. A fresh agent starts from this section alone.
- Goal: what and why, at most 10 lines.
- Context: the current state, with file paths and line numbers checked against the code.
- Approach: the chosen design only, not the alternatives.
- Critical files: path and what is added, changed or deleted.
- Reuse: existing functions, helpers and test fixtures to use instead of writing new ones.
- Checklist: pre-work, work, post-work.
- Tasks: what to do, roughly where, tests first (tdd). Each task carries a one-line why. A task of a different kind than the slice's headline, such as a benchmark or Go tests in an e2e slice, says why it belongs in this slice.
- Observable results: what differs when the task is done.
- Verification: the exact commands and expected output. How is it proven that the problem is solved? Can a test prove it at each layer of the testing pyramid (unit, handler or API, CLI, browser; a layer that fits none of them, such as scene tests with mocks, goes with the nearest one)? A layer left out says why. Each path a user can take to the changed code (retry, reload, repeat, error) gets a check at the layer the user acts on (browser for web).
- Review gate: who or what checks before the PR is ready. For a code PR the gate names the review: a fresh `theta-agent` runs `/code-review high` on the branch, and a separate `theta-agent` evaluates each finding and fixes the ones that hold. The PR's Verification section lists what was fixed and what was skipped. Name the review only when the plan's author wants it; it is not a default for every PR.
- Acceptance criteria: what counts as success.
- PR handling: ready for review unless the human asks for a draft; never merge. Plans do not name branches or worktrees; the implementing session creates them with the `create-worktree` skill.
- Open items: minor findings left unfixed and questions left unanswered.
- Appendix: findings, data and long lists.

## Writing and checking

- Delegate drafting to `theta-agent`. The `Plan` agent type is read-only and cannot write the files.
- Give the delegate absolute paths, not references to the conversation.
- Tell the delegate to apply the `unslop` skill to the plan files before it reports.
- Path check: a `theta-agent` checks every path, line number, count and command against the code before you present the plan.
- User-path check: a fresh `theta-agent` lists every path a user can take to the changed code and the testing pyramid layer whose test proves it. Each uncovered path becomes a test in Verification or an accepted risk with a reason.
- Cold read: a fresh `theta-agent` reads the plan cold, with only the plan and the repo. It reports every step it could not act on and every term it had to guess.
- The three checks run once per plan, under the Budget. If one was not run, put it in an "Owed checks" list in the plan README and say so in the reply.
- Present the plan and wait. Do not edit code until the human says so.

## Budget

Planning is boxed like a spike.

1. One delegate drafts.
2. Review once on the full draft: path check, user-path check and cold read, in parallel. This is the only full review.
3. A fresh delegate saves a copy of the files, then fixes every major finding and the cheap minor ones. The rest go to Open items.
4. A fresh reviewer gets the findings and the diff, and checks only those and the changed lines. If it finds a major issue, repeat steps 3 and 4 once.
5. One final scan: cold read and `unslop`, for logic, contradictions and readability. Text-only fixes land directly.

Major means a delegate would build the wrong thing, a test passes without proving its claim, or two parts contradict. Minor findings never start a round.

If the second step 4 still finds a major issue, stop and skip step 5. Plan an alternative: slice the work, or build a prototype (`prototype.md`) to test the claim against real code. Report both to the human.

Size gate, before step 2: apply the size rule in `slice.md`. If the plan outgrows one reviewable change, slice first. As a signal, not a limit, when Critical files lists more than about 8 production files that change behaviour, check that rule before planning further. Mechanical edits, such as renames and signature additions or removals that only propagate, do not count.
