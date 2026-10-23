---
name: spec-create
description: Create the spec package of a user story from the board (Requirements, then Design, then Tasks) with its security assessment, scenarios, test cases and gate — extracting what the story says and deriving what it needs but does not say. Use when starting work on a story or a hotfix.
---

# Create a spec

A spec is the contract — what, why, how, and how we will know it is done — written before code.

1. **Read the story on the board** — title, description, acceptance criteria, comments and attachments —
   with the tools available; if it cannot be read, ask the user to paste it. Stories are never created
   or edited by agents. The ID is the story key (for example `HU-12`); a hotfix uses `HOTFIX` with the
   incident instead. Do not design yet.
2. **Create the package:** `python sdd/tools/sdd.py spec new <ID> "<Title>"` → `specs/<ID>-<slug>/` with
   `spec.md`, `security.md`, `test-cases.md` and `gate.md`, and the branch `feature/<ID>-<slug>` from the
   integration branch.
3. **Requirements** (`analyst`): the story copied as written; problem, goals and non-goals; affected
   paths (from the code, checked against `sdd/security/critical-paths.md`); use and abuse cases;
   acceptance criteria in EARS form — the story's own as `STATED`, and what the feature needs but the
   story does not say as `DERIVED: <why>`; measurable quality requirements (or N/A); the twelve security
   triggers and the profile they imply. **Stop for agreement.**
4. **Security assessment** (`security-assessment`; `threat-model` when the profile is HIGH or CRITICAL).
   The security requirements (SR) it produces go back into Requirements.
5. **Design and tasks** (`architect`, skills `design` and `adr`). **Stop for agreement** after Design.
6. **Scenarios and test cases** (`qa-engineer`, skill `test-design`): the scenarios around the story with
   their disposition; every AC, QR and SR covered at the right level; the fifteen security categories
   reviewed. Scenarios that change the requirements go back to step 3.
7. **Validate:** `python sdd/tools/sdd.py spec validate specs/<ID>-<slug>` until there are no errors.
   UNKNOWN answers are allowed; they stay visible in the gate.
8. Set `Status: DRAFT` and run `spec-review`. The link from the story on the board to the package is
   added by a person, or by the agent only when the user asks.

Never write secrets or real personal data in the package. Do not implement in this skill.
