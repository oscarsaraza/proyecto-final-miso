# Infrastructure and pipeline rules

> Infrastructure, containers and CI/CD rules. Load when editing IaC, Dockerfiles or pipelines. Paths: `terraform/**`, `infra/**`, `**/*.tf`, `**/Dockerfile*`, `**/docker-compose*.yml`, `.github/workflows/**`, `.gitlab-ci.yml`, `**/k8s/**`, `**/helm/**`.

- TLS end to end: certificates on load balancers, HTTPS between CDN and origin, origin reachable only from the CDN.
- Secrets in a secrets manager injected as secrets (for example ECS `secrets`, Kubernetes secrets from a
  vault); never plain environment variables, variable defaults, committed `.tfvars` or Terraform state readable by everyone.
- Least-privilege IAM for workloads and deploys; short-lived OIDC credentials instead of static keys in CI.
- Private databases; security groups with restricted egress; encryption at rest with customer-managed keys
  and rotation; backups with defined retention and deletion protection.
- Logs with defined retention and no personal data or secrets.
- Containers: pinned base images, non-root user, no secrets baked in, hash-verified dependencies.
- Pipelines: actions pinned by SHA, minimal `permissions`, approval before deploy and destroy, user input
  passed through environment variables (never interpolated into scripts), no secrets in logs or artifacts.
- Base image, network topology, IAM and key changes need an ADR (the ADR gate enforces it).

Language skills: `code-review-terraform` and `secure-coding-terraform`.
