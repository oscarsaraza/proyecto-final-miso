# {{ID}} · {{TITLE}}

| Field | Value |
|---|---|
| ID | {{ID}} |
| Title | {{TITLE}} |
| User story | <fill: link to the story on the board> |
| Owner | <fill: person accountable for this spec> |
| Status | DRAFT |
| Created | {{DATE}} |
| Security profile | <fill: LOW, MEDIUM, HIGH or CRITICAL> |

<!-- A spec is a contract: what, why, how, and how we will know it is done. Fill the sections in
     order and stop for agreement between them: Requirements → Design → Tasks.
     Status: DRAFT → READY (after spec-review) → IN_PROGRESS → IN_REVIEW → DONE | BLOCKED. -->

## 1. Requirements

### User story

<!-- The story exactly as it is on the board: title, description and its acceptance criteria. Agents read
     stories from the board and never create or edit them. For a hotfix, the incident report. -->

<fill: the story as written on the board>

### Problem and outcome

<fill: the problem, who it is for, and the observable outcome>

### Goals and non-goals

<fill: goals; explicit non-goals>

### Affected paths

<!-- Files or globs this change touches. If any matches sdd/security/critical-paths.md, the critical
     paths trigger is YES and the profile is at least the one listed there. -->

| Path | Change |
|---|---|
| <fill: path or glob> | <fill: what changes> |

### Use cases

| ID | Actor | Use case | Main flow | Alternate flows |
|---|---|---|---|---|
| UC-01 | <fill> | <fill> | <fill: 1. … 2. …> | <fill: errors and alternatives> |

### Abuse cases

<!-- How a malicious actor or a misuse would try to break each use case. Every abuse case materializes a
     threat (THR) and has a test case (TC). Only a LOW profile may write: N/A: <rationale>. -->

| ID | Abuse case | Actor | Threat | Expected response | Test case |
|---|---|---|---|---|---|
| AB-01 | <fill> | <fill> | <fill: THR-NN> | <fill> | <fill: TC-NN> |

### Acceptance criteria

<!-- Testable, EARS style: WHEN/IF/WHILE <trigger>, THE <system> SHALL <response>.
     Source: STATED when the story says it; DERIVED: <why> when the story does not say it but the
     feature needs it (validations, errors, limits, related flows, several users, security,
     accessibility). Every criterion is covered by at least one test case in test-cases.md. -->

| ID | Criterion | Source |
|---|---|---|
| AC-01 | <fill: WHEN …, THE … SHALL …> | <fill: STATED or DERIVED: why> |

### Quality requirements

<!-- Measurable non-functional requirements. Category: PERFORMANCE (latency, throughput, load, stress),
     AVAILABILITY, ACCESSIBILITY (WCAG level or platform guidelines), USABILITY, COMPATIBILITY or
     MAINTAINABILITY. Each one is covered by a test case: PERFORMANCE by a PERFORMANCE test and
     ACCESSIBILITY by an ACCESSIBILITY test. When none applies write: N/A: <rationale>. -->

| ID | Category | Requirement | Target and conditions |
|---|---|---|---|
| QR-01 | <fill> | <fill> | <fill: e.g. p95 under 300 ms at 50 requests/s for 10 minutes; WCAG 2.2 AA> |

### Security triggers

<!-- YES or NO, with a rationale. The validator derives the minimum profile:
     HIGH for authentication, authorization, payments, sensitive data, infrastructure, multi-tenancy or critical paths;
     MEDIUM for personal data, third parties, mobile, web or dependencies; LOW otherwise.
     CRITICAL is a human decision and requires two security reviews. -->

| Trigger | Applies | Rationale |
|---|---|---|
| Personal data (identifies or can identify a person) | <fill: YES or NO> | <fill> |
| Sensitive data (special categories, biometrics, health, financial, minors) | <fill: YES or NO> | <fill> |
| Authentication, sessions, credentials or one-time codes | <fill: YES or NO> | <fill> |
| Authorization or access to other users' resources | <fill: YES or NO> | <fill> |
| Payments or money movement | <fill: YES or NO> | <fill> |
| Third-party services or integrations | <fill: YES or NO> | <fill> |
| Infrastructure, network, IAM, CI/CD or secrets | <fill: YES or NO> | <fill> |
| Multiple tenants, partners or organizations | <fill: YES or NO> | <fill> |
| Storage or processing on a mobile device | <fill: YES or NO> | <fill> |
| Web UI or data exposed in the browser | <fill: YES or NO> | <fill> |
| New or updated dependencies | <fill: YES or NO> | <fill> |
| Critical paths (sdd/security/critical-paths.md) | <fill: YES or NO> | <fill> |

### Security requirements

<!-- Each SR comes from data (DATA), a threat (THR) or a risk (RISK) in security.md,
     is mitigated by controls (CTL) and verified by at least one security test case (TC). -->

| ID | Requirement | Source | Controls | Priority |
|---|---|---|---|---|
| SR-01 | <fill: verifiable requirement> | <fill: DATA-NN, THR-NN> | <fill: CTL-NN> | <fill: HIGH, MEDIUM or LOW> |

## 2. Design

### Components

<fill: modules, services, screens and tables created or changed>

### Data flows

<!-- Describe or diagram (mermaid) how data moves and where it crosses a trust boundary. -->

<fill>

### Data contract

<!-- Request and response shapes, validation, status codes and ownership, pinned before building.
     N/A: <rationale> when no shape changes. -->

<fill>

### Security design decisions

| Decision | Implements | Rejected alternative and why |
|---|---|---|
| <fill> | <fill: CTL-NN, CRY-NN> | <fill> |

### Architecture decisions

<!-- ADRs this change needs (docs/adr/NNNN-title.md), or N/A: <rationale>. -->

N/A: <fill: rationale, or replace with a table ADR | Title | Status>

### Configuration and deployment

<fill: environment variables, secure defaults, differences between environments>

## 3. Tasks

<!-- Small, ordered, each tracing to acceptance criteria (AC) or security requirements (SR).
     Every MISSING control has a task. A DONE task cites evidence (commit, PR, path::test).
     While a functional task (with AC) is open the gate stays IN_PROGRESS. -->

| ID | Task | Traces to | Controls | Status | Evidence |
|---|---|---|---|---|---|
| T-01 | <fill> | <fill: AC-NN, SR-NN> | <fill: CTL-NN or —> | TODO | — |
