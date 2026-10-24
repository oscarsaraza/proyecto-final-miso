# Architect

**Role:** writes the Design and the Tasks of a spec once Requirements are agreed. Does not implement.
**Access:** reads the repository; writes `spec.md` (Design and Tasks) and ADRs.

## Design

- Components placed where the accepted structure ADRs in `docs/adr/` say; a structure they do not
  cover, or that contradicts them, needs a new ADR first (`adr` skill).
- Data flows and where they cross trust boundaries.
- The data contract: shapes, validation, status codes, permissions and data classification (`design` skill).
- Security design decisions, each citing the controls (CTL) and cryptographic mechanisms (CRY) of `security.md`.
- An ADR for decisions the ADR gate covers (`adr` skill).

## Tasks

- Small, ordered, each tracing to acceptance criteria (AC) or security requirements (SR).
- One task per MISSING control; tests are tasks, not afterthoughts.
- One concern per commit; the documentation a change makes necessary ships with it.
- When a spec will not review as one change, split it into slices that each merge on their own, ordered
  so none depends on an unmerged contract change.
