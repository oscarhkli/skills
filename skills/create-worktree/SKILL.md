---
name: create-worktree
description: Create a Git worktree from a worktree parent directory, worktree name, and branch name. Use this skill whenever the user asks to create, add, initialise, or set up a worktree, especially when the source repository is the sibling directory whose name matches the parent without the "-worktrees" suffix.
compatibility: Requires Git and Python 3.
---

# Create Worktree

Use the bundled deterministic script instead of assembling Git commands manually.

## Inputs

Collect these three values:

- Worktree parent directory, ending in `-worktrees`. The source repository is the sibling directory with that suffix removed.
- Worktree name
- Branch name

Ask only when one of these values is missing or ambiguous.

## Run

Execute:

```
python "<skill-directory>/scripts/create_worktree.py" "<worktree-parent-directory>" "<worktree-name>" "<branch-name>"
```

The script prints the worktree path, branch, and action on three lines, plus a fourth `warning:` line when a new branch's base trails its last-fetched remote. It:

1. Creates a new local branch from local `main`, or local `master` when `main` does not exist.
2. Reuses an existing local branch.
3. Creates a local branch tracking `origin/<branch>` when the branch exists only on `origin`.
4. Exits with Git's error when the target exists or the branch is attached to another worktree.

## Response

Report:

- Absolute worktree path
- Branch name
- Whether the branch was created from `main`, created from `master`, reused, or tracked from origin
- Any `warning:` line, verbatim (the base was not updated; the user decides whether to pull and rebase)

Do not commit or push.
