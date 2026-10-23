# ADR 0001 · System: separated applications that talk only through the backend API

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-10-22 |
| Story | none |
| Deciders | The team (to be confirmed) |

## Context

Solventa serves sales advisors, policyholders (the insured) and, later, partners. The repository holds
four applications in separate top-level folders:

- `backend/`: a FastAPI API. Its domain modules run in one FastAPI application (`backend/app/main.py`)
  and one container (`backend/Dockerfile`), which ECS Fargate runs as two tasks (`terraform/modules/ecs`).
- `web/`: the advisors' Angular portal, synced to S3 and served by CloudFront, which also sends `/api/*`
  and `/health` to the load balancer (`terraform/modules/web_hosting`).
- `movil/`: the insured's Android app. No workflow builds or publishes it; the README (section 5.3) and
  `scripts/apk-local.sh` build a debug APK with Gradle. The API address is the `apiBaseUrl` build
  property (`movil/app/build.gradle.kts`).
- `terraform/`: the AWS infrastructure for the backend and the web portal.

`backend/app/main.py` mounts one backend-for-frontend (BFF) router per channel from `backend/app/bff/`:

| BFF | Prefix | Client | Verified in |
|---|---|---|---|
| `auth` | `/api/v1/auth` | insured's mobile app | `movil/.../data/auth/HttpAuthApi.kt` |
| `experience` | `/api/v1/experience` | advisors' web portal | `web/src/app/core/*/*.service.ts` |
| `quote_edge` | `/api/v1/quote-edge` | partners | no client yet; a placeholder |

Each client calls only its own BFF. No folder imports code from another application; each client keeps
its own copy of the DTOs it uses. `.github/workflows/ci.yml` has one job per application (`backend-ci`,
`web-ci`, `mobile-ci`, `terraform-ci`) plus the shared `sonarcloud` and `sdd-gate`. `deploy.yml` runs
`deploy-infra`, then `deploy-backend` (ECR image, new ECS deployment) and `deploy-web` (S3 sync,
CloudFront invalidation) as separate jobs.

## Options considered

| Option | Pros | Cons |
|---|---|---|
| A. Separated applications, one BFF per channel | Matches the code; each client gets endpoints shaped for its user and its authentication; each application builds, tests and deploys on its own | A contract change touches up to three folders; DTOs are copied by hand |
| B. One general-purpose API for all clients | One set of endpoints; less routing code | Advisors, insured and partners authenticate differently and have different permissions; their rules mix in the same endpoints; payloads fit no client well |
| C. Server-rendered web inside the backend | No DTO copy for the portal; one deployment | Portal releases tied to backend releases; the mobile app still needs an API; the Angular portal and its S3 + CloudFront hosting would be rewritten |

## Decision

Option A.

```
backend/     HTTP API; one BFF router per channel in app/bff/<channel>/; container on ECS Fargate
web/         advisors' portal; static build on S3 behind CloudFront
movil/       insured's app; APK built with Gradle, distributed outside AWS
terraform/   AWS infrastructure for the backend and the web portal
```

Rules:

1. Each application owns its code, build, tests and CI job. No application imports code from another.
2. Clients reach the backend only through its HTTP API, never its database, queue or buckets.
3. One BFF per channel: `auth` for the mobile app, `experience` for the web portal, `quote_edge` for
   partners. A client calls only its own BFF. A new channel gets a new BFF.
4. Applications share contracts, not code. The contract rules are in ADR 0002.
5. Each application's internal architecture has its own ADRs: backend 0003–0007, web 0008–0012,
   mobile 0013–0017, infrastructure 0018–0019.
6. Each application deploys to its own target: the backend image to ECR and ECS, the web build to S3
   and CloudFront, the mobile app outside AWS.

## Consequences

- Easier: a change to one client does not touch the other; each channel keeps its own authentication
  and limits; a reviewer knows which folder and which ADRs apply.
- Harder: a contract change needs the backend and its clients updated in one story (ADR 0002).
- When next touched: the docstring of `backend/app/bff/experience/router.py`, which says it serves web
  and mobile, is corrected to the web portal.

## Security and privacy impact

Each BFF is the trust boundary of its channel. `experience` requires the `advisor` role except on login,
refresh and its two catalogs; the `auth` device endpoints require the `insured` role (`require_roles` in
`backend/app/core/security.py`). Behind the API, the database accepts connections only from the ECS
security group and is not public, ECS tasks have no public IPs, and both buckets block public access
(modules `rds`, `ecs`, `storage_events`, `web_hosting`).

Known exposures, each tracked for its own spec: `quote_edge` only checks that an `X-Partner-Id` header is
present, so partners are not authenticated; the load balancer listens only on HTTP port 80 and
CloudFront reaches it over HTTP (modules `alb`, `web_hosting`). The decision adds no data, keys or trust
boundaries.
