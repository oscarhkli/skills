# Watch PR playbook

Use it after every push to an open PR: a new PR, a follow-up commit, a merge of main, a review fix.

- Watch the checks with `gh pr checks --watch`. If it prints "No checks reported" and exits 1, the PR has no checks: there is nothing to watch, so go straight to the last stage.
- Never pipe `gh pr checks` through `head` or `tail`. Report the head SHA (`gh pr view <n> --json headRefOid`) and the full check list, with every non-success check named. The coordinator tells the human CI is green only from that output, or has a research delegate produce it, never from a delegate's summary sentence.
- If one fails, read the failing step's log, find the cause, plan the fix, push it as a new commit and watch again. Repeat until every check is green.
- A failure the PR did not cause (the same check also fails on main), or one that needs a decision, secret or setting change from the human, is reported with evidence instead of fixed.
- After three failed fix rounds on the same check, stop and report the root cause and options.
- The coordinator runs self-review once, at the last stage: when the work is finished, read `../../self-review/SKILL.md` and run it before telling the human the PR is ready for review. It does not wait for CI; any fix it pushes is a new push, so watch the checks again. Skip it after earlier or small follow-up pushes. A delegate that pushed does not run it; it reports the green checks.
- Before telling the human the PR is ready, write one line: `head <sha>; CI <N/N> on <sha>; self-review verifier on <sha> or n/a (state why); comment audit on <sha> or 'diff has no comment lines'`. Any push after a gate invalidates it. A grep of the diff or your own judgment is not the audit, and moved comments count.
