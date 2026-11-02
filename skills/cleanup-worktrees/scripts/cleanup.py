#!/usr/bin/env python3
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

GH = shutil.which("gh") or "gh"
COLUMNS = ["class", "reason", "branch", "worktree", "pr_state", "pr_url", "changes", "unpushed"]


def git(repo, *args, check=True):
    result = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    if check and result.returncode != 0:
        sys.exit(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result


def worktrees(repo):
    entries = []
    for block in git(repo, "worktree", "list", "--porcelain").stdout.strip().split("\n\n"):
        fields = dict(line.split(" ", 1) if " " in line else (line, "") for line in block.splitlines())
        entries.append((fields["worktree"], fields.get("branch", "-").replace("refs/heads/", "", 1)))
    return entries


def default_branch(repo):
    head = git(repo, "symbolic-ref", "--short", "refs/remotes/origin/HEAD", check=False).stdout.strip()
    if head:
        return head.split("/", 1)[1]
    has_main = git(repo, "show-ref", "--verify", "--quiet", "refs/heads/main", check=False).returncode == 0
    return "main" if has_main else "master"


def slug(repo):
    url = re.sub(r"\.git$", "", git(repo, "remote", "get-url", "origin").stdout.strip())
    return "/".join(re.split(r"[:/]", url)[-2:])


def skill_links():
    links = []
    for folder in (".agents", ".claude"):
        skills = Path.home() / folder / "skills"
        if skills.is_dir():
            links += [(entry.name, os.path.normcase(os.path.realpath(entry))) for entry in skills.iterdir()]
    return links


def classify(repo, repo_slug, branch):
    if branch == "-":
        return "keep", "no PR", None
    result = subprocess.run(
        [GH, "pr", "list", "--repo", repo_slug, "--state", "all", "--head", branch,
         "--json", "number,state,url,headRefOid"],
        capture_output=True, text=True, stdin=subprocess.DEVNULL,
    )
    if result.returncode != 0:
        sys.exit(result.stderr.strip() or "gh pr list failed")
    prs = json.loads(result.stdout or "[]")
    head = git(repo, "rev-parse", f"refs/heads/{branch}").stdout.strip()
    rules = [
        ("keep", "open PR", lambda p: p["state"] == "OPEN"),
        ("target", "merged", lambda p: p["state"] == "MERGED" and p["headRefOid"] == head),
        ("keep", "commits after merge", lambda p: p["state"] == "MERGED"),
        ("keep", "closed without merge", lambda p: p["state"] == "CLOSED"),
    ]
    for cls, reason, match in rules:
        pr = next((p for p in prs if match(p)), None)
        if pr:
            return cls, reason, pr
    return "keep", "no PR", None


def row(repo, repo_slug, links, branch, path):
    cls, reason, pr = classify(repo, repo_slug, branch)
    keys = {branch} - {"-"}
    changes = unpushed = "-"
    if pr:
        keys |= {str(pr["number"]), f"#{pr['number']}"}
    if path != "-":
        status = git(path, "status", "--porcelain", "--untracked-files=all", check=False)
        changes = str(len(status.stdout.splitlines())) if status.returncode == 0 else "missing"
        name = Path(path).name
        keys |= {name, os.path.normcase(os.path.abspath(path))}
        if name.startswith("proto-"):
            cls, reason = "target", f"proto ({reason})"
            if branch != "-":
                unpushed = git(repo, "rev-list", "--count", f"refs/heads/{branch}", "--not", "--remotes").stdout.strip()
        real = os.path.normcase(os.path.realpath(path))
        link = next((n for n, target in links if target == real or target.startswith(real + os.sep)), None)
        if link:
            cls, reason = "keep", f"linked: {link}"
    state, url = (pr["state"], pr["url"]) if pr else ("-", "-")
    return keys, [cls, reason, branch, path, state, url, changes, unpushed]


def audit(repo):
    git(repo, "fetch", "--prune", "--quiet")
    entries = worktrees(repo)
    skip = {default_branch(repo), entries[0][1]} - {"-"}
    repo_slug, links = slug(repo), skill_links()
    items = [(branch, path) for path, branch in entries[1:] if branch not in skip]
    attached = {branch for _, branch in entries}
    for branch in git(repo, "for-each-ref", "--format=%(refname:short)", "refs/heads").stdout.split():
        if branch not in skip and branch not in attached:
            items.append((branch, "-"))
    return [row(repo, repo_slug, links, branch, path) for branch, path in items]


def matching(rows, name):
    wanted = {name, os.path.normcase(os.path.abspath(name))}
    return [fields for keys, fields in rows if keys & wanted]


def remove(repo, rows, names):
    chosen, refused = {}, []
    for name in names:
        hits = matching(rows, name)
        if not hits or any(fields[0] != "target" for fields in hits):
            refused.append(name)
        chosen.update({(fields[2], fields[3]): fields for fields in hits})
    if refused:
        sys.exit(f"refused, not a target: {' '.join(refused)}")
    commands = []
    for branch, path in chosen:
        commands += [["worktree", "remove", "--force", path]] if path != "-" and os.path.isdir(path) else []
        commands += [["branch", "-D", branch]] if branch != "-" else []
    for args in commands + [["worktree", "prune"]]:
        print("+ git " + " ".join(args), flush=True)
        git(repo, *args)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("repo")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--only", help="branch, worktree path or directory name, or PR number")
    group.add_argument("--remove", nargs="+", metavar="NAME", help="remove these targets")
    args = parser.parse_args()
    rows = audit(args.repo)
    if args.remove:
        return remove(args.repo, rows, args.remove)
    fields = [f for _, f in rows]
    if args.only:
        fields = matching(rows, args.only)
        if not fields:
            sys.exit(f"no worktree or local branch matches {args.only}")
    print("\t".join(COLUMNS))
    for f in fields:
        print("\t".join(f))


if __name__ == "__main__":
    main()
