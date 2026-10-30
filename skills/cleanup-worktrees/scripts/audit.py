#!/usr/bin/env python3
import json
import re
import shutil
import subprocess
import sys
from pathlib import PurePosixPath

NOTE = re.compile(r'^\?\? .*\.(md|log)"?$')
GH = shutil.which("gh") or "gh"


def git(repo, *args, check=True):
    result = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    if check and result.returncode != 0:
        sys.exit(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result


def worktrees(repo):
    entries = []
    for block in git(repo, "worktree", "list", "--porcelain").stdout.strip().split("\n\n"):
        fields = dict(line.split(" ", 1) if " " in line else (line, "") for line in block.splitlines())
        branch = fields.get("branch", "-").replace("refs/heads/", "", 1)
        entries.append((fields["worktree"], branch))
    return entries


def default_branch(repo):
    head = git(repo, "symbolic-ref", "--short", "refs/remotes/origin/HEAD", check=False).stdout.strip()
    if head:
        return head.split("/", 1)[1]
    has_main = git(repo, "show-ref", "--verify", "--quiet", "refs/heads/main", check=False).returncode == 0
    return "main" if has_main else "master"


def slug(repo):
    url = git(repo, "remote", "get-url", "origin").stdout.strip()
    url = re.sub(r"\.git$", "", url)
    return "/".join(re.split(r"[:/]", url)[-2:])


def changes(path):
    result = git(path, "status", "--porcelain", "--untracked-files=all", check=False)
    if result.returncode != 0:
        return "missing"
    lines = result.stdout.splitlines()
    if not lines:
        return "clean"
    other = sum(1 for line in lines if not NOTE.match(line))
    return f"other:{other}" if other else "notes-only"


def tracked(path):
    result = git(path, "status", "--porcelain", "--untracked-files=no", check=False)
    return str(len(result.stdout.splitlines())) if result.returncode == 0 else "-"


def unpushed(repo, branch):
    if branch == "-":
        return "-"
    return git(repo, "rev-list", "--count", f"refs/heads/{branch}", "--not", "--remotes").stdout.strip()


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


def row(repo, repo_slug, branch, path):
    cls, reason, pr = classify(repo, repo_slug, branch)
    dirty, edits = "-", "-"
    commits = unpushed(repo, branch)
    if path != "-":
        dirty = changes(path)
        edits = tracked(path)
        if PurePosixPath(path.replace("\\", "/")).name.startswith("proto-"):
            cls, reason = "target", f"proto ({reason})"
            risks = []
            if commits not in ("-", "0"):
                risks.append("unpushed commits")
            if edits not in ("-", "0"):
                risks.append("tracked changes")
            if risks:
                cls, reason = "ask", f"proto ({', '.join(risks)})"
    state, url = (pr["state"], pr["url"]) if pr else ("-", "-")
    print("\t".join([cls, reason, branch, path, state, url, dirty, edits, commits]))


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: audit.py <repo>")
    repo = sys.argv[1]
    git(repo, "fetch", "--prune", "--quiet")
    entries = worktrees(repo)
    skip = {default_branch(repo), entries[0][1]} - {"-"}
    repo_slug = slug(repo)
    print("class\treason\tbranch\tworktree\tpr_state\tpr_url\tchanges\ttracked\tunpushed")
    for path, branch in entries[1:]:
        if branch not in skip:
            row(repo, repo_slug, branch, path)
    attached = {branch for _, branch in entries}
    for branch in git(repo, "for-each-ref", "--format=%(refname:short)", "refs/heads").stdout.split():
        if branch not in skip and branch not in attached:
            row(repo, repo_slug, branch, "-")


if __name__ == "__main__":
    main()
