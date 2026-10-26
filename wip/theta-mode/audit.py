#!/usr/bin/env python3
"""Audit a theta-mode session transcript for dropped rules.

Usage: audit.py <transcript.jsonl | Copilot session dir>
Reads a Copilot CLI events.jsonl, or a Claude Code session .jsonl plus its subagents/.
Prints one finding per line and exits 1 when there are any.
"""
import json
import re
import sys
from pathlib import Path

EDIT_TOOLS = {"edit", "create", "Edit", "Write", "MultiEdit", "NotebookEdit"}
SPAWN_TOOLS = {"task", "Task", "Agent"}
CLAUDE_DENY = "The user doesn't want to proceed"
THETA_MODE = "theta-mode/skill.md"


def norm(path):
    return (path or "").replace("\\", "/").lower()


def ev(agent, line, kind, **data):
    return {"agent": agent, "line": line, "kind": kind, **data}


def tool_event(agent, line, name, path, args):
    if name in ("view", "Read"):
        yield ev(agent, line, "read", path=path)
    elif name in EDIT_TOOLS:
        yield ev(agent, line, "edit", path=path)
    elif name in SPAWN_TOOLS:
        kind = args.get("agent_type") or args.get("subagent_type")
        yield ev(agent, line, "spawn", type=kind, prompt=args.get("prompt", ""))


def copilot_events(path):
    calls = {}
    for line, raw in enumerate(path.open(encoding="utf-8"), 1):
        e = json.loads(raw)
        t, d, agent = e.get("type"), e.get("data") or {}, e.get("agentId") or "main"
        if t == "user.message" and agent == "main":
            yield ev(agent, line, "human", text=str(d.get("content", "")))
        elif t == "assistant.message" and d.get("content"):
            yield ev(agent, line, "reply", text=d["content"])
        elif t == "session.compaction_complete" and d.get("success"):
            yield ev(agent, line, "compact")
        elif t == "permission.completed":
            result = d.get("result") or {}
            if result.get("kind", "").startswith("denied") and result.get("feedback"):
                yield ev(agent, line, "deny", feedback=result["feedback"])
        elif t == "tool.execution_start":
            name, args = d.get("toolName"), d.get("arguments") or {}
            if not isinstance(args, dict):
                args = {}
            calls[d.get("toolCallId")] = (name, args)
            yield from tool_event(agent, line, name, args.get("path"), args)
        elif t == "tool.execution_complete":
            name, args = calls.get(d.get("toolCallId"), (None, {}))
            content = str((d.get("result") or {}).get("content", ""))
            if name == "glob" and content.startswith("No files matched"):
                paths = args.get("paths") or ""
                yield ev(agent, line, "glob_empty", path=", ".join(paths) if isinstance(paths, list) else str(paths))


def claude_file_events(path, agent):
    calls = {}
    for line, raw in enumerate(path.open(encoding="utf-8"), 1):
        e = json.loads(raw)
        ref = line if agent == "main" else f"{path.name}:{line}"
        if e.get("isCompactSummary") or e.get("subtype") == "compact_boundary":
            yield ev(agent, ref, "compact")
            continue
        msg = e.get("message")
        if not isinstance(msg, dict):
            continue
        content = msg.get("content")
        blocks = content if isinstance(content, list) else []
        if e.get("type") == "user":
            human = agent == "main" and not e.get("isMeta")
            texts = [content] if isinstance(content, str) else [b.get("text", "") for b in blocks if b.get("type") == "text"]
            if human and texts:
                yield ev(agent, ref, "human", text="\n".join(texts))
            for b in blocks:
                if b.get("type") != "tool_result":
                    continue
                text = json.dumps(b.get("content"))
                if CLAUDE_DENY in text and "the user said:" in text:
                    yield ev(agent, ref, "deny", feedback=text.split("the user said:", 1)[1])
                name, args = calls.get(b.get("tool_use_id"), (None, {}))
                if name == "Glob" and "No files found" in text:
                    yield ev(agent, ref, "glob_empty", path=str(args.get("path") or args.get("pattern")))
        elif e.get("type") == "assistant":
            for b in blocks:
                if b.get("type") == "text":
                    yield ev(agent, ref, "reply", text=b["text"])
                elif b.get("type") == "tool_use":
                    args = b.get("input") or {}
                    calls[b.get("id")] = (b.get("name"), args)
                    yield from tool_event(agent, ref, b.get("name"), args.get("file_path"), args)


def claude_events(path):
    yield from claude_file_events(path, "main")
    for sub in sorted((path.parent / path.stem / "subagents").glob("*.jsonl")):
        yield from claude_file_events(sub, sub.stem)


def load(arg):
    path = Path(arg).expanduser()
    if path.is_dir():
        path = path / "events.jsonl"
    return list(copilot_events(path) if path.name == "events.jsonl" else claude_events(path))


def cited(text, label, pattern):
    match = re.search(label + r":(.*)", text)
    return re.findall(pattern, match[1]) if match else []


def audit(events):
    findings = []
    read, stale, denied, reported = {}, {}, {}, set()
    turn = {"seq": 0, "line": None, "edits": set(), "spawned": False}

    def close_turn():
        if len(turn["edits"]) >= 3 and not turn["spawned"]:
            findings.append((turn["seq"], f"L{turn['line']} [main] edited {len(turn['edits'])} files in one turn without theta-agent"))

    for seq, e in enumerate(events):
        agent, kind, line = e["agent"], e["kind"], e["line"]
        if kind == "human":
            close_turn()
            turn = {"seq": seq, "line": line, "edits": set(), "spawned": False}
            denied.clear()
        elif kind == "compact":
            read[agent] = set()
            stale[agent] = line
            reported = {r for r in reported if r[0] != agent}
        elif kind == "read":
            path = norm(e["path"])
            read.setdefault(agent, set()).add(path)
            if path.endswith(THETA_MODE):
                stale.pop(agent, None)
        elif kind == "edit":
            if agent == "main":
                turn["edits"].add(norm(e["path"]))
            if agent in stale:
                findings.append((seq, f"L{line} [{agent}] edited after compaction at L{stale.pop(agent)} without reading theta-mode SKILL.md again"))
        elif kind == "spawn" and e["type"] == "theta-agent":
            turn["spawned"] = True
            if "theta-mode" not in e["prompt"] or "SKILL.md" not in e["prompt"]:
                findings.append((seq, f"L{line} [{agent}] theta-agent brief lacks the theta-mode SKILL.md path"))
        elif kind == "glob_empty" and "/.agents" in norm(e["path"]):
            findings.append((seq, f"L{line} [{agent}] glob found nothing under {e['path']}; glob skips linked directories"))
        elif kind == "deny":
            denied.setdefault(agent, []).append(line)
            if len(denied[agent]) == 2:
                findings.append((seq, f"L{line} [{agent}] denied with feedback again in one human turn (first at L{denied[agent][0]}): {e['feedback'][:80]!r}"))
        elif kind == "reply" and agent == "main":
            have = read.get(agent, set())
            cites = [(n, f"/{n}/skill.md", "cites") for n in cited(e["text"], "Principles applied", r"principle-[a-z0-9-]+")]
            cites += [(n, norm(n), "lists playbook") for n in cited(e["text"], "Playbooks read", r"[\w./-]+\.md")]
            for name, needle, verb in cites:
                if (agent, name) not in reported and not any(p.endswith(needle) for p in have):
                    reported.add((agent, name))
                    findings.append((seq, f"L{line} [main] {verb} {name} without reading it since the last compaction"))
    close_turn()
    return [msg for _, msg in sorted(findings)]


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    events = load(sys.argv[1])
    if not any(e["kind"] == "human" and re.search(r"(^|\s)/theta-mode\b", e["text"]) for e in events):
        print("no /theta-mode request from the human; nothing to audit")
        return
    findings = audit(events)
    print("\n".join(findings) or "no findings")
    sys.exit(1 if findings else 0)


if __name__ == "__main__":
    main()
