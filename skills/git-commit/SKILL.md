---
name: git-commit
description: Use when the user wants to commit, git commit, commit changes, commit staged changes, commit files, or create a commit. Also invoke proactively before running any git commit command as part of a larger task. Formats the message as a Conventional Commit and stages only the files belonging to the change.
---

# Conventional Commits

Format every commit message per **Conventional Commits 1.0.0**. The agent may commit, push a feature branch and open a ready-for-review PR without asking, titled in Conventional Commit style. It never pushes to the default branch or force-pushes unless the user says so.

## Rules

- The scope names the affected skill or folder, as in `feat(theta-mode)` or `fix(cleanup-worktrees)`. Use `skills` for a change across several.
- The subject is a short imperative summary: lowercase, no trailing period, 72 characters or fewer on the first line.
- Add a body only when the subject is not self-evident. Keep it to 1-3 lines and explain why, not how.
- Apply `../unslop/SKILL.md` to the subject and body before committing.

## Branch names

Name a new branch `<type>/<short-kebab-summary>`, with the same types as commits (`feat`, `fix`, `refactor`, `chore`, `docs`, `test`, `perf`, `build`, `ci`, `style`, `revert`). Never use `sync/` or another prefix outside this list. The one exception is the throwaway `proto/<topic>` branch from the prototype playbook, which is never pushed.

## Staging

- Stage only the files of this one logical change, by explicit path, so each commit stays small and focused. Never use `git add -A`, `git add .` or `git add -f`: they sweep in unrelated edits, scratch files, secrets and ignored files.
- Run `git status` first. Leave unrelated changes unstaged and mention them in your reply.
- If the user already staged files, commit exactly those and do not restage.

## Authorship footer

If an AI agent authored or materially contributed to the change, credit it with a `Co-Authored-By:` footer, one blank line after any body:

- Use the attribution line supplied in the session context verbatim when there is one.
- Otherwise write `Co-Authored-By: <your model name> <noreply address of your vendor>`.
- Omit the footer only when the user wrote or edited the whole diff themselves.
