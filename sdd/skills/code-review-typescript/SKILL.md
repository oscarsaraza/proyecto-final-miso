---
name: code-review-typescript
description: TypeScript and Angular conventions and review checklist — strict typing, standalone components, signals, zoneless change detection, control flow, services and HTTP, forms, styles with design tokens and Vitest component tests. Use when writing or reviewing TypeScript, Angular templates or styles.
---

# TypeScript and Angular — conventions and review

Applies to `*.ts`, Angular templates and component styles. Follow it when writing; when reviewing,
`code-review` gives the process and this skill gives what to check. Secure patterns are in
`secure-coding-typescript`; screens also follow `ui-ux` and `accessibility`.

References: Angular style guide (https://angular.dev/style-guide), TypeScript handbook.

## TypeScript

- New code compiles as if `strict` were on: no implicit `any`, no unchecked `null`. No `any`; use
  `unknown` and narrow. No non-null assertions (`!`) to silence the compiler.
- Interfaces or types for every DTO, mirroring the API contract field by field; enums or union literals
  for closed sets.
- `const` by default; `readonly` for injected services, inputs and signals that are not reassigned.
- Format with the project's Prettier configuration; adding a linter is a dependency change (`dependency-review`).

## Components

- Standalone components; no NgModules.
- State in signals: `signal`, `computed`, `linkedSignal` for state that resets from an input; inputs and
  outputs with `input()`, `input.required()`, `output()` and `model()`.
- The app is zoneless: state that the template reads changes only through signals, never by mutating
  plain fields and waiting for change detection. Keep OnPush change detection: it is the default from
  Angular 22; never set `ChangeDetectionStrategy.Eager` (or the older `Default`).
- Built-in control flow: `@if`, `@for (…; track item.id)`, `@switch`, `@defer`; not `*ngIf`/`*ngFor`.
- `inject()` for dependencies. Members used only by the template are `protected`.
- Components show and collect data; rules, HTTP and mapping live in services.
- Feature routes are lazy (`loadComponent` or `loadChildren`) and have a `title`.

## Services and HTTP

- `providedIn: 'root'` services that return typed `Observable<T>` from `HttpClient`; the base URL comes
  from the injection token, never a hard-coded host.
- One subscription per user action; no nested `subscribe` (use `switchMap`, `concatMap`, `exhaustMap`
  for double-submit). Long-lived streams end with `takeUntilDestroyed()` or become signals with `toSignal()`.
- Errors become user messages in one place (the shared HTTP error helper); no silent `catchError(() => EMPTY)`
  that leaves the screen without feedback.

## Forms

- Follow the approach the forms ADR sets and the feature already uses; do not mix two approaches in one
  form. Angular 22 also ships signal-based forms (`@angular/forms/signals`); adopting them is an ADR decision.
- Every field has a label, its constraints (`required`, `maxlength`, `pattern`) match the backend's, and
  its error message is shown next to it (see `accessibility`). Client validation is a convenience; the
  server validates again.

## Styles

- Colors, type, spacing and radii come from the design tokens (`var(--…)` in the global styles); no new
  hard-coded hex values or `style="…"` attributes.
- Component styles stay within the component budget; shared patterns move to the global styles.

## Tests (Vitest with the Angular test builder)

- `TestBed` with `provideZonelessChangeDetection()`; HTTP through `provideHttpClientTesting()` and
  `HttpTestingController`, with `verify()` after each test.
- Query the DOM the way a user perceives it — role, label, text — or `data-testid`, not CSS structure.
- Test behavior: what the user sees after an action, the request sent, the error shown.

## Review checklist

- [ ] No `any`, no `!`, DTOs typed and matching the contract.
- [ ] State in signals; no `Eager` change detection; built-in control flow with `track`.
- [ ] No business logic or HTTP in components; no nested subscriptions; streams cleaned up.
- [ ] Every error path gives the user feedback; double submit prevented.
- [ ] Styles from tokens; no inline styles; no new hard-coded colors.
- [ ] Lazy feature routes with titles.
- [ ] Tests assert user-visible behavior and the HTTP contract.

## In this repository

- Architecture: ADRs [0008](../../../docs/adr/0008-web-components-and-signals.md) (components and signals),
  [0009](../../../docs/adr/0009-web-feature-structure.md) (folders: `core/`, `features/`, `shared/ui/`),
  [0010](../../../docs/adr/0010-web-http-and-session.md) (HTTP and session),
  [0011](../../../docs/adr/0011-web-forms.md) (forms) and [0012](../../../docs/adr/0012-web-styles-and-design-tokens.md)
  (styles). Check new code against them. The API base URL is the `API_BASE_URL` token
  (default `/api/v1`); errors go through `core/utils/http-error.ts`.
- Zoneless (`provideZonelessChangeDetection()` in `app.config.ts`); forms are template-driven with
  signals; money is formatted with `Intl.NumberFormat('es-CO', …)` in `core/money.ts`.
- Design tokens in `web/src/styles.css`, taken from `prototipos/web`.
- `tsconfig.json` does not enable `strict`; Prettier is configured (`printWidth` 100, single quotes); no
  ESLint. Test names are in Spanish and cite the story or test case ID.
- Commands: `cd web && npm test -- --watch=false` and `npm run build`.
