---
name: self-review
disable-model-invocation: true
description: Adversarial review of code written or generated in this session, by the agent, a delegate or the human, run after the pull request's GitHub Actions checks pass. Use for self-review or adversarial review of own changes. One full review, at most two fix-and-verify rounds, one minor pass and one escalation round, then stop with a report. Code only: a plan or design is reviewed with the `theta-mode/playbooks/plan.md` Budget. Not for others' work, which is `theta-mode/playbooks/review-others.md`.
---

# Self review

The coordinator orchestrates and adjudicates. It never reviews the change itself. Reviewers are read-only: no writes to PRs, issue trackers or remotes, and no push.

## Setup

- Start after the pull request's GitHub Actions checks pass. Fixes land afterwards as new commits. Every verifier, including the minor pass and escalation verifiers, starts after CI passes on the fix push. A project or company playbook may change this trigger and this default.
- Stop if the change has no code diff. A plan or design is reviewed with the `theta-mode/playbooks/plan.md` Budget. The reply is that pointer and nothing else; do not review the document.
- Read `modes.yaml` in this directory. Use the mode the caller names, else `mode` under `self-review:` in `~/.agents/project-brain/<project>/settings.yaml` (shape: `self-review:` then an indented `mode: standard`), else the mode an extra playbook names for this tool, else `default` in `modes.yaml`.
- `<project>` is the code repo's name, which is the main checkout's directory name. For a project that spans several repos, look it up under Projects in `~/.agents/project-brain/README.md`. If `settings.yaml` does not exist, skip it. This use only reads; create nothing.
- Reviewer count is the number of `reviewers` entries. Pass each entry as that agent's model.
- If any reviewer model of the chosen mode is not in this tool's model list, run the `standard` mode instead. If `standard` itself has such a model, that entry uses the mode's `fixer` model.
- The fixer and the verifier use the mode's `fixer` model.
- Never ask the human about models.

## Loop

Prompt skeletons: [references/reviewer-brief.md](references/reviewer-brief.md).

1. Full review, once. Start all reviewers in parallel, each on the whole change, with a different lens:
   - Lens 1: requirements and correctness.
   - Lens 2: tests prove their claims, edge cases, user paths.
   - With one reviewer, that reviewer gets both lenses in one brief.
   - A reviewer that finds a build or test failure reports it as a finding. The coordinator decides what to do with it.
   - A reviewer that cannot complete stops the run as REVIEW FAILED. Do not treat the other review as enough.
2. A fresh agent verifies every finding against the source and marks it ACCEPTED, REJECTED or PARTIAL, with one line of evidence. The coordinator reads no source itself. It records the verdicts and does not ask the human.
3. A fresh fixer fixes every major finding and the cheap minor ones, then builds and runs the tests. It lists the rest with what blocks each.
4. A fresh verifier gets every finding, major and minor, and the diff. It checks the fix to each finding and the changed lines, and nothing else. If it finds a major issue, repeat 3 and 4 once.
5. After the last verifier, which is the first or the second:
   - A major issue after the second verifier, with or without minor issues: follow Escalate.
   - Only minor issues: follow Minor pass.
   - Otherwise stop. Do not start another full review.

Major means the code does the wrong thing, a test passes without proving its claim, or two parts contradict. A minor issue starts no further fix-and-verify round. It starts the escalation round when the minor pass verifier still reports one, because recurring minor issues can mean a design problem. A minor issue blocked only by a decision that is the human's follows Open items.

If every review returned CLEAN, skip steps 3 and 4. The report is CLEAN.

## Minor pass

Run it once, when the last verifier finds minor issues and no major issue.

1. A fresh fixer fixes only the minor issues that verifier reported, including expensive ones the earlier fixer skipped unless a decision that is the human's blocks them, then builds and runs the tests.
2. A fresh verifier checks only those changes, once.
3. Any minor or major issue it reports follows Escalate.

## Escalate

When a problem appears, the coordinator decides from the verifier's verdicts. Escalate only when:

- a finding needs a redesign or slicing of the change,
- the second verifier still finds a major issue, with or without minor issues,
- the minor pass verifier finds any minor or major issue, or
- a build or test failure remains that the fixer cannot resolve.

Then run these steps. Do not start a new full review.

1. A fresh agent investigates the remaining findings in the code and the failed fixes. It first checks whether the coding plan still meets the original requirement and names the root cause. Then it looks for a fix that complies with the original requirement. If the plan has drifted or the design is the cause, the report says so.
2. If it finds one, it applies that fix, which also fixes any minor issues in the findings, and builds and runs the tests. A fresh verifier checks that fix once. The report states the decision, what drifted from the original change, and why it solves the problem. This is the only extra round after the minor pass.
3. If no fix complies with the original requirement, or the check still finds a major or minor issue, the report to the human gives the findings, the root cause, and at least two alternatives, each with pros, cons and tradeoff. One alternative slices the change. When a claim needs real code to settle, one alternative is a prototype per `theta-mode/playbooks/prototype.md`. It ends with a recommendation. The status is `NEEDS HUMAN`.

## Open items

Every item states what blocks it. When the block is a reversible, in-scope choice (a reasonable default, a local code or doc change, running tests), the fixer resolves it and acts instead of parking the item, and the report states the assumption. An item stays open only when the block is a decision that is the human's: a destructive or hard-to-reverse action, publishing outside the machine, cost, security or credentials, or materially different scope or user-visible behaviour. The fixer and the escalation agent read `../principle-never-block-on-the-human/SKILL.md` first.

## Report

- Table: finding, verdict, resolution.
- Open items, each with its blocker.
- Status: `CLEAN`, `OPEN ITEMS` or `NEEDS HUMAN`. Use `NEEDS HUMAN` only after every independent reversible step is done, and name the single decision needed with the recommended choice. A failed reviewer reports `REVIEW FAILED`.
