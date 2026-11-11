# Watch PR playbook

Use it after every push to an open PR: a new PR, a follow-up commit, a merge of main, a review fix.

- Watch the checks with `gh pr checks --watch`.
- If one fails, read the failing step's log, find the cause, plan the fix, push it as a new commit and watch again. Repeat until every check is green.
- A failure the PR did not cause (the same check also fails on main), or one that needs a decision, secret or setting change from the human, is reported with evidence instead of fixed.
- After three failed fix rounds on the same check, stop and report the root cause and options.
- After every check is green, read `../../self-review/SKILL.md` and run it before telling the human the PR is ready for review.
