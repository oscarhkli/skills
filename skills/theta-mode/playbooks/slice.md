# Slice playbook

Turns an initiative (a large goal) into stories, before any implementation plan exists. A story here is a brief. Its implementation plan comes later, in `plan.md`'s shape.

## Choose the strategy

Pick by what the goal needs. Mix them across the stories of one initiative.

| Goal | Strategy |
| --- | --- |
| A user-visible capability ships | Vertical slice. The default. Each story cuts through every layer it needs and changes behaviour someone can see. |
| Code must change first with no behaviour change (a refactor, a seam, a shared type) | Technical story. It must name the next story that uses it. Without one, drop it. |
| Replacing an existing path | Expand then contract, also called branch by abstraction. Add the new path beside the old one, switch the callers, then delete the old one in one final story. That story holds all the deletion-only work, so do not make one story per deleted thing. |
| Unfinished work must be deployed before it is ready | Feature flag. If nothing is deployed that consumes the work, say the flag does not apply and skip it. |
| The breakdown depends on a design question that reading cannot settle, such as a state machine or concurrency | Prototype first. Read `prototype.md`, and slice after the answer. A formal model can be added to this step later. |

## Rules

- Independently deployable: after each story, everything is green and existing callers still work.
- Aim for one problem per story. A story that closes two usually splits; two stories that close one usually merge. This is the default, not a ban. A story may close several related problems when splitting them leaves neither one deployable or reviewable alone.
- Size is the reviewer's cognitive load, not line count. The number of files, layers touched and behaviour changes to hold in mind at once are signals, with no hard limit. If a story is too much to review in one sitting, look for two problems in it. A long list of one kind of mechanical edit is fine. The size gate in `plan.md` is the same kind of signal.
- Docs travel with the story that makes them false. There is no separate docs story.

## A story is a brief

A brief says what and why. It never says how: no file names, test names or line numbers. It holds:

- The problem it closes.
- The behaviour change for each consumer (browser, CLI, API, other services), or "none, technical story".
- The proving test, described by what it shows, and whether it can fail. A proof that depends on randomness or a long multi-round run must first be shown deterministic, or moved to a lower layer.
- What it assumes from earlier stories.

## Just in time

- Write the implementation plan (`plan.md`) only for the next story, after the previous one merged. Later stories stay briefs.
- After each merge, re-read the remaining briefs against what shipped. Fix their assumptions before planning the next story.

## Output

- For the human: an index table with one row per story: story, scope, depends on and why, merge order.
- For the agent that plans a story: that story's brief. It reads only its own brief and the stories it depends on.

Then read `plan-multi.md` for the index and the dependency rules.
