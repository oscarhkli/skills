#!/usr/bin/env python3
import argparse
import subprocess
import sys


def git(repo, *args, check=True):
    print("+ git " + " ".join(args), flush=True)
    result = subprocess.run(["git", "-C", repo, *args])
    if check and result.returncode != 0:
        sys.exit(result.returncode)
    return result.returncode


def out(repo, *args):
    result = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    return result.stdout.split("\t")[0].strip() if result.returncode == 0 else ""


def main():
    parser = argparse.ArgumentParser(description="Remove a worktree, its local branch and its remote branch.")
    parser.add_argument("repo")
    parser.add_argument("branch", help="'-' for none")
    parser.add_argument("worktree", nargs="?", default="-", help="'-' for none")
    parser.add_argument("--force", action="store_true", help="remove the worktree despite local changes")
    parser.add_argument("--keep-remote", action="store_true", help="keep the remote branch")
    args = parser.parse_args()

    if args.worktree != "-":
        git(args.repo, "worktree", "remove", *(["--force"] if args.force else []), args.worktree)
    if args.branch != "-":
        local = out(args.repo, "rev-parse", f"refs/heads/{args.branch}")
        git(args.repo, "branch", "-D", args.branch)
        remote = "" if args.keep_remote else out(args.repo, "ls-remote", "--heads", "origin", f"refs/heads/{args.branch}")
        if remote and remote != local:
            print(f"skipped remote delete: origin/{args.branch} is at {remote[:8]}, local was at {local[:8]}", flush=True)
        elif remote:
            git(args.repo, "push", "origin", "--delete", args.branch)
    git(args.repo, "worktree", "prune")


if __name__ == "__main__":
    main()
