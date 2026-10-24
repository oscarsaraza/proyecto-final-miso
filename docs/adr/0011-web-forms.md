# ADR 0011 · Web: template-driven forms bound to signals

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-10-22 |
| Story | none |
| Deciders | The team (to be confirmed) |

## Context

The portal has three forms: sign-in (`features/auth/login.component.ts`), client data
(`client-data-step`) and consent (`consent-step`). `payment-step` uses radio buttons without
`FormsModule`.

- The two steps import `FormsModule` and bind `[ngModel]` with `(ngModelChange)` into signals
  (`linkedSignal` when an input seeds the value). Validity is computed (`isFormValid`, `isOtpValid`).
  Sign-in differs: plain fields with `[(ngModel)]` and validity from `loginForm.valid`.
- The web repeats the backend's lengths and patterns (`backend/app/modules/profile/models.py`):
  document 5–20, names at least 2, OTP of six digits. The insurable age of 18–75 is checked on both
  sides (`profile/service.py`). The web also requires a phone of at least 7 characters and an `@` in
  the email, which the backend schema does not check.
- Errors appear in one banner per form (`role="alert"`). Only the birth date has a message under the
  field. No element in `web/src` uses `aria-describedby` or `aria-invalid`.
- `client-data-step` disables submit while `isFormValid()` is false, so the specific messages built in
  `onSubmit()` (lines 721–735) never show after a click: the advisor sees a dimmed button and no reason.
  The `disabled` attribute also takes the button out of the tab order.
- For a 422, `core/utils/http-error.ts` joins FastAPI's `detail` items into one `loc: msg` string for
  the banner, with API field names such as `document_number`.
- The installed `@angular/forms` 22.2.1 ships `@angular/forms/signals` (Signal Forms). Its `form()`
  and `FormField` are marked `@publicApi 22.0` in the typings (`types/_structure-chunk.d.ts`). No code
  uses it.

## Options considered

| Option | Pros | Cons |
|---|---|---|
| A. Template-driven forms with values in signals and computed validity | Matches the step forms; one source of truth (the signals); small | Validity and error wiring are written by hand |
| B. Reactive forms (`FormGroup`, `Validators`) | Mature; built-in validators and control status | Rewrites three forms; Observable-based value stream beside the signals |
| C. Signal Forms (`@angular/forms/signals`) | The model is a signal; schema validators; field state as signals | Rewrites three forms; not used in this codebase yet |

## Decision

Option A.

1. `FormsModule` with `[ngModel]` and `(ngModelChange)` writing into signals; no `[(ngModel)]` on
   plain fields.
2. Validity lives in computed signals: one per field rule and one for the form.
3. Constraints mirror the backend schema. When the web needs a stricter rule, the backend gets it too.
4. Each field shows its own error under it, linked with `aria-describedby`, and sets `aria-invalid`
   when invalid. The banner is kept only for errors that belong to no field.
5. Submit is blocked while a request is pending and stays focusable (`aria-disabled`, click ignored).
   Invalid input does not disable it: submitting shows the field errors.
6. Server field errors (422 with `loc`) go to the matching field when the API returns them.
7. Moving to Signal Forms needs a new ADR, reviewed before the next new form.

## Consequences

- Easier: no rewrite; errors next to the field are readable by screen readers.
- Harder: field error wiring repeats across forms until a field component exists in `shared/ui/`.
- Migration when next touched: sign-in fields to signals; per-field messages and a focusable submit in
  `client-data-step` and `consent-step`; `http-error.ts` also returns errors by field.

## Security and privacy impact

Client checks are a convenience; the backend decides. The phone and email checks exist only in the web
today, a gap tracked for its own spec. The TOTP and OTP codes stay in component state and are never
echoed in a message. `http-error.ts` builds 422 messages from `loc` and `msg`, but falls back to the
whole item as JSON when `msg` is missing; mapping errors to fields must keep to `loc` and `msg`. Field
messages and ARIA attributes add no data.
