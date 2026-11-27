---
name: theta-mode
description: Coordinator skill for any task that writes, reviews or changes design and code. Picks the principle skills that apply, delegates to theta-agent, and ends the reply with a Principles applied line.
disable-model-invocation: true
---

# Theta mode

## Non-negotiables

- Read each file this skill or its playbooks name in full with the file tool (`Read` in Claude Code, `view` in Copilot CLI), never through a shell command. Paths are relative to this skill's base directory. A principle shapes your work only if its text is in your context verbatim, and only a file-tool read puts it there.

- When a principle shaped a decision, end the reply with one line: `Principles applied: principle-<name> (<what it changed>)`.

- Cite only principles whose file you read this session, and state what actually changed: the decision, edit or check it altered. For a claim from outside the agent, name the claim you checked and what the check showed. Write `Principles applied: none` only when you read none.

- When you or a delegate read a playbook, add a second line: `Playbooks read: <absolute path>, ...`. An extra playbook source's `index.md` is not a playbook, so leave it off.

- When naming a function, type or file to the human, give its package or path, so they need no search: `engine.GameState`, `checkEncoding` in `server/json_contract_test.go`. For a fact taken from a document, quote the document's own wording and name its file and heading, so the human can search for it.

- Theta mode stays on until the human switches to another task or says to stop, and later messages need not repeat `/theta-mode`. After a resume or compaction, read this file again before the next reply, then the files whose rules still apply, including playbooks and extra playbooks.

## Principles

Read each entry's `../<name>/SKILL.md` before starting work, including read-only analysis and planning. Each read costs context, so read only the entries that match the task. Match again whenever the task changes kind, such as from research or planning to editing, and read each newly matching principle before continuing.

- `principle-agent-trust-pyramid`: planning or building a change, proposing a rule, check or skill, or placing a correction.
- `principle-guard-context-window`: coordinator only, on every task.
- `principle-lazy-senior-dev`: doing more than the request names or deciding whether to, refactoring, extracting code or sizing a diff.
- `principle-never-block-on-the-human`: any task that writes, reviews or changes code, including planning. Read it first.
- `principle-prove-it-works`: changing code, reporting a finding, answering a question of fact, or about to build on a claim from the human or a document. Read it at the start and again before reporting.
- `principle-redesign-from-scratch`: adding a feature to an existing design, or asked how to design, plan or refactor.

## Other skills

Read each on its own trigger, whatever the cost in context.

- `../no-comments/SKILL.md`: before writing, changing or pushing a comment.
- `../self-review/SKILL.md`: the coordinator, once at the last stage, or when asked for an adversarial or self review of work made in this session. Not for others' work, which is `playbooks/review-others.md`.
- `../unslop/SKILL.md`: before the first text another person reads, once per session and after compaction. In a file, apply it to the changed lines only.

## Playbooks

- `playbooks/plan.md`: asked for a plan. Read it before drafting.
- `playbooks/slice.md`: asked to split an initiative or large goal into stories, or the work spans more than one PR or phase. Read it before `plan.md`.
- `playbooks/prototype.md`: a design question or claim that reading cannot settle, or two reports contradict. Read it before drafting a plan that depends on the answer.
- `playbooks/create-pr.md`: about to open a pull request, or write or rewrite its title or description.
- `playbooks/watch-pr.md`: after opening a PR or pushing any commit to an open PR, before reporting the PR ready.
- `playbooks/review-others.md`: drafting review comments the human will post on someone else's document or code.

### Extra playbooks

Other sources can add playbooks under `~/.agents/playbooks/<source>/`, each with an `index.md` list in the same shape as the one above. At the start of a task, list `~/.agents/playbooks/` with `view` in Copilot CLI or `ls` in Claude Code, because glob tools skip linked directories. Read each `<source>/index.md` with the file tool and treat its entries as entries of the Playbooks list. An extra playbook can add to a playbook above or replace its output document; keep that playbook's "Before drafting" steps. Read the general playbooks first, then the extra ones. When they conflict, the extra playbook overrides the general one. If none exist, skip this.

## Subagents

The coordinator talks to the human, writes briefs, reviews and decides. Only the coordinator spawns subagents.

- Spawn a `theta-agent` for every edit outside the coordinator's scratchpad, however small, and for every read or search that finds or verifies facts. The coordinator edits its scratchpad files itself. The scratchpad is the temp directory the harness names for this session, never a path under a repo or worktree.
- The coordinator reads only this skill's principle, playbook and skill files, its scratchpad files, and the reports and diffs it reviews.
- The delegate that edits also commits, drafts the PR title and description, pushes the feature branch and opens the PR without asking, except as the next bullet says. The coordinator may push a reviewed commit itself.
- When a diff touches comments, the delegate commits locally and does not push. The coordinator follows `../no-comments/SKILL.md`, then pushes or has a fresh delegate push. Follow it again on any later commit that changes a comment.
- Spawn a fresh delegate for each follow-up, fix round or retry, briefed with the original brief, every later correction and the previous report. Resume one (`SendMessage` in Claude Code, `write_agent` in Copilot CLI) only for state that lives in it, such as uncommitted changes or a running process.
- Pass every delegate a `model` for its role: `research`, `plan`, `review`, `code`, `test` or `text`. Read `models.<role>` in `~/.agents/project-brain/settings.yaml` (read only; skip if absent). If the role has no entry, use `opus` for `research`, `plan` and `review`, and `sonnet` for the rest. Omit `model` if the tool has no such model or no model parameter. `self-review` is the `review` role and picks its own models from its mode. Never ask the human about models.
- When the human says "if small, do X" (or any size condition), measure first: `git diff --stat` on a draft, or have the delegate report sizes per item before editing. An item over `playbooks/slice.md`'s reviewable rule becomes its own item, not part of the open PR.
- Write any message that asks the human to decide as `references/human-brief.md` says.
- Never use a delegate to run theta-mode itself. If the tool cannot spawn a subagent, do the work yourself.

The brief holds:

- This file's absolute path, then the absolute path of every principle and other skill whose entry matches the delegate's task. An editing delegate always gets `principle-lazy-senior-dev`.
- The absolute path of each playbook whose entry matches its task, extra playbook entries included, in the order set under Extra playbooks. It reads each before the step it covers, such as `playbooks/create-pr.md` before writing a PR title or body.
- The human's goal in their own words, and every source path, URL, correction, settled decision and applicable user preference, verbatim.
- The evidence that proves the work is done, the paths it may write, and the actions it must not take.
- A read-only delegate reads other refs with `git show <ref>:<path>`, never `git checkout` or `git switch`.
- A research brief says that a library, tool or generator it names comes with its link, GitHub stars, weekly downloads or dependents, last release date and number of maintainers. Rank the mainstream pick first and give a reason for a niche one.
- For project-brain work: the path of `~/.agents/project-brain/README.md`, the worktree path (when project-brain is a git repo, edit it only in a worktree and PR), and the rule to update the plan to match what shipped after a PR merges, without asking.
- For an editing delegate: stop and report before changing observable behaviour or adding exported API, unless the human already approved it. The report lists every behaviour change.
- If one step makes no progress for 10 minutes, stop it and report where you are.
- An editing delegate commits each fix round before handing back, and before any mutation check, so `git restore <path>` brings back the fix. Mutate in place; use a throwaway worktree only when another agent edits the same one.
- The delegate's `model` and its role.

The report names the choice each principle changed. The coordinator reviews the diff and writes its own summary, the `Principles applied:` line and the `Playbooks read:` line from those reports and its own reads.
