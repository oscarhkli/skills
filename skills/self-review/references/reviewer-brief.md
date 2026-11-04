# Briefs

## Reviewer

- Read-only. Do not edit files, commit, push, or write to PRs or issue trackers.
- Review the whole change at `<path or branch>` against `<requirements>`. Lens: `<lens>`.
- Verify each claim in the code before raising it.
- Return findings as: severity (major or minor), location, problem, impact, correction.
- Major: wrong thing built, a test passes without proving its claim, two parts contradict.
- Return `CLEAN` when nothing is wrong. Report any tool or permission failure as `REVIEW FAILED`.

## Fixer

- Fix every major finding and the cheap minor ones in `<findings>`. Skip the rest and list each with what blocks it.
- Read `../../principle-never-block-on-the-human/SKILL.md` first. Resolve reversible, in-scope blocks yourself and state the assumption.
- Keep the diff minimal. Build and run the affected tests. Report the result.

## Verifier

- Input: every finding, major and minor, and the diff only.
- Check that the fix to each finding holds and that the changed lines add no major issue. Check nothing else.
- Return remaining findings with severity, or `CLEAN`.
