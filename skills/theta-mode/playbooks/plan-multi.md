# Parallel stories playbook

For agents that build the stories of a split in parallel, or write PR comments for a multi-PR set. Read `slice.md` first. It holds the index, dependencies and ownership.

## Concurrency

- Stories with no dependency between them are built by separate agents at the same time.
- Each agent works in its own worktree and touches only the files its story owns.

## PR comments

- A PR comment lists open deferred items and open decisions only. Fixed gaps go in the PR summary.
- Update a branch only for the story the human reviews next. Each update reruns CI.
