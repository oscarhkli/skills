import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "create_worktree.py"
GIT_ENV = ["-c", "user.name=t", "-c", "user.email=t@example.com", "-c", "init.defaultBranch=main"]


def git(cwd, *args):
    result = subprocess.run(["git", *GIT_ENV, "-C", str(cwd), *args], capture_output=True, text=True, check=True)
    return result.stdout.strip()


def commit(repo, name):
    (repo / name).write_text(name)
    git(repo, "add", name)
    git(repo, "commit", "-m", name)


class CreateWorktreeTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name).resolve()
        self.origin = self.root / "origin.git"
        subprocess.run(["git", *GIT_ENV, "init", "--bare", "-q", str(self.origin)], check=True)
        self.app = self.root / "app"
        subprocess.run(["git", *GIT_ENV, "clone", "-q", str(self.origin), str(self.app)], check=True, capture_output=True)
        commit(self.app, "one")
        git(self.app, "push", "-q", "origin", "HEAD:main")
        git(self.app, "branch", "-M", "main")
        git(self.app, "branch", "--set-upstream-to=origin/main", "main")

    def advance_origin(self):
        other = self.root / "other"
        subprocess.run(["git", *GIT_ENV, "clone", "-q", str(self.origin), str(other)], check=True, capture_output=True)
        commit(other, "two")
        git(other, "push", "-q", "origin", "HEAD:main")
        return git(other, "rev-parse", "HEAD")

    def run_script(self, *args, cwd=None):
        return subprocess.run(
            [sys.executable, "-I", str(SCRIPT), *args], cwd=cwd or self.app, capture_output=True, text=True
        )

    def test_new_branch_starts_from_fetched_origin_base(self):
        want = self.advance_origin()
        result = self.run_script("fix", "feat/fix")
        self.assertEqual(result.returncode, 0, result.stderr)
        target = self.root / "app-worktrees" / "fix"
        self.assertEqual(git(target, "rev-parse", "HEAD"), want)
        self.assertEqual(git(self.app, "rev-parse", "main"), git(self.app, "rev-parse", "origin/main~1"))
        lines = result.stdout.splitlines()
        self.assertEqual(lines[:3], [str(target), "feat/fix", "created from origin/main"])
        self.assertEqual(len(lines), 3)

    def test_new_branch_does_not_track_the_base(self):
        self.run_script("fix", "feat/fix")
        result = subprocess.run(
            ["git", "-C", str(self.root / "app-worktrees" / "fix"), "rev-parse", "--abbrev-ref", "feat/fix@{upstream}"],
            capture_output=True, text=True,
        )
        self.assertNotEqual(result.returncode, 0)

    def test_failed_fetch_falls_back_to_local_base_with_warning(self):
        want = git(self.app, "rev-parse", "main")
        git(self.app, "remote", "set-url", "origin", str(self.root / "missing.git"))
        result = self.run_script("fix", "feat/fix")
        self.assertEqual(result.returncode, 0, result.stderr)
        target = self.root / "app-worktrees" / "fix"
        self.assertEqual(git(target, "rev-parse", "HEAD"), want)
        lines = result.stdout.splitlines()
        self.assertEqual(lines[2], "created from main")
        self.assertTrue(lines[3].startswith("warning: "), lines)

    def test_repo_without_origin_uses_local_base_without_warning(self):
        git(self.app, "remote", "remove", "origin")
        result = self.run_script("fix", "feat/fix")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines()[2:], ["created from main"])

    def test_default_parent_works_from_inside_a_worktree(self):
        first = self.run_script("one", "feat/one")
        self.assertEqual(first.returncode, 0, first.stderr)
        second = self.run_script("two", "feat/two", cwd=self.root / "app-worktrees" / "one")
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertTrue((self.root / "app-worktrees" / "two").is_dir())

    def test_explicit_parent_names_the_repo(self):
        parent = self.root / "app-worktrees"
        result = self.run_script("fix", "feat/fix", "--parent", str(parent), cwd=self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((parent / "fix").is_dir())

    def test_parent_without_worktrees_suffix_is_refused(self):
        result = self.run_script("fix", "feat/fix", "--parent", str(self.app))
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.app / "fix").exists())

    def test_submodule_without_parent_is_refused(self):
        lib = self.root / "lib"
        lib.mkdir()
        git(lib, "init", "-q")
        commit(lib, "lib")
        subprocess.run(
            ["git", *GIT_ENV, "-c", "protocol.file.allow=always", "-C", str(self.app),
             "submodule", "add", "-q", str(lib), "sub"],
            check=True, capture_output=True,
        )
        sub = self.app / "sub"
        result = self.run_script("fix", "feat/fix", cwd=sub)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--parent", result.stderr)

    def test_existing_local_branch_is_reused(self):
        git(self.app, "branch", "feat/old")
        result = self.run_script("old", "feat/old")
        self.assertEqual(result.stdout.splitlines()[2], "reused")


if __name__ == "__main__":
    unittest.main()
