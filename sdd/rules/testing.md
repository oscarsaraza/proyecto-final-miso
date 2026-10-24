# Testing rules

> Testing rules and thresholds. Load when writing or reviewing tests. Paths: `**/tests/**`, `**/test/**`, `**/*.spec.*`, `**/*.test.*`, `**/test_*.py`, `**/*Test.kt`.

- Follow the project's existing test conventions (runner, layout, naming, fixtures). Read two or three
  neighboring tests before writing one.
- Every acceptance criterion, quality requirement and security requirement has a test that fails if the
  behavior regresses, at the cheapest level that can observe it: UNIT, INTEGRATION, CONTRACT, E2E,
  PERFORMANCE, ACCESSIBILITY or STATIC (the `test-design` skill says when to use each).
- Many unit tests, fewer integration tests, few end-to-end journeys. An end-to-end test does not
  replace the unit and integration tests of the rules it crosses.
- Security tests are negative tests: another user's resource, missing permission, expired or tampered
  token, malicious input, wrong key, failing dependency, concurrent requests.
- Test data is fictitious. Never real personal data or real secrets; build fake secrets at runtime.
- A test that only asserts a mock of the unit under test does not count.
- Do not lower a coverage threshold or delete an assertion to make a pipeline green.
- Performance, stress and dynamic security tests run only in an isolated environment, with fictitious
  data, third parties stubbed and thresholds written before the run. Never against production, shared
  environments or third parties without written authorization.
- Automated accessibility checks find only part of the problems; an ACCESSIBILITY test case includes a
  keyboard and screen reader pass.
- Green tests are not a substitute for exercising the change in the running application.

Project thresholds and commands are in the project section of `AGENTS.md`.
