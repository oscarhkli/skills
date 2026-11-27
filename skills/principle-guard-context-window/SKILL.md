---
name: principle-guard-context-window
description: Coordinator only. Delegate heavy reads and keep only the summary in the main context.
disable-model-invocation: true
---

# Guard context window

Accumulated context degrades reasoning quality. The main agent's context is for the conversation with the human, decisions and review. Raw payloads and exploration narratives crowd those out.

This applies to the coordinator only. A delegate does the heavy work itself and never delegates further.

## Probe before reading

What to delegate follows `theta-mode`'s Subagents section.

Treat an unknown size as large and probe it first. Check a file's length (`wc -l`) or a diff's size (`git diff --stat`) before reading it, and count a search's matches (`grep -c`) before listing them, narrowing the pattern if the count is high. Once a file's content has been read, carry its summary forward instead of reading it again.

## Result

Ask for a summary of about 30 lines or fewer, with file paths and line numbers, not raw dumps or step-by-step narration. Write it the way `unslop` would: conclusion first, no narration, no restated task, no recap. Apply that standard without loading the skill, since loading it costs the context this principle protects.

Read a cited file yourself only to verify a claim that matters.

## While waiting

When you wait on a delegate, reply in two or three short lines: what you delegated and what comes back. Give no partial answer. Present the full answer when the delegate reports.
