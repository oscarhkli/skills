#!/usr/bin/env python3
"""Stop hook: flag hedged or unfinished final replies, log each hit, and block the blocking checks once per turn.
Env: REPLY_HYGIENE_BLOCK, REPLY_HYGIENE_MODE, REPLY_HYGIENE_LOG; defaults live in DEFAULT_BLOCKING."""
from __future__ import annotations

import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HEDGES = [
    r"(?<=[\w`\"'\u2019,]\s)if you want\b(?!\s+to\b)(?=\s+me to\b|[^.?!\n]*\b(?:run|ran|test|check|verify|confirm|fix|commit|push|open|write|add|do|update|refactor|create|start|investigate|watch)(?:s|ed|d|ing)?\b)",
    r"\b(?:run|test|check|verify|confirm|fix|commit|push|open|write|add|do|update|refactor|create|start|investigate|watch)\b[^.?!\n]*?(?<=[\w`\"'\u2019,]\s)if you want\b(?=[ \t]*(?:[.,;?!\n]|$)|\s+(?:that|it|me)\b)",
    r"\bif you want\b(?:(?!\b(?:what|why|how|who|when|where|which|whether|that)\b)[^.?!\n])*?[, \t](?:I(?:['\u2019]ll| will| can| could)|tell me)\b",
    r"\bif you want\b[^.?!\n]*?,\s*say\b",
    r"\bif you want\s*,",
    r"say so if",
    r"(?<!nothing )(?<!nothing was )(?<!nothing is )\bleft for you\b",
    r"I can (?:do|run) .* if you",
    r"do you want me to",
    r"^[\s*\-#]*(?:and\s+)?want me to",
    r"\bshall I\b",
    r"should I (?:push|merge|open|proceed|go ahead|start|run|commit|try|add|test|check|edit|update)",
    r"\bI (?:haven['\u2019]t|have not) (?:tested|checked(?! in\b)|run(?! into\b)|verified|confirmed)(?![^.?!\n]*\b(?:because|since|needs?|requires?)\b[^.?!\n]*\b(?:credentials?|secrets?|tokens?|passwords?|api keys?|production|prod|costs?|billing|paid|human|approval|your (?:call|decision))\b)",
    r"would you like me to",
    r"let me know if",
    r"\bwhich (?:one )?do you want\b",
]
HEDGE_RE = re.compile("|".join(f"(?:{p})" for p in HEDGES), re.IGNORECASE)
OFFER_RE = re.compile(r"^[\s*\-#]*(?:and\s+)?(?:want me to|should I|do you want me to|shall I|would you like me to)\b", re.IGNORECASE)
HARNESS_PROMPT_START = "Another Claude session sent a message"
HARNESS_PROMPT_TAG = "<task-notification>"
TRAILER_PREFIXES = ("Principles applied:", "Playbooks read:")
PENDING_DELEGATE_RE = re.compile(
    r"^(?:[\w-]+\s+){0,3}(?:delegates?|subagents?|agents?)\s+(?:is|are)\s+(?:(?:now|still|currently|also|both|all)\s+)?\w+ing\b",
    re.IGNORECASE,
)
REPORT_BACK_RE = re.compile(r"\bI(?:['\u2019]ll| will) (?:then )?(?:report|send|show|compare|confirm|share|give|ask)\b", re.IGNORECASE)
WORK_CLAIM_RE = re.compile(
    r"\b(?:fixed|found|edited|added|removed|ran|passed|failed|changed|created|deleted|merged|pushed|committed)\b",
    re.IGNORECASE,
)
CHANGE_CLAIM_RE = re.compile(
    r"\b(?:pushed|committed|implemented|drafted)\b|(?<!is )(?<!was )(?<!are )\b(?:fixed|added|updated|removed|wrote|created|edited|renamed|merged)\b|\bopened (?:an? |the )?PR\b|\bopen as (?:\w+ )?PR\b|\bPR\b.{0,24}\bis open\b|\bcommits? `[0-9a-f]{7,40}`|\bPR #\d+ now has\b",
    re.IGNORECASE,
)
CLAUDE_THETA_MARKER = "<command-name>/theta-mode</command-name>"
DEFAULT_BLOCKING = frozenset({"hedge", "offer_question"})
BLOCK_REASON = (
    "Who is blocking you? Do the action or the check now, or name the one decision only the human can make. "
    "Ending with \"I haven't tested/checked/run/verified X\" or \"want me to X\" for reversible, in-scope work means do X before replying. "
    "Allowed: \"I haven't X\" only when you cannot do X (it needs credentials, a human decision, or cost or production access) and the reply names why. "
    "Allowed: \"Decision for you: ...\" for a materially different scope or an irreversible action, with the options, pros and cons, and your pick. "
    "In theta mode, end with a `Principles applied:` line."
)
SNIPPET_MAX = 160
READ_RETRIES = 3
RETRY_DELAY = 0.3


def parse_entries(raw: str) -> list[dict]:
    entries = []
    for line in raw.splitlines():
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if isinstance(entry, dict):
            entries.append(entry)
    return entries


def claude_text(entry: dict) -> str:
    message = entry.get("message")
    if entry.get("type") != "assistant" or entry.get("isSidechain") or not isinstance(message, dict):
        return ""
    content = message.get("content")
    if isinstance(content, str):
        return content.strip()
    if not isinstance(content, list):
        return ""
    parts = [b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"]
    return "\n".join(parts).strip()


def copilot_text(entry: dict) -> str:
    data = entry.get("data")
    if entry.get("type") != "assistant.message" or not isinstance(data, dict):
        return ""
    content = data.get("content")
    return content.strip() if isinstance(content, str) else ""


def detect_tool(entries: list[dict]) -> str:
    for entry in entries:
        kind = entry.get("type")
        if isinstance(kind, str) and "." in kind:
            return "copilot"
        if kind in ("assistant", "user", "system") and "message" in entry:
            return "claude"
    return "unknown"


def harness_event(text: str) -> bool:
    stripped = text.strip()
    reminder_only = stripped.startswith("<system-reminder>") and stripped.endswith("</system-reminder>")
    return stripped.startswith((HARNESS_PROMPT_START, HARNESS_PROMPT_TAG)) or reminder_only


def claude_prompt(entry: dict) -> str | None:
    text = claude_user_text(entry)
    return None if text is None or entry.get("isMeta") or harness_event(text) else text


def claude_user_text(entry: dict) -> str | None:
    message = entry.get("message")
    if entry.get("type") != "user" or entry.get("isSidechain") or not isinstance(message, dict):
        return None
    content = message.get("content")
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return None
    blocks = [b for b in content if isinstance(b, dict)]
    if any(b.get("type") == "tool_result" for b in blocks):
        return None
    return "\n".join(str(b.get("text", "")) for b in blocks if b.get("type") == "text")


def copilot_prompt(entry: dict) -> str | None:
    data = entry.get("data")
    if entry.get("type") != "user.message" or not isinstance(data, dict):
        return None
    content = data.get("content")
    return content if isinstance(content, str) else None


def last_reply(entries: list[dict], tool: str) -> str:
    extract, prompt = (copilot_text, copilot_prompt) if tool == "copilot" else (claude_text, claude_prompt)
    for entry in reversed(entries):
        if prompt(entry) is not None:
            return ""
        text = extract(entry)
        if text:
            return text
    return ""


def claude_tool_call(entry: dict) -> bool:
    message = entry.get("message")
    if entry.get("type") != "assistant" or entry.get("isSidechain") or not isinstance(message, dict):
        return False
    content = message.get("content")
    return isinstance(content, list) and any(isinstance(b, dict) and b.get("type") == "tool_use" for b in content)


def copilot_tool_call(entry: dict) -> bool:
    data = entry.get("data")
    return entry.get("type") == "assistant.message" and isinstance(data, dict) and bool(data.get("toolRequests"))


def turn_used_tools(entries: list[dict], tool: str) -> bool:
    called, prompt = (copilot_tool_call, copilot_prompt) if tool == "copilot" else (claude_tool_call, claude_prompt)
    for entry in reversed(entries):
        if prompt(entry) is not None:
            return False
        if called(entry):
            return True
    return False


def is_theta_claude(entries: list[dict]) -> bool:
    return any(CLAUDE_THETA_MARKER in (claude_prompt(e) or "") for e in entries)


def is_theta_copilot(entries: list[dict]) -> bool:
    return any((copilot_prompt(e) or "").strip().startswith("/theta-mode") for e in entries)


def check_hedges(reply: str) -> list[tuple[str, str, str]]:
    lines = []
    inside = []
    fenced = False
    for ln in reply.splitlines():
        if ln.lstrip().startswith(("```", "~~~")):
            fenced = not fenced
            inside = []
        elif ln.strip():
            (inside if fenced else lines).append(ln)
    if fenced:
        lines += inside
    while lines and lines[-1].strip().startswith(TRAILER_PREFIXES):
        lines.pop()
    hits = []
    for line in lines[-2:]:
        match = HEDGE_RE.search(line)
        if match:
            hits.append(("hedge", match.group(0), line.strip()))
    return hits


def last_paragraph(reply: str) -> list[str]:
    paragraphs: list[list[str]] = [[]]
    fenced = False
    for ln in reply.splitlines():
        if ln.lstrip().startswith(("```", "~~~")):
            fenced = not fenced
            paragraphs.append([])
        elif fenced:
            continue
        elif not ln.strip():
            paragraphs.append([])
        elif not ln.strip().startswith(TRAILER_PREFIXES):
            paragraphs[-1].append(ln.strip())
    return next((p for p in reversed(paragraphs) if p), [])


def check_offer_question(reply: str) -> list[tuple[str, str, str]]:
    hits = []
    for line in last_paragraph(reply):
        if line.startswith((">", '"', "“")):
            continue
        for sentence in re.split(r"(?<=[.!?])\s+", line):
            match = OFFER_RE.match(sentence)
            if match and sentence.rstrip("*_\"')").endswith("?"):
                hits.append(("offer_question", match.group(0), sentence))
    return hits


def announces_pending_delegate(lines: list[str]) -> bool:
    first_line = re.split(r"(?<=[.!?])\s+", lines[0].strip())
    last = re.split(r"(?<=[.!?])\s+", lines[-1].strip())[-1].lstrip("*- ")
    if any(WORK_CLAIM_RE.search(ln) for ln in lines):
        return False
    answers_first = re.match(r"(?:yes|no)\b", first_line[0], re.IGNORECASE)
    return bool(not answers_first and any(PENDING_DELEGATE_RE.match(sentence) for sentence in first_line) and REPORT_BACK_RE.search(last))


def check_principles(reply: str, owed: bool) -> list[tuple[str, str, str]]:
    lines = [ln for ln in reply.splitlines() if ln.strip()]
    if not owed or len(lines) <= 3:
        return []
    if any(ln.lstrip().startswith("Principles applied:") for ln in lines):
        return []
    if announces_pending_delegate(lines) or not CHANGE_CLAIM_RE.search(lines[0]):
        return []
    return [("missing_principles_line", "Principles applied:", lines[-1].strip())]


def log_path() -> Path:
    override = os.environ.get("REPLY_HYGIENE_LOG")
    if override:
        return Path(override)
    return Path.home() / ".agents" / "hooks" / "logs" / "reply_hygiene.jsonl"


def blocking_checks() -> frozenset[str] | None:
    mode = os.environ.get("REPLY_HYGIENE_MODE", "").strip().lower()
    if mode == "log":
        return frozenset()
    if mode == "block":
        return None
    listed = os.environ.get("REPLY_HYGIENE_BLOCK")
    if listed is None:
        return DEFAULT_BLOCKING
    return frozenset(name.strip() for name in listed.split(",") if name.strip())


def append_log(
    tool: str,
    session: str,
    check: str,
    phrase: str,
    line: str,
    payload_keys: list[str] | None = None,
    blocked: bool = False,
    first_line: str | None = None,
) -> None:
    record = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "tool": tool,
        "session": session,
        "check": check,
        "phrase": phrase,
        "snippet": line[:SNIPPET_MAX],
        "blocked": blocked,
    }
    if first_line is not None:
        record["first_line"] = first_line[:SNIPPET_MAX]
    if payload_keys is not None:
        record["payload_keys"] = payload_keys
    path = log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def transcript_file(payload: dict, session: str) -> Path | None:
    raw = payload.get("transcript_path") or payload.get("transcriptPath")
    if raw:
        return Path(raw)
    if session:
        return Path.home() / ".copilot" / "session-state" / session / "events.jsonl"
    return None


def payload_reply(payload: dict) -> str:
    for key in ("last_assistant_message", "lastAssistantMessage"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def read_reply(path: Path, have_text: bool) -> tuple[list[dict], str, str]:
    retries = 0 if have_text else READ_RETRIES
    while True:
        entries = parse_entries(path.read_text(encoding="utf-8", errors="replace"))
        tool = detect_tool(entries)
        reply = last_reply(entries, tool)
        if reply or retries == 0:
            return entries, tool, reply
        retries -= 1
        time.sleep(RETRY_DELAY)


def run(payload: dict, blocking: frozenset[str] | None) -> str | None:
    if payload.get("stop_hook_active") or payload.get("stopHookActive"):
        return None
    session = str(payload.get("session_id") or payload.get("sessionId") or "")
    guess = "copilot" if "sessionId" in payload or "transcriptPath" in payload else "claude"
    keys = sorted(payload)
    path = transcript_file(payload, session)
    given = payload_reply(payload)
    entries: list[dict] = []
    tool = "unknown"
    reply = ""
    try:
        if path is None:
            raise OSError("no transcript path")
        entries, tool, reply = read_reply(path, bool(given))
    except OSError as exc:
        if not given:
            append_log(guess, session, "transcript_unreadable", type(exc).__name__, str(path), keys)
            return None
    reply = given or reply
    if not reply:
        append_log(tool if tool != "unknown" else guess, session, "no_reply_found", tool, str(path), keys)
        return None
    if tool == "unknown":
        tool = guess
    theta = is_theta_copilot(entries) if tool == "copilot" else is_theta_claude(entries)
    owed = theta and turn_used_tools(entries, tool)
    hedges = check_hedges(reply)
    hits = hedges + ([] if hedges else check_offer_question(reply)) + check_principles(reply, owed)
    first_line = next((ln.strip() for ln in reply.splitlines() if ln.strip()), "")
    blocked = [blocking is None or check in blocking for check, _, _ in hits]
    for (check, phrase, line), hit_blocks in zip(hits, blocked):
        extra = {"first_line": first_line} if check == "missing_principles_line" else {}
        append_log(tool, session, check, phrase, line, blocked=hit_blocks, **extra)
    if any(blocked):
        return json.dumps({"decision": "block", "reason": BLOCK_REASON})
    return None


def main() -> None:
    try:
        payload = json.loads(sys.stdin.buffer.read().decode("utf-8", "replace") or "{}")
        out = run(payload if isinstance(payload, dict) else {}, blocking_checks())
        if out:
            print(out)
    except Exception:
        pass
    sys.exit(0)


if __name__ == "__main__":
    main()
