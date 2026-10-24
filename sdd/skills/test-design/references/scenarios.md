# Deriving scenarios from a story

A story says what should happen; the scenarios are what can happen around it. They come from this
story's own elements and from the code it touches — not from a fixed list per kind of feature. Two
stories about "the same" feature produce different scenarios when their actors, rules or states differ.

## 1. Model the story

Read the story on the board and the code it touches, then list its elements. Short notes are enough.

| Element | What to write down |
|---|---|
| Actors and roles | Who acts; who else could act on the same thing; the roles that exist today |
| Data | Every field the story captures, shows or changes: type, format, limits, owner, classification |
| Rules | Each condition, calculation or limit the story states, and the ones the code already applies |
| States | What has a lifecycle (an account, a quote, a policy, a payment, a session, a code) and its transitions |
| Steps | The flow the user follows, screen by screen or call by call |
| Dependencies | Other modules, external providers, the device, the network |
| Before and after | What must already exist for the story to start, and what the user does next |
| Time | Expiries, waiting periods, schedules, dates and time zones |

## 2. Look at each element through the kinds

The kinds of the coverage table are lenses. Apply each one to the elements of *this* story; skip a
kind only with a reason that holds for this story.

| Kind | Applied to the model |
|---|---|
| Main flow | The steps with valid data, end to end, and what is stored, shown or sent |
| Alternate flows | Each optional step, each other path the rules allow, cancelling or editing before confirming |
| Invalid input and errors | Each field empty, of the wrong type or format, or too long; each dependency failing, slow or answering something unexpected |
| Limits and boundaries | Each rule and field limit just below, at and just above; zero, one and many; the last allowed attempt |
| Related flows before and after | Each precondition missing or changed; each next step still consistent after this change |
| Several users, sessions, devices or roles | Each actor against another actor's data; the same user twice at once; each role; a role changed mid-flow |
| State and time | Each allowed and forbidden transition; each expiry; interruption, retry, double submission, going back, offline |

## 3. Sharpen with test design techniques

| Technique | Use it when |
|---|---|
| Equivalence classes | A field accepts many values that behave the same: one value per class, valid and each kind of invalid |
| Boundary values | There is a limit: below, at and above it |
| Decision tables | A rule combines conditions: one column per combination that changes the result |
| State transitions | Something has a lifecycle: every allowed transition and the forbidden ones that matter |
| Pairs | Many options combine: cover every pair instead of every combination |
| Error guessing | The area has history: past bugs, incidents and review findings in the same code |

## 4. Decide each scenario

- **In scope** — it gets a test case and is implemented, even when the story does not say it. If the
  story does not state the behavior, add a `DERIVED: <why>` acceptance criterion to `spec.md`, for
  example *the story does not say how an expired code is answered*.
- **Out of scope** — `OUT OF SCOPE: <why>`: behavior that exists and is already tested, another story on
  the board, or a product owner's decision.
- **Unclear** — ask the product owner before the spec is READY, and record the answer as a criterion or as
  out of scope.

Stories live on the board: read them, never create or edit them.

## Illustration

Story: *as an advisor, I issue a policy from an accepted quote*.

- **Model:** the advisor and the insured; the quote (accepted or expired) and the policy (issued); a
  payment dependency; issuance must happen once per quote.
- **Lenses and scenarios:**
  - State and time: the quote expires between acceptance and issuance → DERIVED criterion and a test.
  - Several users: two advisors issue from the same quote at once → one policy, a test with concurrent requests.
  - Errors: the payment provider times out → no policy without a confirmed payment.
  - Related flows: the insured withdraws consent before issuance → OUT OF SCOPE if another story on the
    board covers withdrawal.

Another story yields other elements, and so other scenarios.
