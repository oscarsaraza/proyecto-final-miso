# Reconnaissance checklist

Build an inventory before looking for findings.

| Area | Questions |
|---|---|
| Entry points | HTTP routes (including framework-generated ones such as `/docs`), GraphQL, gRPC, webhooks, queues, scheduled jobs, CLI, mobile deep links, exported components |
| Authentication | Mechanisms (password, OTP, OAuth/OIDC, API keys, device credentials, mTLS); where tokens are issued, verified, refreshed and revoked; what a token proves (audience, issuer, role, version) |
| Authorization | Where permissions are checked; whether ownership or tenant scope is a parameter of every query; roles and how they are assigned |
| Identity sources | Values the client controls that the server trusts: IDs in paths and bodies, tenant or partner headers, forwarded IP headers, roles in tokens signed with a shared key |
| Data stores | Databases, caches, object storage, queues, mobile storage, browser storage; what each holds and its classification; encryption at rest |
| Trust boundaries | Client ↔ CDN ↔ load balancer ↔ service ↔ database ↔ third parties; what is validated at each; TLS on every hop |
| Third parties | SMS, email, payments, analytics, CI and code-quality services; what data each receives; how credentials reach them |
| Configuration | Defaults in code and IaC, environment variables (names only), debug flags, test data loading, CORS, security headers, documentation endpoints |
| Deployment | Images, IAM, network exposure, secrets injection, logging and retention, backups |
| Supply chain | Manifests and lockfiles, pinned versions, CI actions and their permissions |
