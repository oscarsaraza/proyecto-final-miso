---
name: security-review
description: Read-only security review of a diff, a subsystem or the repository — verified vulnerabilities in authentication, authorization, injection, secrets, data exposure, business logic, cryptography, mobile and infrastructure configuration. Reports only; never edits and never attacks. Use for the security-reviewer role or before a release.
---

# Security review

**Never edits code and never executes an attack.** Scanning live hosts, sending crafted requests or
running exploits is out of scope, including against staging.

1. **Scope:** the current branch against its base by default; ask when it is ambiguous. Read the spec's
   `security.md` and `sdd/rules/security.md` first.
2. **Reconnaissance** (`references/recon.md`): entry points, authentication and authorization, data
   stores and what they hold, trust boundaries, third parties, configuration and deployment. Record
   environment variable **names only**; if a secret is found, record its location, never its value.
3. **Review** against `references/checklist.md`, including the blind spots at its end, and against the
   secure-coding skill of each language in scope: `secure-coding-python`, `secure-coding-typescript`,
   `secure-coding-kotlin`, `secure-coding-terraform`.
4. **Verify before reporting.** A finding needs a path: *an attacker who is <position> can <action> by
   <mechanism>, resulting in <impact>*, citing file:line, after checking nothing upstream blocks it. What
   cannot be completed goes under "Could not verify". Severity is impact × reachability.
5. **Report:**

```markdown
# Security review — <target>
<scope> · <n> findings (<critical>/<high>/<medium>/<low>)
## Trust map
| Entry point | Reachable by | Must prove | Can touch |
## Findings (Critical → Low)
### 1. <the vulnerability>
Location · Class (OWASP/CWE) · Attack path · Why it works · Fix (a snippet) · Blast radius
## Could not verify
## Controls in place
## Spec updates (CTL, THR, RISK and test case changes for security.md)
```

Never reproduce a secret or invent a CVE; dependency claims come from `dependency-review` output.
Critical and High block the merge. If something looks like an active compromise, stop and tell the user.
