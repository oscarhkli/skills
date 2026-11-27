# Human brief

A message that asks the human to decide has four parts, in this order:

1. The situation, in plain business words with named actors.
2. The question. With several decisions, number them and give each its own pick and reply.
3. Your pick, with its cost.
4. The exact reply you expect.

Define a term in a clause the first time you use it. A trivial, reversible pick needs no message: act and report. For other reversible picks, act on the pick in the same turn; the message lets the human overrule. An irreversible pick waits for the reply. Never end a reversible, in-scope step with "say go", except the plan and the slice index, which wait for approval.

## Sample

The nightly export job sometimes cannot get a database lock, because another job holds it.

### Bad

> The export hits lock contention on `export_state`. Options: (A) unbounded retry with backoff, (B) bounded retry, N=5, then fail, (C) skip the run and alert. A has starvation risk, B changes the SLA semantics, C needs a pager rule. Thoughts?

- Jargon with no definition: "lock contention", "starvation", "SLA semantics".
- Three options and no pick.
- No stated reply, so the human has to guess what to type.

### Good

> The nightly export needs a database lock, and the cleanup job sometimes holds it. When the lock is taken, the export waits one minute and asks again.
>
> Question: should the export ask again forever, or give up after 5 tries?
>
> My pick: give up after 5 tries. A stuck export then shows up as a failed run the same morning, where retrying forever hides it until someone notices the missing file. The cost: on a bad night the export does not run.
>
> Reply "5" to accept, or a different number. I proceed with 5 meanwhile.
