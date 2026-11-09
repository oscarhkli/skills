#!/usr/bin/env python3
"""Stop hook for Claude Code and Copilot CLI: flag hedged or unfinished final replies.

REPLY_HYGIENE_MODE=log (default) only appends to a JSONL log; block asks the agent to redo the reply.
REPLY_HYGIENE_LOG overrides the log path.
The payload's last_assistant_message is preferred over the transcript, which can lag the Stop event.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HEDGES = [
    r"if you want",
    r"say so if",
    r"your call",
    r"left for you",
    r"I haven['’]t (?:confirmed|checked|verified)",
    r"\bunverified\b",
    r"not verified",
    r"I can (?:do|run) .* if you",
    r"do you want me to",
    r"want me to",
    r"shall I",
    r"should I (?:push|merge|open|proceed|go ahead|start|run|commit)",
    r"would you like me to",
    r"let me know if",
]
HEDGE_RE = re.compile("|".join(f"(?:{p})" for p in HEDGES), re.IGNORECASE)
TRAILER_PREFIXES = ("Principles applied:", "Playbooks read:")
CLAUDE_THETA_MARKER = "<command-name>/theta-mode</command-name>"
BLOCK_REASON = (
    "Do the action or the check now. If it is a real decision for the human, "
    "state the decision, the options with pros and cons, and your pick. "
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


def claude_prompt(entry: dict) -> str | None:
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


def is_theta_claude(entries: list[dict]) -> bool:
    return any(CLAUDE_THETA_MARKER in (claude_prompt(e) or "") for e in entries)


def is_theta_copilot(entries: list[dict]) -> bool:
    return any((copilot_prompt(e) or "").strip().startswith("/theta-mode") for e in entries)


def check_hedges(reply: str) -> list[tuple[str, str, str]]:
    lines = [ln for ln in reply.splitlines() if ln.strip()]
    while lines and lines[-1].strip().startswith(TRAILER_PREFIXES):
        lines.pop()
    hits = []
    for line in lines[-2:]:
        match = HEDGE_RE.search(line)
        if match:
            hits.append(("hedge", match.group(0), line.strip()))
    return hits


def check_principles(reply: str, theta: bool) -> list[tuple[str, str, str]]:
    lines = [ln for ln in reply.splitlines() if ln.strip()]
    if not theta or len(lines) <= 3:
        return []
    if any(ln.lstrip().startswith("Principles applied:") for ln in lines):
        return []
    return [("missing_principles_line", "Principles applied:", lines[-1].strip())]


def log_path() -> Path:
    override = os.environ.get("REPLY_HYGIENE_LOG")
    if override:
        return Path(override)
    return Path.home() / ".agents" / "hooks" / "logs" / "reply_hygiene.jsonl"


def append_log(tool: str, session: str, check: str, phrase: str, line: str, payload_keys: list[str] | None = None) -> None:
    record = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "tool": tool,
        "session": session,
        "check": check,
        "phrase": phrase,
        "snippet": line[:SNIPPET_MAX],
    }
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


def run(payload: dict, mode: str) -> str | None:
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
    hits = check_hedges(reply) + check_principles(reply, theta)
    for check, phrase, line in hits:
        append_log(tool, session, check, phrase, line)
    if hits and mode == "block":
        return json.dumps({"decision": "block", "reason": BLOCK_REASON})
    return None


def main() -> None:
    try:
        payload = json.loads(sys.stdin.buffer.read().decode("utf-8", "replace") or "{}")
        mode = os.environ.get("REPLY_HYGIENE_MODE", "log").strip().lower()
        out = run(payload if isinstance(payload, dict) else {}, mode)
        if out:
            print(out)
    except Exception:
        pass
    sys.exit(0)


if __name__ == "__main__":
    main()
