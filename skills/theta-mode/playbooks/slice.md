# Slice playbook

Turns an initiative (a large goal) into stories before any implementation plan exists. A story is a brief. Its plan comes later, in `plan.md`'s shape.

## Choose the strategy

Pick by what the goal needs. Mix them across the stories of one initiative.

| Goal | Strategy |
| --- | --- |
| A user-visible capability ships | Vertical slice. The default. Each story cuts through every layer it needs and changes behaviour someone can see. |
| Code must change first with no behaviour change (a refactor, a seam, a shared type) | Technical story. It must name the next story that uses it. Without one, drop it. |
| Replacing an existing path | Expand then contract (branch by abstraction). Add the new path beside the old one, switch the callers, then delete the old one in one final story that holds all the deletion-only work. |
| Unfinished work must be deployed before it is ready | Feature flag. If nothing deployed consumes the work, skip the flag. |
| The breakdown depends on a design question that reading cannot settle, such as a state machine or concurrency | Prototype first. Read `prototype.md`, and slice after the answer. |

## Rules

- Independently deployable: after each story, everything is green and existing callers still work.
- One problem per story. A story that closes two splits, and two stories that close one merge, unless one is an enabler (a technical story that names its consumer). Exception: keep several related problems together when splitting leaves neither deployable or reviewable alone.
- Size is a balance. Each story is independently developable, testable and deployable. In theory, cut as small as possible. In practice each story carries fixed review and merge overhead, so merge neighbouring stories until the overhead is acceptable and the diff stays reviewable.
- Reviewable means the reviewer's cognitive load, not line count. Files, layers and behaviour changes to hold in mind at once are signals, with no hard limit. A critical file, one that changes behaviour, weighs more than a mechanical one, and a long list of one kind of mechanical edit is fine. If a story's plan or implementation outgrows one reviewable change, re-slice it and look for two problems in it.
- Once a story's plan lists its files, each file, finding or task belongs to exactly one story. Check by listing every owner and finding no gaps or overlaps. Two stories editing the same file is a dependency; record it.
- Put shared prerequisites, such as a type, helper or test fixture several stories need, in their own first story.
- Docs travel with the story that makes them false. There is no separate docs story.

## A story is a brief

A brief says what and why. It adds a how only for a non-obvious technical constraint a planner could not find from the code. `plan.md` owns the how: files, tests and steps. It holds:

- The problem it closes.
- The behaviour change for each consumer (browser, CLI, API, other services), or "none, technical story".
- The proving test, described by what it shows, and whether it can fail. A proof that depends on randomness or a long multi-round run must first be shown deterministic, or moved to a lower layer.
- What it assumes from earlier stories.

## Just in time

- Write a story's implementation plan (owned by `plan.md`) when that story is next to start, after the stories it depends on have merged. Stories with no dependency on each other may start together. Later stories stay briefs.
- After each merge, re-read the remaining briefs against what shipped. Fix their assumptions before planning the next story.

## Index (README)

One README next to the briefs and plans holds:

- Goal and why the work is split, at most 10 lines.
- A table: story, scope, depends on, can run in parallel with, owner agent.
- The merge order, and why each dependency exists.
- Shared files and the story that owns each edit.
- Counts that must reconcile, such as findings per story summing to the total.
- Kickoff: the one-line prompt that starts a story, so the human does not retype context. Each story plan's Start here supplies the rest once it is written.

## Dependencies and concurrency

- A story starts from the default branch plus the stories it depends on. Say which, by name.
- Stories with no dependency between them run concurrently.
- When a dependency merges after a story has started, rebase and rerun the story's verification.
- Each story's verification passes on its own branch, without the other stories.

## Keeping stories current

- When a story changes something its dependents rely on, such as a name, a signature, a file owner or a decision, spawn one `theta-agent` per affected dependent. Each updates that story's brief, or its plan if one exists, and its row in the index. Then rerun the index check.
- When a story merges, refresh the deferred and decision sections of every remaining story's PR. Delete the ones that are now settled.

## Checking

- A `theta-agent` checks the index against the story plans: every story listed once, dependencies symmetric, counts reconciled, no file owned twice.
- Present the index and the story plans together, and wait.

## Output

- For the human: the index.
- For the agent that plans a story: that story's brief. It reads only its own brief and the stories it depends on.
