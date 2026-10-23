# Secure development

Security, privacy and cryptography are part of how a feature is specified, built, tested and reviewed —
not a pass at the end. This folder is the reference; the day-to-day guidance is in the skills.

| File | Holds |
|---|---|
| [controls.md](controls.md) | Control catalog by domain, the starting point for a spec's controls table |
| [critical-paths.md](critical-paths.md) | Paths whose change requires a spec with a minimum profile |
| [references.md](references.md) | Standards cited by the rules and skills, with verified versions |

## Building a feature securely

| Step | What you do | Skill |
|---|---|---|
| Specify | Mark the twelve security triggers; the profile (LOW to CRITICAL) sets the depth | `spec-create` |
| Assess | Inventory and classify the data, map who can reach what, list threats, pick controls | `security-assessment`, `threat-model` |
| Design | Data contract with types, limits, permissions and errors; each security decision cites its control | `design` |
| Build | Implement each control with the secure patterns of your language | `secure-coding-python`, `secure-coding-typescript`, `secure-coding-kotlin`, `secure-coding-terraform` |
| Test | Negative tests: another user's resource, missing permission, expired token, malicious input, failing dependency | `test-design` |
| Check | No secrets in the diff, new dependencies evaluated | `python sdd/tools/sdd.py scan secrets --diff <base>`, `dependency-review` |
| Review | Independent, read-only review of the real diff | `security-review` |
| Close | The gate computes SECURITY_VERIFIED, or RISK_ACCEPTED signed by a person | `spec-close`, `risk-acceptance` |

## Principles

1. **From the specification.** Triggers are marked before designing; the profile sets the depth.
2. **Proportional.** What does not apply is `N/A: <rationale>`; the validator rejects N/A only where a
   trigger requires the section.
3. **Traceable.** Data and threats lead to security requirements, controls, test cases and evidence.
4. **Honest.** UNKNOWN is a valid answer that keeps the gate down; an invented answer is not. No claims of
   compliance or certification.
5. **Minimal data.** Nothing collected without purpose; no real personal data in tests, logs, docs or prompts.
6. **People decide.** Agents prepare analysis and evidence; people sign reviews and accept risk. A package
   is never "secure" because an agent wrote documentation or a scanner found nothing.

## Proportional assessment

| Minimum profile | Triggers |
|---|---|
| HIGH | Authentication, authorization, payments, sensitive data, infrastructure, multi-tenancy, critical paths |
| MEDIUM | Personal data, third parties, mobile, web, dependencies |
| LOW | None |
| CRITICAL | Human decision (real money movement, sensitive data at scale). Requires two human security reviews |

Sections of `security.md` that cannot be N/A:

| Section | Cannot be N/A when |
|---|---|
| Inventory, actors, trust boundaries, data flows, attack surface, cryptography, risk register | the profile is MEDIUM or higher |
| Data lifecycle | there is CONFIDENTIAL or RESTRICTED data |
| Third-party services | the third-party trigger is YES |
| Threat model (STRIDE) | sensitive data, authentication, authorization, payments, third parties, infrastructure, multi-tenancy or critical paths |
| Secrets and keys | authentication, third parties, payments or infrastructure |
| Authentication, authorization and sessions | authentication or authorization |
| Data isolation and multi-tenancy | multi-tenancy |
| Dependencies | the profile is above LOW or there are new dependencies |
| Controls | always |

When the mobile, web or infrastructure trigger is YES there must be an applicable control of that domain.

## What the validator enforces

`python sdd/tools/sdd.py spec validate <package>`

| Code | Rule |
|---|---|
| E01–E06 | Files, sections, tables and fields complete, including the story as written on the board and the source of each criterion (STATED or DERIVED); valid and unique identifiers |
| E07 | Every cited ID exists in the package |
| E08 | Every security requirement has an applicable control |
| E09 | Every security requirement has a security test case |
| E10 | Every applicable control, cryptographic mechanism, abuse case and applicable test category has test cases |
| E11 | Every N/A, NOT APPLICABLE or NO has a rationale |
| E12 | Every MISSING control has a task |
| E13 | Every MEDIUM or higher threat has an applicable control; mobile, web and infrastructure triggers have controls of their domain |
| E14 | Personal data at least CONFIDENTIAL, sensitive data RESTRICTED, and a complete lifecycle for both |
| E15 | Every CONFIDENTIAL or RESTRICTED datum is protected by a security requirement |
| E16 | Every RESTRICTED datum has a cryptographic mechanism with algorithm, rationale, keys, permissions, rotation, recovery, failure behavior and tests |
| E17 | Forbidden or confused cryptography: reversible or fast password hashing, MD5, SHA-1, DES, RC4, ECB, TLS 1.0/1.1, custom schemes, unauthenticated CBC, HMAC declared as a signature |
| E18–E20 | Test cases complete, with a valid kind and level; PASS only with evidence; evidence citing `path::test` must exist in the repository |
| E21 | An EVALUATED dependency has a method, date and result |
| E22 | ACCEPTED risk only with an authorized person's approval; decisions and acceptances never by an AI agent |
| E23 | The declared gate state does not exceed the computed one |
| E24 | Profile and triggers are consistent with the inventory and the critical paths |
| E25 | No secret in the package (blocks the gate) |
| E26 | A person signs the security review |
| E27 | Valid enumeration values |
| E28 | A DONE task has evidence |
| E29 | A production test has a recorded authorization |
| E30 | A MITIGATED risk has no MISSING controls |
| E31 | A risk level is not below the likelihood × impact matrix |
| E32 | No claims of compliance or certification |
| E33 | Every acceptance criterion and quality requirement has a test case |
| E34 | A DONE spec has a closeout with every criterion and quality requirement MET and evidenced |
| E35 | A DONE spec has a SECURITY_VERIFIED or RISK_ACCEPTED gate |
| E36 | A PERFORMANCE quality requirement has a PERFORMANCE test case; an ACCESSIBILITY one, an ACCESSIBILITY test case |
| E37 | Every use case has scenarios; every scenario has a disposition (a test case or OUT OF SCOPE with the reason); every applicable scenario kind cites scenarios; authentication requires related flows and state and time, authorization or tenants several users |

Warnings: W01–W02 real-looking emails and phone numbers; W03 a control still MISSING after its tasks are
DONE; W04 a control linked to nothing; W06 bcrypt instead of Argon2id; W07 no recognized authenticated
encryption mode; W08 TLS without a minimum version; W09 a declared state more conservative than the
computed one; W10 a web or mobile change without an accessibility requirement.

## Known limits

The validator checks **structure, traceability and consistency**. It does not prove that a control works:
tests and human review do. A test that exists is not a test that passes — PASS must come from a run.
Secret detection is pattern-based. A clean dependency query means no known vulnerabilities in that source
today. A package without errors is a complete package, not a secure feature.
