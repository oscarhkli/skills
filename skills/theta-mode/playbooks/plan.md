# Plan playbook

A plan is a document a fresh `theta-agent` can execute without this conversation. Its shape follows the plan-mode artifact: why, approach, critical files, reuse, verification. Plan mode itself is not required.

## Before drafting

- Read `../interview/SKILL.md` (relative to `theta-mode`'s base directory) and follow it, unless the request already settles scope, slicing and constraints.
- Read the repo's existing plan docs, such as `docs/plans/`, and match their shape. Use the structure below where they are silent.
- Write to the directory the human names, else the repo's plan directory.

## Structure

Each plan, one file per vertical slice plus a README that indexes them and states the order and dependencies:

- Goal: what and why, at most 10 lines.
- Context: the current state, with file paths and line numbers checked against the code.
- Approach: the chosen design only, not the alternatives.
- Critical files: path and what is added, changed or deleted.
- Reuse: existing functions, helpers and test fixtures to use instead of writing new ones.
- Checklist: pre-work, work, post-work.
- Tasks: what to do, roughly where, tests first (tdd).
- Observable results: what differs when the task is done.
- Verification: the exact commands and expected output.
- Review gate: who or what checks before the PR is ready.
- Acceptance criteria: what counts as success.
- PR handling: branch, worktree, draft or ready, merge order.
- Appendix: findings, data and long lists.

Slices are vertical, so several agents can work in separate worktrees and PRs at once. Name the slices that block each other.

## Writing and checking

- Delegate drafting to `theta-agent`. The `Plan` agent type is read-only and cannot write the files.
- Give the delegate absolute paths, not references to the conversation.
- Have a second `theta-agent` check every path, line number, count and command against the code before you present the plan.
- Present the plan and wait. Do not edit code until the human says so.
