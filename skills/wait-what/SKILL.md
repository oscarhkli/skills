---
name: wait-what
description: Repair a confusing or wrong assistant reply after the user signals confusion. Use when the user types /wait-what, or says things like "wait, what?", "huh?", "what does that mean?", "where did that term come from?", "that contradicts what you said earlier", "that's not what the doc says", or "this is off-topic". Re-checks the last reply against the session and any cited files, then sends a clearer, corrected reply and logs what went wrong. Use it even when the user doesn't name the skill but is clearly lost or disputing the reply.
---

# Wait, What

The user is confused by your last reply. Treat that as evidence the reply has a defect, and find it before answering again. Apologies and defensive explanations only delay the answer.

## Steps

1. **Triage.** Re-read your last reply and the user's words. Decide which kind of problem it is. The user rarely says, so infer it.
   - **Factual defect**: the content may be wrong. Go to step 2.
     - *Invented term*: a name or concept that doesn't exist in the project, tool, or domain, or was never introduced.
     - *Contradiction*: conflicts with something said earlier in the session.
     - *Misquote*: differs from a file, doc, or output you cited.
   - **Clarity defect**: the content may be right but the user can't follow it. Skip to step 3 and don't re-open sources.
     - *Muddy*: a wall of text, buried point, or several ideas tangled together.
     - *Jargon or ambiguity*: undefined acronyms, vague pronouns, two possible readings.
     - *Off-topic*: doesn't answer what was asked.
     - *Slop*: filler, recap, hedging.
2. **Verify (factual only).** Check the claim against the earlier messages or re-open the cited source. Don't rely on memory. Decide which side is right. Report the correct fact plainly, for example "retry.md says 3 retries".
3. **Rewrite.** Send a corrected reply that keeps the same facts for a clarity defect and fixes them for a factual one. It:
   - starts with the answer and contains no apology, not even "sorry" or "my mistake";
   - uses terms the user already uses, or defines a new term in a few words;
   - says each point once, in plain words, with no filler;
   - drops anything off-topic.
4. **Log it.** Append one entry to `wait-what-log.jsonl` (see below), only when you found a real defect.
5. **If nothing is clearly wrong**, the reply was probably fine and the user wants more or different detail. Don't invent a flaw, don't log, and don't pad. Ask one short question about which part was unclear, or give one brief clarification of the most likely confusing word.

## De-slop

If an `/unslop` skill is installed, apply it to the rewrite. Otherwise apply these rules: cut filler and recap, remove hedges that add no information, prefer short sentences, one idea per paragraph, and concrete words over abstract ones.

## Log

Append to `wait-what-log.jsonl` in the session's state or files directory when the agent has one. Otherwise use the current working directory. Create the file if missing. Append one line holding one JSON object, with no line breaks inside it and double quotes in text escaped as `\"`:

```
{"ts":"<ISO date and time>","type":"<type>","offending":"<short exact quote>","fix":"<one line>","task":"<few words on what the session was doing>"}
```

`type` is one of: `invented term`, `contradiction`, `misquote`, `muddy`, `off-topic`, `ambiguity`, `slop`.

The log is for a later review, so keep entries short and quote the exact phrase.

## Example

User: "wait what, what's a 'sync gate'?"
Earlier reply: "Add a sync gate before the deploy step."
Check: no "sync gate" exists in the project's pipeline config.
Corrected reply: "I made that term up. I meant a manual approval step before deploy. In `pipeline.yml` that is the `approval:` key."
Log: Type: invented term; Offending text: "sync gate"; Fix: replaced with "manual approval step".
