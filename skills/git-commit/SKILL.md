---
name: git-commit
description: Use when the user wants to commit, git commit, commit changes, commit staged changes, commit files, or create a commit. Also invoke proactively before running any git commit command as part of a larger task. Formats the message as a Conventional Commit and stages only the files belonging to the change.
---

# Conventional Commits

Format every commit message per **Conventional Commits 1.0.0**. This skill covers how to commit, not whether to: commit only when the user has asked, and never push.

## Message structure

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

## Rules

1. The `type` is required: a noun such as `feat` or `fix`, followed by an optional scope, an optional `!`, and a required `: `.
2. Use `feat` for a new feature and `fix` for a bug fix.
3. The scope is optional: a noun in parentheses naming the affected part of the codebase, e.g. `feat(engine)`, `fix(web/access)`.
4. The description is required and follows the prefix immediately. It is a short imperative summary: lowercase, no trailing period, under 72 characters in total on the first line.
5. The body is optional. Omit it when the description is self-evident. Otherwise start it one blank line after the description, keep it to 1-3 lines, and explain why, not how.
6. Each footer is optional, separated from the body by one blank line, in the form `Token: value` or `Token #value`.
7. If a commit fits more than one type, use the highest-impact one (`feat` > `fix` > `chore`) and mention the rest in the body.

## Examples

```
feat(server): update Room.LastActivity when someone edits the state
```

```
fix(cli): refine command instruction layout
```

```
feat(api): add endpoint for bulk user import

Allows importing multiple users at once via a CSV payload.
Supports up to 500 records per request.
```

## Staging

- Stage only the files that belong to this one logical change, by explicit path. Never use `git add -A` or `git add .`: they sweep in unrelated edits, scratch files and secrets.
- Run `git status` first. If unrelated changes exist, leave them unstaged and mention them in your reply.
- Never force-add ignored files (`git add -f`, or `git add` on a path `.gitignore` excludes). Ignored files are ignored on purpose (secrets, local config, build output). If the only changes are in ignored files, say so instead of committing.
- If the user already staged files, commit exactly those and do not restage.
- Prefer small, focused commits: one logical change per commit.

## Authorship footer

If an AI agent authored or materially contributed to the change, credit it with a `Co-Authored-By:` footer, one blank line after any body:

- Use the attribution line supplied in the session context verbatim when there is one.
- Otherwise write `Co-Authored-By: <your model name> <noreply address of your vendor>`.
- Omit the footer only when the user wrote or edited the whole diff themselves.
