# ADR 0020 · Infrastructure: a private load balancer that only CloudFront reaches

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-10-22 |
| Story | none |
| Deciders | The team (to be confirmed) |

## Context

CloudFront serves the portal from S3 and forwards `/api/*` and `/health` to the backend's load balancer.
Until this change the load balancer was internet-facing in the public subnets, with only an HTTP:80
listener and a security group open to `0.0.0.0/0` on 80 and 443 (`terraform/modules/alb/main.tf`).
CloudFront reached it with `origin_protocol_policy = "http-only"`
(`terraform/modules/web_hosting/main.tf`). Two consequences:

- Tokens, passwords, one-time codes and personal data crossed the internet unencrypted between
  CloudFront and the load balancer.
- Anyone could call the load balancer directly, skipping CloudFront and reaching `/docs`.

HTTPS to the origin needs a certificate for a domain the team controls, and the team has no domain yet.
The viewers use `*.cloudfront.net` with CloudFront's default certificate.

## Options considered

| Option | Pros | Cons |
|---|---|---|
| A. Internal load balancer reached through a CloudFront VPC origin | No domain needed; the load balancer has no public address; the CloudFront hop travels on AWS's private network | The load balancer is recreated once; viewers keep the default certificate, which cannot enforce a TLS 1.2 minimum |
| B. Domain and ACM certificate with an HTTPS listener | HTTPS end to end and a TLS 1.2 minimum for viewers | Needs a domain and DNS validation the team does not have yet |
| C. Keep it public, restricted to CloudFront's prefix list and a secret header | Smallest change | The hop stays plain HTTP over the internet |

## Decision

Option A.

1. The load balancer is internal (`internal = true`) and lives in the private subnets.
2. CloudFront reaches it through `aws_cloudfront_vpc_origin`. The origin uses HTTP inside AWS's network.
3. Its security group accepts port 80 only from the CloudFront origin-facing managed prefix list.
4. CloudFront adds security headers to every response: HSTS, a Content Security Policy, `nosniff`,
   `DENY` framing and a referrer policy. The portal's production build does not inline scripts
   (`inlineCritical: false`), so the policy allows only `'self'` for scripts.
5. Portal deep links are rewritten to `/index.html` by a CloudFront Function on the S3 behavior only.
   The API's real status codes reach the clients.
6. A team domain with an ACM certificate (option B) is a later ADR, layered on top of this one.

## Consequences

- Easier: the backend is unreachable except through CloudFront; reviews of exposure look at one place.
- Harder: debugging needs CloudFront or access inside the VPC; the load balancer cannot be called
  from a laptop.
- Deploying this recreates the load balancer, with a few minutes without API.
- The VPC must keep its internet gateway, which CloudFront VPC origins require.
- Still open, each for its own story or hotfix: a TLS 1.2 minimum for viewers (needs a domain),
  restricted egress, deletion protection and access logs.

## Security and privacy impact

Removes a public entry point and the unencrypted internet hop. Inside the VPC the hop is HTTP on AWS's
network. Viewer TLS still allows the protocol versions of CloudFront's default certificate until there
is a domain. The Content Security Policy blocks injected scripts and framing of the portal.
