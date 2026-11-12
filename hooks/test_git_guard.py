import io
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import git_guard as gg

GIT_ENV = {
    **os.environ,
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@example.com",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@example.com",
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_SYSTEM": os.devnull,
}


def git(cwd, *args):
    subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, env=GIT_ENV)


class Repos:
    def __init__(self, test):
        tmp = tempfile.TemporaryDirectory()
        test.addCleanup(tmp.cleanup)
        root = Path(tmp.name).resolve()
        self.remote = root / "remote.git"
        self.work = root / "work"
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(self.remote)], check=True, env=GIT_ENV)
        subprocess.run(["git", "clone", "-q", str(self.remote), str(self.work)], check=True, capture_output=True, env=GIT_ENV)
        git(self.work, "checkout", "-q", "-b", "main")
        git(self.work, "commit", "-q", "--allow-empty", "-m", "base")
        git(self.work, "push", "-q", "-u", "origin", "main")

    def feature_branch(self):
        git(self.work, "checkout", "-q", "-b", "feat/x")


class DenyAllowTest(unittest.TestCase):
    def check(self, cmd, cwd):
        return gg.check(cmd, str(cwd))

    def test_stateless_rules(self):
        repos = Repos(self)
        repos.feature_branch()
        cases = [
            ("add all short", "git add -A", True),
            ("add all long", "git add --all", True),
            ("add dot", "git add .", True),
            ("add dot after dashes", "git add -- .", True),
            ("add force", "git add -f ignored.txt", True),
            ("add combined flags", "git add -Av", True),
            ("add after cd", "cd /tmp && git add -A", True),
            ("add with -C", "git -C /some/dir add .", True),
            ("add after env prefix", "GIT_TRACE=1 git add .", True),
            ("add explicit path", "git add path/file.go", False),
            ("add dotfile", "git add .gitignore", False),
            ("add dir under dot", "git add ./src/a.go", False),
            ("add update", "git add -u", False),
            ("add patch", "git add -p file", False),
            ("add words in commit message", 'git commit -m "never git add -A or git add ."', False),
            ("add words in echo", "echo git add -A", False),
            ("push force long", "git push --force origin feat/x", True),
            ("push force lease", "git push --force-with-lease origin feat/x", True),
            ("push force lease value", "git push --force-with-lease=feat/x origin feat/x", True),
            ("push force short", "git push -f origin feat/x", True),
            ("push force clustered", "git push -fu origin feat/x", True),
            ("push plus refspec", "git push origin +feat/x", True),
            ("push force trailing", "git push origin feat/x --force", True),
            ("push force in chain", "git commit -m x && git push -f", True),
            ("push feature", "git push -u origin feat/x", False),
            ("push feature head", "git push origin HEAD", False),
            ("push feature refspec", "git push origin HEAD:feat/y", False),
            ("push with push option", "git push -o ci.skip origin feat/x", False),
            ("push message mentions force", 'git commit -m "explain git push --force"', False),
            ("branch named force-thing", "git push origin force-thing", False),
            ("push main", "git push origin main", True),
            ("push master", "git push origin master", True),
            ("push refspec to main", "git push origin feat/x:main", True),
            ("push full ref to main", "git push origin HEAD:refs/heads/main", True),
            ("push all", "git push --all origin", True),
            ("push mirror", "git push --mirror", True),
            ("push main with -C", "git -C /x push origin main", True),
            ("push branch containing main", "git push origin domain-main", False),
            ("push tag", "git push origin v1.0", False),
            ("fetch main", "git fetch origin main", False),
            ("pull main", "git pull origin main", False),
            ("log", "git log --oneline", False),
            ("not git", "ls -la", False),
            ("unparsable", 'git commit -m "unterminated', False),
            ("empty", "", False),
        ]
        for name, cmd, deny in cases:
            with self.subTest(name):
                got = self.check(cmd, repos.work)
                self.assertEqual(got is not None, deny, got)

    def test_bare_push_depends_on_current_branch(self):
        repos = Repos(self)
        for cmd in ("git push", "git push origin", "git push origin HEAD", "git push -u origin HEAD"):
            with self.subTest("on main " + cmd):
                self.assertIsNotNone(self.check(cmd, repos.work))
        repos.feature_branch()
        for cmd in ("git push", "git push origin", "git push origin HEAD"):
            with self.subTest("on feature " + cmd):
                self.assertIsNone(self.check(cmd, repos.work))

    def test_project_brain_may_push_main(self):
        repos = Repos(self)
        for cmd in ("git push origin main", "git push", "git push origin HEAD"):
            with self.subTest(cmd):
                with mock.patch.object(gg, "PROJECT_BRAIN", repos.work):
                    self.assertIsNone(self.check(cmd, repos.work))

    def test_project_brain_exception_does_not_cover_force(self):
        repos = Repos(self)
        with mock.patch.object(gg, "PROJECT_BRAIN", repos.work):
            self.assertIsNotNone(self.check("git push --force origin main", repos.work))


class MainTest(unittest.TestCase):
    def run_main(self, payload):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch("sys.stdin", io.StringIO(payload)), mock.patch("sys.stdout", out), mock.patch("sys.stderr", err):
            code = gg.main()
        return code, out.getvalue(), err.getvalue()

    def test_dangerous_command_asks_with_reason(self):
        code, out, err = self.run_main(json.dumps({"tool_input": {"command": "git add -A"}, "cwd": "/"}))
        got = json.loads(out)["hookSpecificOutput"]
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assertEqual(got["hookEventName"], "PreToolUse")
        self.assertEqual(got["permissionDecision"], "ask")
        self.assertIn("git add", got["permissionDecisionReason"])

    def test_ordinary_command_gives_no_decision(self):
        code, out, err = self.run_main(json.dumps({"tool_input": {"command": "git add a.go"}, "cwd": "/"}))
        self.assertEqual((code, out, err), (0, "", ""))

    def test_bad_payload_gives_no_decision(self):
        for payload in ("", "not json", "[]", json.dumps({"tool_input": {}})):
            with self.subTest(payload):
                self.assertEqual(self.run_main(payload), (0, "", ""))


if __name__ == "__main__":
    unittest.main()
