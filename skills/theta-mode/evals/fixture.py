"""Fixture for the theta-mode evals.

python3 fixture.py install      copy fixture/eval-fixture to ~/.agents/playbooks/eval-fixture
python3 fixture.py remove       delete that copy
python3 fixture.py repo <name>  create ./<name>, a git repo whose branch feat/add-grid has one commit

The fixture rows match only repos named eval-*, so real playbook sources on the machine never collide with it.
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


def repo(name):
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


command = sys.argv[1] if len(sys.argv) > 1 else ""
if command == "install":
    shutil.rmtree(DEST, ignore_errors=True)
    shutil.copytree(HERE / "fixture" / "eval-fixture", DEST)
elif command == "remove":
    shutil.rmtree(DEST, ignore_errors=True)
elif command == "repo" and len(sys.argv) == 3:
    repo(sys.argv[2])
else:
    sys.exit(__doc__)
