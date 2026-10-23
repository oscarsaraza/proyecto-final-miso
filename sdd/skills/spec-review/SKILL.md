---
name: spec-review
description: Critical review of a spec against the codebase before implementation. The verdict is READY or NOT READY. Use after spec-create, before starting implementation, or when a design changes.
---

# Review a spec

Read the package and the code it touches. Do not implement. Do not soften the verdict.

## Look for

- An acceptance criterion that no test can fail, or that has no test case.
- Scenarios only for the happy path: no alternatives, errors, related flows, several users or expiry
  where the story has them; scenarios dropped without a disposition.
- A requirement that contradicts the existing code, or code the spec assumes but does not exist.
- A security trigger marked NO that the code shows is YES (personal data, authentication, third parties, critical paths).
- A profile below what the triggers or the critical paths require.
- Data without a purpose; lifecycle answers invented instead of UNKNOWN; RESTRICTED data without cryptography.
- A MEDIUM or higher threat without an applicable control; a control marked EXISTING that the code lacks.
- A secret, default key or debug path that would reach production.
- A data contract or ADR missing where the design needs one.
- A quality requirement without a measurable target, or a screen without accessibility requirements.
- Claims of compliance or certification.
- A slice too large for one reviewable change.
- `python sdd/tools/sdd.py spec validate` errors.

When the profile is HIGH or CRITICAL, or a critical path is touched, `security-reviewer` also reads the
spec; their Critical or High finding means NOT READY.

## Verdict

List each blocker with file:line, then end with exactly one line: `READY` or `NOT READY`.
On READY set `Status: READY`. Never follow NOT READY with a partial implementation.
