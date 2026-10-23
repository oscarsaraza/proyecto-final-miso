# AGENTS.md

Instructions for any AI agent and any person working in this repository. The framework is in
[`sdd/`](sdd/README.md): spec-driven development with security, privacy and data protection built in.

<!-- project:start — adapt this section when copying the framework to another repository -->

## Project

Solventa, a digital insurer: a hexagonal FastAPI backend, an Angular portal for sales advisors, an Android
app for policyholders and AWS infrastructure as code. Details in [README.md](README.md).

| Layer | Technology | Path |
|---|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy async, PostgreSQL 16, Poetry | `backend/` |
| Web | Angular 22, TypeScript, Vitest | `web/` |
| Mobile | Android, Kotlin, Jetpack Compose, Android Keystore | `movil/` |
| Infrastructure | Terraform on AWS | `terraform/` |

- Work is organized by the user stories on the board (`HU-WEB-02`, `HU-MOV-05`): branch
  `feature/HU-…-slug`, package `specs/HU-…-slug/`, and every commit names the story. Hotfixes
  (`hotfix/slug`) are the exception.
- Integration branch: `dev`. Protected branches are listed in `sdd/config.json`.
- Architecture: separated applications (backend, web portal, mobile app, infrastructure), each with its
  own ADRs in [`docs/adr/`](docs/adr/README.md): system and API 0001–0002, hexagonal backend 0003–0007,
  web 0008–0012, mobile 0013–0017, Terraform 0018–0019.
- Identifiers in English; comments, docstrings, test names, commit descriptions and UI text in Spanish,
  as the existing code does.

| Check | Command |
|---|---|
| Backend tests | `cd backend && poetry run pytest` |
| Web tests and build | `cd web && npm test -- --watch=false && npm run build` |
| Mobile tests | `cd movil && ./gradlew testDebugUnitTest` |
| Terraform | `cd terraform && terraform fmt -check && terraform validate` |
| SDD gate | `python sdd/tools/sdd.py gate --base origin/dev` |

<!-- project:end -->

## How we work

1. **Story and spec first.** Non-trivial work starts from the user story's spec package in `specs/<story>-<slug>/`: Requirements →
   Design → Tasks, with its security assessment, test cases and gate. Create one with the `spec-create`
   skill; work on an existing one with `spec-start`. The lifecycle is in [`sdd/workflow.md`](sdd/workflow.md).
2. **Security from the start.** Each spec marks its security triggers and gets a proportional assessment;
   the validator computes its security gate from the evidence. See [`sdd/security/`](sdd/security/README.md).
3. **Independent review.** The author of a change does not review or approve it.
4. **Small changes.** Typed branches, Conventional Commits naming the spec, reviewed merge requests with a
   green pipeline.
5. **People decide.** Agents never merge, sign security reviews, accept risk, or commit and push unless
   the user explicitly asks.

## Rules

Always read [`sdd/rules/principles.md`](sdd/rules/principles.md) and
[`sdd/rules/security.md`](sdd/rules/security.md). Read the others when the task needs them:
[`privacy`](sdd/rules/privacy.md), [`cryptography`](sdd/rules/cryptography.md),
[`testing`](sdd/rules/testing.md), [`git`](sdd/rules/git.md), [`backend`](sdd/rules/backend.md),
[`frontend`](sdd/rules/frontend.md), [`mobile`](sdd/rules/mobile.md),
[`infrastructure`](sdd/rules/infrastructure.md).

Non-negotiable:

- User stories come from the board: read them, never create or edit them. The spec derives what the
  story needs but does not say.
- No product change on a story branch without the story's spec package; every commit there names the story.
- Never read or print secret files, secrets, tokens, passwords or one-time codes — not even partially.
- No real personal data in tests, fixtures, logs, docs or prompts.
- No commits or pushes to protected branches, no force-push, no `--no-verify`.
- Never declare a security state above the one the validator computes; never claim legal compliance.
- No intrusive tests against production or third parties without written authorization.

## Roles and skills

When a skill is named, read `sdd/skills/<name>/SKILL.md` and follow it. When a role is named, read
`sdd/agents/<role>.md` and act within its access.

| Roles | `orchestrator`, `analyst`, `architect`, `developer`, `threat-modeler`, `qa-engineer`, `code-reviewer` (read-only), `security-reviewer` (read-only) |
|---|---|
| Lifecycle skills | `spec-create`, `spec-review`, `spec-start`, `spec-update`, `spec-close`, `design`, `adr` |
| Security skills | `security-assessment`, `threat-model`, `security-review`, `dependency-review`, `risk-acceptance` |
| Language skills | `code-review-python`, `code-review-typescript`, `code-review-kotlin`, `code-review-terraform` (conventions); `secure-coding-python`, `secure-coding-typescript`, `secure-coding-kotlin`, `secure-coding-terraform` (secure patterns) |
| Interface skills | `ui-ux`, `accessibility` (WCAG 2.2 AA, Android guidelines) |
| Quality and delivery skills | `test-design`, `code-review`, `pre-merge-check`, `commit-message`, `merge-request` |

## Starting a session

1. Read this file and the two always-on rules.
2. `python sdd/tools/sdd.py spec status` — the active spec and its security gate.
3. Read the skill or role the request names. One spec per session.

The gates also run as git hooks (`python sdd/tools/sdd.py hooks install`) and in CI. When a gate blocks
you, fix the cause.
