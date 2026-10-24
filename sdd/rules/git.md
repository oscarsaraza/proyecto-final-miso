# Git workflow

> Branches, commits and merge requests. Load before branching, committing or opening a merge request.

Work is organized by the user stories on the board. A story's branch names it, every commit on that
branch names it, and its spec package is what unlocks product code there. A hotfix is the exception.

| Work | Branch | Commit subject | Spec package |
|---|---|---|---|
| A user story | `feature/<story>-<slug>` | `type(scope): <story> <summary>` | Required: `specs/<story>-<slug>/` |
| A fix to a story not yet released | `fix/<story>-<slug>` | `type(scope): <story> <summary>` | The story's package |
| An urgent fix in production | `hotfix/<slug>` | `type(scope): <summary>` | Recommended; required when it touches a critical path |

- The story key and the story branch pattern are set in `sdd/config.json` (`storyBranch`). On a story
  branch the gates reject commits that do not name the story and product code without its package.
- A hotfix package uses `HOTFIX` as its ID (`python sdd/tools/sdd.py spec new HOTFIX "<title>"`) and is
  activated with `spec start`.
- A change on a critical path needs a spec package on any branch; CI checks it.
- Branch from the latest integration branch. One story, one branch, one session or worktree.
- Conventional Commits, imperative, one concern each, in the language the project section of `AGENTS.md`
  sets. Types: feat, fix, chore, docs, refactor, test, perf, ci, build, security, revert, style.
- Never commit or push to a protected branch, never force-push, never `--no-verify`.
- Nothing is committed or pushed unless the user explicitly asks. Skills draft; people decide.
- Waivers need a person's agreement and stay in the history: `ADR-EXEMPT: <reason>` in a commit message;
  `SPEC-EXEMPT: <reason>` only for a critical-path change that cannot have a package, such as installing
  this framework.
- Merge requests target the integration branch, link the story and its package, and are merged only with
  a green pipeline and a human review.
