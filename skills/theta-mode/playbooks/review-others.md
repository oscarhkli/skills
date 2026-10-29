# Review playbook

Use it when drafting review comments on someone else's document or code for the human to approve. The author may not be using theta-mode.

## Drafting findings

Give each finding in these parts, in plain words:

- **Code:** what the diff shows, with `path:line`. Use **Missing:** instead when the finding is about something absent. Never phrase it as the author's words.
- **Where:** product code, test or style.
- **Covers:** for a test finding, the production change the test protects, with `path:line`.
- **Ask:** the change and why, citing a precedent on the latest remote default branch, by commit SHA when the remote is readable, or stating that none was found.
- **Comment:** the exact text to post.

Severity follows the playbook or reviewer skill in use. Present nitpick-level findings last; the human decides which to post.

An absolute word such as all, every, never or none needs the count it rests on.

Give each open decision for the human the same **Code** and **Ask** parts, with `path:line` and the quoted source.

The human must be able to judge each finding without opening the file.

## Re-review

When the author updates after your review, mark each of your earlier threads addressed, partly addressed (say what is left) or not addressed. Whether the author's choice on the rest is acceptable is the human's call. Resolve the addressed threads, then draft only new findings.
