# Create PR playbook

Use it when about to open or rewrite a pull request description. The text is for a reviewer who has not seen this session.

## Sections

- **Why:** the problem or goal.
- **What:** what changed, as behaviour a reviewer can see.
- **Scope:** what is in, and what is explicitly out.
- **Tradeoffs:** alternatives rejected and costs accepted. Include prototype results briefly: the finding and the decision it drove (see `prototype.md`).
- **Verification:** what was run and the result, honestly. Say what was not run.

## Rules

- Write the description as an elevator pitch. A reviewer gets the important points in 60 seconds, and the code change holds the details. Keep each section to a few lines, with no file-by-file tour.
- Title the PR in Conventional Commit style, `type(scope): summary`, with the types from the `git-commit` skill.
- Open the PR ready for review, not as a draft. Never merge it.
- Apply `../unslop/SKILL.md` before posting: no review-round history, no em dashes.
- End the description with the PR attribution line the session instructs.
- Never include a `Claude-Session:` link.
