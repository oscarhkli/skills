# Plan playbook

- A plan is the how for one PR, written when its story is next, so a fresh `theta-agent` can build it without this conversation.
  - Write one only when the code does not show the how. A small item needs only its backlog paragraph.

## Before drafting

- The coordinator, not the drafting delegate, reads `../interview/SKILL.md` and follows it, because a delegate cannot ask the human.
  - Pass the answers verbatim in the drafting brief.
  - Skip the interview only when the request already settles scope and constraints.
- A plan is a design question. The coordinator reads `../principle-redesign-from-scratch/SKILL.md` and `../principle-agent-trust-pyramid/SKILL.md` and puts both paths in the drafting brief.
  - Choose the design by root cause, language idiom and the highest trust layer first, then size the diff and the stories.
  - A smaller diff or a quicker fix is not a reason to pick a design.
- When the first test needs a spec, write a stub spec first.
- If a design question is open, read `prototype.md` and run it before choosing.
- Write to the directory the human names, else `~/.agents/project-brain/<project>/`, where `<project>` is the name its `README.md` gives the project.

## Structure

- Give each section one line of intent. State each fact once, in the section that owns it.
- A plan has only the sections below, and adds another only when absolutely necessary. Do not copy the shape of older plans in the same folder.
- Every line must change what the implementer does.
  - Findings that repeat the backlog, measured numbers, rejected alternatives and decision history go to the backlog entry or nowhere.
- Goal: what and why, at most 10 lines.
- Context: the current state, as file paths and symbols checked against the code.
  - Name the helpers and test fixtures to reuse, the repo, and the check command if `AGENTS.md` does not name it.
  - No line numbers: another change in flight shifts them.
- Approach: the chosen design as ordered steps, tests first (tdd), not the alternatives.
  - Each step names the files it touches and carries a one-line why.
  - A step of a different kind than the slice's headline, such as a benchmark or Go tests in an e2e slice, says why it belongs in this slice.
  - Decisions the plan can default go here, not in Open items.
- Verification: how the problem is shown solved, with the exact commands and expected output. It also holds what counts as success.
  - Can a test prove it at each layer of the testing pyramid (unit, handler or API, CLI, browser; a layer that fits none of them, such as scene tests with mocks, goes with the nearest one)? A layer left out says why.
  - Each path a user can take to the changed code (retry, reload, repeat, error) gets a check at the layer the user acts on (browser for web).
- Open items: only decisions `../principle-never-block-on-the-human/SKILL.md` leaves to the human, each naming the task it blocks. Omit the section when there are none.

## Writing

- Delegate drafting to `theta-agent`. The `Plan` agent type is read-only and cannot write the files.
- Tell the delegate to remove line-number references (`:123`, `L123`, "line 123") from every file it writes, design docs and backlog entries included, and to paste the Goal section into its report word for word.
- Size gate, before the review: apply the size rule in `slice.md`, where reviewable is the reviewer's load and not a line count. Set no line-count threshold. If the plan outgrows one reviewable change, slice first.

## Review

- Review the draft with the loop in `../self-review/SKILL.md`, with three reviewers instead of its two lenses. All three always run, in parallel, even when the delegate ran its own path check or the human said not to ask questions.
  - Path check: checks every path, symbol, count and command against the code. It runs each count, status and command and does not read it off the plan.
  - User-path check: lists every path a user can take to the changed code and the testing pyramid layer whose test proves it. Each uncovered path becomes a test in Verification or an accepted risk with a reason.
  - Cold read: reads the plan with only the plan and the repo. It reports every step it could not act on and every line it did not need as delete candidates, and every term it had to guess.
- Present the plan path and the Goal, copied word for word from the delegate's report. Add no summary, no list of checks run or skipped, and no question. Do not edit code until the human approves.
