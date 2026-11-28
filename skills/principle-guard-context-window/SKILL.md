---
name: principle-guard-context-window
description: Coordinator only. Keep file contents and command output out of the main context and work from delegate summaries.
disable-model-invocation: true
---

# Guard context window

Accumulated context degrades reasoning quality. The main agent's context is for the conversation with the human, decisions and review. Raw payloads and exploration narratives crowd those out.

This applies to the coordinator only. A delegate does the heavy work itself and never delegates further. What to delegate follows `theta-mode`'s Subagents section.

## Probe the size first

Treat an unknown size as large and probe it first. Check a file's length (`wc -l`) or a diff's size (`git diff --stat`) before putting its content in your context, and count a search's matches (`grep -c`) before listing them, narrowing the pattern if the count is high. Once you know what a file says, from your own look or a delegate's summary, carry that summary forward instead of opening the file again.

## Result

Ask for a summary of about 30 lines or fewer, with file paths and line numbers, not raw dumps or step-by-step narration. Write it the way `unslop` would: conclusion first, no narration, no restated task, no recap.

Have a delegate check a cited claim that matters.

## While waiting

When you wait on a delegate, reply in two or three short lines: what you delegated and what comes back. Give no partial answer. Present the full answer when the delegate reports.
