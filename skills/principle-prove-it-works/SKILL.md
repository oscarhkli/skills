---
name: principle-prove-it-works
description: Principle for finishing a task. Before declaring it done, prove it works by running the real thing, not by inference or a clean compile.
disable-model-invocation: true
---

# Prove It Works

A clean compile and a read-through of the diff prove nothing about behaviour. Check the real thing directly.

## Rules

- **Run it.** Run the changed code path and compare the result with what the task asked for. Run the relevant tests.
- **Prove the change.** For a behaviour change or defect fix, find a check that fails without the change and passes with it. Report the result in one line. Do not paste before and after output into the chat.
- **Cover the edges.** Verify each edge case. Do not list them in the chat.
- **Capture what users see.** For visible behaviour, save evidence to a file: logs, a screenshot or an end-to-end test result. Link the file, do not paste it.
- **Pick the lowest level.** Use the lowest level of the testing pyramid that proves the claim. Use end-to-end only when lower levels cannot show it, such as when wiring, UI or a cross-service flow is the risk. Judge this per change.
- **Try every route.** Never stop at the first check that fails. Try tests, a throwaway script, a local run or a query against a dev database, inside or outside the repo. If none works, name the check, why it failed and the alternatives you tried, then propose the next best proof. A check you could not run is not a check you skipped.
- **Check your own claims.** Before reporting, verify what you or a delegate said about coverage, precedent, behaviour or "done". Never cite what you did not check this session. Answer a human's question of fact after checking, not with an "I haven't checked" caveat.
- **Report what ran.** One line per check with its result.

## Scripted verification

Automate checks as tests that run the same way every time and catch regressions.

Keep them in the codebase as unit, integration or end-to-end tests. If a script cannot live there, put it in `~/.agents/project-brain/<project>/verification/` (`<project>` is the name that `~/.agents/project-brain/README.md` gives the project; if the README does not name it, the code repo's name; if there is no repo, a short meaningful name you choose) and tell the human its path.
