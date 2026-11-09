import io
import json
import os
import tempfile
import types
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


CLAUDE_TOOL_RESULT_USER = {
    "type": "user",
    "message": {
        "role": "user",
        "content": [{"type": "tool_result", "tool_use_id": "t1", "content": "<command-name>/theta-mode</command-name>"}],
    },
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


def fake_stdin(data):
    if isinstance(data, str):
        data = data.encode("utf-8")
    return types.SimpleNamespace(buffer=io.BytesIO(data))


def run_main(stdin_payload):
    out = io.StringIO()
    with mock.patch("sys.stdin", fake_stdin(json.dumps(stdin_payload))), redirect_stdout(out):
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
        cases = [
            ("Your call.", "Your call"),
            ("Left for you.", "Left for you"),
            ("I haven't checked it.", "I haven't checked"),
            ("I haven\u2019t checked it.", "I haven\u2019t checked"),
            ("I haven't verified it.", "I haven't verified"),
            ("That is unverified.", "unverified"),
            ("Not verified.", "Not verified"),
            ("I can do that now if you like.", "I can do that now if you"),
            ("I can run it if you prefer.", "I can run it if you"),
            ("Say so if needed.", "Say so if"),
            ("Do it if you want.", "if you want"),
        ]
        for text, want in cases:
            with self.subTest(text=text):
                got = [phrase.lower() for _, phrase, _ in rh.check_hedges("Result.\n" + text)]
                self.assertEqual(got, [want.lower()])

    def test_question_form_closers(self):
        cases = [
            ("Do you want me to push the branch and open the PR?", "do you want me to"),
            ("Want me to run the e2e tests too?", "want me to"),
            ("Shall I proceed?", "shall i"),
            ("Should I push it?", "should i push"),
            ("Should I go ahead with the merge?", "should i go ahead"),
            ("Should I commit now?", "should i commit"),
            ("Would you like me to open the PR?", "would you like me to"),
            ("Let me know if the wording needs work.", "let me know if"),
        ]
        for text, want in cases:
            with self.subTest(text=text):
                got = [phrase.lower() for _, phrase, _ in rh.check_hedges("Result.\n" + text)]
                self.assertEqual(got, [want])

    def test_statements_containing_question_words_are_not_flagged(self):
        for text in ["I see, marshall I see.", "You want me to be brief, so I was.", "Marshall I see nothing."]:
            with self.subTest(text=text):
                self.assertEqual(rh.check_hedges("Result.\n" + text), [])

    def test_line_start_question_forms_are_flagged(self):
        cases = [
            ("Shall I merge?", "shall i"),
            ("Want me to run it?", "want me to"),
            ("- Want me to run it?", "- want me to"),
        ]
        for text, want in cases:
            with self.subTest(text=text):
                got = [phrase.lower() for _, phrase, _ in rh.check_hedges("Result.\n" + text)]
                self.assertEqual(got, [want])

    def test_decision_question_is_logged_for_review(self):
        got = rh.check_hedges("Option A keeps the route, option B drops it.\nShould I start with B?")
        self.assertEqual([phrase.lower() for _, phrase, _ in got], ["should i start"])

    def test_question_form_before_last_two_lines_is_ignored(self):
        got = rh.check_hedges("Do you want me to push?\nline two\nline three")
        self.assertEqual(got, [])

    def test_hedge_on_second_to_last_line_after_trailers_are_dropped(self):
        got = [phrase for _, phrase, _ in rh.check_hedges("Say so if x.\nDone.")]
        self.assertEqual(got, ["Say so if"])
        got = [phrase for _, phrase, _ in rh.check_hedges("Say so if x.\nDone.\nPrinciples applied: y")]
        self.assertEqual(got, ["Say so if"])

    def test_hedge_before_trailing_theta_lines_is_logged(self):
        reply = "Fixed.\nSay so if you want it fixed.\nPrinciples applied: x\nPlaybooks read: none"
        got = [(c, line) for c, _, line in rh.check_hedges(reply)]
        self.assertEqual(got, [("hedge", "Say so if you want it fixed.")])

    def test_hedge_quoted_only_in_principles_line_is_ignored(self):
        reply = "Fixed.\nTests pass.\nPrinciples applied: x (I haven't checked)\nPlaybooks read: none"
        self.assertEqual(rh.check_hedges(reply), [])

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
        self.assertTrue(rh.is_theta_copilot([copilot_user("/theta-mode foo")]))
        self.assertTrue(rh.is_theta_copilot([copilot_user("  /theta-mode")]))
        self.assertFalse(rh.is_theta_copilot([copilot_user("stop theta-mode")]))
        self.assertFalse(rh.is_theta_copilot([copilot_user("please /theta-mode this")]))
        self.assertFalse(rh.is_theta_copilot([copilot_user("hello")]))

    def test_claude_theta_needs_a_real_user_prompt(self):
        self.assertFalse(rh.is_theta_claude([CLAUDE_TOOL_RESULT_USER]))
        self.assertFalse(rh.is_theta_claude([claude_reply("<command-name>/theta-mode</command-name>")]))
        self.assertTrue(rh.is_theta_claude([THETA_USER]))
        block_prompt = {"type": "user", "message": {"role": "user", "content": [{"type": "text", "text": THETA_USER["message"]["content"]}]}}
        self.assertTrue(rh.is_theta_claude([block_prompt]))

    def test_claude_tool_result_marker_does_not_make_a_theta_session(self):
        env = Env(self)
        path = env.transcript([{"type": "user", "message": {"role": "user", "content": "hi"}}, CLAUDE_TOOL_RESULT_USER, claude_reply("a\nb\nc\nd")])
        run_main({"session_id": "s", "transcript_path": str(path)})
        self.assertEqual(env.records(), [])

    def test_earlier_turn_reply_is_not_rechecked_when_final_turn_has_no_text(self):
        env = Env(self)
        user = {"type": "user", "message": {"role": "user", "content": "go"}}
        path = env.transcript([user, claude_reply("Done.\nYour call."), user, CLAUDE_TOOL_ONLY, CLAUDE_TOOL_RESULT_USER, CLAUDE_TOOL_ONLY])
        run_main({"session_id": "s", "transcript_path": str(path)})
        self.assertEqual([r["check"] for r in env.records()], ["no_reply_found"])

    def test_reply_after_tool_results_in_final_turn_is_used(self):
        user = {"type": "user", "message": {"role": "user", "content": "go"}}
        entries = [user, claude_reply("old"), user, CLAUDE_TOOL_ONLY, CLAUDE_TOOL_RESULT_USER, claude_reply("new")]
        self.assertEqual(rh.last_reply(entries, "claude"), "new")

    def test_copilot_earlier_turn_reply_is_not_rechecked(self):
        env = Env(self)
        path = env.transcript([copilot_user("go"), copilot_reply("Done.\nYour call."), copilot_user("again"), copilot_reply("")])
        run_main({"sessionId": "c", "transcriptPath": str(path)})
        self.assertEqual([r["check"] for r in env.records()], ["no_reply_found"])

    def test_crlf_transcript(self):
        env = Env(self)
        path = Path(env.dir.name) / "crlf.jsonl"
        lines = [json.dumps(e) for e in [THETA_USER, claude_reply("Done.\nYour call.")]]
        path.write_bytes("\r\n".join(lines).encode("utf-8") + b"\r\n")
        run_main({"session_id": "s", "transcript_path": str(path)})
        self.assertEqual([r["check"] for r in env.records()], ["hedge"])

    def test_non_utf8_line_is_skipped(self):
        env = Env(self)
        path = Path(env.dir.name) / "bad.jsonl"
        path.write_bytes(b"\xff\xfe not json\n" + json.dumps(claude_reply("Done.\nYour call.")).encode("utf-8") + b"\n")
        code, out = run_main({"session_id": "s", "transcript_path": str(path)})
        self.assertEqual((code, out), (0, ""))
        self.assertEqual([r["check"] for r in env.records()], ["hedge"])

    def test_empty_transcript_is_logged_as_no_reply(self):
        env = Env(self)
        path = Path(env.dir.name) / "empty.jsonl"
        path.write_bytes(b"")
        code, out = run_main({"session_id": "s", "transcript_path": str(path)})
        self.assertEqual((code, out), (0, ""))
        self.assertEqual([r["check"] for r in env.records()], ["no_reply_found"])

    def test_very_long_line_is_handled(self):
        env = Env(self)
        path = env.transcript([claude_reply("x" * 2_000_000 + "\nYour call.")])
        run_main({"session_id": "s", "transcript_path": str(path)})
        self.assertEqual([r["check"] for r in env.records()], ["hedge"])

    def test_log_write_failure_exits_zero_with_empty_stdout(self):
        env = Env(self, mode="block")
        blocker = Path(env.dir.name) / "file"
        blocker.write_text("x", encoding="utf-8")
        path = env.transcript([claude_reply("Done.\nYour call.")])
        with mock.patch.dict(os.environ, {"REPLY_HYGIENE_LOG": str(blocker / "sub" / "out.jsonl")}):
            code, out = run_main({"session_id": "s", "transcript_path": str(path)})
        self.assertEqual((code, out), (0, ""))

    def test_camel_case_stop_hook_active_exits_without_reading(self):
        env = Env(self)
        code, out = run_main({"stopHookActive": True, "transcriptPath": "/nonexistent"})
        self.assertEqual((code, out, env.records()), (0, "", []))

    def test_non_object_payload_exits_zero(self):
        env = Env(self)
        code, out = run_main([])
        self.assertEqual((code, out), (0, ""))
        self.assertEqual([r["check"] for r in env.records()], ["transcript_unreadable"])

    def test_missing_transcript_path_is_logged(self):
        env = Env(self)
        code, out = run_main({})
        self.assertEqual((code, out), (0, ""))
        self.assertEqual([r["check"] for r in env.records()], ["transcript_unreadable"])

    def test_copilot_events_file_fallback_under_home(self):
        env = Env(self)
        home = Path(env.dir.name) / "home"
        events = home / ".copilot" / "session-state" / "c1" / "events.jsonl"
        events.parent.mkdir(parents=True)
        events.write_text("\n".join(json.dumps(e) for e in [copilot_user("go"), copilot_reply("Done.\nYour call.")]) + "\n", encoding="utf-8")
        with mock.patch.dict(os.environ, {"HOME": str(home), "USERPROFILE": str(home)}):
            code, out = run_main({"sessionId": "c1"})
        self.assertEqual((code, out), (0, ""))
        self.assertEqual([(r["tool"], r["check"]) for r in env.records()], [("copilot", "hedge")])

    def test_log_is_opened_with_unix_newlines(self):
        env = Env(self)
        real_open = Path.open
        seen = []

        def spy(self, *args, **kwargs):
            seen.append(kwargs.get("newline"))
            return real_open(self, *args, **kwargs)

        with mock.patch.object(Path, "open", spy):
            rh.append_log("claude", "s", "hedge", "p", "line")
        self.assertEqual(seen, ["\n"])
        self.assertTrue(env.log.read_bytes().endswith(b"}\n"))

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

    def test_payload_reply_is_checked_when_transcript_lacks_it(self):
        env = Env(self)
        path = env.transcript([THETA_USER, CLAUDE_TOOL_ONLY])
        payload = {"session_id": "s", "transcript_path": str(path), "last_assistant_message": "Done.\nYour call."}
        with mock.patch("time.sleep") as sleep:
            run_main(payload)
        self.assertEqual([r["check"] for r in env.records()], ["hedge"])
        sleep.assert_not_called()

    def test_payload_reply_camel_case_for_copilot(self):
        env = Env(self)
        path = env.transcript([copilot_user("hi")])
        run_main({"sessionId": "c", "transcriptPath": str(path), "lastAssistantMessage": "Done.\nLet me know if."})
        self.assertEqual([(r["tool"], r["check"]) for r in env.records()], [("copilot", "hedge")])

    def test_payload_reply_still_uses_transcript_for_theta(self):
        env = Env(self)
        path = env.transcript([THETA_USER, CLAUDE_TOOL_ONLY])
        run_main({"session_id": "s", "transcript_path": str(path), "last_assistant_message": "a\nb\nc\nd"})
        self.assertEqual([r["check"] for r in env.records()], ["missing_principles_line"])

    def test_payload_reply_is_checked_when_transcript_is_unreadable(self):
        env = Env(self)
        run_main({"session_id": "s", "transcript_path": str(Path(env.dir.name) / "none"), "last_assistant_message": "Done.\nYour call."})
        self.assertEqual([r["check"] for r in env.records()], ["hedge"])

    def test_empty_payload_reply_falls_back_to_transcript(self):
        env = Env(self)
        path = env.transcript([claude_reply("Done.\nYour call.")])
        run_main({"session_id": "s", "transcript_path": str(path), "last_assistant_message": "  "})
        self.assertEqual([r["check"] for r in env.records()], ["hedge"])

    def test_transcript_read_is_retried_until_reply_appears(self):
        env = Env(self)
        path = env.transcript([THETA_USER, CLAUDE_TOOL_ONLY])
        late = [THETA_USER, CLAUDE_TOOL_ONLY, claude_reply("Done.\nYour call.")]

        def append_reply(_seconds):
            path.write_text("\n".join(json.dumps(e) for e in late) + "\n", encoding="utf-8")

        with mock.patch("time.sleep", side_effect=append_reply) as sleep:
            run_main({"session_id": "s", "transcript_path": str(path)})
        self.assertEqual([r["check"] for r in env.records()], ["hedge"])
        self.assertEqual(sleep.call_count, 1)

    def test_retries_are_bounded_then_no_reply_is_logged(self):
        env = Env(self)
        path = env.transcript([THETA_USER, CLAUDE_TOOL_ONLY])
        with mock.patch("time.sleep") as sleep:
            run_main({"session_id": "s", "transcript_path": str(path)})
        self.assertEqual([r["check"] for r in env.records()], ["no_reply_found"])
        self.assertEqual([c.args for c in sleep.call_args_list], [(0.3,)] * 3)

    def test_failure_logs_record_payload_keys_without_values(self):
        env = Env(self)
        path = env.transcript([THETA_USER, CLAUDE_TOOL_ONLY])
        with mock.patch("time.sleep"):
            run_main({"session_id": "secret-id", "transcript_path": str(path), "hook_event_name": "Stop"})
            run_main({"session_id": "secret-id", "transcript_path": str(path.with_name("none")), "cwd": "/x"})
        got = [(r["check"], r["payload_keys"]) for r in env.records()]
        self.assertEqual(got, [
            ("no_reply_found", ["hook_event_name", "session_id", "transcript_path"]),
            ("transcript_unreadable", ["cwd", "session_id", "transcript_path"]),
        ])

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
        with mock.patch("sys.stdin", fake_stdin("not json")), redirect_stdout(out):
            with self.assertRaises(SystemExit) as ctx:
                rh.main()
        self.assertEqual((ctx.exception.code, out.getvalue()), (0, ""))


if __name__ == "__main__":
    unittest.main()
