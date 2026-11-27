---
name: git-commit
description: Use when the user wants to commit or create a commit. Formats the message as a Conventional Commit.
---

# Conventional Commits

Format every commit message per **Conventional Commits 1.0.0**.

- Subject: short imperative summary. Lowercase, no trailing period, 72 characters or fewer.
- Body: only when the subject is not self-evident. 1-3 lines, why not how.
- New branch: `<type>/<short-kebab-summary>`, same types as commits.
  - Exception: the throwaway `proto/<topic>` branch from the prototype playbook, never pushed.
- Stage only the files of this one logical change, by explicit path. Never `git add -A`, `git add .` or `git add -f`.
  - If the user already staged files, commit exactly those.
- Footer: when an AI agent authored or materially contributed to the change, end with a `Co-Authored-By:` line, one blank line after any body.
  - Use the attribution line supplied in the session context verbatim. If none: `Co-Authored-By: <your model name> <noreply address of your vendor>`.
