---
name: design
description: Write the Design section of a spec — components, data flows, the data contract, security design decisions and configuration. Use after Requirements are agreed and before Tasks.
---

# Design

Write `## 2. Design` of the active spec.

1. **Components** created or changed: modules, services, screens, tables — in the folders and files the
   accepted structure ADRs (`docs/adr/`) give. A new folder, layer or pattern needs an ADR first.
2. **Data flows**, with a mermaid diagram when it helps, marking where data crosses a trust boundary.
3. **Data contract**, before any handler or screen, for each operation:
   - method and path, and the operation name
   - request and response fields with types, lengths, formats and required flags
   - the classification of each field, matching `security.md`
   - validation rules and the generic error the client sees
   - status codes, including 401, 403, the 404 for out-of-scope resources, 409, 422 and 429 where they apply
   - the permission and the ownership or tenant scope enforced on the server
   - idempotency for operations that can be retried
   A field without a purpose is removed. Generated clients are regenerated, never edited by hand.
4. **Security design decisions**: each cites the controls (CTL) or mechanisms (CRY) it implements and the
   alternative rejected.
5. **Architecture decisions**: run `adr` when the ADR gate applies; otherwise `N/A: <rationale>`.
6. **Configuration and deployment**: variables, secure defaults, differences between environments.
7. **Screens**, when there is a user interface: each screen with its states (loading, empty, error,
   success), the components it reuses and its accessibility notes, following `ui-ux` and `accessibility`.

Stop for agreement before writing Tasks.
