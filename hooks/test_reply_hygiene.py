import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

import reply_hygiene as rh

THETA_USER = {
    "type": "user",
    "message": {"role": "user", "content": "<command-name>/theta-mode</command-name>"},
}


def claude_reply(text, sidechain=False):
    return {
        "type": "assistant",
        "isSidechain": sidechain,
        "message": {"role": "assistant", "content": [{"type": "thinking", "thinking": ""}, {"type": "text", "text": text}]},
    }


CLAUDE_TOOL_ONLY = {
    "type": "assistant",
    "message": {"role": "assistant", "content": [{"type": "tool_use", "name": "Bash", "input": {}}]},
}


def copilot_reply(text):
    return {"type": "assistant.message", "data": {"content": text, "toolRequests": []}}


def copilot_user(text):
    return {"type": "user.message", "data": {"content": text}}


class Env:
    def __init__(self, test, mode="log"):
        self.dir = tempfile.TemporaryDirectory()
        test.addCleanup(self.dir.cleanup)
        self.log = Path(self.dir.name) / "logs" / "out.jsonl"
        patcher = mock.patch.dict(os.environ, {"REPLY_HYGIENE_LOG": str(self.log), "REPLY_HYGIENE_MODE": mode})
        patcher.start()
        test.addCleanup(patcher.stop)

    def transcript(self, entries):
        path = Path(self.dir.name) / "t.jsonl"
        path.write_text("\n".join(json.dumps(e) for e in entries) + "\n", encoding="utf-8")
        return path

    def records(self):
        if not self.log.exists():
            return []
        return [json.loads(ln) for ln in self.log.read_text(encoding="utf-8").splitlines()]


def run_main(stdin_payload):
    out = io.StringIO()
    with mock.patch("sys.stdin", io.StringIO(json.dumps(stdin_payload))), redirect_stdout(out):
        with unittest.TestCase().assertRaises(SystemExit) as ctx:
            rh.main()
    return ctx.exception.code, out.getvalue()


class ReplyHygieneTest(unittest.TestCase):
    def test_claude_hedge_in_last_two_lines_is_logged(self):
        env = Env(self)
        path = env.transcript([claude_reply("Done.\n\nI can run the suite if you want.")])
        code, out = run_main({"session_id": "s1", "transcript_path": str(path)})
        self.assertEqual((code, out), (0, ""))
        got = [(r["tool"], r["session"], r["check"]) for r in env.records()]
        self.assertEqual(got, [("claude", "s1", "hedge")])

    def test_copilot_camel_case_keys_and_last_nonempty_message(self):
        env = Env(self)
        path = env.transcript([
            copilot_user("hi"),
            copilot_reply("All good.\nSay so if you disagree."),
            copilot_reply(""),
        ])
        code, out = run_main({"sessionId": "c1", "transcriptPath": str(path)})
        self.assertEqual((code, out), (0, ""))
        got = [(r["tool"], r["session"], r["check"]) for r in env.records()]
        self.assertEqual(got, [("copilot", "c1", "hedge")])

    def test_hedge_before_last_two_lines_is_ignored(self):
        env = Env(self)
        path = env.transcript([claude_reply("If you want more, ask.\nline two\nline three")])
        run_main({"session_id": "s", "transcript_path": str(path)})
        self.assertEqual(env.records(), [])

    def test_each_hedge_phrase(self):
        phrases = [
            "Your call.", "Left for you.", "I haven't checked it.", "I haven't verified it.",
            "That is unverified.", "Not verified.", "I can do that now if you like.",
            "I can run it if you prefer.", "Say so if needed.",
        ]
        for phrase in phrases:
            with self.subTest(phrase=phrase):
                self.assertEqual(len(rh.check_hedges("Result.\n" + phrase)), 1)

    def test_clean_reply_logs_nothing(self):
        env = Env(self)
        path = env.transcript([claude_reply("Tests pass.")])
        run_main({"session_id": "s", "transcript_path": str(path)})
        self.assertEqual(env.records(), [])

    def test_stop_hook_active_exits_without_reading(self):
        env = Env(self)
        code, out = run_main({"stop_hook_active": True, "transcript_path": "/nonexistent"})
        self.assertEqual((code, out, env.records()), (0, "", []))

    def test_sidechain_and_tool_only_entries_are_skipped(self):
        entries = [claude_reply("Real reply."), claude_reply("Sub reply, your call.", sidechain=True), CLAUDE_TOOL_ONLY]
        self.assertEqual(rh.last_reply(entries, "claude"), "Real reply.")

    def test_claude_theta_without_principles_line_is_logged(self):
        env = Env(self)
        path = env.transcript([THETA_USER, claude_reply("a\nb\nc\nd")])
        run_main({"session_id": "s", "transcript_path": str(path)})
        self.assertEqual([r["check"] for r in env.records()], ["missing_principles_line"])

    def test_claude_theta_with_principles_line_or_short_reply_is_clean(self):
        for text in ["a\nb\nc\nPrinciples applied: none", "a\nb\nc"]:
            with self.subTest(text=text):
                env = Env(self)
                path = env.transcript([THETA_USER, claude_reply(text)])
                run_main({"session_id": "s", "transcript_path": str(path)})
                self.assertEqual(env.records(), [])

    def test_non_theta_long_reply_is_clean(self):
        env = Env(self)
        path = env.transcript([claude_reply("a\nb\nc\nd\ne")])
        run_main({"session_id": "s", "transcript_path": str(path)})
        self.assertEqual(env.records(), [])

    def test_copilot_theta_detection(self):
        self.assertTrue(rh.is_theta_copilot([copilot_user("please /theta-mode this")]))
        self.assertFalse(rh.is_theta_copilot([copilot_user("hello")]))

    def test_copilot_theta_without_principles_line_is_logged(self):
        env = Env(self)
        path = env.transcript([copilot_user("/theta-mode go"), copilot_reply("a\nb\nc\nd")])
        run_main({"sessionId": "c", "transcriptPath": str(path)})
        self.assertEqual([r["check"] for r in env.records()], ["missing_principles_line"])

    def test_unreadable_transcript_is_logged_and_exits_zero(self):
        env = Env(self)
        code, out = run_main({"session_id": "s", "transcript_path": str(Path(env.dir.name) / "missing.jsonl")})
        self.assertEqual((code, out), (0, ""))
        self.assertEqual([r["check"] for r in env.records()], ["transcript_unreadable"])

    def test_transcript_without_reply_is_logged(self):
        env = Env(self)
        path = env.transcript([THETA_USER, CLAUDE_TOOL_ONLY])
        run_main({"session_id": "s", "transcript_path": str(path)})
        self.assertEqual([r["check"] for r in env.records()], ["no_reply_found"])

    def test_snippet_is_capped(self):
        env = Env(self)
        path = env.transcript([claude_reply("your call " + "x" * 400)])
        run_main({"session_id": "s", "transcript_path": str(path)})
        self.assertEqual(len(env.records()[0]["snippet"]), 160)

    def test_block_mode_prints_decision_on_hit_only(self):
        env = Env(self, mode="block")
        path = env.transcript([claude_reply("Done.\nYour call.")])
        code, out = run_main({"session_id": "s", "transcript_path": str(path)})
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out), {"decision": "block", "reason": rh.BLOCK_REASON})
        clean = env.transcript([claude_reply("Done.")])
        self.assertEqual(run_main({"session_id": "s", "transcript_path": str(clean)}), (0, ""))

    def test_block_mode_does_not_block_on_unreadable_transcript(self):
        env = Env(self, mode="block")
        code, out = run_main({"session_id": "s", "transcript_path": str(Path(env.dir.name) / "none")})
        self.assertEqual((code, out), (0, ""))

    def test_garbage_stdin_never_crashes(self):
        Env(self)
        out = io.StringIO()
        with mock.patch("sys.stdin", io.StringIO("not json")), redirect_stdout(out):
            with self.assertRaises(SystemExit) as ctx:
                rh.main()
        self.assertEqual((ctx.exception.code, out.getvalue()), (0, ""))


if __name__ == "__main__":
    unittest.main()
