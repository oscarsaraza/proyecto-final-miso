# ADR 0019 · Infrastructure: environments and Terraform state

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-10-22 |
| Story | none |
| Deciders | The team (to be confirmed) |

## Context

**One cloud environment, production.** The root defaults are `environment = "production"` and
`aws_region = "us-east-1"` (`terraform/variables.tf`). `deploy.yml` and `destroy.yml` pass no variables
file, so they use these defaults, and they name production resources directly
(`solventa-cluster-production`, `solventa-web-portal-production`…). The environment name reaches
resource names and tags but not the backend: the ECS task definition sets no `ENVIRONMENT` or
`SMS_PROVIDER` (`terraform/modules/ecs/main.tf`), so `backend/app/core/config.py` falls back to
`development` and `console`.

**A local emulator, Floci.** `docker-compose.yml` runs `floci/floci:latest` on port 4566.
`terraform/environments/local.tfvars.example` sets `environment = "local"` and
`use_local_emulator = true`, so `versions.tf` sends its AWS endpoints to Floci. The working copy
`environments/local.tfvars` is git-ignored. `scripts/deploy-local.sh` starts Floci and runs
`terraform apply -var-file=environments/local.tfvars -auto-approve`. `deploy-local.yml` (manual) runs
`init -backend=false` and the same apply on a GitHub-hosted runner, with no Floci service and no
variables file in the checkout; its `auto_approve` input is unused. The emulator keeps local state.

**State.** `versions.tf` declares an empty `backend "s3" {}`. `deploy.yml` and `destroy.yml` complete it
at `init`: bucket `solventa-tfstate-<account id>`, key `production/terraform.tfstate`, region from a
repository secret or `us-east-1`. If the bucket is missing, `deploy.yml` creates it with the AWS CLI and
enables versioning; it sets no encryption, KMS key or public access block, and no lock (no DynamoDB
table, no `use_lockfile`). Both workflows share the concurrency group `production-deployment`, so GitHub
runs them one at a time.

**Validation and apply.** `ci.yml` (`terraform-ci`) runs `init -backend=false`, `fmt -check` and
`validate` on every push and pull request; no job runs `plan`. `deploy.yml` runs
`terraform apply -auto-approve` on every push to `main` and on manual dispatch. `destroy.yml` is manual,
asks for the word `DESTRUIR` and runs `terraform destroy -auto-approve`. Both authenticate to AWS with
an access key pair stored as repository secrets.

## Options considered

| Option | Pros | Cons |
|---|---|---|
| A. One cloud environment plus the local emulator | Matches the code; one state; low cost, and `destroy.yml` turns it off | Changes reach production after only the emulator and `validate`; the emulator does not reproduce every AWS behavior |
| B. dev, staging and production from the start | Changes tried in the cloud before production | Two or three times the cost (NAT gateway, Multi-AZ database, load balancer each); more states and workflows |
| C. Terraform workspaces on one root | No duplicated files | One backend and one set of credentials for every environment; applying in the wrong workspace hits the wrong environment |

## Decision

Option A now. A second cloud environment arrives with its own root (ADR 0018, option B) and a new ADR.

```
terraform/environments/
  local.tfvars.example    Floci: use_local_emulator = true; local state
  <env>.tfvars.example    non-secret values of each cloud environment
s3://solventa-tfstate-<account id>/<env>/terraform.tfstate    one state per cloud environment
```

Rules:

1. One cloud environment (production) and the local emulator. No workspaces.
2. Each environment's non-secret values live in `environments/<env>.tfvars.example`; the working copy
   `<env>.tfvars` stays git-ignored. Secrets go in neither (ADR 0018, rule 5).
3. The state bucket is private, versioned, encrypted and locked against concurrent applies.
4. CI validates without a backend: `init -backend=false`, `fmt -check`, `validate`.
5. Production applies run a saved plan that a person reviews and approves.

Known gaps between today and this decision, each tracked for its own spec:

- No state lock; only the GitHub concurrency group serializes the two workflows.
- The workflow configures versioning only: no encryption or public access block of its own.
- `deploy.yml` applies with `-auto-approve` on every push to `main`, without a saved plan or approval.
- Production has no `environments/production.tfvars.example`; it runs on the root defaults.

## Consequences

- Easier: one state to protect; changes tried locally at no cloud cost; `destroy.yml` removes the cloud
  environment when it is not needed.
- Harder: no cloud environment between the emulator and production. A second one needs a new root and
  the production names in `deploy.yml` and `destroy.yml` made per environment.

## Security and privacy impact

- The state holds sensitive values in plain text, including the database password passed to the
  database instance and the task definition; `sensitive = true` only hides it from command output.
  Whoever reads the bucket, or an old version of the state, reads the password. Hence rule 3.
- Today a push to `main` reaches the production apply with no approval step; rule 5 adds one.
- The backend in AWS runs with `ENVIRONMENT=development` and `SMS_PROVIDER=console` (see Context). With
  those, the insured BFF returns the one-time code in `debug_code` (`backend/app/bff/auth/router.py`),
  and the test accounts in `backend/seeds/`, which `backend/Dockerfile` copies into the image, are
  created at startup (`backend/app/modules/identity/service.py`). Tracked for its own spec.
- The emulator uses fixed dummy credentials and `localhost`; `local.tfvars.example` holds no secrets.
