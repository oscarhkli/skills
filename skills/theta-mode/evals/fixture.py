"""Fixture for the theta-mode evals.

python3 fixture.py install      copy fixture/eval-fixture to ~/.agents/playbooks/eval-fixture
python3 fixture.py remove       delete that copy
python3 fixture.py repo <name> [--callers N]
                                create ./<name>, a git repo on branch feat/add-grid;
                                --callers N adds N modules that each call grid.draw

The fixture entries match only repos named eval-*, so real playbook sources on the machine never collide with it.
"""
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
DEST = Path.home() / ".agents" / "playbooks" / "eval-fixture"


def git(repo, *args):
    subprocess.run(
        ["git", "-C", str(repo), "-c", "user.name=eval", "-c", "user.email=eval@example.com", *args],
        check=True, capture_output=True,
    )


def repo(name, callers=0):
    root = Path(name)
    root.mkdir()
    git(root, "init", "-b", "main")
    (root / "README.md").write_text("# widgets\n\nA small gird library.\n")
    (root / "grid.py").write_text("def draw(cells):\n    return cells\n")
    git(root, "add", "-A")
    git(root, "commit", "-m", "chore: initial commit")
    git(root, "switch", "-c", "feat/add-grid")
    (root / "grid.py").write_text(
        "def draw(cells):\n    return cells\n\n\ndef grid(width, height):\n    return [[0] * width for _ in range(height)]\n"
    )
    git(root, "add", "grid.py")
    git(root, "commit", "-m", "feat(grid): add a grid builder")
    if callers:
        for i in range(callers):
            (root / f"caller_{i}.py").write_text(f"from grid import draw\n\n\ndef show_{i}(cells):\n    return draw(cells)\n")
        git(root, "add", "-A")
        git(root, "commit", "-m", f"feat(grid): add {callers} callers of draw")


command = sys.argv[1] if len(sys.argv) > 1 else ""
if command == "install":
    shutil.rmtree(DEST, ignore_errors=True)
    shutil.copytree(HERE / "fixture" / "eval-fixture", DEST)
elif command == "remove":
    shutil.rmtree(DEST, ignore_errors=True)
elif command == "repo" and len(sys.argv) == 3:
    repo(sys.argv[2])
elif command == "repo" and len(sys.argv) == 5 and sys.argv[3] == "--callers":
    repo(sys.argv[2], int(sys.argv[4]))
else:
    sys.exit(__doc__)
