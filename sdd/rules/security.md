# Security rules

> Always on.

Security is part of the spec, the design, the tasks, the tests and the Definition of Done — never a
pass at the end. The module is in `sdd/security/`.

## Never

- Read, print, paste into a prompt or log a secret, token, password, key or one-time code — not even partially.
  Check presence by name (`test -n "$VAR"`), never by value. Find secrets with
  `python sdd/tools/sdd.py scan secrets`, which only shows type, location and fingerprint.
- Commit secrets, or add default values for keys or passwords to code, infrastructure, images or CI artifacts.
- Use real personal data in tests, fixtures, logs, docs or prompts. Use reserved domains (`example.com`,
  `.test`) and fictitious data.
- Design cryptography, encrypt passwords reversibly, or confuse hashing, MAC, signatures, encryption and tokenization.
- Trust the client: identity, permissions, tenant, prices and IP addresses are decided on the server.
  A header such as `Client-Id`, `X-Partner-Id` or `X-Forwarded-For` proves nothing by itself.
- Run intrusive tests against production or third-party services, or scan live hosts, without written authorization.
- Claim legal compliance or certification. Describe controls and evidence instead.
- Accept a risk, sign a security review, or declare a gate state above the computed one.

## Always

- Classify every new datum (PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED) and collect only what has a purpose.
- Authorize per resource on the server; answer 404 for resources of other users or tenants.
- Validate input on the server (type, length, format, range), including headers and identifiers.
- Return generic errors; log events, never secrets or personal data.
- Use maintained libraries and authenticated encryption; keys in a secrets manager or platform keystore,
  one key per purpose and per environment, with rotation and revocation planned.
- Evaluate every new dependency (OSV.dev or the ecosystem's audit tool) before adding it.
- Keep the spec's `security.md` true: update it in the same change that moves a control.

`security-reviewer` reads diffs against these rules. Critical and High findings block the merge request.
