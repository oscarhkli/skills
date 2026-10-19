---
name: retro
description: Review a finished session for every point where the human had to step in, and work out with them how to make the next session need less of it. Manual only.
disable-model-invocation: true
---

# Retro

Goal: fewer human interventions next time. Every correction, push back or repeated request is a failure of the environment, so find the cause and fix it there. Turn what you find into an actionable plan for the human to approve: linter and hook changes, skill and `CLAUDE.md` edits, refactoring steps.

## Find the transcript

- Claude Code: `~/.claude/projects/<project-dir>/<session>.jsonl`. Take the most recent file in the project's directory, otherwise use the current conversation.
- Copilot CLI: `~/.copilot/session-state/<session-id>/events.jsonl`, with `workspace.yaml` holding the working directory. Match the session by its `cwd`, then take the most recent. User turns are `user.message` events. Fall back to the current conversation.

## Active instructions

Read the instructions the session ran with, so you can tell a rule that was ignored from a missing one. An ignored rule needs enforcement at layer 1 or 2, or one line on why none is possible. A missing rule needs a new or changed line. If an instruction file is unreadable, say so and continue.

- Claude Code: global `~/.claude/CLAUDE.md`, and the project's `CLAUDE.md` and `.claude/CLAUDE.md`, including nested ones along the paths touched.
- Copilot CLI: global `~/.copilot/copilot-instructions.md` and `~/.copilot/instructions/**/*.instructions.md`. Project `.github/copilot-instructions.md`, `.github/instructions/**/*.instructions.md`, `AGENTS.md`, `CLAUDE.md` and `.claude/CLAUDE.md`. Copilot combines them with no precedence, so conflicting lines across files are themselves a finding.

## Intervention signals

Read the whole transcript and collect each time the human stepped in:

- Frustration, push back or a correction of the agent's output.
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

When a finding is a repeatable check, propose a verification skill, script or process instead of a prose rule.

## Before proposing

Read `../principle-lazy-senior-dev/SKILL.md` (relative to this file). Propose the smallest fix. Prefer deleting a rule over adding one. A finding that only adds a rule needs a one-line reason why layers 1 and 2 cannot cover it.

## Output

Produce an action plan the human can approve and then execute, not a list of observations. Edit nothing until they approve.

Each action has:

- Removes: the interventions it should prevent, with evidence (quote or turn).
- Cause: why the agent needed the human.
- Layer: 1-4.
- Change: the exact artifact and edit, with its scope (global or project) and file path, such as a lint rule, hook, test, CI step, script, skill, a `CLAUDE.md` line to add or delete, or a refactoring step. Include the draft text or config.
- Check: how the next sessions show it worked, such as the intervention no longer appearing in the transcript.

Order actions by layer, top first, and mark the quick wins. Drop one-offs that no change can prevent.

## Confirm the plan

The `interview` skill is manual-only, so read `../interview/SKILL.md` (relative to this file) and follow it. What the transcript and instructions already answer is not a question. Ask only what the human decides: which interventions mattered and which were one-offs, the priority order, and global or project scope. Attach your best answer to each as the default. Keep notes only if the human names a directory.

After approval, execute the approved actions, or write them up as tasks if they are too large for this session.
