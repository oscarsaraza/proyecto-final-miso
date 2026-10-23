# HU-FIX-02 · Help text on the home screen

| Field | Value |
|---|---|
| ID | HU-FIX-02 |
| Title | Help text on the home screen |
| User story | none (fictitious scenario for the validator tests) |
| Owner | Owner Person |
| Status | IN_REVIEW |
| Created | 2026-10-20 |
| Security profile | LOW |

## 1. Requirements

### User story

**HU-FIX-02 · Texto de ayuda.** Como asegurado quiero ver un texto de ayuda en el inicio.

### Problem and outcome

Clarify the help text on the home screen.

### Goals and non-goals

Only a static text changes.

### Affected paths

| Path | Change |
|---|---|
| app/src/main/res/values/strings.xml | Help text |

### Use cases

| ID | Actor | Use case | Main flow | Alternate flows |
|---|---|---|---|---|
| UC-01 | Insured | Read the help | Opens the screen and reads the text | None |

### Abuse cases

N/A: a static text offers no input to an attacker.

### Acceptance criteria

| ID | Criterion | Source |
|---|---|---|
| AC-01 | WHEN the home screen opens, THE app SHALL show the new help text | STATED |

### Quality requirements

N/A: static text in an existing screen; it inherits that screen's performance and accessibility checks.

### Security triggers

| Trigger | Applies | Rationale |
|---|---|---|
| Personal data (identifies or can identify a person) | NO | Static text |
| Sensitive data (special categories, biometrics, health, financial, minors) | NO | Static text |
| Authentication, sessions, credentials or one-time codes | NO | Unchanged |
| Authorization or access to other users' resources | NO | Unchanged |
| Payments or money movement | NO | Unchanged |
| Third-party services or integrations | NO | Unchanged |
| Infrastructure, network, IAM, CI/CD or secrets | NO | Unchanged |
| Multiple tenants, partners or organizations | NO | Unchanged |
| Storage or processing on a mobile device | NO | Stores nothing |
| Web UI or data exposed in the browser | NO | Unchanged |
| New or updated dependencies | NO | Unchanged |
| Critical paths (sdd/security/critical-paths.md) | NO | strings.xml is not in the registry |

### Security requirements

| ID | Requirement | Source | Controls | Priority |
|---|---|---|---|---|

## 2. Design

### Components

Text resource of the home screen.

### Data flows

No new data flows.

### Data contract

N/A: no request or response shape changes.

### Security design decisions

The text contains no personal or internal information.

### Architecture decisions

N/A: no architectural decision is introduced.

### Configuration and deployment

None.

## 3. Tasks

| ID | Task | Traces to | Controls | Status | Evidence |
|---|---|---|---|---|---|
| T-01 | Change the help text | AC-01 | — | DONE | commit 1a2b3c4 |
