# ADR 0018 · Infrastructure: one Terraform root composing a local module per AWS component

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-10-22 |
| Story | none |
| Deciders | The team (to be confirmed) |

## Context

`terraform/` has one root. `versions.tf` holds Terraform `>= 1.5.0`, provider `hashicorp/aws ~> 5.0`,
an empty `backend "s3" {}` and the provider, which switches to dummy credentials and the local emulator's
endpoints when `use_local_emulator` is true (ADR 0019); the workflows pin Terraform 1.10.5. `main.tf`
holds module blocks only, all with local sources (`./modules/...`). The root's 7 variables and 6
outputs are all typed and described. Seven modules, each with `main.tf`, `variables.tf` and `outputs.tf`:

| Module | Resources |
|---|---|
| `vpc` | VPC, public and private subnets in two zones, internet gateway, one NAT gateway, routes |
| `alb` | internet-facing load balancer, security group, target group, HTTP listener |
| `ecr` | backend image repository, lifecycle policy |
| `ecs` | cluster, log group, IAM roles, task definition, Fargate service, CPU autoscaling |
| `rds` | PostgreSQL 16 Multi-AZ, KMS key, subnet group, security group |
| `storage_events` | documents bucket, events queue and dead-letter queue, KMS key |
| `web_hosting` | portal bucket, CloudFront distribution with origin access control |

No module calls another; the root wires outputs to variables. `rds` and `ecs` use each other's outputs
(security group, database address), wired in `main.tf`. Module variables are all typed, but only 5 of
37 have a description (4 in `vpc`, 1 in `web_hosting`), and none of the 25 module outputs has one.

The root `db_password` is marked `sensitive` but has a default value (a secret is present in
`terraform/variables.tf`). The root passes it to `rds` and to `ecs`, which writes it into the task
definition as the plain environment variables `DB_PASSWORD` and `DATABASE_URL`. No secrets manager is
used.

## Options considered

| Option | Pros | Cons |
|---|---|---|
| A. One root composing local modules | Matches the code; the whole topology in one file | Environments would share the root; a wrong variable reaches production |
| B. One root per environment calling the same modules | Separate state and blast radius per environment | Duplicated wiring; premature with one cloud environment |
| C. A wrapper tool or workspaces | Less duplication across many environments | Extra tooling and concepts for one environment |

## Decision

Option A while there is one cloud environment. Option B, through a new ADR, when a second one appears
(ADR 0019).

```
terraform/
  versions.tf                         Terraform and provider versions, provider, partial S3 backend
  main.tf                             module blocks and the wiring between them; no resources
  variables.tf, outputs.tf            root inputs and outputs
  environments/<env>.tfvars.example   non-secret values per environment (ADR 0019)
  modules/<component>/
    main.tf                           the component's resources
    variables.tf, outputs.tf          its inputs and outputs
```

Rules:

1. The root only composes. Resources live in a module.
2. One module per AWS component or concern. A new component gets a new module.
3. Modules do not call each other. The root wires one module's outputs to another's variables.
4. An external module needs `dependency-review`, an exact version and an ADR.
5. Secrets appear only as references to a secrets manager: never as a value, a default, a `.tfvars`
   entry or a plain container environment variable (`secure-coding-terraform`).
6. Network, IAM, keys, listeners and base images change only with an ADR. The ADR gate
   (`sdd/tools/sddlib/config.py`) enforces it when a commit adds a security group, IAM resource, KMS
   key, database instance or listener to a `.tf` file, or a `FROM` line to a Dockerfile.
7. Every variable has a type and a description; every output has a description.

## Consequences

- Easier: the topology in one file; each module reviewed as one concern.
- Harder: separating environments later means moving state to new roots, a planned step.
- When next touched: a module gets descriptions on its variables and outputs.
- Not changed by this ADR, each tracked for its own spec: the database password as a plain variable
  with a default and as plain container environment variables; the HTTP-only listener; open egress
  (`0.0.0.0/0`) on the `alb`, `ecs` and `rds` security groups; no deletion protection on the load
  balancer or the database (`skip_final_snapshot = true`).

## Security and privacy impact

Module boundaries follow trust boundaries: network (`vpc`, `alb`), compute (`ecr`, `ecs`), data (`rds`,
`storage_events`) and delivery (`web_hosting`). A change to one is reviewed with its blast radius
visible. The database, documents bucket and queues use KMS keys created in their modules. Rule 5 keeps
new secrets out of code and variables. The decision adds no data, keys or trust boundaries.
