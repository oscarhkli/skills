---
name: interview
description: Settle the premises before producing something substantial, by verifying from source what can be verified and asking the human only what cannot. Keeps findings and answers in a notes directory so a new session can resume. Run as /interview before drafting a design, plan, migration or refactor proposal.
disable-model-invocation: true
---

# Interview

A wrong premise spreads into every downstream document, task and review, and unwinding it costs more than checking. Settle the premises before drafting.

Find what is recorded (code, docs, history, threads); ask only what a person decides (intent, priority, scope, product calls, the future). Split hybrids: "does this field allow nulls" is findable, "should it" is a decision.

## Steps

1. **Locate the notes directory.** The user may bring a one-line idea or point at a directory of earlier investigation. If they point at one, read all of it before listing unknowns. If not, ask where notes go.
2. **List the unknowns the work depends on.** An unknown earns a place only if a different answer changes what you produce.
3. **Find the findable ones first.** Reading the code dissolves some questions and surfaces sharper ones.
4. **Ask the rest in rounds.** Each round:
   - **Pick at most three questions**, the ones whose answers most change what comes next. Hold the rest, since answers often change or remove them. Raise the limit only if the user asks.
   - **Attach your best answer to each**, with the evidence and what changes under each reply. A pointer request ("where is the schema?") counts as a question and carries a guess, such as the likely path.
   - **Send it as one ask-tool form**: a field per question, your answer as the default, the evidence in the description, and a message that restates the context so it reads alone. Without an ask tool, use a numbered list.
   - **Then verify what the answers raise** and run the next round, until step 7.
5. **Record each answer verbatim.** Quote the user's words and where they said them. Paraphrase drifts and cannot be checked later. When sources conflict, a direct answer from the decision owner beats a document, and a document beats a mockup. State which rule you used.
6. **Triage what stays open.** If the work ships either way, park it and mark it owed. Otherwise it blocks: settle it now.
7. **Stop when you can state the premises back and the user agrees.** The notes directory then holds them.

## Notes directory

The notes directory holds everything a new session needs to continue the initiative. The user starts a fresh session when this one grows too large and points it at the directory, so it must be complete without this conversation.

Update it in the same turn as every finding and every user instruction. Do not batch updates to the end. A fact that exists only in the conversation is lost.

Contents:

- **Verified facts**, each with its source (file and symbol, command, link) and the date checked. Not line numbers: they rot on the next commit.
- **User instructions and answers**, verbatim, with where they were said.
- **Decisions**, and the authority rule that settled any conflict.
- **Open items**, each marked blocking or parked.
- **Next step.**

Keep an `index.md` that links every file and states the goal in a sentence, so a new session reads one file first. Edit entries in place to the current state. Keep no old values or "changed from" notes, even in parentheses. The checked date is enough.

Location follows the project. Some repos keep notes in the tree, some owners keep them outside it. Use the directory the user names. If they name none, ask once, then stay consistent. Do not add files to a repo that has not asked for them.

## When the human pushes back

Treat a challenge as evidence of a defect. Re-derive the claim from the source. If it does not hold, say so in one line and correct it. If it does, show the evidence instead of restating the conclusion more firmly. Adding caveats or turning an uncertainty into a blocker usually means you are protecting an earlier overstatement.

## Facts go stale

Re-check cheap facts carried from another session or document before relying on them. When reading discussion threads, fetch replies as well as top-level comments, since a missed reply looks like an unanswered question.

When a decision replaces an earlier one, search the notes directory for the old value and rewrite every hit in the same turn. A note that the source or a later note contradicts is a defect: fix it in place when you find it, not only report it.

## Example

Task: plan a change so a setting can differ per tenant.

- **Findable, so checked first:** the setting is read in two places and currently holds one global value.
- **A decision, so asked:** "What should a tenant without an override get? I suggest the global value, since it needs no migration."
- **Left open, parked:** whether to hide or delete the old setting. A product call, and the work ships either way.
