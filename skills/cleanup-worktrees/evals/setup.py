#!/usr/bin/env python3
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


class Scratch:
    def __init__(self, root, name):
        self.root = root
        self.repo = root / name
        self.trees = root / f"{name}-worktrees"
        self.home = root / "home"
        self.prs = {}
        origin = root / "origin.git"
        self.run(root, "init", "--quiet", "--bare", "-b", "main", str(origin))
        self.run(root, "init", "--quiet", "-b", "main", str(self.repo))
        self.git("config", "user.name", "eval")
        self.git("config", "user.email", "eval@example.com")
        self.git("config", "core.autocrlf", "false")
        (self.repo / "README.txt").write_text("base\n")
        self.git("add", "-A")
        self.git("commit", "--quiet", "-m", "base")
        self.git("remote", "add", "origin", str(origin))
        self.git("push", "--quiet", "-u", "origin", "main")
        self.git("remote", "set-head", "origin", "main")
        self.trees.mkdir()

    @staticmethod
    def run(cwd, *args):
        return subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True).stdout.strip()

    def git(self, *args):
        return self.run(self.repo, *args)

    def branch(self, name):
        commit = self.git("commit-tree", "-p", "main", "-m", name, "main^{tree}")
        self.git("update-ref", f"refs/heads/{name}", commit)
        self.git("push", "--quiet", "origin", name)

    def worktree(self, dirname, branch):
        self.branch(branch)
        path = self.trees / dirname
        self.git("worktree", "add", "--quiet", str(path), branch)
        return path

    def pr(self, branch, state, number):
        self.prs.setdefault(branch, []).append({
            "number": number,
            "state": state,
            "url": f"https://github.com/example/{self.repo.name}/pull/{number}",
            "headRefOid": self.git("rev-parse", f"refs/heads/{branch}"),
        })


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def case1(root):
    s = Scratch(root, "app")
    a = s.worktree("feat-a", "feat/a")
    s.pr("feat/a", "MERGED", 11)
    write(a / "NOTES.md", "merge follow-ups\n")
    s.worktree("feat-b", "feat/b")
    s.pr("feat/b", "OPEN", 12)
    x = s.worktree("proto-x", "proto/x")
    write(x / "PROTOTYPE.md", "approach two wins\n")
    s.branch("old/merged")
    s.pr("old/merged", "MERGED", 9)
    return s


def case4(root):
    s = Scratch(root, "kit")
    y = s.worktree("proto-y", "proto/y")
    Scratch.run(y, "commit", "--quiet", "--allow-empty", "-m", "unpushed experiment")
    z = s.worktree("proto-z", "proto/z")
    with (z / "README.txt").open("a") as handle:
        handle.write("half-done edit\n")
    return s


def case2(root):
    s = Scratch(root, "svc")
    c = s.worktree("feat-c", "feat/c")
    s.pr("feat/c", "MERGED", 21)
    Scratch.run(c, "commit", "--quiet", "--allow-empty", "-m", "work after merge")
    s.worktree("feat-d", "feat/d")
    s.pr("feat/d", "MERGED", 22)
    return s


def case3(root):
    s = Scratch(root, "lib")
    e = s.worktree("feat-e", "feat/e")
    s.pr("feat/e", "MERGED", 31)
    target = e / "skills" / "e-skill"
    write(target / "SKILL.md", "# e-skill\n")
    link = s.home / ".agents" / "skills" / "e-skill"
    link.parent.mkdir(parents=True)
    if os.name == "nt":
        subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)], check=True, capture_output=True, stdin=subprocess.DEVNULL)
    else:
        link.symlink_to(target, target_is_directory=True)
    s.worktree("feat-f", "feat/f")
    s.pr("feat/f", "MERGED", 32)
    return s


def install_fake_gh(s):
    bin_dir = s.root / "bin"
    bin_dir.mkdir()
    fake = bin_dir / "fake_gh.py"
    shutil.copy(HERE / "fake_gh.py", fake)
    (bin_dir / "prs.json").write_text(json.dumps(s.prs, indent=2))
    write(bin_dir / "gh", f'#!/usr/bin/env bash\nexec python3 "{fake.as_posix()}" "$@"\n')
    (bin_dir / "gh").chmod(0o755)
    write(bin_dir / "gh.cmd", f'@python3 "{fake}" %*\r\n')
    write(s.root / "env.sh", (
        f'export HOME="$(cygpath -u \'{s.home}\' 2>/dev/null || echo \'{s.home.as_posix()}\')"\n'
        f'export USERPROFILE=\'{s.home}\'\n'
        f'export PATH="$(cygpath -u \'{bin_dir}\' 2>/dev/null || echo \'{bin_dir.as_posix()}\'):$PATH"\n'
    ))
    write(s.root / "env.ps1", f'$env:HOME = "{s.home}"\n$env:USERPROFILE = "{s.home}"\n$env:PATH = "{bin_dir}" + [IO.Path]::PathSeparator + $env:PATH\n')


def main():
    cases = {"1": case1, "2": case2, "3": case3, "4": case4}
    if len(sys.argv) != 3 or sys.argv[1] not in cases:
        sys.exit("usage: setup.py <1|2|3|4> <empty-dir>")
    root = Path(sys.argv[2]).resolve()
    root.mkdir(parents=True, exist_ok=True)
    if any(root.iterdir()):
        sys.exit(f"{root} is not empty")
    (root / "home").mkdir()
    s = cases[sys.argv[1]](root)
    install_fake_gh(s)
    print(f"repo: {s.repo}")
    print(f"bash: source {(root / 'env.sh').as_posix()}")
    print(f"powershell: . {root / 'env.ps1'}")


if __name__ == "__main__":
    main()
