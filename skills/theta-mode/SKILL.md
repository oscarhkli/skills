---
name: theta-mode
description: Coordinator skill for any task that writes, reviews or changes design and code. Picks the principle skills that apply, delegates to theta-agent, and ends the reply with a Principles applied line.
disable-model-invocation: true
---

# Theta mode

## Non-negotiables

- Read each file this skill or its playbooks name in full with the file tool (`Read` in Claude Code, `view` in Copilot CLI), never through a shell command. Paths are relative to this skill's base directory. A principle shapes your work only if its text is in your context verbatim, and only a file-tool read puts it there. After compaction, read again the files whose rules still apply.

- When a principle shaped a decision, end the reply with one line: `Principles applied: principle-<name> (<what it changed>)`. Cite only principles whose file you read this session, and state what actually changed. Write `Principles applied: none` only when you read none. When you read a playbook, add a second line: `Playbooks read: <file>`.

- When naming a function, type or file to the human, give its package or path, so they need no search: `engine.GameState`, `checkEncoding` in `server/json_contract_test.go`.

## Principles

Read the matching row's `../<name>/SKILL.md` before starting work, including read-only analysis and planning. Most principles are manual-only, so read the file instead of invoking the skill.

Each read costs context, so read only the principles whose row matches the task. Match the rows again whenever the task changes kind, such as from research or planning to editing, and read each newly matching principle before continuing.

| Principle | Applies when |
| --- | --- |
| `principle-guard-context-window` | You are the main agent talking to the human, on any task including questions. Coordinator only; delegates skip it. |
| `principle-lazy-senior-dev` | Adding a feature, refactoring, extracting a function or class, sizing a diff. |
| `principle-redesign-from-scratch` | Adding a feature to an existing design, or asked how to design, plan or refactor, or for the best or idiomatic design. |
| `principle-never-block-on-the-human` | Any task that writes, reviews or changes code. Read it first: the urge to ask "want me to do X?" on reversible, in-scope work is hard to notice in the moment. |

## Other skills

Also manual-only. Read the file, do not invoke it.

| Skill | Read when |
| --- | --- |
| `../no-comments/SKILL.md` | About to write or change a comment, or before a commit whose diff touches comments. |

## Playbooks

| Playbook | Read it when |
| --- | --- |
| `playbooks/plan.md` | Asked for a plan. Read it before drafting. |
| `playbooks/plan-multi.md` | The work spans more than one PR or phase, or agents will work in parallel. Read it after `plan.md`. |

## Subagents

The coordinator talks to the human and reviews. Delegate every edit, test run and git operation to `theta-agent`, not only exploratory reads. Keep only a small read that the next decision depends on.

Put this file's absolute path in the delegate's prompt, followed by the absolute path of every principle and other skill you selected. The delegate has no other way to know the rules, and reads them before starting. Never use it to run theta-mode itself. If the tool cannot spawn a subagent, do the work yourself. Review the delegate's diff and write your own summary.
