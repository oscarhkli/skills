# Multi-PR plan playbook

For work split into several PRs or phases, possibly built by agents in parallel. Read `plan.md` first. Each slice gets its own plan in that shape. This file adds the layer above them.

## Slicing

- Slice vertically: each slice delivers a working, mergeable change, not a layer that only works once the others land.
- Each file, finding or task belongs to exactly one slice. Check by listing every owner and finding no gaps or overlaps. Two slices editing the same file is a dependency; record it.
- Put shared prerequisites, such as a type, helper or test fixture several slices need, in their own first slice.

## Index (README)

One README next to the slice plans holds:

- Goal and why the work is split, at most 10 lines.
- A table: slice, scope, depends on, can run in parallel with, owner agent.
- The merge order, and why each dependency exists.
- Shared files and the slice that owns each edit.
- Counts that must reconcile, such as findings per slice summing to the total.
- Kickoff: the one-line prompt that starts a slice, so the human does not retype context. Each slice plan's Start here supplies the rest.

## Dependencies and concurrency

- A slice starts from the default branch plus the slices it depends on. Say which, by name.
- Slices with no dependency between them run concurrently.
- Say what to do when a dependency merges after a slice has started: rebase, and rerun the slice's verification.
- Each slice's verification passes on its own branch, without the other slices.

## Keeping slices current

- When a slice changes something its dependents rely on, such as a name, a signature, a file owner or a decision, spawn one `theta-agent` per affected dependent. Each updates that slice's plan and its row in the index. Then rerun the index check below.
- When a slice merges, refresh the deferred and decision sections of every remaining slice's PR. Delete the ones that are now settled.

## PR comments

- A PR comment lists open deferred items and open decisions only. Fixed gaps go in the PR summary.
- Update a branch only for the slice the human reviews next. Each update reruns CI.

## Checking

- A `theta-agent` checks the index against the slice plans: every slice listed once, dependencies symmetric, counts reconciled, no file owned twice.
- Present the index and the slice plans together, and wait.
