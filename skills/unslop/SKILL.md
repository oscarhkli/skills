---
name: unslop
description: Remove AI tells and narration from writing so only the substance remains. Use whenever drafting, editing, or reviewing text another person will read, including PR review comments and replies, PR titles and descriptions, commit messages, issues, emails, messages, design docs, specs, any markdown in the repo, and chat replies. Also use when the user says "too long", "no narrative", "sounds like AI", "tighten", "just the conclusion", or "write it as if X never existed", or when updating a doc to reflect a changed decision.
---

# Unslop

Readers want the current state and the decision, not the discussion, review rounds, or agent iterations behind it. They also stop trusting text that reads like a chatbot. Edit existing text, or write new text, so only the substance remains.

## Scope

Apply to text meant for other people and to markdown inside the user's own repo.

Leave untouched: code, identifiers, file names, quoted text, logs, data values, and content from external sources.

Code comments get the style patterns only (em dashes, chatbot phrases, and the like). Never delete or judge a comment. Keeping or killing comments belongs to `no-comments`.

## Workflow

1. Scan against the patterns below.
2. Remove or rephrase each hit. Keep the meaning, facts, and decisions.
3. Keep rationale only when a reader would otherwise reverse the decision. Write it as one short clause, not a story.
4. When updating a doc to a new decision, rewrite the affected lines in place. Do not add "changed from" or "previously" notes.
5. For text in a file, edit the file in place. For pasted text, return the edited text. Do not add a changelog of what you removed.
6. For chat replies and fresh drafts, apply the patterns while writing. The editing method below is for files only.

Keep two things that look like narration but are not: verification results (tests added, tests run), and real shipped behaviour a reader must migrate from.

## Editing method (files)

- Edit in place with the `edit` tool, one change per call. Do not script find/replace across files.
- Check the diff afterwards. Every difference must be one you intended.
- If the file is not under version control, copy it first and diff against the copy.

## Patterns: narration

### 1. Discussion and decision history

Mentions of who said what, review threads, or how a decision was reached.

- Before: "After discussing with the reviewer, we agreed to move validation into the service layer instead of the controller."
- After: "Validation lives in the service layer."

### 2. "Previously / no longer / removed" framing

Describing the current design relative to a draft, rejected option, or older revision. Write as if the rejected thing never existed.

- Before: "The adapter interface was removed; the parser is now called directly."
- After: "The service calls the parser directly."

### 3. Iteration, round, and revision logs

Agent-process residue: review rounds, attempts, "updated per feedback", "Revision 2", "fixed in this pass", "I investigated X, then found Y".

- Before: "In the second review round a missing null check was found, which has now been added."
- After: "Return early when `user` is null."

### 4. Restating the obvious

Notes that repeat what the heading or name already says.

- Before: "This section describes the caching design."
- After: delete.

### 5. Hedging, padding, and unrequested advice

Long preambles, "it is worth noting", stacked caveats, alternatives nobody asked for, or telling the reader how to do their job. Lead with the conclusion, in one sentence.

- Before: "It may be worth considering that, if the team is receptive, they could update the document to reflect that the cache also applies here, by default for 20 minutes, configurable from 0 to 60."
- After: "The cache applies here too."

## Patterns: style

- **Em dashes.** Avoid them entirely, because readers take them as an AI tell. Reword the sentence around the dash with full stops or commas. Do not swap the character mechanically.
- **Chatbot phrases.** "I hope this helps!", "Let me know if...", "Of course!", "Certainly!". Remove.
- **Sycophancy.** "Great question! You're absolutely right!" Respond directly.
- **Filler phrases.** "In order to" becomes "To". "Due to the fact that" becomes "Because". "It is important to note that" gets deleted.
- **"Not just X, but Y".** "It's not just a fix, it's a redesign." State the point once.
- **Recap endings.** "In summary...", "Overall, this ensures...". The body already said it. Cut the closer.
- **Stacked threes and bullet-everything.** Reflexive lists of three adjectives or points, and bullets where a sentence would do. Keep only items that carry information.
- **Inflated vocabulary.** "leverage", "robust", "seamless", "delve", "crucial". Use the plain word.
