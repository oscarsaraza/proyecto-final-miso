# SDD — spec-driven development with mandatory security

A general framework for building software with AI agents and people under explicit contracts. Every
non-trivial change starts as a spec and ends as a reviewed change traceable to it. Security, privacy and
cryptography are part of the spec, the design, the tasks, the tests and the Definition of Done.

It does not depend on any particular AI tool. Any agent that reads [`AGENTS.md`](../AGENTS.md) — the
cross-tool convention for agent instructions — finds the rules, roles and skills here as plain Markdown,
and the gates run as git hooks and in CI for everyone.

| Path | Holds |
|---|---|
| [`workflow.md`](workflow.md) | The lifecycle, the gates and the security states |
| [`rules/`](rules/) | `principles` and `security` always apply; the rest by layer or task |
| [`agents/`](agents/) | Roles: orchestrator, analyst, architect, developer, threat modeler, QA, code and security reviewers |
| [`skills/`](skills/) | Procedures and guides, one `SKILL.md` each: lifecycle, security, per-language conventions and secure coding, UI and accessibility, delivery |
| [`templates/`](templates/) | The spec package (`spec`, `security`, `test-cases`, `gate`) and the ADR |
| [`security/`](security/) | Secure development: how security fits each step, the control catalog, critical paths, verified references |
| [`hooks/`](hooks/) | Gates: git hooks (`pre-commit`, `commit-msg`, `pre-push`) and an entry point for agent hooks |
| [`tools/`](tools/) | `sdd.py`: validator, scanners and CLI, with its tests. Python 3.11+, standard library only |
| [`config.json`](config.json) | Project settings: protected branches, spec-first scope, branch and commit patterns |

Spec packages live in `specs/`. Local session state (the active spec, worklogs) lives in `.sdd/`, which
is gitignored.

## Skills

| Group | Skills |
|---|---|
| Lifecycle | `spec-create`, `spec-review`, `spec-start`, `spec-update`, `spec-close`, `design`, `adr` |
| Security | `security-assessment`, `threat-model`, `security-review`, `dependency-review`, `risk-acceptance` |
| Conventions per language | `code-review-python`, `code-review-typescript`, `code-review-kotlin`, `code-review-terraform` |
| Secure coding per language | `secure-coding-python`, `secure-coding-typescript`, `secure-coding-kotlin`, `secure-coding-terraform` |
| Interfaces | `ui-ux`, `accessibility` |
| Quality and delivery | `test-design`, `code-review`, `pre-merge-check`, `commit-message`, `merge-request` |

The language skills cover this repository's stacks. For another language, add `code-review-<language>`
and `secure-coding-<language>` with the same sections and list them in `code-review` and `security-review`.

## Commands

```bash
python sdd/tools/sdd.py spec new <ID> "<Title>"     # create a spec package
python sdd/tools/sdd.py spec validate --all         # validate and compute each security gate
python sdd/tools/sdd.py spec start <ID>             # activate a hotfix package (story branches activate their own)
python sdd/tools/sdd.py spec status | spec stop
python sdd/tools/sdd.py scan secrets [paths] [--diff <base>]   # never prints values
python sdd/tools/sdd.py scan paths --base <base>    # critical paths changed without a spec
python sdd/tools/sdd.py scan deps --base <base>     # new dependencies without an evaluation
python sdd/tools/sdd.py gate --base <base>          # everything CI runs
python sdd/tools/sdd.py hooks install               # git hooks
python sdd/tools/sdd.py doctor
python -m unittest discover -s sdd/tools/tests -t sdd/tools/tests
```

## Gates

| Gate | Where | Blocks |
|---|---|---|
| Story first | git `commit-msg`, agent hook | Committing (or, with an agent hook, editing) product code on a story branch without the story's package; commits there that do not name the story |
| Secrets | git `pre-commit`, agent hook, CI | Committing a secret; with an agent hook, reading secret files or printing secrets |
| Protected branches | git `pre-commit` and `pre-push`, agent hook | Commits and pushes to protected branches, force-push, `--no-verify` |
| Structure | git `commit-msg`, agent hook | Commit subjects outside Conventional Commits |
| ADR | git `commit-msg` | Base image, infrastructure security, authentication, key or AI SDK changes without an ADR or `ADR-EXEMPT: <reason>` |
| Spec validation | CI, agent hook at the end of a session | Incomplete specs, broken traceability, a declared state above the computed one |
| Critical paths and dependencies | CI | Critical files changed without an updated spec; new dependencies without an evaluation |

### Agent hooks (optional)

Agents that support command hooks can run the same gates before each tool call:
`sh sdd/hooks/gate pre-tool` reads a JSON description of the call on stdin (`tool_name`, `tool_input` with
`command` or `file_path`, `cwd`), exits 2 with the reason on stderr to block, and with `--json` also
prints `{"decision": …, "reason": …}`. `sh sdd/hooks/gate stop` blocks the end of a session once while
the active spec has validation errors. Configure it in your agent's own settings; nothing tool-specific is
committed here. The gate needs a POSIX shell and Python 3.11+, and allows the action (saying so) when it
cannot run.

## Install in another repository

1. Copy `sdd/` and `AGENTS.md`, and adapt the project section of `AGENTS.md`.
2. Add `.sdd/` to `.gitignore` and create an empty `specs/`.
3. Adapt `sdd/config.json`, the project section of `sdd/security/critical-paths.md`, the layer rules in
   `sdd/rules/`, and the language skills (their "In this repository" sections, or new ones for other languages).
4. `python sdd/tools/sdd.py hooks install` and `python sdd/tools/sdd.py doctor`.
5. Add `python sdd/tools/sdd.py gate --base <target branch>` and the test command to the CI pipeline.
