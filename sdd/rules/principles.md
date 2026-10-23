# Working principles

> Always on.

When a request conflicts with the project section of `AGENTS.md`, say so and follow AGENTS.md.

1. **Spec before code.** Non-trivial work starts from a spec. The spec is the source of truth — not the
   chat and not the worklog. If the code has to differ from the spec, update the spec first and say why.
2. **Understand before changing.** State assumptions; ask when a request has more than one reasonable
   reading. Before implementing, restate the goal in one sentence and list the checks that could fail.
3. **Minimum change.** Solve the stated problem and nothing more. Touch only what the task needs and match
   the existing style. New code goes where the structure ADRs (`docs/adr/`) say; no new folders, layers
   or files beyond what the task needs.
4. **Proof, not claims.** Done means the checks ran and passed and the behavior was exercised. A summary
   that says it works is not evidence.
5. **Independent review.** The author of a change does not review or approve it.
6. **Know when to stop.** After three failed attempts at the same problem, stop and report the likely
   cause — an unclear spec, missing context or a broken environment — instead of retrying blindly.
7. **Small, focused work.** One spec per session or working copy; one concern per commit. Load the rules
   and skills a task needs, not all of them.
8. **People decide.** An agent never merges, accepts risk, signs reviews, or commits and pushes unless the
   user explicitly asks.
9. **Fix the rule, not just the output.** When a mistake repeats, propose the rule or skill change that
   prevents it.
