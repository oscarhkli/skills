#!/usr/bin/env python3
"""Print each human turn of one or more session transcripts as "#<n> L<line>: <text>".

Usage: human_turns.py [--full] <transcript.jsonl>...
--full prints each turn in full, preceded by the tail of the agent reply before it.
Handles Claude Code transcripts and Copilot CLI events.jsonl.
"""
import json
import sys

MAX_CHARS = 300
REPLY_TAIL_CHARS = 1500


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


def reply_of(event):
    if event.get("type") == "assistant.message":
        return event.get("data", {}).get("content", "")
    if event.get("type") != "assistant":
        return ""
    content = event.get("message", {}).get("content")
    if isinstance(content, list):
        content = "".join(part.get("text", "") for part in content if part.get("type") == "text")
    return (content or "").strip()


def print_turns(path, full):
    turn = 0
    last_reply = ""
    with open(path, encoding="utf-8") as f:
        for line_no, line in enumerate(f):
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            last_reply = reply_of(event) or last_reply
            text = text_of(event)
            if not text:
                continue
            turn += 1
            if full:
                print(f"--- agent before #{turn}:\n{last_reply[-REPLY_TAIL_CHARS:]}\n--- #{turn} L{line_no}:\n{text}\n")
            else:
                print(f"#{turn} L{line_no}: {text[:MAX_CHARS]!s}".replace("\n", " "))


def main(args):
    sys.stdout.reconfigure(encoding="utf-8")
    full = "--full" in args
    paths = [a for a in args if a != "--full"]
    for path in paths:
        if len(paths) > 1:
            print(f"=== {path}")
        print_turns(path, full)


if __name__ == "__main__":
    main(sys.argv[1:])
