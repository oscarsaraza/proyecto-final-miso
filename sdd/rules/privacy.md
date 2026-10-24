# Privacy and data protection

> Data classification, data lifecycle and minimization. Load when a change captures, stores, transmits or deletes personal data.

## Classification

| Level | Includes |
|---|---|
| PUBLIC | Information that can be published without harm |
| INTERNAL | Operational information without personal data |
| CONFIDENTIAL | Personal data: identifies or can identify a person (name, email, phone, ID number, IP, account identifiers) |
| RESTRICTED | Credentials, secrets, one-time codes, special-category data (health, biometrics, minors), detailed financial data |

Personal data is never below CONFIDENTIAL; sensitive data is always RESTRICTED. The validator enforces both.

## The twelve lifecycle questions

For every CONFIDENTIAL or RESTRICTED datum, `security.md` answers: what it contains; why it is needed;
who can access it; where it is captured; how it is transmitted; where it is stored; which copies, caches
and backups exist (logs, replicas, snapshots, mobile saved state, browser storage, CI artifacts); how
long it is kept; how access is audited; how it is deleted or anonymized; what happens if it leaks; and
whether it is transferred to third parties. UNKNOWN is honest and keeps the gate at IMPLEMENTED.

## Minimization

- No purpose, no collection. Remove fields nobody needs.
- Define retention and purge for every table with personal data, including audit and security tables.
- Logs record events, not content. Never passwords, codes, tokens, secrets or request bodies with personal data.
- Never copy production data into development, tests or prompts.
- Biometrics: platform APIs (BiometricPrompt, LocalAuthentication) never give the app the template; if a
  feature ever captures or sends biometric data it becomes special-category data.

## Legal requirements

Legal and contractual requirements reach the spec from the product owner, as acceptance criteria or
security requirements with their source. Agents do not interpret law and never claim compliance.
