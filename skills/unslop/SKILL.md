---
name: unslop
description: Remove AI tells and narration from any writing so only the substance remains.
---

# Unslop

Human wants the current state and the decision, not the discussion, review rounds, or agent iterations behind it. Edit existing text to remove AI patterns. Preserve meaning and facts.

## Scope

Apply to text meant for other people, including your own replies and drafts, and to markdown inside the user's own repo.

Leave untouched: code, quoted text, logs, data values, and content from external sources.

Code comments: apply the style patterns only. Never delete or judge a comment (`no-comments` owns that).

## Rules

- Remove each hit. Keep the meaning, facts, and decisions.
- Keep rationale only when a reader would otherwise reverse the decision, as one short clause.
- When updating a doc to a new decision, rewrite the affected lines in place. No "changed from" or "previously" notes, no changelog.
- In a file, edit in place and check the diff. If untracked, copy it first.
- Keep two things that look like narration but are not: verification results (tests added, tests run), and real shipped behaviour a reader must migrate from.

## Remove

- Decision history: who said what, review threads, how a decision was reached.
  - Before: "After discussing with the reviewer, we agreed to move validation into the service layer instead of the controller."
  - After: "Validation lives in the service layer."
- "Previously", "no longer", "removed": write as if the rejected thing never existed.
  - Before: "The adapter interface was removed; the parser is now called directly."
  - After: "The service calls the parser directly."
- Round and revision logs: review rounds, attempts, "updated per feedback", "Revision 2", "fixed in this pass", "I investigated X, then found Y".
  - Before: "In the second review round a missing null check was found, which has now been added."
  - After: "Return early when `user` is null."
- Restating the obvious notes that repeat the heading or name: "This section describes the caching design".
- Hedging, padding, unrequested advice.
  - Before: "It may be worth considering that, if the team is receptive, they could update the document to reflect that the cache also applies here, by default for 20 minutes, configurable from 0 to 60."
  - After: "The cache applies here too."
- Em dashes: avoid them entirely, because readers take them as an AI tell. Reword around the dash with full stops or commas. Do not swap the character.
- Chatbot phrases: "I hope this helps!", "Let me know if...", "Of course!", "Certainly!".
- Sycophancy: "Great question! You're absolutely right!"
- Filler phrases: "In order to" becomes "To". "Due to the fact that" becomes "Because". "It is important to note that" gets deleted.
- Recap endings: "In summary...", "Overall, this ensures...".
- Stacking ideas in threes, or bullets where a sentence would do.
- Inflated vocabulary: "leverage", "robust", "seamless", "delve", "crucial".
- Coined labels: short codes invented during the work (J2, PR0, O6, A3, PMB) that the reader never saw defined.
  - Before: "Option 1: short J2 now, long J2 in PR3."
  - After: "Option 1: the VS CPU sudden-death test plays one CPU turn now; the multi-round version arrives in PR3."
- Long sentences in a single line: 300 words with 10 sentences in a single line.
- Feelings without evidence: "I feel this is the best approach".

## Write instead

- Lead with the conclusion in one sentence.
- One idea per sentence. Break an enumeration into nested bullets.
- Use numbers, facts, pros/cons and trade-offs.

## Plain English (prefer, not enforced)

- Use the common word. Aim for the roughly 1,500 most common English words, plus the terms of the topic.
- Define each topic term in one short clause the first time you use it.
- Use the active voice and short sentences. One idea per sentence.
- Put the condition first: "After the build passes, merge." not "Merge after the build passes."
- Say what a thing does before what it is called.
