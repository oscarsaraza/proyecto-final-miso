---
name: spec-close
description: Prove the delivery against the spec, reconcile differences and close it. Use when the change is reviewed and ready to merge, or merged.
---

# Close a spec

A spec is not DONE while any acceptance criterion lacks proof.

1. Re-read the acceptance criteria, tasks, security requirements and risks.
2. Fill `## Closeout` in `gate.md`: each acceptance criterion and quality requirement MET, NOT MET or PARTIAL, with `file:line`, `path::test`
   or the CI run as evidence. An empty or unproven row blocks.
3. Check the other obligations: tests at the project thresholds, docs updated, ADRs in place, no MISSING
   controls, dependencies evaluated, `python sdd/tools/sdd.py scan secrets --diff <base>` clean.
4. If the code differs from the spec, update the spec to match reality and say so.
5. `python sdd/tools/sdd.py spec validate <package>`: the gate must compute SECURITY_VERIFIED or
   RISK_ACCEPTED. Otherwise list what is pending and stop.
6. Only when every row is MET and the user agrees: `Status: DONE`.
7. Release the marker: `python sdd/tools/sdd.py spec stop`.
8. If something went wrong that a rule would have prevented, propose that rule in `sdd/rules/` or the skill.

Never mark DONE or release the marker with an unmet criterion. Never sign the security review.
