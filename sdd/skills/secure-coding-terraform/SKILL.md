---
name: secure-coding-terraform
description: Secure infrastructure patterns for Terraform on AWS — secrets without defaults and injected from a secrets manager, encrypted and locked state, HTTPS end to end, origin reachable only from the CDN, restricted security groups, least-privilege IAM and OIDC for CI, encrypted and protected data stores, immutable images and reviewed applies. Use when writing or reviewing Terraform or deployment pipelines.
---

# Secure coding — Terraform on AWS

Infrastructure code decides who can reach what. Each pattern names the weakness it prevents (CWE) and
how to check it in the plan or the deployed environment.

## Secrets (CWE-798, CWE-522)

```hcl
variable "db_password" {
  type      = string
  sensitive = true
}
```

- No `default` for a secret, no secret in a committed `.tfvars`, no secret as a plain container environment variable.
- Prefer secrets the service manages and rotates:

```hcl
resource "aws_db_instance" "main" {
  manage_master_user_password = true
  storage_encrypted           = true
  kms_key_id                  = aws_kms_key.rds.arn
  publicly_accessible         = false
  deletion_protection         = var.environment == "production"
  backup_retention_period     = 7
  skip_final_snapshot         = var.environment != "production"
  final_snapshot_identifier   = "${var.project_name}-db-final-${var.environment}"
}
```

- Containers receive secrets by reference:

```hcl
secrets = [
  { name = "DB_PASSWORD", valueFrom = "${aws_db_instance.main.master_user_secret[0].secret_arn}:password::" },
  { name = "JWT_SECRET_KEY", valueFrom = aws_secretsmanager_secret.jwt.arn },
]
```

The task execution role may read only those secrets and decrypt only with their key. Every variable the
application requires in production (secrets, `ENVIRONMENT`) is set explicitly; a missing one must make
the application fail, not fall back to a development default.

## State (CWE-312)

State holds secrets in clear text: the backend bucket is private, encrypted with KMS, versioned and
locked against concurrent writes; access is limited to the deploy role and administrators.

## HTTPS end to end (CWE-319)

```hcl
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.main.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = aws_acm_certificate_validation.api.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend.arn
  }
}
```

- The HTTP listener only redirects to HTTPS.
- The CDN uses `viewer_protocol_policy = "redirect-to-https"` and reaches the origin with
  `origin_protocol_policy = "https-only"`, which needs a certificate on the load balancer for a domain
  the team controls.
- Security headers (HSTS, CSP, `nosniff`, frame options) through a CDN response headers policy.

## Network (CWE-284)

```hcl
data "aws_ec2_managed_prefix_list" "cloudfront" {
  name = "com.amazonaws.global.cloudfront.origin-facing"
}

resource "aws_vpc_security_group_ingress_rule" "alb_from_cdn" {
  security_group_id = aws_security_group.alb.id
  prefix_list_id    = data.aws_ec2_managed_prefix_list.cloudfront.id
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
}
```

- The origin accepts traffic only from the CDN; the database only from the application's security group.
- Egress is restricted to what each component needs (database port, HTTPS to AWS endpoints and named providers), not `0.0.0.0/0` on every port.

## IAM (CWE-250, CWE-269)

- Separate task execution and task roles; each with the actions and resources it uses, no `*` without
  a written reason.
- CI authenticates with short-lived OIDC credentials: an identity provider for the CI platform and a
  role whose trust policy pins the repository and the branch or environment. No static access keys.

## Data stores (CWE-311, CWE-1188)

- Buckets: public access blocked, KMS encryption, versioning, a policy denying requests without TLS
  (`aws:SecureTransport`), `force_destroy = false` in production.
- Databases: encrypted, private, backups with retention, deletion protection and a final snapshot in production.
- KMS keys with rotation and a key policy limited to the roles that use them.
- Logs with a defined retention, encrypted, without personal data.

## Images and deploys (CWE-494)

- Image repositories with immutable tags and scanning on push; tasks deploy by digest, not `latest`.
- Pipelines pin third-party actions or images by digest, grant minimal permissions, and apply a saved,
  reviewed plan with a human approval for production. No `-auto-approve` on push to production.

## Review checklist

- [ ] No secret defaults, committed secret values or secrets in plain environment variables.
- [ ] Every production setting the application needs is passed explicitly.
- [ ] State bucket private, encrypted, versioned and locked.
- [ ] HTTPS listener with a current TLS policy; HTTP only redirects; CDN to origin over HTTPS.
- [ ] Origin reachable only from the CDN; database only from the application; egress restricted.
- [ ] Least-privilege roles; CI with OIDC, no static keys.
- [ ] Buckets and databases encrypted, private, protected from deletion, with backups.
- [ ] Immutable images deployed by digest; reviewed plan and approval before production applies.
