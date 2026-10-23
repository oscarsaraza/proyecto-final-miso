---
name: pre-merge-check
description: Pass or fail check before a commit, a push or a merge request. Reports and stops; never commits. Use before merge-request.
---

# Pre-merge check

Run each check and report PASS or FAIL with the evidence, then stop.

| Check | How |
|---|---|
| Branch and commits | Not protected; named as `sdd/rules/git.md` says; on a story branch every commit names the story |
| Spec | `python sdd/tools/sdd.py spec validate <package>`: no errors; tasks and evidence current |
| Gate | The computed state, never declared above it |
| Tests and linters | The project's commands (AGENTS.md) for what changed |
| Secrets | `python sdd/tools/sdd.py scan secrets --diff <base>`: nothing outside tests |
| Critical paths | `python sdd/tools/sdd.py scan paths --base <base>`: every critical file covered |
| Dependencies | `python sdd/tools/sdd.py scan deps --base <base> --require-evaluation` |
| Reviews | `code-reviewer` done; `security-reviewer` done when the profile is HIGH or CRITICAL; findings resolved |
| Docs | Docs, ADRs and changelog the change makes stale are updated |
| Running app | The change was exercised in the running application, not only in tests |

If anything fails, say what and stop. Do not commit or push unless the user asks.
