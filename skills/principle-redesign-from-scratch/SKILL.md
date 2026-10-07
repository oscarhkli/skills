---
name: principle-redesign-from-scratch
description: Principle for design work. When adding a feature to an existing design, or answering "How should we design/refactor this?" or "What is the best/idiomatic/industry-standard design?", design as if the codebase were empty and the feature existed from day one, instead of gluing it onto the current architecture.
disable-model-invocation: true
---

# Redesign from Scratch

Existing code may be badly designed. Following its habits makes the design worse.

## Three kinds of input

| Kind | Examples | Treatment |
|---|---|---|
| Hard constraints | Persisted data formats, public or deployed APIs, wire protocols, other consumers' contracts | Inputs to the design. Breaking one is called out as a migration. |
| Language and ecosystem idiom | Effective Go, JS/TS industry conventions, framework conventions | The target. Design the idiomatic way. |
| This codebase's own habits | Odd naming, a layering quirk, a pattern copied because it was already there | Ignore. |

## Steps

- Read every affected file, tests included, to find the hard constraints and understand the current design. Do not read to learn what to imitate.
- Ask: "If we were doing this from scratch, what would we build?"
- Examine the consequences: blast radius, migration order, what gets deleted.
- Propagate the change through every reference.

## Output

Present the target design, the gap to today's code, and the smallest sequence of steps to get there. Implement the first step only if the task asked for implementation. Do not rewrite everything at once.
