#!/usr/bin/env python3
"""Usage: create_worktree.py <worktree-parent-dir> <worktree-name> <branch-name>"""
import subprocess
import sys
from pathlib import Path

parent, name, branch = sys.argv[1:4]
parent = Path(parent).resolve()
if not parent.name.endswith("-worktrees"):
    sys.exit(f"Parent directory must end with '-worktrees': {parent}")

repo = parent.with_name(parent.name.removesuffix("-worktrees"))
target = parent / name


def git(*args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)


def has_ref(ref):
    return git("show-ref", "--verify", "--quiet", ref).returncode == 0


warning = ""
if has_ref(f"refs/heads/{branch}"):
    cmd, action = [str(target), branch], "reused"
elif has_ref(f"refs/remotes/origin/{branch}"):
    cmd, action = ["--track", "-b", branch, str(target), f"origin/{branch}"], "tracked from origin"
else:
    base = next((b for b in ("main", "master") if has_ref(f"refs/heads/{b}")), None)
    if base is None:
        sys.exit(f"No local 'main' or 'master' branch in {repo}")
    cmd, action = ["-b", branch, str(target), base], f"created from {base}"
    if has_ref(f"refs/remotes/origin/{base}"):
        behind = git("rev-list", "--count", f"{base}..origin/{base}").stdout.strip()
        if behind not in ("", "0"):
            warning = f"\nwarning: {base} is {behind} commits behind origin/{base} (as of last fetch)"

result = git("worktree", "add", *cmd)
if result.returncode != 0:
    sys.exit(result.stderr.strip())
print(f"{target}\n{branch}\n{action}{warning}")
