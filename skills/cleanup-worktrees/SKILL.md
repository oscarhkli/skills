---
name: cleanup-worktrees
description: Remove Git worktrees and local branches whose pull request is merged, plus throwaway proto-* worktrees. Use when the user asks to clean up worktrees, remove merged branches, prune stale worktrees, delete finished feature branches, or says a PR is merged and its worktree can go.
compatibility: Requires Git, an authenticated GitHub CLI (gh), and Python 3.9 or later. Works on macOS and Windows.
---

# Cleanup Worktrees

`scripts/cleanup.py` (relative to this file) runs every Git and `gh` command. Remote branches are never touched. `<repo>` is the main checkout, the first path `git worktree list` prints. Run nothing from inside a worktree you might remove.

## Modes

- **Targeted:** the human names one PR, branch or worktree. Pass it with `--only`.
- **Full scan:** any other request. Audit everything.

## 1. Audit

`python3 "<skill-directory>/scripts/cleanup.py" "<repo>" [--only <name>]` prints one TSV row per worktree and local branch, skipping the default branch and the main checkout: `class`, `reason`, `branch`, `worktree`, `pr_state`, `pr_url`, `changes` (uncommitted and untracked files), `unpushed` (`proto-*` rows only). `-` means none. `--only` matches a branch, worktree path, directory name or PR number (`22` or `#22`), and fails when nothing matches.

`target` means a merged PR whose head is the local head, or a `proto-*` worktree. Everything else is `keep` with its reason: no PR, open PR, closed without merge, commits after merge, or `linked: <name>` when a skill in `~/.agents/skills` or `~/.claude/skills` points into the worktree. Remove a `keep` row only when the human names it after seeing its reason.

## 2. Open sessions

Ask which of the human's sessions are still open, unless they already said. Drop any target an open session uses, and name the session as the reason.

## 3. Confirm

Full scan: show the targets and the kept rows with reasons, then ask once, listing every worktree and local branch to delete, and state that their uncommitted edits, unpushed commits and untracked files are lost.

Targeted: when the named row is a `target` with `pr_state` `MERGED` and `changes` 0, skip the question. Otherwise ask as in a full scan.

## 4. Remove

`python3 "<skill-directory>/scripts/cleanup.py" "<repo>" --remove <branch-or-worktree>...` with exactly the confirmed names. It re-runs the audit, refuses anything that is not a target, then removes each worktree with `--force`, deletes the local branch with `branch -D`, and runs `git worktree prune`.

## Response

Report what was removed, everything kept with its reason, and any failed command with its error.
