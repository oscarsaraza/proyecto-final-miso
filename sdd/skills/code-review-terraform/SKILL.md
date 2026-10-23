---
name: code-review-terraform
description: Terraform conventions and review checklist — layout, naming and tags, variables and outputs, provider pinning, for_each over count, safe refactors with moved blocks, and reading the plan for replacements and destroys. Use when writing or reviewing Terraform.
---

# Terraform — conventions and review

Applies to `*.tf`, `*.tfvars.example` and `.terraform.lock.hcl`. Follow it when writing; when reviewing,
`code-review` gives the process and this skill gives what to check. Secure patterns are in
`secure-coding-terraform`.

Reference: Terraform style guide (https://developer.hashicorp.com/terraform/language/style).

## Layout and style

- `terraform fmt -recursive` clean; `terraform validate` clean.
- Root: `versions.tf` (Terraform and providers), `main.tf`, `variables.tf`, `outputs.tf`. Modules:
  `modules/<name>/{main,variables,outputs}.tf`.
- `snake_case` for every name; resource local names describe the role (`main`, `backend`), not the type.
- Physical names follow one pattern (`"${var.project_name}-<component>-${var.environment}"`); tags come
  from the provider's `default_tags` plus a `Name` per resource.

## Variables and outputs

- Every variable has `type` and `description`; constrained inputs have `validation` blocks.
- Defaults only for values that are safe in every environment. Secrets never have defaults and are
  `sensitive = true` (see `secure-coding-terraform`).
- Every output has a `description`; outputs that carry secrets are `sensitive = true`, or better, are not outputs.
- No hard-coded account IDs, regions or ARNs: variables or data sources.

## Providers and versions

- `required_version` and provider constraints (`~>`) pinned; `.terraform.lock.hcl` committed and updated
  deliberately (`terraform init -upgrade` is a reviewed change).
- External modules pinned to an exact version and evaluated with `dependency-review`.

## Changing infrastructure safely

- `for_each` with stable keys for collections; `count` only for on/off switches.
- Renames and moves use `moved` blocks; never a destroy and create of a stateful resource.
- Stateful resources (databases, buckets with data, keys) have `lifecycle { prevent_destroy = true }` in
  production and deletion protection where the service offers it.
- Read the plan before approving: any `-/+` (replace) or `-` (destroy) on a stateful resource, a security
  group, a key or an IAM policy needs an explanation in the merge request.
- One concern per change: network, data, compute and IAM changes are reviewed separately when possible.

## Review checklist

- [ ] `fmt -recursive` and `validate` clean.
- [ ] Variables and outputs typed and described; validations for constrained inputs.
- [ ] No default for a secret; no hard-coded account, region or ARN.
- [ ] Providers and modules pinned; lock file updated on purpose.
- [ ] `for_each` with stable keys; `moved` for renames; `prevent_destroy` on stateful resources.
- [ ] Plan read: no unexplained replace or destroy.
- [ ] An ADR when the change touches network topology, IAM, keys or base images (the ADR gate enforces it).

## In this repository

- Architecture: ADRs [0018](../../../docs/adr/0018-terraform-root-and-modules.md) (root and modules) and
  [0019](../../../docs/adr/0019-terraform-environments-and-state.md) (environments and state). The root composes local
  modules `vpc`, `alb`, `ecr`, `ecs`, `rds`, `storage_events`, `web_hosting`. AWS provider `~> 5.0` with
  a committed lock file; Terraform 1.10.5 in CI.
- Partial S3 backend configured by the pipelines; `terraform/environments/local.tfvars.example` for the
  local emulator. Root variable descriptions are in Spanish.
- CI runs `terraform fmt -check` on the root only and `terraform validate`; run the recursive check locally.
- Commands: `cd terraform && terraform fmt -check -recursive && terraform init -backend=false && terraform validate`.
