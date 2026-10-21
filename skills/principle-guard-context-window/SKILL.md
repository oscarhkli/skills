---
name: principle-guard-context-window
description: Principle for the main agent that talks to the human and orchestrates subagents. When a task needs many file reads, large command output or long searches, delegate it and keep only the summary in the main context.
disable-model-invocation: true
---

# Guard context window

Accumulated context degrades reasoning quality. The main agent's context is for the conversation with the human, decisions and review. Raw payloads and exploration narratives crowd those out.

This applies to the coordinator only. A delegate does the heavy work itself and never delegates further.

## When to delegate

- About 1,000 lines of tool output already sit in the main context, whoever asked for them. Small reads add up over a back-and-forth, so count the session, not the task. Delegate every further exploratory read.
- A single read or command is likely to return over about 300 lines, such as a large file, test logs, diffs or listings.
- The work is heavy and independent of the conversation, so a self-contained brief can describe it. A small task is cheaper to do yourself than to brief.

Treat an unknown size as large and probe it first. Check a file's length (`wc -l`) or a diff's size (`git diff --stat`) before reading it, and count a search's matches (`grep -c`) before listing them, narrowing the pattern if the count is high.

A small read that the very next decision depends on stays in the main agent. Once a file's content has been read, carry its summary forward instead of reading it again.

## Brief

Give the delegate the goal, absolute paths and the shape of the answer wanted. It has none of this conversation, so anything left out is lost.

## Result

Ask for a summary of about 30 lines or fewer, with file paths and line numbers, not raw dumps or step-by-step narration. Write it the way `unslop` would: conclusion first, no narration, no restated task, no recap. Apply that standard without loading the skill, since loading it costs the context this principle protects.

Read a cited file yourself only to verify a claim that matters.
