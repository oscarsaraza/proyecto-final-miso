---
name: security-assessment
description: Fill the proportional security and privacy assessment (security.md) of a spec — data and lifecycle, actors, trust boundaries, flows, third parties, attack surface, controls, cryptography, secrets, authentication, tenancy, dependencies, risks and decisions. Use during spec-create and whenever the design changes.
---

# Security assessment

Read `sdd/rules/security.md`, `sdd/rules/privacy.md` and, when keys or hashes are involved,
`sdd/rules/cryptography.md`. Work on the active spec's `security.md`.

## Proportionality

The profile in `spec.md` sets the depth; not every feature needs every control.

| Profile | Required |
|---|---|
| LOW | Controls table; the rest may be `N/A: <rationale>` |
| MEDIUM | Inventory, lifecycle of personal data, actors, boundaries, flows, attack surface, cryptography, dependencies, risks |
| HIGH | MEDIUM plus the STRIDE threat model (`threat-model`), secrets and the authentication checklist |
| CRITICAL | HIGH plus two human security reviews |

The validator rejects `N/A` where a trigger requires the section (see `sdd/security/README.md`).

## Steps

1. **Inventory** the data the change really touches — from the code and the data contract, not from
   assumptions. Classify it: personal data at least CONFIDENTIAL; credentials and sensitive data
   RESTRICTED. Drop data without a purpose.
2. **Lifecycle:** answer the twelve questions for every CONFIDENTIAL or RESTRICTED item. Write UNKNOWN
   rather than guess; UNKNOWN keeps the gate at IMPLEMENTED until someone finds out.
3. **Actors, trust boundaries, data flows, third parties, attack surface:** who can reach what, what they
   must prove, what each boundary validates. Third parties include hosting, messaging, analytics, CI and
   code-quality services.
4. **Controls:** start from `sdd/security/controls.md`. EXISTING only if the code implements it today
   (cite file:line); MISSING needs a task; NOT APPLICABLE needs a rationale. Every applicable control has a test case.
   How to implement each one in code is in the `secure-coding-<language>` skills.
5. **Cryptography:** one CRY block per mechanism (transport, at rest, app level, passwords, MAC,
   signatures, tokenization) with algorithm, key management, permissions, rotation, recovery, failure
   behavior and tests.
6. **Secrets and keys:** names and locations, never values.
7. **Authentication and tenancy checklists** when their triggers apply.
8. **Dependencies:** new or updated ones and the critical ones the change relies on, evaluated with `dependency-review`.
9. **Risks and decisions:** residual risk per threat (likelihood × impact); decisions that need a person.
10. Copy the resulting security requirements (SR) into `spec.md` and the test cases into `test-cases.md`.
11. `python sdd/tools/sdd.py spec validate <package>` until there are no errors.

Never open secret files or print secrets to answer a lifecycle question: record the location and ask the user.
