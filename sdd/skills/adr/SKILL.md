---
name: adr
description: Record an architecture decision in docs/adr — including structure decisions that fix the folders and files of a layer — following the ADR writing rules. Use when the ADR gate applies (base images, infrastructure security, authentication, keys, security-relevant SDKs), for a new layer, module, pattern or shaping dependency, or when code needs a structure the accepted ADRs do not give.
---

# Architecture decision record

1. Read the index `docs/adr/README.md` and the accepted ADRs of the layer. If one already decides the
   question, follow it; if the change contradicts it, the new ADR supersedes it explicitly.
2. Copy `sdd/templates/adr.md` to `docs/adr/NNNN-<slug>.md` with the next free number. Never renumber.
3. Write one decision, readable in five minutes:
   - **Context:** what exists today (read the code, cite paths), the forces and the problems.
   - **Options considered:** at least two real alternatives with pros and cons.
   - **Decision:** what is chosen. A structure decision includes the folder and file layout as a tree, what
     goes in each file, and numbered rules (dependency direction, size limits, when to split). No new
     layers or folders "for later".
   - **Consequences:** what becomes easier and harder, and the migration: at once or when touched.
   - **Security and privacy impact:** data, keys, trust boundaries and threats added, removed or changed.
4. Add it to the index with status `Proposed`, link it from the spec's `### Architecture decisions`, and
   ship it in the same change as the code it governs.

The team accepts, supersedes or deprecates ADRs, with names and date; agents draft only. An accepted ADR
is not edited — a new one supersedes it. A waiver of the ADR gate is `ADR-EXEMPT: <reason>` in the commit
message, only when the user accepts it.
