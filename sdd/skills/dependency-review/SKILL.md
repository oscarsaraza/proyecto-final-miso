---
name: dependency-review
description: Review dependencies for known vulnerabilities, loose versions, unmaintained or suspicious packages and licenses, or vet a package before adding it. Uses real tool output, never memory. Use before adding or upgrading a dependency and for the spec's dependency table.
---

# Dependency review

**Never state a vulnerability, version, date or license from memory.** Every claim comes from a command
run now or a file in the repository; if a check cannot run, say which.

1. Find manifests and lockfiles (`references/ecosystems.md`). A manifest without a lockfile is the first finding.
2. List what changed: `python sdd/tools/sdd.py scan deps --base <base>`.
3. Vulnerabilities: the ecosystem's audit tool, or OSV.dev with the exact locked versions. Classify by
   reachability (runtime or build-only, direct or transitive) × severity.
4. Health: last release, maintenance, declared but unused, pre-release versions in production, typosquatting, install scripts.
5. Record each one in the spec's dependency table: version, component, use, criticality, evaluation
   (method and date, for example `OSV.dev 2026-10-21`), result, and EVALUATED, PENDING or REJECTED.
6. Upgrades and removals are proposals; apply one only when the user names the package and version.

"No known vulnerabilities in this source today" is not "safe".
