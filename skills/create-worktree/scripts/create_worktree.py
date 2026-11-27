#!/usr/bin/env python3
"""Usage: create_worktree.py <worktree-name> <branch-name> [--parent <worktree-parent-dir>]

Without --parent, run it inside the repo: the parent is <repo toplevel>-worktrees.
"""
import argparse
import subprocess
import sys
from pathlib import Path

args = argparse.ArgumentParser()
args.add_argument("name")
args.add_argument("branch")
args.add_argument("--parent")
opts = args.parse_args()
name, branch = opts.name, opts.branch


def run_git(repo, *cmd):
    return subprocess.run(["git", "-C", str(repo), *cmd], capture_output=True, text=True)


if opts.parent:
    parent = Path(opts.parent).resolve()
    if not parent.name.endswith("-worktrees"):
        sys.exit(f"Parent directory must end with '-worktrees': {parent}")
    repo = parent.with_name(parent.name.removesuffix("-worktrees"))
else:
    common = run_git(".", "rev-parse", "--path-format=absolute", "--git-common-dir")
    if common.returncode != 0:
        sys.exit(common.stderr.strip())
    repo = Path(common.stdout.strip()).parent
    parent = repo.with_name(repo.name + "-worktrees")

target = parent / name


def git(*cmd):
    return run_git(repo, *cmd)


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
    start, action = base, f"created from {base}"
    if git("remote", "get-url", "origin").returncode == 0:
        if git("fetch", "origin", base).returncode == 0:
            start, action = f"origin/{base}", f"created from origin/{base}"
        else:
            warning = f"\nwarning: fetch of origin/{base} failed; branch is based on local {base}, which may be stale"
    cmd = ["--no-track", "-b", branch, str(target), start]

result = git("worktree", "add", *cmd)
if result.returncode != 0:
    sys.exit(result.stderr.strip())
print(f"{target}\n{branch}\n{action}{warning}")
