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

Each `hooks/*.py` (except `test_*.py`) is copied into `~/.agents/hooks/`, overwriting a changed copy.

- Set `AGENTS_HOOKS_DIR` to install somewhere else.
- Registering a hook in `~/.claude/settings.json` or `~/.copilot/hooks/` is manual.
- Run the tests with `python3 -I -m unittest discover -s hooks`.

`hooks/reply_hygiene.py` is a Stop hook. It checks the final reply of each turn and logs hits.

- Checks:
  - `hedge`: the last two lines offer work instead of doing it ("if you want", "let me know if").
    - "I haven't tested/checked/run/verified X" also counts.
    - It passes when the same line says why X cannot be done (credentials, human decision, cost).
  - `offer_question`: the last paragraph has a sentence that starts with "Want me to" or similar,
    such as "Done. Want me to push?". It is skipped when `hedge` already hit.
  - `missing_principles_line`: a theta-mode reply over 3 lines, after tool use, lacks a
    `Principles applied:` line and its first line claims a change ("pushed", "fixed", "merged").
- Blocking by default:
  - `hedge` and `offer_question` block.
  - `missing_principles_line` only logs.
- Environment variables:
  - `REPLY_HYGIENE_BLOCK`: comma-separated check names that block. It replaces the default list.
    - Empty blocks nothing.
  - `REPLY_HYGIENE_MODE=log`: every check only logs.
  - `REPLY_HYGIENE_MODE=block`: every check blocks.
    - Both modes win over `REPLY_HYGIENE_BLOCK`.
  - `REPLY_HYGIENE_LOG`: log file path.
- A block:
  - Asks the agent to do the action or name the one decision only the human can make.
  - Fires once per turn: the hook does nothing when `stop_hook_active` is set.
  - Never fires for `transcript_unreadable` or `no_reply_found`, which are logged only.
- The log is `~/.agents/hooks/logs/reply_hygiene.jsonl`, one JSON record per hit, never rotated.
  - Fields: `ts`, `tool`, `session`, `check`, `phrase`, `snippet`, `blocked`.
  - `snippet` is the matched line, cut to 160 characters.
  - `missing_principles_line` adds `first_line`.
  - `transcript_unreadable` and `no_reply_found` add `payload_keys`.

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

Write `$HOME`, not `~`, because Windows PowerShell 5.1 does not expand `~`.

- On Windows, `python3` can be the Microsoft Store stub. Use `python` or `py -3` then.
- PowerShell has no `VAR=x cmd` form. To override a default, set the variable first:
  `"powershell": "$env:REPLY_HYGIENE_BLOCK='hedge'; python \"$HOME/.agents/hooks/reply_hygiene.py\""`
- A hook that fails to start fails open in both tools, so check that the log file appears.

## Layout

```
skills/<name>/SKILL.md   one folder per skill; optional scripts/, references/, evals/
agents/<name>.md         custom agents that skills call by name
hooks/<name>.py          Stop hooks for Claude Code and Copilot CLI, with test_<name>.py
scripts/install.sh       deploys skills into ~/.agents/skills and agents into ~/.claude/agents, ~/.copilot/agents, hooks into ~/.agents/hooks
```

Evals live inside the skill they test and only exist where output is objectively checkable.
