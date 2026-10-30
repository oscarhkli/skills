---
name: retro
description: Review a finished session for every point where the human had to step in, and work out with them how to make the next session need less of it. Manual only.
disable-model-invocation: true
---

# Retro

Goal: fewer human interventions next time. Every correction, push back or repeated request is a failure of the environment, so find the cause and fix it there. Turn what you find into an actionable plan for the human to approve: linter and hook changes, skill and `CLAUDE.md` edits, refactoring steps.

## Find the transcripts

A retro covers the current session, or one or more other sessions the human names by ID, title, date or topic. A long session often runs its retro in a fresh session, and then the most recent transcript is the retro itself, never the target.

- Claude Code: `~/.claude/projects/<project-dir>/<session>.jsonl`.
- Copilot CLI: `~/.copilot/session-state/<session-id>/events.jsonl`, with `workspace.yaml` holding the working directory. Match the session by its `cwd`. User turns are `user.message` events.
- Find a named session by grepping the transcripts for its title or a phrase from it, narrowed by file date. Confirm the match from its first human turn.
- With no session named, use the current conversation.
- List the human turns with `scripts/human_turns.py <transcript>...` (relative to this file). Add `--full` to print each turn in full with the tail of the agent reply before it, then read around each turn that looks like an intervention.
- With several sessions, merge an intervention that recurs across them into one finding and cite every session.

## Active instructions

Read the instructions the session ran with, so you can tell a rule that was ignored from a missing one. An ignored rule needs enforcement at layer 1 or 2, or one line on why none is possible. A missing rule needs a new or changed line. If an instruction file is unreadable, say so and continue.

- Claude Code: global `~/.claude/CLAUDE.md`, and the project's `CLAUDE.md` and `.claude/CLAUDE.md`, including nested ones along the paths touched.
- Copilot CLI: global `~/.copilot/copilot-instructions.md` and `~/.copilot/instructions/**/*.instructions.md`. Project `.github/copilot-instructions.md`, `.github/instructions/**/*.instructions.md`, `AGENTS.md`, `CLAUDE.md` and `.claude/CLAUDE.md`. Copilot combines them with no precedence, so conflicting lines across files are themselves a finding.

Check whether the rule reached the agent that broke it. A delegate loads neither memory nor the parent's skills, so it sees a skill, playbook or reference only when its brief names the path. A rule the delegate never saw is missing, not ignored.

## Intervention signals

Read the whole transcript and collect each time the human stepped in:

- Frustration, push back or a correction of the agent's output.
- Plain-language confusion: "I don't understand", "what do you mean", "why did you add that". The human may say this without typing `/wait-what`.
- A `/wait-what` call: the previous reply was confusing.
- A `/unslop` call: the agent wrote slop on its own.
- The same instruction repeated, or a rule from `CLAUDE.md`, `AGENTS.md`, or a skill the agent ignored.
- Work the agent stopped to ask about although it was reversible and in scope.

## Layers

Starting point from poteto's retro layers: https://x.com/poteto/status/2111133080526495985

For each intervention, find the cause and the highest layer that removes it. Spend effort at the top. Each layer down catches less and costs more attention.

1. Codebase: better architecture, types, invariants and boundaries, so the easy path is the right one. This removes a problem for good.
2. Static analysis: lint rules, tests, CI, formatters, hooks. Cheap in tokens, catches issues before review.
3. Prose: comments, AGENTS.md rules, skills. Not enforceable and relies on agent judgment, so use sparingly.
4. Human review: does not scale. Reserve it for what the layers above cannot check.

When a finding is a repeatable check, propose a verification skill, script or process instead of a prose rule. A lint or hook earns its place only when a pattern decides the result with few false positives. Length, tone and structure are judgment, not lint.

At layer 3, prefer a skill, playbook or reference over memory, since they are portable across tools and reach delegates. For style and format, a worked sample in `references/` beats a list of rules.

## Before proposing

Read `../principle-lazy-senior-dev/SKILL.md` (relative to this file). Propose the smallest fix. Prefer deleting a rule over adding one. A finding that only adds a rule needs a one-line reason why layers 1 and 2 cannot cover it.

## Output

Produce an action plan the human can approve and then execute, not a list of observations. Edit nothing until they approve.

Each action has:

- Removes: the interventions it should prevent, each with its session, turn and a quote. The human may not remember a long session, so a change with several parts, such as lint checks or config keys, cites evidence per part.
- Cause: why the agent needed the human.
- Layer: 1-4.
- Change: the exact artifact and edit, with its scope (global or project) and file path, such as a lint rule, hook, test, CI step, script, skill, a `CLAUDE.md` line to add or delete, or a refactoring step. Include the draft text or config.
- Tradeoffs: pros, cons and pitfalls, such as false positives, cost per session, scope creep or a perverse incentive.
- Check: how the next sessions show it worked, such as the intervention no longer appearing in the transcript.

Order actions by layer, top first, and mark the quick wins. Drop one-offs that no change can prevent.

## Confirm the plan

The `interview` skill is manual-only, so read `../interview/SKILL.md` (relative to this file) and follow it. What the transcript and instructions already answer is not a question. Ask only what the human decides: which interventions mattered and which were one-offs, the priority order, and global or project scope. Attach your best answer to each as the default. Keep notes only if the human names a directory.

After approval, execute the approved actions, or write them up as tasks if they are too large for this session.
