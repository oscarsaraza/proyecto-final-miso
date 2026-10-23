---
name: commit-message
description: Draft Conventional Commit messages that name the user story, and split a working tree into one-concern commits. Drafts only; commits only when the user explicitly asks.
---

# Commit message

```
type(scope): <story> <imperative summary in the project's language>

Why the change was needed, when it is not obvious.

ADR-EXEMPT: <reason>    (only when the user accepts the waiver)
```

- The story comes from the branch name (`feature/HU-WEB-02-…` → `HU-WEB-02`) and is required on
  `feature/` and `fix/` branches; never invent one. `hotfix/` commits have no story.
- Types: feat, fix, chore, docs, refactor, test, perf, ci, build, security, revert, style. The scope is
  the layer or module (`web`, `movil`, `backend`, `identity`, `terraform`).
- One concern per commit; the subject says what, the body says why.
- Include lockfiles with their manifests and the docs the change makes stale.
- Never stage secrets, `.env` files, keys or `.sdd/`; never use `--no-verify`; no interactive staging.
- If a file mixes two concerns, propose a split the user can apply.

Examples (the language follows AGENTS.md): `feat(web): HU-12 validate the insured's age` on
`feature/HU-12-insured-age`; `fix(auth): reject revoked refresh tokens` on `hotfix/revoked-refresh-tokens`.

Show the messages. Commit only when the user explicitly asks; the commit-msg hook checks them.
