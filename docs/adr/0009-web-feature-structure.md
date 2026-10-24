# ADR 0009 · Web: feature-based structure with a container per flow

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-10-22 |
| Story | none |
| Deciders | The team (to be confirmed) |

## Context

ADRs 0008, 0010, 0011 and 0012 cover the component model, HTTP and session, forms and styles. This one
covers where code lives. `web/src/app` today:

- `core/` has a service folder per backend domain (`auth`, `catalogs`, `client`, `consent`, `payments`,
  `policies`, `quotes`), DTO interfaces in `core/models/*.model.ts`, plus `guards/`, `interceptors/` and
  `utils/`. `core/money.ts` sits at the root of `core/`.
- `features/auth/login.component.ts` is the sign-in screen. `features/cotizador/` has the container
  `cotizador.component.ts` and one subfolder per part: `client-data-step`, `consent-step`,
  `payment-step`, `premium-breakdown`.
- The container holds the flow in signals (current step, client, risk, consent, quote, emission). Steps
  call `core` services for their own data (catalogs, client validation, consent, payment) and report
  with `output()`. No step injects `Router`.
- Templates and styles are inline in all six feature components. `client-data-step` has 776 lines (a
  template of about 330), `consent-step` 551 (about 220), `cotizador` 397.
- `app.routes.ts` imports both screens eagerly; no route has a `title`. There is no `shared/` folder.
- Components, services, the guard, the interceptor and `http-error.ts` have their spec beside them,
  except `core/money.ts` and the payment and policy services.

## Options considered

| Option | Pros | Cons |
|---|---|---|
| A. Feature folders; a container per flow with its parts beside it | Matches the code; one place per flow; parts tested alone | Needs discipline on container size and on what goes to `shared/` |
| B. Feature folders; one route per step, flow state in a service | Deep links and back button per step | Flow data must outlive each route, in a service or storage; guards to stop skipped steps |
| C. Folders by type (`components/`, `services/`, `models/`) | Familiar | A feature is scattered across folders; grows poorly |

## Decision

Option A.

```
web/src/app/
  app.config.ts, app.routes.ts, app.component.*  bootstrap, providers, top-level routes
  core/                                          singletons, no UI
    <domain>/<domain>.service.ts                 HTTP for one backend domain
    models/<domain>.model.ts                     DTO interfaces mirroring the API
    auth/  guards/  interceptors/  utils/        cross-cutting concerns
  shared/ui/<component>/                         presentational components used by two or more features
  features/<feature>/
    <feature>.routes.ts                          the feature's lazy routes, each with a title
    <feature>.component.ts                       container: flow state, data between steps, navigation
    <part>/<part>.component.ts                   a step or section of the flow
```

Rules:

1. `core/` has no components. Code that is not a service, model, guard or interceptor goes in `utils/`.
2. The container owns the flow: the current step, the data passed between steps and the navigation.
3. A part owns its form, may call `core` services for its own data, reports with `output()` and never
   navigates.
4. A component moves to `shared/ui/` only when a second feature needs it.
5. `app.routes.ts` loads each feature's routes lazily; every route that shows a screen has a `title`.
6. A template stays inline while it is under about 150 lines; past that, `.html` and `.css` go beside
   the `.ts`. A component over about 400 lines is split into parts.
7. File names in kebab-case with their type suffix (`.component.ts`, `.service.ts`, `.model.ts`,
   `.guard.ts`, `.interceptor.ts`), with the spec beside the file.

## Consequences

- Easier: new screens land in a known place; reviews check one folder per flow; parts stay small.
- Harder: a step that grows needs splitting before it passes the limits.
- Migration when next touched, not all at once:
  - `client-data-step`: template and styles to files; split into parts, for example its two fieldsets
    (holder data, credit and risk data).
  - `consent-step`: template and styles to files; split if it still passes 400 lines.
  - Add `features/cotizador/cotizador.routes.ts` and `features/auth` routes, lazy and with titles.
  - Move `core/money.ts` to `core/utils/`; add specs for the payment and policy services.

## Security and privacy impact

Flow data (client identity, contact details, loan amount) lives in the container's signals, in memory,
and is gone when the advisor leaves the flow or reloads. Option B would have kept it in a service or in
storage. Lazy loading
is not access control: every chunk is public, guards only hide screens and the backend authorizes each
call. HTTP stays in `core`, so a review of backend access covers `core` alone.
