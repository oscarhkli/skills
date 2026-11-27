---
name: principle-agent-trust-pyramid
description: Put a change, rule or correction in the highest layer that works, from codebase down to human review.
disable-model-invocation: true
---

# Agent Trust Pyramid

A correction that lands in a higher layer is cheaper and lasts longer. A codebase that makes wrong code hard to write needs no reminder. A rule in prose needs the agent to read it and follow it every time.

The layers come from the retro layers by poteto: https://x.com/poteto/status/2111133080526495985

## Layers

Highest first. Cost rises downward.

1. Codebase: good API design, architecture, refactoring. Wrong code is hard to write.
2. Static analysis: lints, types, compilers, tests, CI. Wrong code fails a gate.
3. Verification: formal and runtime checks. Wrong behaviour shows up when run.
4. Prose: rules, skills, `AGENTS.md`. An agent has to read and follow them.
5. Human review: last resort.

A hook counts as layer 4, prose, because hooks are hard to manage for now and a skill with a script is easier to manage, so a hook is a last resort.

## Rules

- **Pick the highest layer that works.** When planning or building a change, or deciding where a correction lands, name the layer.
- **Justify a lower pick.** When the layer is not the top, add one line on why the layers above cannot cover it. A prose rule or a human check always needs that line.
- **Comments are liabilities.** Deleting a comment beats maintaining it. A lint that blocks one beats a rule that asks.
