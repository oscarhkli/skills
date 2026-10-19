---
name: theta-mode
description: Coordinator skill for any task that writes, reviews or changes design and code. Picks the principle skills that apply, delegates to theta-agent, and ends the reply with a Principles applied line.
---

# Theta mode

## Principles

A principle only shapes your work if its text is in your context, and only a Read tool call on its file puts it there verbatim. Open the matching row's file with the Read tool, not `cat` through Bash, in full, before starting work, including read-only analysis and planning. Paths are relative to this skill's base directory (`../principle-<name>/SKILL.md`). Most principles are manual-only and may not appear in the skill list.

Each read costs context, so open only the principles whose row matches the task. A task that matches no row, such as a question, reads none.

| Principle | Applies when |
| --- | --- |
| `principle-lazy-senior-dev` | Adding a feature, refactoring, extracting a function or class, sizing a diff. |
| `principle-redesign-from-scratch` | Adding a feature to an existing design, or asked how to design, plan or refactor, or for the best or idiomatic design. |
| `principle-never-block-on-the-human` | Any task that writes, reviews or changes code. Read it first: the urge to ask "want me to do X?" on reversible, in-scope work is hard to notice in the moment. |

When a principle shaped a decision, end the reply with one line: `Principles applied: principle-<name> (<what it changed>)`. Cite only principles whose file you read this session.

## Playbooks

| Playbook | Read it when |
| --- | --- |
| `playbooks/plan.md` | Asked for a plan. Read it before drafting. |
| `playbooks/plan-multi.md` | The work spans more than one PR or phase, or agents will work in parallel. Read it after `plan.md`. |

## Subagents

Delegate with the `theta-agent` agent and put this file's absolute path in the prompt, followed by the absolute path of each principle you selected. The delegate reads them in full before starting. Never use it to run theta-mode itself. If the tool cannot spawn a subagent, do the work yourself. Review the delegate's diff and write your own summary.
