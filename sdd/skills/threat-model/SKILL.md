---
name: threat-model
description: Proportional STRIDE threat model of a spec — assets, actors, trust boundaries, threats, likelihood × impact, controls and residual risk. Use when the profile is HIGH or CRITICAL or the change touches sensitive data, authentication, payments, integrations, infrastructure or critical paths.
---

# Threat model

Proportional: a trivial change gets none; a login flow gets a real one. Write it in `security.md`
sections 3–8 and 16.

1. **Assets:** the data (DATA-NN) and capabilities worth protecting — accounts, money, keys, availability.
2. **Actors and positions:** unauthenticated user, any authenticated user, a user of another tenant, a
   low-privilege role, someone holding the device, an insider with repository access, a compromised dependency.
3. **Trust map:** for each entry point, who can reach it, what they must prove, what it can touch. Most
   real flaws are a mismatch between two rows of this map.
4. **STRIDE per boundary:** Spoofing, Tampering, Repudiation, Information disclosure, Denial of service,
   Elevation of privilege. Be specific ("change the policy number in the URL"), and check the cases
   scanners miss: cross-tenant access, business-logic abuse, races on value-bearing operations, alternate
   routes to the same handler, identity taken from the client, debug paths in production.
5. **Rate** likelihood (LOW, MEDIUM, HIGH) × impact (LOW, MEDIUM, HIGH, CRITICAL). The validator rejects a
   level below the matrix in `sdd/workflow.md`.
6. **Controls:** each MEDIUM or higher threat gets at least one applicable control (EXISTING with
   file:line, or MISSING with a task) and a security test case.
7. **Residual risk:** one RISK row per threat that remains; an open CRITICAL risk blocks the gate. Only a
   person accepts risk (`risk-acceptance`).
8. Add abuse cases (AB-NN) to `spec.md` for the threats a user could act out.

Name the missing control and its impact; do not write exploit steps or payloads.
