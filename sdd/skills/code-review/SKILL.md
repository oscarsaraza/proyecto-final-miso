---
name: code-review
description: Read-only review of a diff for correctness, spec conformance, tests, conventions and maintainability, delegating language conventions to the code-review-<language> skills. Reports blockers separately from nits; never edits. Use for the code-reviewer role or before a merge request.
---

# Code review

Read-only. The default target is the current branch against its base. The review is against the spec
and the project's conventions, not against taste.

1. **Scope:** `git diff --stat <base>...HEAD`; read each changed file where the change matters.
2. **Language skills:** load the skill for each language in the diff and apply its checklist.

   | Files | Skill |
   |---|---|
   | `*.py` | `code-review-python` |
   | `*.ts`, Angular templates and styles | `code-review-typescript` |
   | `*.kt`, `*.kts`, Android XML resources and manifests | `code-review-kotlin` |
   | `*.tf`, `*.tfvars.example`, `.terraform.lock.hcl` | `code-review-terraform` |
   | Screens and components (web or mobile) | also `ui-ux` and `accessibility` |

   A language without a skill: its official style guide and the project's linters.
3. **Spec conformance:** the diff implements the tasks it claims and nothing else; any difference is reflected in the spec.
4. **Correctness:** for each change, the input that breaks it — boundaries, nulls, errors, concurrency,
   time zones, retries. A finding needs a concrete failing scenario.
5. **Tests:** each criterion, quality requirement and security requirement it touches has a test at the
   right level that fails on regression. Run the tests and linters and read the output, not the summary.
6. **Security basics** (the deep review is `security-review`): authorization per resource, validation,
   secrets, personal data in logs, error messages.
7. **Structure and maintainability:** files where the accepted ADRs in `docs/adr/` put them, no new
   folders or layers outside them, dependency directions respected, files under the size the ADR sets;
   duplicated helpers, dead code introduced, comments that explain why rather than what.
8. **Delivery:** Conventional Commits naming the story (except on a hotfix branch), docs
   updated, generated files untouched, branch not protected.

```markdown
# Code review — <branch> (<story>)
Verdict: approve | changes requested
## Blockers
1. <file:line> — <what breaks and the scenario> — <the fix>
## Nits
## Verified
<tests and linters run, with their result>
```

A blocker breaks a rule or leaves a criterion unproven. A convention the surrounding code does not follow
yet is a nit unless the change makes it worse. Never review work you wrote.
