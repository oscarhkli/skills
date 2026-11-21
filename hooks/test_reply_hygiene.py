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


USER_GO = {"type": "user", "message": {"role": "user", "content": "go"}}


def copilot_tool_call():
    return {"type": "assistant.message", "data": {"content": "", "toolRequests": [{"name": "bash"}]}}


class Env:
    def __init__(self, test, mode="log", block=None):
        self.dir = tempfile.TemporaryDirectory()
        test.addCleanup(self.dir.cleanup)
        self.log = Path(self.dir.name) / "logs" / "out.jsonl"
        patcher = mock.patch.dict(os.environ, {"REPLY_HYGIENE_LOG": str(self.log)})
        patcher.start()
        test.addCleanup(patcher.stop)
        for name, value in (("REPLY_HYGIENE_MODE", mode), ("REPLY_HYGIENE_BLOCK", block)):
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value

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
            ("Left for you.", "Left for you"),
            ("I can do that now if you like.", "I can do that now if you"),
            ("I can run it if you prefer.", "I can run it if you"),
            ("Say so if needed.", "Say so if"),
            ("Do it if you want.", "Do it if you want"),
            ("Which do you want?", "Which do you want"),
            ("Which one do you want first?", "Which one do you want"),
        ]
        for text, want in cases:
            with self.subTest(text=text):
                got = [phrase.lower() for _, phrase, _ in rh.check_hedges("Result.\n" + text)]
                self.assertEqual(got, [want.lower()])

    def test_if_you_want_offers_are_flagged(self):
        for text in [
            "Say if you want me to make it.",
            "I'll run it now, if you want, to find out which.",
            "If you want a PR from this branch, say so and I'll open one.",
            "If you want its content kept, I can recover it from git history.",
            "The roadmap item could be dropped, or take it now if you want story 7 watched.",
            "If you want X I'll do it.",
            "If you want, run it.",
            "If you want me to push it I'll do it",
            "Say if you want it run.",
            "I can update the README if you want.",
            "I can also refactor it if you want.",
            "I can create the file if you want.",
        ]:
            with self.subTest(text=text):
                got = [c for c, _, _ in rh.check_hedges("Result.\n" + text)]
                self.assertEqual(got, ["hedge"])

    def test_if_you_want_tradeoff_asides_are_not_flagged(self):
        for text in [
            "If you want one word for both, the table needs a decision, and that is your call.",
            "I'd pick option 2. If you want a package that others maintain, I'd pick option 1.",
            "If you want fewer items to track, the alternative is one plan with two PRs.",
            "If you want a fourth option, `WithRoomIDGenerator` would be the natural one.",
            "- **Possible gap:** if you want agents in other repos to find the backlog, add a line.",
            "If you want to know what I can do, read the README.",
            "If you want to know why I will not, see the log.",
            "If you want X\nI can see why.",
            "Say if you want them cut.",
            "I can pull TD-072 earlier if you want.",
            "I can update my view if you want to know why.",
            "Use refactor if you want speed.",
            "I can check the docs if you want to know more.",
        ]:
            with self.subTest(text=text):
                self.assertEqual(rh.check_hedges("Result.\n" + text), [])

    def test_reports_of_fact_and_open_decisions_are_not_flagged(self):
        for text in [
            "Still unverified: that the payload carries the field.",
            "I haven't run into problems.",
            "I have not run into problems.",
            "I haven't checked in the change.",
            "I tested it and it passes.",
            "The fix is not yet verified.",
            "The result was not verified by me.",
            "That is your call, and it is open.",
            "Pick the one that matches what you want.",
        ]:
            with self.subTest(text=text):
                self.assertEqual(rh.check_hedges("Result.\n" + text), [])

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

    def test_untested_admissions_and_should_i_offers(self):
        cases = [
            ("I haven't tested it yet. Should I try it?", ["I haven't tested"]),
            ("Should I add that to the TD-009 note?", ["Should I add"]),
            ("I haven\u2019t confirmed the version.", ["I haven\u2019t confirmed"]),
            ("I haven't checked which side is newer.", ["I haven't checked"]),
            ("I have not verified it.", ["I have not verified"]),
            ("I have not run the suite.", ["I have not run"]),
            ("Should I check the log or edit the config?", ["Should I check"]),
        ]
        for text, want in cases:
            with self.subTest(text=text):
                got = [phrase for _, phrase, _ in rh.check_hedges("Result.\n" + text)]
                self.assertEqual(got, want)

    def test_tested_statements_and_fenced_offers_are_not_flagged(self):
        for reply in [
            "Result.\nI tested it and the suite passes.",
            "Result.\nWe have tested, checked and run it.",
            "Result.\n```\nI haven't tested it. Should I try it?\n```\nDone.\nAll green.",
            "I haven't tested it.\nThe suite passes.\nAll green.",
        ]:
            with self.subTest(reply=reply):
                self.assertEqual(rh.check_hedges(reply), [])

    def test_statements_containing_question_words_are_not_flagged(self):
        for text in [
            "I see, marshall I see.",
            "You want me to be brief, so I was.",
            "Marshall I see nothing.",
            "Report goes to your caller.",
            "The result arrives via your callback.",
            "Nothing was left for you to do.",
            "> Want me to rerun?",
        ]:
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

    def test_fenced_lines_are_left_out_of_the_last_two_lines(self):
        reply = "Done.\nTests pass.\n```\nwant me to\n```"
        self.assertEqual(rh.check_hedges(reply), [])
        got = rh.check_hedges("Want me to rerun?\n```\nx\n```")
        self.assertEqual([phrase.lower() for _, phrase, _ in got], ["want me to"])

    def test_unclosed_fence_keeps_the_lines_after_it(self):
        cases = [
            ("Done.\n```\ncode\n```\nTests pass.\n```\nWant me to rerun?", ["want me to"]),
            ("Done.\n```\nWant me to rerun?\n```", []),
        ]
        for reply, want in cases:
            with self.subTest(reply=reply):
                got = [phrase.lower() for _, phrase, _ in rh.check_hedges(reply)]
                self.assertEqual(got, want)

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

    def test_offer_question_in_last_paragraph_is_flagged(self):
        cases = [
            "Want me to add a test?",
            "Should I add a test?",
            "Do you want me to add a test?",
            "Shall I add a test?",
            "Would you like me to add a test?",
            "Should I wire it into the hook as well?",
            "The hook is updated.\n\nI found the cause. Want me to add a test? It takes a minute.",
            "Done.\n\n- Should I add a test?",
            "Done.\n\nWant me to add a test?\n\nPrinciples applied: x\nPlaybooks read: none",
            "Done.\n\n```\nok\n```\n\nShould I add a test?",
            "Done.\n\n**Want me to add a test?**",
            "Done.\n\nWant me to add a test?\"",
        ]
        for text in cases:
            with self.subTest(text=text):
                got = [check for check, _, _ in rh.check_offer_question(text)]
                self.assertEqual(got, ["offer_question"])

    def test_offer_question_snippet_is_the_matching_sentence(self):
        got = rh.check_offer_question("Done.\n\nI found the cause. Want me to add a test? It takes a minute.")
        self.assertEqual(got, [("offer_question", "Want me to", "Want me to add a test?")])

    def test_non_offer_endings_are_not_flagged(self):
        cases = [
            "Done.\n\nWant me to add a test. I will.",
            "Done.\n\nWhich of these two options do you want, A or B?",
            "Done.\n\nYou asked: Want me to add a test?",
            "Done.\n\n> Want me to add a test?",
            "Done.\n\n\"Should I add a test?\" was the question.",
            "Done.\n\n```\nShould I add a test?\n```",
            "Should I add a test?\n\nNo. The suite already covers it.",
            "Should I add a test?\n\nNo.\n\nPrinciples applied: x",
            "Done.\n\nI wonder whether I should add a test?",
        ]
        for text in cases:
            with self.subTest(text=text):
                self.assertEqual(rh.check_offer_question(text), [])

    def test_offer_question_is_logged_with_its_own_check_name(self):
        env = Env(self)
        path = env.transcript([claude_reply("Done.\n\nShould I wire it into the hook as well?")])
        run_main({"session_id": "s", "transcript_path": str(path)})
        self.assertEqual([r["check"] for r in env.records()], ["offer_question"])

    def test_existing_hedge_hit_is_not_logged_twice(self):
        env = Env(self)
        path = env.transcript([claude_reply("Done.\n\nShould I push it?")])
        run_main({"session_id": "s", "transcript_path": str(path)})
        self.assertEqual([r["check"] for r in env.records()], ["hedge"])

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
        entries = [claude_reply("Real reply."), claude_reply("Sub reply, left for you.", sidechain=True), CLAUDE_TOOL_ONLY]
        self.assertEqual(rh.last_reply(entries, "claude"), "Real reply.")

    def test_claude_theta_without_principles_line_is_logged(self):
        env = Env(self)
        path = env.transcript([THETA_USER, CLAUDE_TOOL_ONLY, CLAUDE_TOOL_RESULT_USER, claude_reply("Pushed the fix\nb\nc\nd")])
        run_main({"session_id": "s", "transcript_path": str(path)})
        self.assertEqual([r["check"] for r in env.records()], ["missing_principles_line"])

    def test_hand_back_messages_stay_in_the_turn_that_owes_the_line(self):
        hand_back = {
            "type": "user",
            "message": {"role": "user", "content": "Another Claude session sent a message:\n<agent-message from=\"a1\">\n[Subagent hand-back] report</agent-message>"},
        }
        notification = {
            "type": "user",
            "message": {"role": "user", "content": [{"type": "text", "text": "<task-notification>\n<task-id>a1</task-id>\n</task-notification>"}]},
        }
        reminder = {"type": "user", "message": {"role": "user", "content": "<system-reminder>\n<tools-used-before-summary>Skill</tools-used-before-summary>\n</system-reminder>"}}
        for event in [hand_back, notification, reminder]:
            with self.subTest(event=event["message"]["content"]):
                self.assertIsNone(rh.claude_prompt(event))
                env = Env(self)
                path = env.transcript([THETA_USER, CLAUDE_TOOL_ONLY, CLAUDE_TOOL_RESULT_USER, event, claude_reply("Pushed the fix\nb\nc\nd")])
                run_main({"session_id": "s", "transcript_path": str(path)})
                self.assertEqual([r["check"] for r in env.records()], ["missing_principles_line"])

    def test_skill_body_message_stays_in_the_turn_that_owes_the_line(self):
        skill_body = {
            "type": "user",
            "isMeta": True,
            "message": {"role": "user", "content": [{"type": "text", "text": "Base directory for this skill: /x\n\n# Skill"}]},
        }
        skill_call = {
            "type": "assistant",
            "message": {"role": "assistant", "content": [{"type": "tool_use", "name": "Skill", "input": {}}]},
        }
        self.assertIsNone(rh.claude_prompt(skill_body))
        entries = [THETA_USER, skill_call, CLAUDE_TOOL_RESULT_USER, skill_body, claude_reply("Pushed the fix\nb\nc\nd")]
        self.assertTrue(rh.turn_used_tools(entries, "claude"))

    def test_prompt_that_quotes_the_task_notification_tag_is_still_a_prompt(self):
        entry = {"type": "user", "message": {"role": "user", "content": "Why does the hook skip <task-notification> entries?"}}
        self.assertIsNotNone(rh.claude_prompt(entry))

    def test_prompt_with_a_system_reminder_and_human_text_is_still_a_prompt(self):
        blocks = [{"type": "text", "text": "<system-reminder>x</system-reminder>"}, {"type": "text", "text": "go on"}]
        entry = {"type": "user", "message": {"role": "user", "content": blocks}}
        self.assertIsNotNone(rh.claude_prompt(entry))

    def test_human_prompt_after_a_hand_back_still_starts_a_new_turn(self):
        hand_back = {"type": "user", "message": {"role": "user", "content": "Another Claude session sent a message:\nx"}}
        entries = [THETA_USER, CLAUDE_TOOL_ONLY, hand_back, USER_GO, claude_reply("Pushed the fix\nb\nc\nd")]
        self.assertFalse(rh.turn_used_tools(entries, "claude"))

    def test_theta_answer_without_tool_use_in_the_turn_is_clean(self):
        env = Env(self)
        path = env.transcript([THETA_USER, CLAUDE_TOOL_ONLY, CLAUDE_TOOL_RESULT_USER, claude_reply("ok"), USER_GO, claude_reply("Pushed the fix\nb\nc\nd")])
        run_main({"session_id": "s", "transcript_path": str(path)})
        self.assertEqual(env.records(), [])

    def test_copilot_theta_answer_without_tool_use_is_clean(self):
        env = Env(self)
        path = env.transcript([copilot_user("/theta-mode go"), copilot_reply("a\nb\nc\nd")])
        run_main({"sessionId": "c", "transcriptPath": str(path)})
        self.assertEqual(env.records(), [])

    def test_claude_theta_with_principles_line_or_short_reply_is_clean(self):
        for text in ["a\nb\nc\nPrinciples applied: none", "a\nb\nc"]:
            with self.subTest(text=text):
                env = Env(self)
                path = env.transcript([THETA_USER, claude_reply(text)])
                run_main({"session_id": "s", "transcript_path": str(path)})
                self.assertEqual(env.records(), [])

    def principles_checks(self, text):
        env = Env(self)
        path = env.transcript([THETA_USER, CLAUDE_TOOL_ONLY, CLAUDE_TOOL_RESULT_USER, claude_reply(text)])
        run_main({"session_id": "s", "transcript_path": str(path)})
        return [r["check"] for r in env.records()]

    def test_pending_delegate_announcement_is_not_flagged(self):
        replies = [
            "Two delegates are running in separate worktrees.\n- **A:** builds it.\n- **B:** checks it.\n\nI'll report both together when they finish.",
            "A Haiku delegate is applying the edits to the backlog.\n- one\n- two\n\nI'll show you the diagram when it reports.",
            "A delegate is now reading the code.\nIt lists each rule.\nIt cites the file.\n\nI'll send you the table once it reports.",
            "A subagent is still checking the lock.\n- It reads server.go.\n- It runs the tests.\n\nI will report the result when it finishes.",
            "Two subagents are running in parallel.\n- **A:** edits the hook.\n- **B:** checks the log.\n\ni'll Report both when they finish.",
            "A delegate is drafting the PR text.\n- Decision: keep the rule strict.\n- It follows the unslop skill.\n\nI'll report the link when it finishes.",
            "The retro is running. A research delegate is reading this session's transcript and the skills it touched.\n- It lists each miss.\n- It cites the file.\n\nWhen it reports I'll then ask you about priorities and scope, and edit nothing until you approve.",
            "My first attempt was denied. A second delegate is now editing a project-brain worktree and will commit locally only.\n- It touches one file.\n- It runs the checks.\n\nWhen it finishes I'll ask whether to push and open a PR for it.",
        ]
        for text in replies:
            with self.subTest(text=text):
                self.assertEqual(self.principles_checks(text), [])

    def test_pending_delegate_announcement_with_a_change_claiming_first_line_is_not_flagged(self):
        text = "A delegate is running the tests on commit `9f01b93`.\n- It reads the log.\n- It checks the exit code.\n\nI'll report the result when it finishes."
        self.assertEqual(self.principles_checks(text), [])

    def test_report_without_principles_line_is_still_flagged(self):
        replies = [
            "Yes, it fits and is pushed. A delegate is measuring before it rates the item.\n- **One:** counts.\n- **Two:** lint.\n\nI'll report the counts when it finishes.",
            "The fixes are pushed, and a delegate is now re-checking them.\n- **One:** done.\n- **Two:** done.\n\nI'll report the result when it finishes.",
            "Both fixes are pushed. A delegate found two bugs.\n- **One:** the lock is missing.\n- **Two:** the test is flaky.\n\nBoth are fixed.",
            "Committed the prototype and two claims fail.\n- **Submit:** aliases.\n- **Config:** aliases.\n\nI'll report once the second prototype finishes.",
            "Drafted the cleanup. A delegate is cleaning up the worktree.\n- It checks the PR.\n- It removes the branch.\n\nDecision for you: remove the prototypes too? I'd recommend it.",
            "Opened the PR. A delegate is done.\n- **One:** checked.\n- **Two:** checked.\nI fixed the lock in server.go and it passes.\n\nI'll report the commit later.",
            "Pushed the fix. The agent is right about the lock.\n- **One:** it is shared.\n- **Two:** it is held.\n\nI'll report back.",
            "Committed the edit. A delegate is running the tests.\n- I edited server.go.\n- I added a test.\n\nI'll report the commit when it finishes.",
        ]
        for text in replies:
            with self.subTest(text=text):
                self.assertEqual(self.principles_checks(text), ["missing_principles_line"])

    def test_first_line_that_claims_a_change_owes_the_principles_line(self):
        firsts = [
            "PR #17 now has the 8-story plan and index (commits `9feff1f`)",
            "Both fixes are pushed to PR #17 as `9f01b93`",
            "The docs/design.md fix is pushed to PR #129 as `e8bfdfd`",
            "Implemented the hook change in hooks/reply_hygiene.py",
            "Added the retry to server.go and tests pass",
            "Fixed the lock",
            "Merged PR #5",
            "Updated the docs",
            "Opened the PR for the hook",
            "PR #30 is open as PR on the skills repo",
            "The ending-question check is open as skills PR #30: a link",
            "The PR for the hook is open",
            "Fixed in commit `9f01b93`",
        ]
        for first in firsts:
            with self.subTest(first=first):
                self.assertEqual(self.principles_checks(first + "\n- one\n- two\n\nDone."), ["missing_principles_line"])

    def test_first_line_without_a_change_claim_does_not_owe_the_principles_line(self):
        firsts = [
            "PR #17 is merged, main is pulled and the worktree is removed",
            "My recommendation: merge stories 4, 5 and 6 first",
            "#1 What server/openapi_wire_test.go is about",
            "The check is back and story 2 fails",
            "I opened the file and the lock is shared",
        ]
        for first in firsts:
            with self.subTest(first=first):
                self.assertEqual(self.principles_checks(first + "\n- one\n- two\n\nDone."), [])

    def test_change_claim_with_the_principles_line_is_never_flagged(self):
        text = "Both fixes are pushed to PR #17 as `9f01b93`\n- one\n- two\n\nPrinciples applied: none"
        self.assertEqual(self.principles_checks(text), [])

    def test_change_claim_on_a_later_line_does_not_owe_the_principles_line(self):
        text = "Here is the status.\n- one\n- two\n\nBoth fixes are pushed to PR #17."
        self.assertEqual(self.principles_checks(text), [])

    def test_pending_delegate_reply_with_a_blocking_ask_is_still_a_hedge(self):
        text = "Two delegates are running and the fix is pushed.\n- **A:** builds it.\n- **B:** checks it.\n\nDecision for you: should I add it to the plan?"
        self.assertEqual(self.principles_checks(text), ["hedge", "missing_principles_line"])

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
        path = env.transcript([{"type": "user", "message": {"role": "user", "content": "hi"}}, CLAUDE_TOOL_RESULT_USER, claude_reply("Pushed the fix\nb\nc\nd")])
        run_main({"session_id": "s", "transcript_path": str(path)})
        self.assertEqual(env.records(), [])

    def test_earlier_turn_reply_is_not_rechecked_when_final_turn_has_no_text(self):
        env = Env(self)
        user = {"type": "user", "message": {"role": "user", "content": "go"}}
        path = env.transcript([user, claude_reply("Done.\nLet me know if."), user, CLAUDE_TOOL_ONLY, CLAUDE_TOOL_RESULT_USER, CLAUDE_TOOL_ONLY])
        run_main({"session_id": "s", "transcript_path": str(path)})
        self.assertEqual([r["check"] for r in env.records()], ["no_reply_found"])

    def test_reply_after_tool_results_in_final_turn_is_used(self):
        user = {"type": "user", "message": {"role": "user", "content": "go"}}
        entries = [user, claude_reply("old"), user, CLAUDE_TOOL_ONLY, CLAUDE_TOOL_RESULT_USER, claude_reply("new")]
        self.assertEqual(rh.last_reply(entries, "claude"), "new")

    def test_copilot_earlier_turn_reply_is_not_rechecked(self):
        env = Env(self)
        path = env.transcript([copilot_user("go"), copilot_reply("Done.\nLet me know if."), copilot_user("again"), copilot_reply("")])
        run_main({"sessionId": "c", "transcriptPath": str(path)})
        self.assertEqual([r["check"] for r in env.records()], ["no_reply_found"])

    def test_crlf_transcript(self):
        env = Env(self)
        path = Path(env.dir.name) / "crlf.jsonl"
        lines = [json.dumps(e) for e in [THETA_USER, claude_reply("Done.\nLet me know if.")]]
        path.write_bytes("\r\n".join(lines).encode("utf-8") + b"\r\n")
        run_main({"session_id": "s", "transcript_path": str(path)})
        self.assertEqual([r["check"] for r in env.records()], ["hedge"])

    def test_non_utf8_line_is_skipped(self):
        env = Env(self)
        path = Path(env.dir.name) / "bad.jsonl"
        path.write_bytes(b"\xff\xfe not json\n" + json.dumps(claude_reply("Done.\nLet me know if.")).encode("utf-8") + b"\n")
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
        path = env.transcript([claude_reply("x" * 2_000_000 + "\nLet me know if.")])
        run_main({"session_id": "s", "transcript_path": str(path)})
        self.assertEqual([r["check"] for r in env.records()], ["hedge"])

    def test_log_write_failure_exits_zero_with_empty_stdout(self):
        env = Env(self, mode="block")
        blocker = Path(env.dir.name) / "file"
        blocker.write_text("x", encoding="utf-8")
        path = env.transcript([claude_reply("Done.\nLet me know if.")])
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
        events.write_text("\n".join(json.dumps(e) for e in [copilot_user("go"), copilot_reply("Done.\nLet me know if.")]) + "\n", encoding="utf-8")
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
        path = env.transcript([copilot_user("/theta-mode go"), copilot_tool_call(), copilot_reply("Pushed the fix\nb\nc\nd")])
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
        payload = {"session_id": "s", "transcript_path": str(path), "last_assistant_message": "Done.\nLet me know if."}
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
        run_main({"session_id": "s", "transcript_path": str(path), "last_assistant_message": "Pushed the fix\nb\nc\nd"})
        self.assertEqual([r["check"] for r in env.records()], ["missing_principles_line"])

    def test_payload_reply_is_checked_when_transcript_is_unreadable(self):
        env = Env(self)
        run_main({"session_id": "s", "transcript_path": str(Path(env.dir.name) / "none"), "last_assistant_message": "Done.\nLet me know if."})
        self.assertEqual([r["check"] for r in env.records()], ["hedge"])

    def test_empty_payload_reply_falls_back_to_transcript(self):
        env = Env(self)
        path = env.transcript([claude_reply("Done.\nLet me know if.")])
        run_main({"session_id": "s", "transcript_path": str(path), "last_assistant_message": "  "})
        self.assertEqual([r["check"] for r in env.records()], ["hedge"])

    def test_transcript_read_is_retried_until_reply_appears(self):
        env = Env(self)
        path = env.transcript([THETA_USER, CLAUDE_TOOL_ONLY])
        late = [THETA_USER, CLAUDE_TOOL_ONLY, claude_reply("Done.\nLet me know if.")]

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
        path = env.transcript([claude_reply("let me know if " + "x" * 400)])
        run_main({"session_id": "s", "transcript_path": str(path)})
        self.assertEqual(len(env.records()[0]["snippet"]), 160)

    def test_block_mode_prints_decision_on_hit_only(self):
        env = Env(self, mode="block")
        path = env.transcript([claude_reply("Done.\nLet me know if.")])
        code, out = run_main({"session_id": "s", "transcript_path": str(path)})
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out), {"decision": "block", "reason": rh.BLOCK_REASON})
        clean = env.transcript([claude_reply("Done.")])
        self.assertEqual(run_main({"session_id": "s", "transcript_path": str(clean)}), (0, ""))

    def stop_with(self, text, mode=None, block=None, entries=None):
        env = Env(self, mode=mode, block=block)
        path = env.transcript(entries or [claude_reply(text)])
        out = run_main({"session_id": "s", "transcript_path": str(path)})
        return env, out

    def test_hedge_and_offer_question_block_by_default(self):
        for text in ["Done.\nLet me know if.", "Done.\n\nShould I wire it into the hook as well?", "Done.\n\nWant me to add a test?"]:
            with self.subTest(text=text):
                env, (code, out) = self.stop_with(text)
                self.assertEqual(code, 0)
                self.assertEqual(json.loads(out)["decision"], "block")
                self.assertEqual([r["blocked"] for r in env.records()], [True])

    def test_missing_principles_line_logs_without_blocking_by_default(self):
        entries = [THETA_USER, CLAUDE_TOOL_ONLY, CLAUDE_TOOL_RESULT_USER, claude_reply("Pushed the fix\nb\nc\nd")]
        env, out = self.stop_with("", entries=entries)
        self.assertEqual(out, (0, ""))
        self.assertEqual([(r["check"], r["blocked"]) for r in env.records()], [("missing_principles_line", False)])

    def test_block_list_overrides_the_defaults(self):
        principles = [THETA_USER, CLAUDE_TOOL_ONLY, CLAUDE_TOOL_RESULT_USER, claude_reply("Pushed the fix\nb\nc\nd")]
        cases = [
            ("hedge,offer_question,missing_principles_line", principles, True),
            (" missing_principles_line , ", principles, True),
            ("", [claude_reply("Done.\nLet me know if.")], False),
            ("offer_question", [claude_reply("Done.\nLet me know if.")], False),
            ("hedge", [claude_reply("Done.\nLet me know if.")], True),
        ]
        for block, entries, blocks in cases:
            with self.subTest(block=block):
                env, (_, out) = self.stop_with("", block=block, entries=entries)
                self.assertEqual(bool(out), blocks)
                self.assertEqual([r["blocked"] for r in env.records()], [blocks])

    def test_mode_log_forces_log_only_for_every_check(self):
        env, out = self.stop_with("Done.\nLet me know if.", mode="log", block="hedge")
        self.assertEqual(out, (0, ""))
        self.assertEqual([r["blocked"] for r in env.records()], [False])

    def test_mode_block_blocks_every_check(self):
        principles = [THETA_USER, CLAUDE_TOOL_ONLY, CLAUDE_TOOL_RESULT_USER, claude_reply("Pushed the fix\nb\nc\nd")]
        env, (_, out) = self.stop_with("", mode="block", block="", entries=principles)
        self.assertEqual(json.loads(out)["decision"], "block")
        self.assertEqual([r["blocked"] for r in env.records()], [True])

    def test_only_blocking_hits_are_marked_blocked(self):
        text = "Two delegates are running and the fix is pushed.\n- one\n- two\n\nDecision for you: should I add it to the plan?"
        entries = [THETA_USER, CLAUDE_TOOL_ONLY, CLAUDE_TOOL_RESULT_USER, claude_reply(text)]
        env, (_, out) = self.stop_with("", entries=entries)
        self.assertEqual(json.loads(out)["decision"], "block")
        self.assertEqual([(r["check"], r["blocked"]) for r in env.records()], [("hedge", True), ("missing_principles_line", False)])

    def test_failure_checks_never_block_even_in_block_mode(self):
        env = Env(self, mode="block")
        code, out = run_main({"session_id": "s", "transcript_path": str(Path(env.dir.name) / "none")})
        self.assertEqual((code, out), (0, ""))
        self.assertEqual([r["blocked"] for r in env.records()], [False])

    def test_loop_guard_and_one_block_per_turn(self):
        env = Env(self, mode=None)
        path = env.transcript([claude_reply("Done.\nLet me know if.")])
        first = run_main({"session_id": "s", "transcript_path": str(path)})
        again = run_main({"session_id": "s", "transcript_path": str(path), "stop_hook_active": True})
        self.assertEqual(json.loads(first[1])["decision"], "block")
        self.assertEqual(again, (0, ""))
        self.assertEqual(len(env.records()), 1)

    def test_missing_principles_line_record_keeps_first_and_last_line(self):
        entries = [THETA_USER, CLAUDE_TOOL_ONLY, CLAUDE_TOOL_RESULT_USER, claude_reply("Pushed the fix\nb\nc\nlast line")]
        env, _ = self.stop_with("", entries=entries)
        record = env.records()[0]
        self.assertEqual((record["first_line"], record["snippet"]), ("Pushed the fix", "last line"))

    def test_other_records_have_no_first_line(self):
        env, _ = self.stop_with("Done.\nLet me know if.")
        self.assertNotIn("first_line", env.records()[0])

    def test_legitimate_asks_and_disclosures_are_not_blocked(self):
        for text in [
            "Done.\n\nDecision for you: A keeps the route, B drops it. I'd pick B.",
            "Done.\n\nStill unverified: that the payload carries the field.",
            "Done.\n\nI haven't run the e2e suite because it needs credentials.",
            "Done.\n\nI have not verified the deploy because it requires production access.",
            "Done.\n\nI haven't confirmed the vendor plan since it needs a human decision on cost.",
        ]:
            with self.subTest(text=text):
                env, out = self.stop_with(text)
                self.assertEqual((out, env.records()), ((0, ""), []))

    def test_the_frustrating_phrases_block_end_to_end(self):
        for text in [
            "Done.\n\nWant me to add a test?",
            "Done.\n\nDo you want me to add a test?",
            "Done.\n\nShall I add a test?",
            "Done.\n\nWould you like me to add a test?",
            "Done.\n\nI can run the suite if you want.",
            "Done.\n\nI can do the rename if you want it.",
            "Done.\n\nI haven't tested it.",
            "Done.\n\nI haven't checked the other callers.",
            "Done.\n\nI haven't run the suite.",
            "Done.\n\nI haven't verified the output.",
            "Done.\n\nI haven't confirmed the version.",
            "Done.\n\nI haven't run the suite because it is slow.",
            "Done.\n\nI haven't tested it because I ran out of time.",
        ]:
            with self.subTest(text=text):
                env, (_, out) = self.stop_with(text)
                self.assertEqual(json.loads(out)["decision"], "block")
                self.assertEqual([r["blocked"] for r in env.records()], [True])

    def test_block_reason_tells_the_agent_to_do_the_work_and_names_the_allowances(self):
        for part in ["do X before replying", "needs credentials, a human decision, or cost or production access", "Decision for you:"]:
            with self.subTest(part=part):
                self.assertIn(part, rh.BLOCK_REASON)

    def test_block_reason_leads_with_the_blocker_question(self):
        self.assertTrue(rh.BLOCK_REASON.startswith(
            "Who is blocking you? Do the action or the check now, or name the one decision only the human can make."
        ))

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
