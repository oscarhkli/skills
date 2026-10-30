#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

MAX_LINES = 200
MAX_OTHERS = 20
SKIP = {"node_modules", "bin", "obj", "dist", "build", "target", "vendor", ".venv", "venv"}


def main():
    if len(sys.argv) != 5:
        sys.exit("usage: save_notes.py <repo> <worktree> <branch> <pr-url>")
    repo, worktree, branch, pr = sys.argv[1:]
    listed = subprocess.run(
        ["git", "-C", worktree, "-c", "core.quotePath=false", "ls-files", "--others", "--", "*.md", "*.log"],
        capture_output=True, text=True, encoding="utf-8", check=True,
    ).stdout.splitlines()
    files = [f for f in listed if not SKIP.intersection(f.split("/")[:-1])]
    others = subprocess.run(
        ["git", "-C", worktree, "-c", "core.quotePath=false", "ls-files", "--others"],
        capture_output=True, text=True, encoding="utf-8", check=True,
    ).stdout.splitlines()
    others = [f for f in others if f not in listed and not SKIP.intersection(f.split("/")[:-1])]
    for f in others[:MAX_OTHERS]:
        print(f"not saved: {f}")
    if len(others) > MAX_OTHERS:
        print(f"not saved: {len(others) - MAX_OTHERS} more")
    if not files:
        return

    name = Path(worktree).name
    out = Path.home() / ".agents" / "worktree-notes" / Path(repo).resolve().name / f"{name}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    parts = ["\n" if out.exists() and out.stat().st_size else ""]
    parts.append(f"# {name}\n\nBranch `{branch}`, PR {pr if pr != '-' else 'none'}\n")
    truncated = []
    for f in files:
        lines = (Path(worktree) / f).read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
        if len(lines) > MAX_LINES:
            truncated.append(f"{f}: kept last {MAX_LINES} of {len(lines)} lines")
            lines = lines[-MAX_LINES:]
        text = "".join(lines)
        if not text.endswith("\n"):
            text += "\n"
        if f.endswith(".log"):
            text = f"```text\n{text}```\n"
        parts.append(f"\n## {f}\n\n{text}")
    with out.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write("".join(parts))
    print(out)
    for note in truncated:
        print(f"truncated {note}")


if __name__ == "__main__":
    main()
