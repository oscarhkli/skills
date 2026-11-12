# skills

My personal agent skills, written once and usable across Claude Code, GitHub Copilot, and Cursor. Each skill is a folder with a `SKILL.md` (the open Agent Skills format) under `skills/`.

The `principle-*` skills are manual-only (`disable-model-invocation: true`). They are also meant to be quoted from `CLAUDE.md` or equivalent instruction files, so agents read them when making decisions.

## Install (deploy)

The repo is the dev environment; `~/.agents/skills/` is the deployed one. Nothing is live until you deploy.

```sh
git clone <this repo> && cd skills
scripts/install.sh        # asks before replacing a changed skill
scripts/install.sh -y     # replace without asking
```

`scripts/install.sh` copies each folder in `skills/` into `~/.agents/skills/`, the user-level location read by Copilot and Cursor. Claude Code reads it through a `~/.claude/skills` -> `~/.agents/skills` symlink, so create that once if you don't have it.

- Missing skills are installed; identical ones are skipped.
- A skill whose deployed copy differs is shown as a diff, and you answer `y` (this one), `N` (skip) or `a` (this one and all remaining).
- The replaced copy is moved to `~/.agents/.skills-backup/<timestamp>/` (outside the skills dir, so it is not loaded twice).
- `evals/` folders are dev-only and never deployed.
- Skills that aren't in this repo are never touched.
- Set `AGENTS_SKILLS_DIR` to deploy somewhere else.

Each `agents/<name>.md` is also copied into `~/.claude/agents/` and `~/.copilot/agents/`, where Claude Code and Copilot CLI look for custom agents (neither finds them inside a skill folder). A changed agent is overwritten without asking. Override the targets with `CLAUDE_AGENTS_DIR` and `COPILOT_AGENTS_DIR`.

Each `hooks/*.py` (except `test_*.py`) is copied into `~/.agents/hooks/`, overwriting a changed copy. Override the target with `AGENTS_HOOKS_DIR`. Registering a hook in `~/.claude/settings.json` or `~/.copilot/hooks/` is manual. `hooks/reply_hygiene.py` is a Stop hook that logs hedged or unfinished final replies to `~/.agents/hooks/logs/reply_hygiene.jsonl`. Each record holds the session id and up to 160 characters of the matched line, and the log never rotates. After the `retro` log review finds most hits real, set `REPLY_HYGIENE_MODE=block` to make it ask for a redo. Run its tests with `python3 -I -m unittest discover -s hooks`.

`hooks/git_guard.py` is a PreToolUse hook for Bash. It asks the human to confirm, with a reason, before a force push (`--force`, `-f`, `--force-with-lease`, a `+` refspec), `git add -A`, `--all`, `-f` or `.`, and a push to `main` or `master` unless `remote.origin.url` ends in `oscarhkli/project-brain` (any machine, any path). Other commands get no decision, and an internal error never blocks. It reads stdin as UTF-8 and recognises `git` and `git.exe`. Register it in `~/.claude/settings.json`, beside any other `Bash` hook:

```json
{"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "python3 \"$HOME/.agents/hooks/git_guard.py\"", "timeout": 15}]}]}}
```

Register it in Claude Code, in `~/.claude/settings.json` (on Windows the command runs in Git Bash):

```json
{"hooks": {"Stop": [{"hooks": [{"type": "command", "command": "python3 \"$HOME/.agents/hooks/reply_hygiene.py\""}]}]}}
```

Register it in Copilot CLI, in `~/.copilot/hooks/reply-hygiene.json` (on Windows the `powershell` command runs):

```json
{"version": 1, "hooks": {"agentStop": [{"type": "command",
  "bash": "python3 \"$HOME/.agents/hooks/reply_hygiene.py\"",
  "powershell": "python \"$HOME/.agents/hooks/reply_hygiene.py\""}]}}
```

Write `$HOME`, not `~`, because Windows PowerShell 5.1 does not expand `~`. On Windows, `python3` can be the Microsoft Store stub, so use `python` or `py -3` if it is. PowerShell has no `VAR=x cmd` form, so for block mode set the variable first: `"powershell": "$env:REPLY_HYGIENE_MODE='block'; python \"$HOME/.agents/hooks/reply_hygiene.py\""`. A hook that fails to start fails open in both tools, so check that the log file appears.

## Layout

```
skills/<name>/SKILL.md   one folder per skill; optional scripts/, references/, evals/
agents/<name>.md         custom agents that skills call by name
hooks/<name>.py          Stop and PreToolUse hooks, with test_<name>.py
scripts/install.sh       deploys skills into ~/.agents/skills and agents into ~/.claude/agents, ~/.copilot/agents, hooks into ~/.agents/hooks
```

Evals live inside the skill they test and only exist where output is objectively checkable.
