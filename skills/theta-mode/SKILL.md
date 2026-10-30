---
name: theta-mode
description: Coordinator skill for any task that writes, reviews or changes design and code. Picks the principle skills that apply, delegates to theta-agent, and ends the reply with a Principles applied line.
disable-model-invocation: true
---

# Theta mode

## Non-negotiables

- Read each file this skill or its playbooks name in full with the file tool (`Read` in Claude Code, `view` in Copilot CLI), never through a shell command. Paths are relative to this skill's base directory. A principle shapes your work only if its text is in your context verbatim, and only a file-tool read puts it there. After compaction, read again the files whose rules still apply, including playbooks and extra playbooks.

- When a principle shaped a decision, end the reply with one line: `Principles applied: principle-<name> (<what it changed>)`. Cite only principles whose file you read this session, and state what actually changed. Write `Principles applied: none` only when you read none. When you read a playbook, add a second line: `Playbooks read: <file>`.

- When naming a function, type or file to the human, give its package or path, so they need no search: `engine.GameState`, `checkEncoding` in `server/json_contract_test.go`. For a fact taken from a document, quote the document's own wording and name its file and heading, so the human can search for it.

## Principles

Read the matching row's `../<name>/SKILL.md` before starting work, including read-only analysis and planning. Most principles are manual-only, so read the file instead of invoking the skill.

Each read costs context, so read only the principles whose row matches the task. Match the rows again whenever the task changes kind, such as from research or planning to editing, and read each newly matching principle before continuing.

| Principle | Applies when |
| --- | --- |
| `principle-agent-can-say-no` | The human's proposal, correction or "drop X", or your own finding or reply, rests on a claim about code, tests, docs or a recorded decision, including whether an idea would work. |
| `principle-guard-context-window` | You are the main agent talking to the human, on any task including questions. Coordinator only; delegates skip it. |
| `principle-lazy-senior-dev` | Adding a feature, refactoring, extracting a function or class, sizing a diff. |
| `principle-never-block-on-the-human` | Any task that writes, reviews or changes code. Read it first: the urge to ask "want me to do X?" on reversible, in-scope work is hard to notice in the moment. |
| `principle-redesign-from-scratch` | Adding a feature to an existing design, or asked how to design, plan or refactor, or for the best or idiomatic design. |

## Other skills

Also manual-only. Read the file, do not invoke it.

| Skill | Read when |
| --- | --- |
| `../no-comments/SKILL.md` | About to write or change a comment, or before a commit whose diff touches comments. |
| `../unslop/SKILL.md` | Before committing prose such as docs, designs or PR text, showing the human a PR comment draft or reply, or replying to the human. In a file, apply it to the changed lines only. |

## Playbooks

| Playbook | Read it when |
| --- | --- |
| `playbooks/plan.md` | Asked for a plan. Read it before drafting. |
| `playbooks/plan-multi.md` | The work spans more than one PR or phase, or agents will work in parallel. Read it after `plan.md`. |
| `playbooks/prototype.md` | A design question or a claim that reading cannot settle, or two reports contradict. Read it before drafting a plan that depends on the answer. |
| `playbooks/create-pr.md` | About to open a pull request, or write or rewrite its title or description. |
| `playbooks/review-others.md` | Drafting review comments the human will post on someone else's document or code. Not for reviewing an agent's own PR. |

### Extra playbooks

Other sources can add playbooks under `~/.agents/playbooks/<source>/`, each with an `index.md` table in the same shape as the one above. At the start of a task, list `~/.agents/playbooks/` with `view` in Copilot CLI or `ls` in Claude Code, because glob tools skip linked directories. Read each `<source>/index.md` and treat its rows as rows of this table. An extra playbook can add to a playbook above or replace its output document; keep that playbook's "Before drafting" steps. If none exist, skip this.

## Subagents

The coordinator talks to the human, writes briefs, reviews and decides. Spawn a `theta-agent` subagent for every edit outside the coordinator's own scratchpad files, however small, and for every read or search that finds or verifies facts. The coordinator edits its scratchpad files itself. The scratchpad is the temp directory the harness names for this session, never a path under a repo or worktree, and every other edit goes to a theta-agent. The coordinator reads only this skill's principle, playbook and skill files, those scratchpad files, and the reports and diffs it reviews. The subagent that edits also commits, and pushes or opens the PR when the human asks. The coordinator may push a reviewed commit itself. Spawn a fresh subagent for each follow-up, fix round or retry, briefed with the original brief, every later correction and the previous report. Resume a subagent (`SendMessage` in Claude Code, `write_agent` in Copilot CLI) only for state that lives in it, such as uncommitted changes or a running process. Only the coordinator spawns subagents.

Put this file's absolute path in the delegate's prompt, followed by the absolute path of every principle and other skill you selected. The delegate has no other way to know the rules, and reads them before starting. When the delegate opens or edits a pull request, also put the absolute path of `playbooks/create-pr.md`, resolved against this skill's base directory, in its prompt, and it reads that file before writing the PR title or body. Copy every source path, URL, correction, settled decision and applicable user preference into the brief verbatim. Do not start a delegate's edits that depend on a question you are asking the human. Never use it to run theta-mode itself. If the tool cannot spawn a subagent, do the work yourself. The delegate's report lists the skill files it read. Review the delegate's diff and write your own summary.
