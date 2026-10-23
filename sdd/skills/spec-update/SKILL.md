---
name: spec-update
description: Keep the active spec current while building — tasks, controls, test cases, evidence and design changes. Use after each coherent batch of work.
---

# Update a spec

The spec must match reality while the work happens, not only at the end.

- A task is done: `Status: DONE` with evidence (commit, merge request, `path::test`).
- A control is implemented: `EXISTING`, citing file:line.
- A test case ran: `PASS` with evidence, or `FAIL` (a failing security test blocks the gate).
- The design changed: update Design, the assessment and the affected test cases **before** more code follows the change.
- A new risk or unknown appears: record it in `security.md`; never hide it.

Then run `python sdd/tools/sdd.py spec validate <package>` and set the gate's `Security status` to the
computed state or a more conservative one — never higher. Add one line to the worklog.

This skill never approves a gate, signs a review or accepts a risk.
