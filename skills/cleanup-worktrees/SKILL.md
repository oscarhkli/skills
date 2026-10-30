---
name: cleanup-worktrees
description: Remove Git worktrees and local and remote branches whose pull request is merged, plus throwaway proto-* worktrees, after saving their untracked notes. Use when the user asks to clean up worktrees, remove merged branches, prune stale worktrees, or delete finished feature branches.
compatibility: Requires Git, an authenticated GitHub CLI (gh), and Python 3.9 or later.
---

# Cleanup Worktrees

The scripts in `scripts/` (relative to this file) run the Git and `gh` commands. You decide what is safe to remove.

Run this skill only when the human asks. A prototype worktree stays until the human says to remove it. On Windows, run the scripts with `python` or `py -3` if `python3` is missing.

`<repo>` is the main checkout: the first path `git worktree list` prints. Run nothing from inside a worktree you might remove. Take every worktree path from the audit. Never type a path by hand or assume a `<repo>-worktrees` layout, because a worktree can live anywhere.

## 1. Audit

```
python3 "<skill-directory>/scripts/audit.py" "<repo>"
```

It fetches with `--prune`, then prints one TSV row per worktree and per local branch, except the default branch and the main checkout. Columns: `class`, `reason`, `branch`, `worktree`, `pr_state`, `pr_url`, `changes`, `tracked`, `unpushed`. A `-` means none.

- `class` is `target` when the branch has a merged PR, no open PR, and a local head equal to the merged PR's head. A worktree directory named `proto-*` is also a `target`, including the control worktree `proto-main-check`. Everything else is `keep`, with `reason` one of: no PR, open PR, closed without merge, commits after merge.
- PR state comes from `gh`, not `git branch --merged`, because squash and rebase merges leave the branch outside the default branch's history.
- `changes` is `clean`, `notes-only` (untracked `.md` and `.log` files), `other:<count>`, or `missing` when the directory is gone.
- `tracked` counts modified tracked files in the worktree. `unpushed` counts commits on the branch that no remote branch has. Prototype code is uncommitted by design, so a `proto-*` row with `tracked` or `unpushed` above 0 is information for the confirmation in step 4, not a stop.

Remove a kept item only when the human names it.

## 2. Check before removing

The audit is advice, not permission. Drop a target from the list, and record why, when any of these holds:

- One of the human's open sessions or chats still uses it. Ask the human which sessions are still open, unless they already said. Name the session as the reason.
- A link points into the worktree, such as deployed skills linked from `~/.agents/skills` or `~/.claude/skills`. List the links in those folders and check where each points. On Windows, list links with `Get-ChildItem <dir> | Where-Object LinkType | Select-Object Name, Target` in PowerShell, because junctions do not show as links in Git Bash. Record the link as the reason.

A target that is not `proto-*` with `changes` of `other:<count>`: show `git -C <worktree> status --porcelain` and ask the human before removing it.

## 3. Save notes

For each target still to remove:

```
python3 "<skill-directory>/scripts/save_notes.py" "<repo>" "<worktree>" "<branch>" "<pr_url>"
```

It appends the worktree's untracked and ignored `.md` and `.log` files, outside build and dependency folders, to `~/.agents/worktree-notes/<repo-name>/<worktree-name>.md` and prints that path. Every `proto-*` worktree has a `PROTOTYPE.md` at its root, so the file name alone does not identify it; the heading `# <worktree-name>` does. It keeps only the last 200 lines of each file and prints a `truncated` line for each file it cut. Any other untracked file, such as the json, image or script a `PROTOTYPE.md` cites as evidence, is not saved. The script prints `not saved: <file>` for each (20 at most), also when there are no notes. Show these in step 4. Copy a file the human wants to keep before removal. The script writes nothing when there are no notes. It appends, never overwrites, because the same worktree name can come back in a later run.

## 4. Show, then ask once, then remove

Show two tables: targets (worktree, branch, PR, notes file, `tracked`, `unpushed`, files not saved) and kept items (worktree or branch, reason). Then ask the human once, listing exactly what will be deleted: the worktrees, the local branches and the remote branches. State that uncommitted edits and unpushed commits in the listed worktrees are lost. Remove nothing until the human says yes.

For each target:

```
python3 "<skill-directory>/scripts/remove.py" "<repo>" "<branch>" "<worktree>" [--force] [--keep-remote]
```

- It removes the worktree, deletes the local branch with `branch -D` (a squash-merged branch is not an ancestor of the default branch), then runs `git worktree prune`.
- It deletes the remote branch only when the remote head equals the local head. If they differ, it skips the remote delete and prints why. Report that line.
- Pass `-` for a missing branch or worktree.
- Pass `--force` for a `proto-*` worktree, for a `notes-only` worktree after step 3, and for an `other:<count>` worktree the human approved. Git refuses to remove a worktree with untracked or modified files otherwise.
- Pass `--keep-remote` unless `pr_state` is `MERGED`, because deleting the branch of an open PR closes it.

## Response

Report what was removed (worktree, local branch, remote branch), each notes file written, everything kept with its reason, any remote delete the script skipped, and any command that failed, with its error.
