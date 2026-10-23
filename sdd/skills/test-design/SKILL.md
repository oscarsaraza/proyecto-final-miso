---
name: test-design
description: Derive the scenarios around a user story (alternatives, errors, limits, related flows, several users or devices, state and time) and design the spec's test cases — functional, quality and security — choosing the level of each (unit, integration, contract, end-to-end, performance, accessibility, static), mapping every acceptance criterion, quality requirement, security requirement and control to a test that fails on regression, and reviewing the fifteen security test categories. Use during spec-create and when writing or reviewing tests.
---

# Test design

The goal is catching regressions, not coverage numbers. Read `sdd/rules/testing.md`, the language skill
(`code-review-<language>` describes the project's runner and fixtures) and two or three neighboring tests
before writing new ones.

## 1. Derive the scenarios

A story says what should happen; the scenarios are everything that can happen around it, derived from
this story — not from a fixed list. Follow `references/scenarios.md`:

1. Model the story from the board and the code it touches: actors, data, rules, states, steps,
   dependencies, what comes before and after, and time.
2. Look at each element through the kinds of the coverage table and write each scenario in
   `## Scenarios` of `test-cases.md` as *Given…, when…, then…*, citing the use case or criterion it comes from.
3. Give each a disposition: the test case that covers it, or `OUT OF SCOPE: <why, or the story that
   covers it>`. Never drop a scenario silently.
4. A scenario in scope that the story does not state becomes a `DERIVED: <why>` acceptance criterion in
   `spec.md`, and is implemented. An unclear one goes to the product owner before the spec is READY.
5. Fill `## Scenario coverage`: each kind YES with its scenarios or NO with a reason that holds for this
   story. Authentication requires related flows and state and time; authorization or tenants require
   several users.

Then, for each acceptance criterion (AC), quality requirement (QR) and security requirement (SR), add
what the scenarios did not cover: every reachable branch, idempotency, concurrency and the bug being
fixed.

## 2. Choose the level

Use the cheapest level that can observe the behavior. Many unit tests, fewer integration tests, few
end-to-end journeys.

| Level | Proves | Typical tools | Use for |
|---|---|---|---|
| UNIT | One unit's logic, isolated from I/O | pytest, Vitest, JUnit with coroutine test dispatchers | Business rules, validators, calculations, mappers, view model state |
| INTEGRATION | A unit with its real collaborators: database, HTTP layer, framework | pytest with a real database and an in-process HTTP client; Angular TestBed with the HTTP testing controller; Robolectric with a mock web server | Authorization per resource, queries, transactions, error mapping, serialization, interceptors |
| CONTRACT | The API shape producer and consumers agree on: status codes, fields, types, errors | Schema or response-model assertions on the producer; consumer fixtures checked against the schema | Any change to an endpoint used by the web or mobile client |
| E2E | A user journey through the running system | Browser automation for the web; instrumented UI tests on a device or emulator for mobile; numbered manual steps otherwise | The few critical journeys: sign in, quote, pay, issue |
| PERFORMANCE | Latency, throughput and behavior under load | A load-testing tool driven by a script under version control | Every PERFORMANCE quality requirement; hot paths |
| ACCESSIBILITY | WCAG 2.2 AA on the web, Android accessibility guidelines on mobile | Automated rule checks, semantics assertions, keyboard and screen reader passes | Every screen or component that changes (see `accessibility`) |
| STATIC | Properties visible without running the code | `python sdd/tools/sdd.py scan secrets`, dependency audits, linters, `terraform validate`, configuration review | Secrets, dependencies, insecure configuration |

A new tool is a new dependency: evaluate it with `dependency-review` before adding it.

## 3. Performance tests

Write the thresholds before the run, from the quality requirement: p95 and p99 latency, error rate and
throughput, under stated conditions (data volume, concurrency, duration).

| Kind | Shape | Answers |
|---|---|---|
| Load | Ramp to the expected peak and hold | Does it meet the requirement at the expected peak? |
| Stress | Keep increasing past the peak until it degrades | Where does it break, and does it fail safely (429 or 503, not 500; no corrupt or duplicated data) and recover when the load drops? |
| Spike | A sudden burst from normal load | Do rate limits, queues and scaling absorb it? |
| Soak | Normal load for hours | Leaks, connection pool exhaustion, growing queues or disks? |

Run them only in an isolated environment sized like the target or with the scaling stated, with
fictitious data and every third party stubbed (SMS, payments, external bureaus). Never against
production, shared environments or a third party without written authorization. Warm up first, repeat
the run, and record the environment, data volume, script version and results as evidence.

## 4. Review the security categories

| Category | Typical test |
|---|---|
| Unauthenticated user | No token or a malformed one: 401 |
| User without permissions | A token of another role: 403 |
| Access to another user's resources | Change the resource identifier: 404, no data |
| Cross-tenant access | Tenant A's credential on tenant B's resources |
| Malicious input | Extreme sizes, wrong types, forged headers, injection payloads |
| Expired tokens | Expired or wrongly signed token: 401 |
| Revoked sessions | Revoked refresh token; an access token issued before a password change |
| Tampered data | Modified ciphertext or signature fails verification |
| Wrong keys | A wrong or invalidated key fails safely |
| External service failures | Provider down or slow: no partial effects, generic message |
| Race conditions | Concurrent requests do not duplicate charges, codes or records |
| Information exposure | Errors, logs and responses carry nothing extra; no account enumeration |
| Secrets in code | `python sdd/tools/sdd.py scan secrets --diff <base>` is clean |
| Insecure configuration | Defaults, debug modes, CORS, documentation endpoints, headers, TLS |
| Vulnerable dependencies | OSV.dev or the ecosystem's audit tool |

YES needs test cases; NO needs a rationale. Most of these are INTEGRATION tests; the last three are STATIC.

## 5. Write each test case

A `### TC-NN · name` block with: Covers (AC, QR, SR), Kind (FUNCTIONAL, QUALITY or SECURITY), Risk
covered (THR or RISK for security), Level, Preconditions, Procedure (numbered and reproducible), Expected
result, Tool or method (`path::test_name`, or `path::"test name"` when the name has spaces), Automation,
Environment, Evidence and Status.

## 6. Run and record

Write the automated tests in the project's runner and record `PASS` only with evidence from a run.
Platform behavior (keystore, biometrics, TLS) needs a device or a deployed test environment — a fake
proves the logic, not the platform. Fixtures are fictitious and fake secrets are built at runtime.
