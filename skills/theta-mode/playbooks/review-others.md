# Review playbook

Use it when drafting review comments on someone else's document or code for the human to approve. The author may not be using theta-mode.

## Drafting findings

Give each finding in these parts, in plain words:

- **Code:** what the diff shows, with `path:line`. Use **Missing:** instead when the finding is about something absent. Never phrase it as the author's words.
- **Where:** product code, test or style.
- **Covers:** for a test finding, the production change the test protects, with `path:line`.
- **Ask:** the change and why, citing a precedent on the latest remote default branch, by commit SHA when the remote is readable, or stating that none was found.
- **Basis:** the rule quoted with its file and heading, or "no rule"; how many siblings on the default branch do the same and how many differ, with one `path:line` each; and what a caller, test or user sees from the code as written. Drop a finding with no rule and no visible effect. For a test finding, also say why the test passes today.
- **Comment:** the exact text to post.

Severity follows the playbook or reviewer skill in use. Present nitpick-level findings last; the human decides which to post.

An absolute word such as all, every, never or none needs the count it rests on.

Give each open decision for the human the same **Code** and **Ask** parts, with `path:line` and the quoted source, and end it with your pick and the reply you expect, per `../references/human-brief.md`.

Open each finding and open decision with one or two plain lines: what this code does in the product, and what goes wrong without the change. Define each term of the area at first use. When the Ask cites a precedent, show its lines next to the PR's lines, so the reader can see the shapes match.

When a comment points at lines outside its anchor, give each as a link pinned to the head commit, with the method name.

Before the human sees any finding, a fresh verifier re-checks each one's Code, Basis and lines against the head commit. Correct the draft from its report. Show only verified findings, never a list of unchecked ones.

The human must be able to judge each finding without opening the file.

## Re-review

When the author updates after your review, mark each of your earlier threads addressed, partly addressed (say what is left) or not addressed. Whether the author's choice on the rest is acceptable is the human's call. Next to each finding's status in the review file, add its one-clause reason. Change a recommendation only on new evidence, and name that evidence in one line. Resolve the addressed threads, then draft only new findings.
