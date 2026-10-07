# skills

My personal agent skills, written once and usable across Claude Code, GitHub Copilot, and Cursor.
Each skill is a folder with a `SKILL.md` (the open Agent Skills format) under `skills/`.

The `principle-*` skills are manual-only (`disable-model-invocation: true`). They are also meant to be
quoted from `CLAUDE.md` or equivalent instruction files, so agents read them when making decisions.

## Install (deploy)

The repo is the dev environment; `~/.agents/skills/` is the deployed one. Nothing is live until you deploy.

```sh
git clone <this repo> && cd skills
scripts/install.sh        # asks before replacing a changed skill
scripts/install.sh -y     # replace without asking
```

`scripts/install.sh` copies each folder in `skills/` into `~/.agents/skills/`, the user-level location read by
Copilot and Cursor. Claude Code reads it through a `~/.claude/skills` -> `~/.agents/skills` symlink, so
create that once if you don't have it.

- Missing skills are installed; identical ones are skipped.
- A skill whose deployed copy differs is shown as a diff, and you answer `y` (this one), `N` (skip) or `a` (this one and all remaining).
- The replaced copy is moved to `~/.agents/.skills-backup/<timestamp>/` (outside the skills dir, so it is not loaded twice).
- `evals/` folders are dev-only and never deployed.
- Skills that aren't in this repo are never touched.
- Set `AGENTS_SKILLS_DIR` to deploy somewhere else.

## Layout

```
skills/<name>/SKILL.md   one folder per skill; optional scripts/, references/, evals/
scripts/install.sh       deploys (copies) skills into ~/.agents/skills
```

Evals live inside the skill they test and only exist where output is objectively checkable.
