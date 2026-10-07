---
name: no-comments
description: Hunt and remove unnecessary code comments. Runs a read-only "comment hater" audit, then acts on the accepted findings.
disable-model-invocation: true
---

# No Comments

Run the audit defined in [references/comment-hater.md](references/comment-hater.md), then act on its findings. The audit only reports; you make the edits.

Spawn a subagent for the audit and pass it the rules file path and the scope. Do not restate the rules. If the tool cannot spawn a subagent, read the rules file and run the audit yourself as a report-only pass before editing anything.

If no scope is provided, the scope is every file touched by the current diff against the main branch. Pass a narrower scope to clean up in phases.

## Steps

- Run the audit with the scope.
- Inspect the report and the diff. Reject scope escapes, deletions protected by an exception, and misjudged `KILL` flags.
- A `Keep` survives only with proof that the comment concerns something we cannot change.
- Fix every trivial `KILL` by deleting the comment.
- A trivial `Refactor` is local and behaviour-preserving (rename, extract a variable or function, state a rule in a test name). Make the change directly when existing tests cover the code. When nothing covers it, write a characterization test first.
- For a non-trivial `Refactor`, investigate yourself: read the affected code and tests, sketch the target design, list blast radius and migration steps. Then implement the additive first step: add the new design beside the old one, keep existing signatures and callers unchanged, and run the tests. Switching callers and deleting the old API stay in the report. Ask the human only about decisions that change visible behaviour or public contracts.
- Run the project's tests after the edits, in each worktree or checkout touched. Report the result.
- Run `unslop` over the comments that survive (style patterns only, never keep-or-kill) to strip AI tells from their wording.
- Report the kill count, kept comments, architecture sketch, fixes, and open work.
