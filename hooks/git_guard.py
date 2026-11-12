#!/usr/bin/env python3
"""Asks instead of denying so the human can still approve a legitimate rewrite.
Limit: git calls hidden inside `bash -c` or `$(...)` are not inspected.
"""
from __future__ import annotations

import json
import re
import shlex
import subprocess
import sys
from pathlib import Path, PureWindowsPath

PROJECT_BRAIN_REMOTE = re.compile(r"(^|[/:])oscarhkli/project-brain(\.git)?/*$", re.IGNORECASE)
DEFAULT_BRANCHES = {"main", "master"}
SEPARATORS = {"&&", "||", ";", "|", "&", "\n", "(", ")"}
ENV_ASSIGN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
PUSH_VALUE_FLAGS = {"-o", "--push-option", "--repo", "--receive-pack", "--exec"}
GLOBAL_VALUE_FLAGS = {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}


def segments(cmd: str) -> list[list[str]]:
    lexer = shlex.shlex(cmd, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    out, cur = [], []
    for tok in lexer:
        if tok in SEPARATORS:
            out.append(cur)
            cur = []
        else:
            cur.append(tok)
    out.append(cur)
    return [s for s in out if s]


def git_call(seg: list[str]) -> tuple[str, list[str], str | None] | None:
    i = 0
    while i < len(seg) and ENV_ASSIGN.match(seg[i]):
        i += 1
    if i >= len(seg) or PureWindowsPath(seg[i]).name.lower() not in {"git", "git.exe"}:
        return None
    i += 1
    workdir = None
    while i < len(seg) and seg[i].startswith("-"):
        if seg[i] == "-C" and i + 1 < len(seg):
            workdir = seg[i + 1]
        i += 2 if seg[i] in GLOBAL_VALUE_FLAGS else 1
    if i >= len(seg):
        return None
    return seg[i], seg[i + 1:], workdir


def run_git(cwd: str, *args: str) -> str | None:
    try:
        done = subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout.strip() if done.returncode == 0 else None


def short_flags(args: list[str]) -> str:
    return "".join(a[1:] for a in args if re.fullmatch(r"-[A-Za-z]+", a))


def check_add(args: list[str]) -> str | None:
    flags = short_flags(args)
    if "--all" in args or "A" in flags or "--force" in args or "f" in flags or "." in args:
        return "git add -A/--all/-f/. stages unrelated or ignored files. Name the paths instead."
    return None


def refspec_branch(spec: str, current: str | None) -> str | None:
    dest = spec.lstrip("+").split(":")[-1]
    if dest == "HEAD":
        return current
    return dest.removeprefix("refs/heads/")


def check_push(args: list[str], cwd: str) -> str | None:
    flags = short_flags(args)
    if any(a == "--force" or a.startswith(("--force-with-lease", "--force-if-includes")) for a in args) or "f" in flags:
        return "force-push rewrites remote history."
    positional, skip = [], False
    for a in args:
        if skip:
            skip = False
        elif a in PUSH_VALUE_FLAGS:
            skip = True
        elif not a.startswith("-"):
            positional.append(a)
    if any(p.startswith("+") for p in positional[1:]):
        return "a + refspec force-pushes."
    if PROJECT_BRAIN_REMOTE.search(run_git(cwd, "config", "--get", "remote.origin.url") or ""):
        return None
    reason = "pushing to the default branch skips the PR."
    if "--all" in args or "--mirror" in args:
        return reason
    current = run_git(cwd, "rev-parse", "--abbrev-ref", "HEAD")
    specs = positional[1:]
    targets = [refspec_branch(s, current) for s in specs] if specs else [current]
    return reason if any(t in DEFAULT_BRANCHES for t in targets) else None


def check(cmd: str, cwd: str) -> str | None:
    try:
        segs = segments(cmd)
    except ValueError:
        return None
    for seg in segs:
        call = git_call(seg)
        if not call:
            continue
        sub, args, workdir = call
        where = str(Path(cwd, workdir)) if workdir else cwd
        reason = {"add": lambda: check_add(args), "push": lambda: check_push(args, where)}.get(sub, lambda: None)()
        if reason:
            return reason
    return None


def main() -> int:
    try:
        payload = json.loads(sys.stdin.buffer.read().decode("utf-8-sig", errors="replace"))
        cmd = payload["tool_input"]["command"]
        cwd = payload.get("cwd") or "."
    except (ValueError, KeyError, TypeError, AttributeError):
        return 0
    try:
        reason = check(cmd, cwd)
    except Exception:
        return 0
    if reason:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": f"git-guard: {reason}",
        }}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
