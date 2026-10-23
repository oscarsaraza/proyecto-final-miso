---
name: spec-start
description: Start implementing a READY spec — on the story's branch, which activates its package and unlocks product code, or with an explicit marker for hotfix packages. Use when implementation begins.
---

# Start a spec

One story per branch, per session and per working copy. The package is the source of truth.

1. Find the package in `specs/<story>-*`. If there is none, run `spec-create`.
2. Check `Status: READY` (spec-review passed). If not, say what is missing and stop.
3. Be on the story's branch, or create it from the latest integration branch:
   `feature/<story>-<slug>` (or `fix/<story>-<slug>`). On that branch the package is active by itself:
   `python sdd/tools/sdd.py spec status` shows it. Never work on a protected branch.
4. Hotfix packages (`hotfix/<slug>` branches) are activated explicitly: `python sdd/tools/sdd.py spec
   start <ID>` writes `.sdd/active-spec.json` and a worklog.
5. Set `Status: IN_PROGRESS` in the spec and the gate.
6. Re-read the spec and report which task is next.

`spec-close` releases an explicit marker. In another working copy (for example a git worktree), check out
the branch there.
