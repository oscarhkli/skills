---
name: cleanup-worktrees
description: Remove Git worktrees and local and remote branches whose pull request is merged, plus throwaway proto-* worktrees. Use when the user asks to clean up worktrees, remove merged branches, prune stale worktrees, or delete finished feature branches.
compatibility: Requires Git, an authenticated GitHub CLI (gh), and Python 3.9 or later.
---

# Cleanup Worktrees

The scripts in `scripts/` (relative to this file) run the Git and `gh` commands. You decide what is safe to remove.

Run this skill only when the human asks. A prototype worktree stays until the human says to remove it.

`<repo>` is the main checkout: the first path `git worktree list` prints. Run nothing from inside a worktree you might remove. Take every worktree path from the audit. Never type a path by hand or assume a `<repo>-worktrees` layout, because a worktree can live anywhere.

## 1. Audit

```
python3 "<skill-directory>/scripts/audit.py" "<repo>"
```

It fetches with `--prune`, then prints one TSV row per worktree and per local branch, except the default branch and the main checkout. Columns: `class`, `reason`, `branch`, `worktree`, `pr_state`, `pr_url`, `changes`, `tracked`, `unpushed`. A `-` means none.

- `class` is `target` when the branch has a merged PR, no open PR, and a local head equal to the merged PR's head. A worktree directory named `proto-*` is also a `target`, including the control worktree `proto-main-check`. Everything else is `keep`, with `reason` one of: no PR, open PR, closed without merge, commits after merge.
- PR state comes from `gh`, not `git branch --merged`, because squash and rebase merges leave the branch outside the default branch's history.
- `changes` is `clean`, `notes-only` (untracked `.md` and `.log` files), `other:<count>`, or `missing` when the directory is gone.
- `tracked` counts modified tracked files in the worktree. `unpushed` counts commits on the branch that no remote branch has. Prototype code is uncommitted by design, so a `proto-*` row with `tracked` or `unpushed` above 0 is information for the confirmation in step 3, not a stop.

Remove a kept item only when the human names it.

## 2. Check before removing

The audit is advice, not permission. Drop a target from the list, and record why, when any of these holds:

- One of the human's open sessions or chats still uses it. Ask the human which sessions are still open, unless they already said. Name the session as the reason.
- A link points into the worktree, such as deployed skills linked from `~/.agents/skills` or `~/.claude/skills`. List the links in those folders and check where each points. On Windows, list links with `Get-ChildItem <dir> | Where-Object LinkType | Select-Object Name, Target` in PowerShell, because junctions do not show as links in Git Bash. Record the link as the reason.

A target that is not `proto-*` with `changes` of `other:<count>`: show `git -C <worktree> status --porcelain` and ask the human before removing it.

## 3. Show, then ask once, then remove

Show two tables: targets (worktree, branch, PR, `changes`, `tracked`, `unpushed`) and kept items (worktree or branch, reason). Then ask the human once, listing exactly what will be deleted: the worktrees, the local branches and the remote branches. State that uncommitted edits and unpushed commits in the listed worktrees are lost. State that each `proto-*` worktree is deleted together with its `PROTOTYPE.md`, uncommitted edits, unpushed commits and untracked files, and that its findings should already be in the PR's tradeoffs or the plan notes. Remove nothing until the human says yes.

Skip the question when the human's request names the exact worktree, the audit shows it as a `target` with PR state `MERGED`, `changes` of `clean` and `tracked` 0, and step 2 drops nothing. Remove it, then show both tables and the results in the response. Every other case asks.

For each target:

```
python3 "<skill-directory>/scripts/remove.py" "<repo>" "<branch>" "<worktree>" [--force] [--keep-remote]
```

- It removes the worktree, deletes the local branch with `branch -D` (a squash-merged branch is not an ancestor of the default branch), then runs `git worktree prune`.
- It deletes the remote branch only when the remote head equals the local head. If they differ, it skips the remote delete and prints why. Report that line.
- Pass `-` for a missing branch or worktree.
- Pass `--force` for a `proto-*` worktree, for a `notes-only` worktree, and for an `other:<count>` worktree the human approved. Git refuses to remove a worktree with untracked or modified files otherwise.
- Pass `--keep-remote` unless `pr_state` is `MERGED`, because deleting the branch of an open PR closes it.

## Response

Report what was removed (worktree, local branch, remote branch), everything kept with its reason, any remote delete the script skipped, and any command that failed, with its error.
