# Handoff playbook

Use it for work that spans sessions or compactions. A fresh agent reads the notes folder instead of the transcript and continues without asking the human to repeat anything.

## Notes folder

- One folder per task, holding an `index.md`. Use the location project instructions name, else pick one outside the repo and tell the human its path. Never commit it.
- Name the folder after the task, such as `<repo>-<task>`, so a later session finds it by name.
- Put detail that does not fit `index.md` in sibling files and link them from the index. A fresh agent opens a sibling only when the index points to it.

## `index.md`

It holds the current state, in these sections:

- **Goal**: what and why, at most 5 lines.
- **Settled decisions**: one line each, with the reason only where a reader would otherwise reverse it.
- **Sources**: requirement sources in precedence order, each with its path or URL. Say which wins on conflict.
- **Open questions**: what the human has not answered, and what is blocked on each.
- **Work**: branches, worktrees and PRs, each with its status.
- **Next step**: the one action a fresh agent takes first.

Keep it under about 60 lines. Rewrite a line in place when it changes. Do not add history, timestamps or "changed from" notes.

## Who reads and writes

- The coordinator reads `index.md` itself. It is short by design, and the next decision depends on it.
- The coordinator is the only writer. Delegates report new decisions, sources and open questions in their result, and the coordinator records them. This avoids two agents editing one file.
- Copy the lines a delegate needs into its brief verbatim. A delegate does not read the notes folder unless the brief names a sibling file.

## When

- **Start**: read `index.md` before any other work. Tell the human in two lines what state you understood and what you will do next.
- **Decision settled**: update the index before replying, so a crash or compaction cannot lose it.
- **After compaction**: read it again.
- **End of a session**: check that Work and Next step match reality.

## Resuming

The index can be stale. Before acting on it, have a delegate confirm that each listed branch, worktree and PR still exists and has the status written. Fix the lines that differ, and tell the human what changed.

If the index and the human's new message disagree, follow the human and update the index.
