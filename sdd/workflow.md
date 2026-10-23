# Workflow

Every non-trivial change starts as a contract and ends as a reviewed change traceable to it.

## Contracts

- **Spec** — what, why, how, and how we will know it is done: `specs/<ID>-<slug>/`.
- **Data contract** — request, response and model shapes, validation and ownership, in the spec's Design.
- **ADR** — an architecture decision with its context, options and consequences: `docs/adr/`.

## The spec package

| File | Holds |
|---|---|
| `spec.md` | Header, then **Requirements** (the story as written on the board, problem, affected paths, use and abuse cases, acceptance criteria stated by the story or derived, quality requirements, security triggers, security requirements) → **Design** (components, data flows, data contract, security design decisions, ADRs) → **Tasks** |
| `security.md` | Proportional security and privacy assessment: data and lifecycle, actors, trust boundaries, flows, third parties, attack surface, threat model, controls, cryptography, secrets, authentication, tenancy, dependencies, risks, decisions |
| `test-cases.md` | The scenarios derived from the story and their coverage; functional, quality and security test cases, each at a level (unit to performance); the review of the fifteen security test categories |
| `gate.md` | Security status, Definition of Done, human reviews, risk acceptance, evidence and closeout |

The package's ID is the key of the user story on the board, used in the branch and every commit; a
hotfix uses `HOTFIX`. Stories are read from the board, never created or edited by agents.
The validator enforces **data or threat → security requirement → control → test case → evidence** and
**acceptance criterion or quality requirement → test case → closeout**.

## Lifecycle

```
spec-create → spec-review → spec-start → build + spec-update → reviews → pre-merge-check → merge-request → spec-close
```

| Step | What it guarantees |
|---|---|
| `spec-create` | Requirements agreed before Design, Design before Tasks; security assessment and test cases included |
| `spec-review` | The spec holds against the code; verdict READY or NOT READY |
| `spec-start` | Work moves to the story's branch, which activates its package; product edits are allowed |
| `spec-update` | Tasks, controls, tests and evidence stay current; design changes update the spec first |
| `code-review`, `security-review`, `test-design` | Independent, read-only review of the real diff and test output |
| `pre-merge-check`, `merge-request` | Every gate passes before the request; drafts only until the user asks |
| `spec-close` | Every acceptance criterion MET with evidence, and a verified gate |

`design` and `adr` belong to the Design step. `threat-model` runs for HIGH and CRITICAL profiles.
While building and reviewing, the language skills apply to the files touched (`code-review-<language>`,
`secure-coding-<language>`), and `ui-ux` and `accessibility` to screens and components.
`risk-acceptance` prepares a record that only an authorized person signs.

## Security states

| State | Computed when |
|---|---|
| `BLOCKED` | a CRITICAL risk has no approved treatment, a security test fails, a secret is in the package, or a rejected dependency is in use |
| `IN_PROGRESS` | a functional task is open or the package has validation errors |
| `IMPLEMENTED` | the feature is built but a required control is missing, protection is UNKNOWN, a dependency is unevaluated, a MEDIUM or HIGH risk is open, or a blocking decision is pending |
| `SECURITY_TESTS_PENDING` | the analysis is complete; security tests or evidence are pending |
| `SECURITY_REVIEW_PENDING` | tests pass; a human security review is missing (two people for CRITICAL) |
| `RISK_ACCEPTED` | verified, with MEDIUM or higher residual risk accepted in writing by an authorized person |
| `SECURITY_VERIFIED` | verified, with no residual risk that needs acceptance |

The state declared in `gate.md` may be more conservative than the computed one, never higher. Done means
`SECURITY_VERIFIED` or `RISK_ACCEPTED` with a complete closeout.

Risk level = likelihood × impact:

| Impact \ Likelihood | LOW | MEDIUM | HIGH |
|---|---|---|---|
| LOW | LOW | LOW | MEDIUM |
| MEDIUM | LOW | MEDIUM | HIGH |
| HIGH | MEDIUM | HIGH | CRITICAL |
| CRITICAL | HIGH | CRITICAL | CRITICAL |

## Branches and commits

Work is organized by user story; the details are in [`rules/git.md`](rules/git.md).

- A story's branch is `feature/<story>-<slug>`; its package `specs/<story>-<slug>/`; every commit names
  the story: `feat(web): HU-12 validate the insured's age`.
- A hotfix (`hotfix/<slug>`) is the exception: no story; it still needs a package when it touches a
  critical path.
- Nothing goes directly to a protected branch. Nothing is committed or pushed unless the user asks.
