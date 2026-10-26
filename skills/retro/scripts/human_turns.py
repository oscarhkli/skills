#!/usr/bin/env python3
"""Print each human turn of a session transcript as "#<n> L<line>: <text>".

Usage: human_turns.py <transcript.jsonl>
Handles Claude Code transcripts and Copilot CLI events.jsonl.
"""
import json
import sys

MAX_CHARS = 300


def text_of(event):
    if event.get("type") == "user.message":
        if "agentId" in event:
            return ""
        return event.get("data", {}).get("content", "")
    if event.get("type") != "user" or event.get("isMeta") or event.get("toolUseResult") is not None:
        return ""
    content = event.get("message", {}).get("content")
    if isinstance(content, list):
        content = " ".join(part.get("text", "") for part in content if part.get("type") == "text")
    content = (content or "").strip()
    if content.startswith("<") and "command-name" not in content[:60]:
        return ""
    return content


def main(path):
    sys.stdout.reconfigure(encoding="utf-8")
    turn = 0
    with open(path, encoding="utf-8") as f:
        for line_no, line in enumerate(f):
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            text = text_of(event)
            if text:
                turn += 1
                print(f"#{turn} L{line_no}: {text[:MAX_CHARS]!s}".replace("\n", " "))


if __name__ == "__main__":
    main(sys.argv[1])
