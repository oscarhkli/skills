# Plan playbook

A plan is the how for one PR, written when that story is next to start, so a fresh `theta-agent` can run it without this conversation. Its shape follows the plan-mode artifact: why, approach, critical files, reuse, verification. Plan mode itself is not required. A backlog paragraph, an initiative README and a story brief are not plans. A small item needs only a paragraph in `backlog.md`. A brief (`slice.md`) holds the what, the why and the non-obvious constraints. Write a plan only when a fresh agent could not find the how from the code. For work spanning several PRs, read `slice.md` first.

## Before drafting

- The coordinator, not the drafting delegate, reads `../interview/SKILL.md` (relative to `theta-mode`'s base directory) and follows it, because a delegate cannot ask the human. It passes the answers verbatim in the drafting brief. Skip the interview only when the request already settles scope and constraints.
- A plan is a design question. The coordinator reads the principles whose Roles cell lists `planner` in `theta-mode`'s `SKILL.md` and puts their paths in the drafting brief, so the delegate reads them too. Choose the design by root cause, language idiom and the highest trust layer first, then size the diff and the stories. A smaller diff or a quicker fix is not a reason to pick a design.
- Read the repo's existing plan docs, such as `docs/plans/`, and match their shape. Use the structure below where they are silent.
- When the first test needs a spec, write a stub spec first.
- If a design question is open, read `prototype.md` and run it before choosing.
- Write to the directory the human names, else `~/.agents/project-brain/<project>/`, where `<project>` is the name its `README.md` gives the project.
- A library, tool or generator named in a reply or plan comes with its link, GitHub stars, weekly downloads or dependents, last release date and number of maintainers. Rank the mainstream pick first and give a reason for a niche one. Put this in every research brief.

## Structure

- Give each section one line of intent. State each fact once, in the section that owns it.
- Every line must change what the implementer does. Findings that repeat the backlog, measured numbers, rejected alternatives and decision history go to the backlog entry or nowhere.
- Start here: repo, base branch, and the files to read first. A fresh agent starts from this section alone. No Terms list: define a term only when the code, the backlog and `docs/design.md` cannot show it, in one clause, inline where it is first used.
- Goal: what and why, at most 10 lines.
- Context: the current state, with file paths and symbols checked against the code. No line numbers in stories or plans: another change in flight shifts them.
- Approach: the chosen design only, not the alternatives. Decisions the plan can default go here, not in Open items.
- Critical files: path and what is added, changed or deleted.
- Reuse: existing functions, helpers and test fixtures to use instead of writing new ones.
- Tasks: what to do, roughly where, tests first (tdd). Each task carries a one-line why. A task of a different kind than the slice's headline, such as a benchmark or Go tests in an e2e slice, says why it belongs in this slice.
- Verification: how the problem is shown solved, with the exact commands and expected output. It also holds what counts as success. Can a test prove it at each layer of the testing pyramid (unit, handler or API, CLI, browser; a layer that fits none of them, such as scene tests with mocks, goes with the nearest one)? A layer left out says why. Each path a user can take to the changed code (retry, reload, repeat, error) gets a check at the layer the user acts on (browser for web).
- Review gate: who or what checks before the PR is ready. For a code PR the gate names the review: a fresh `theta-agent` runs `/code-review high` on the branch, and a separate `theta-agent` evaluates each finding and fixes the ones that hold. The PR's Verification section lists what was fixed and what was skipped. Name the review only when the plan's author wants it; it is not a default for every PR.
- PR handling: ready for review unless the human asks for a draft; never merge. Plans do not name branches or worktrees; the implementing session creates them with the `create-worktree` skill.
- Open items: only a human decision that blocks a task, naming the task. No Appendix.

## Writing and checking

- Delegate drafting to `theta-agent`. The `Plan` agent type is read-only and cannot write the files.
- Give the delegate absolute paths, not references to the conversation.
- Tell the delegate to apply the `unslop` skill to the plan files before it reports, to remove line-number references (`:123`, `L123`, "line 123") from every file it writes, design docs and backlog entries included, and to paste the Goal section into its report word for word.
- Path check: a `theta-agent` checks every path, symbol, count and command against the code before you present the plan. It runs each count, status and command and does not read it off the plan.
- User-path check: a fresh `theta-agent` lists every path a user can take to the changed code and the testing pyramid layer whose test proves it. Each uncovered path becomes a test in Verification or an accepted risk with a reason.
- Cold read: a fresh `theta-agent` reads the plan cold, with only the plan and the repo. It reports every step it could not act on, as a delete candidate, and every term it had to guess.
- The three checks run once per plan, under the Budget, and all three always run: the coordinator launches the cold read with the other two.
- Present the plan as its path, the Goal copied word for word from the delegate's report, and `Say go to implement.` Add no summary and no question. Do not edit code until the human says so.

## Budget

Planning is boxed like a spike.

1. One delegate drafts.
2. Review once on the full draft: path check, user-path check and cold read, in parallel. This is the only full review.
3. A fresh delegate saves a copy of the files, then fixes every major finding and the cheap minor ones. The rest go to the backlog entry or are dropped.
4. A fresh reviewer gets the findings and the diff, and checks only those and the changed lines. If it finds a major issue, repeat steps 3 and 4 once.
5. One final scan: cold read and `unslop`, for logic, contradictions and readability. Text-only fixes land directly.

Major means a delegate would build the wrong thing, a test passes without proving its claim, or two parts contradict. Minor findings never start a round.

If the second step 4 still finds a major issue, stop and skip step 5. Plan an alternative: slice the work, or build a prototype (`prototype.md`) to test the claim against real code. Report both to the human.

Size gate, before step 2: apply the size rule in `slice.md`. If the plan outgrows one reviewable change, slice first. As a signal, not a limit, when Critical files lists more than about 8 production files that change behaviour, check that rule before planning further. Mechanical edits, such as renames and signature additions or removals that only propagate, do not count.
