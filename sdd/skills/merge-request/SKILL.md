---
name: merge-request
description: Draft the title and description of a merge (pull) request for the active spec from the spec and real test output. Drafts only; opens it only when the user asks. Use when the change is ready for review.
---

# Merge request

1. Run `pre-merge-check`. Stop on any FAIL.
2. Title: a Conventional Commit naming the story (none for a hotfix). Target: the
   integration branch in AGENTS.md.
3. Description, with these headings:
   - **Story** — the story key and title, links to its package `specs/<story>-<slug>/` and the story on the board. Use "Closes #N" only in
     the last request of a split spec; otherwise "Part of #N".
   - **Changes** — what and why; call out migrations, new configuration, contract changes, new dependencies and deploy steps.
   - **Tests** — what ran (real output from this branch) and what was exercised in the running app. If a
     suite did not run, say so; never a number a run did not produce.
   - **Security gate** — profile, computed state, reviews done, open and accepted risks with expiry.
   - **Documentation** — what was updated.
   - **For the reviewer** — where to start, what is deliberately unfinished.
4. Show the draft. Push the feature branch and open the request only when the user asks, with the
   repository platform's CLI or web UI. Never push to a protected branch or force-push.
5. Add the link to the spec's evidence (`spec-update`).
