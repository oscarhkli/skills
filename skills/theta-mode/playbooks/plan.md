# Plan playbook

A plan is a document a fresh `theta-agent` can execute without this conversation. Its shape follows the plan-mode artifact: why, approach, critical files, reuse, verification. Plan mode itself is not required. This file covers one plan for one PR. For work spanning several PRs, also read `plan-multi.md`.

## Before drafting

- Read `../interview/SKILL.md` (relative to `theta-mode`'s base directory) and follow it, unless the request already settles scope and constraints.
- Read the repo's existing plan docs, such as `docs/plans/`, and match their shape. Use the structure below where they are silent.
- If a design question is open, read `prototype.md` and run it before choosing.
- Write to the directory the human names, else the repo's plan directory.

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
- Verification: the exact commands and expected output. For behaviour a user reaches, include one check at the layer the user acts on (browser for web), named by the path that triggers it (retry, reload, repeat), and list those paths as risks.
- Review gate: who or what checks before the PR is ready. For a code PR the gate names the review: a fresh `theta-agent` runs `/code-review high` on the branch, and a separate `theta-agent` evaluates each finding and fixes the ones that hold. The PR's Verification section lists what was fixed and what was skipped. Name the review only when the plan's author wants it; it is not a default for every PR.
- Acceptance criteria: what counts as success.
- PR handling: draft or ready; never merge. Plans do not name branches or worktrees; the implementing session creates them with the `create-worktree` skill.
- Appendix: findings, data and long lists.

## Writing and checking

- Delegate drafting to `theta-agent`. The `Plan` agent type is read-only and cannot write the files.
- Give the delegate absolute paths, not references to the conversation.
- Tell the delegate to apply the `unslop` skill to the plan files before it reports.
- Have a second `theta-agent` check every path, line number, count and command against the code before you present the plan.
- Have a third `theta-agent` read the plan cold, with only the plan and the repo. It reports every step it could not act on and every term it had to guess.
- Never offer to skip a check this playbook requires, whatever the token quota. If checks are still owed when you present, put an "Owed checks" list in the plan README, say so in the reply, and answer the question that was asked first.
- Present the plan and wait. Do not edit code until the human says so.
