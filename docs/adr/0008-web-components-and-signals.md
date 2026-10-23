# ADR 0008 · Web: standalone components, signals and zoneless change detection

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-10-22 |
| Story | none |
| Deciders | The team (to be confirmed) |

## Context

The advisors' portal runs Angular 22.2.1 (`web/node_modules/@angular/core/package.json`). Today:

- `web/src/app/app.config.ts` calls `provideZonelessChangeDetection()`. `zone.js` is not in
  `web/package.json`.
- The seven components are standalone. There are no NgModules and no constructor injection; every
  dependency comes from `inject()`.
- Component state uses `signal`, `computed` and `linkedSignal`. Inputs and outputs use `input()`,
  `input.required()` and `output()`. The only shared state is the session signal in
  `core/auth/auth.service.ts`, exposed with `asReadonly()`.
- RxJS appears only around `HttpClient`. Services return Observables and components call `.subscribe()`
  eight times (login 1, client-data-step 3, consent-step 1, cotizador 2, payment-step 1). None ends with
  `takeUntilDestroyed()`, and `toSignal()` is not used.
- No component sets `changeDetection`. In the installed core, OnPush is the default: the typings say
  "OnPush is enabled by default", and the runtime marks a component OnPush unless its strategy is
  `Eager` (`@angular/core/fesm2022/_debug_node-chunk.mjs`).
- Templates use `@if` and `@for` with `track`, except two legacy `*ngIf`: `app.component.html` line 8
  and `features/auth/login.component.ts` line 20.
- There is no state-management library.

## Options considered

| Option | Pros | Cons |
|---|---|---|
| A. Signals with zoneless change detection | Matches the code; no `zone.js`; a view updates when a signal it reads changes; no extra dependency | The boundary with RxJS must be explicit; mutating an object inside a signal does not notify |
| B. `zone.js` with RxJS-based state (`BehaviorSubject`, `async` pipe) | Familiar and widely documented | Adds `zone.js` back; rewrites working code; two reactivity models |
| C. A store library (NgRx) | One store, devtools, strict data flow | New dependency and boilerplate for one flow and one shared value, the session |

## Decision

Option A.

1. Standalone components only; no NgModules.
2. Component state in `signal`, `computed` and `linkedSignal`. Inputs with `input()` or
   `input.required()`, outputs with `output()`; no `@Input` or `@Output` decorators.
3. Shared state is a signal held by a `core` service. Only that service writes it; the rest read it
   through `asReadonly()`, as with the session.
4. RxJS only for HTTP and event streams. A subscription in a component ends with
   `takeUntilDestroyed()` or becomes a signal with `toSignal()`.
5. `OnPush` on every component. In the installed Angular it is the default when `changeDetection` is
   not set, so no component sets `ChangeDetectionStrategy.Eager` or the deprecated `Default`.
6. Built-in control flow: `@if`, `@for` with `track`, `@switch`. No `*ngIf` or `*ngFor`.
7. Dependencies through `inject()`.
8. No state-management library without a new ADR.

## Consequences

- Easier: one reactivity model; no `zone.js` patching; state is visible as fields of the component or
  of one `core` service.
- Harder: an object inside a signal changes only through `set` or `update` with a new value. A library
  that expects `zone.js` must be checked before it is added.
- Migration when next touched, not all at once:
  - Replace the two `*ngIf` with `@if`.
  - End the eight subscriptions with `takeUntilDestroyed()`, or turn read-only loads such as the two
    catalog requests in `client-data-step`'s `ngOnInit` into `toSignal()`.
  - Nothing to do for `OnPush`: the components already run with it.

## Security and privacy impact

No data, keys or trust boundaries change. Template escaping and sanitization work the same with
`OnPush` and without `zone.js`. The only shared state is the session, owned by `core/auth`; where it is
stored is decided in ADR 0010. Ending a subscription with its component also cancels an HTTP request
still in flight, so a late response does not update a screen the advisor has already left.
