---
name: create-worktree
description: Create a Git worktree from a worktree name and branch name, in the repo's sibling "-worktrees" directory. Use this skill whenever the user asks to create, add, initialise, or set up a worktree, especially when the source repository is the sibling directory whose name matches the parent without the "-worktrees" suffix.
compatibility: Requires Git and Python 3.
---

# Create Worktree

Use the bundled deterministic script instead of assembling Git commands manually.

## Inputs

Worktree name and branch name. Pass `--parent` only when the user names another parent directory, which must end in `-worktrees`.

## Run

Run it inside the repo. Without `--parent`, the parent is `<repo toplevel>-worktrees`.

```
python3 "<skill-directory>/scripts/create_worktree.py" "<worktree-name>" "<branch-name>" [--parent "<worktree-parent-directory>"]
```

Report the script's output lines verbatim. They give the worktree path, the branch and how the branch was made, plus a `warning:` line when a new branch could not start from a fresh `origin/<base>`. On failure the script exits with Git's error.
