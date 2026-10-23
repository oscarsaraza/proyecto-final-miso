# ADR 0012 · Web: styles with design tokens and no component library

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-10-22 |
| Story | none |
| Deciders | The team (to be confirmed) |

## Context

- `web/src/styles.css` defines custom properties taken from `prototipos/web/styles.css`: a type scale
  (`--t-xs` to `--t-2xl`), neutrals (`--n-0` to `--n-900`), brand (`--marca-500` to `--marca-700`),
  aliases (`--fondo`, `--superficie`, `--texto`, `--texto-sec`, `--borde`, `--primario`) and the font.
  The prototype also has status colors, radii (`--r-*`), shadows (`--sombra-*`) and a transition, which
  were not copied. Neither file has spacing tokens.
- No component uses `var(--…)`. Component styles hard-code 151 hex colors, 40 distinct: `consent-step`
  37, `client-data-step` 31, `cotizador` 28, `login` 22, `premium-breakdown` 13, `app.component.css`
  13, `payment-step` 7. Most differ from the tokens: headings use `#0f172a` and secondary text
  `#64748b`, while `--texto` is `#1f2733` and `--texto-sec` is `#67748a`.
- `styles.css` has global `.notice` classes. `client-data-step` redefines `.notice` and `.notice-error`
  with other colors (lines 480–496); `cotizador` defines `.notice-info` locally (line 266). Five
  components each define their own primary button.
- `@keyframes spin` exists only in `client-data-step`. Angular scopes keyframe names per component, so
  the `spin` used by `cotizador`'s `.spinner-blue` (line 282) matches no keyframes.
- Inter is loaded twice from Google Fonts: a `<link>` in `web/src/index.html` (line 11) and an
  `@import` in `web/src/styles.css` (line 6).
- `web/package.json` has no component library or CSS framework. Prettier formats; there is no style
  linter. `angular.json` sets a component style budget of 4 kB (warning) and 8 kB (error).

## Options considered

| Option | Pros | Cons |
|---|---|---|
| A. Custom CSS with tokens in `styles.css` and global classes for shared patterns | Matches the prototype; no dependency; small CSS | Needs review discipline; accessible widgets are ours to build |
| B. A component library (Angular Material, PrimeNG) | Ready, tested components and theming | New dependency and bundle size; theme bent to the prototype; templates rewritten; upgrades tied to Angular majors |
| C. A utility-CSS framework (Tailwind) | Consistent scale from one config | Build setup; long class lists; a second token source |

## Decision

Option A.

1. The custom properties in `web/src/styles.css` are the single source of colors, type, spacing and
   radii. Missing tokens are added there first, starting with the prototype's.
2. Component styles use `var(--…)` only; no hex, `rgb()` or named colors.
3. Shared patterns are global classes in `styles.css`: notices, buttons, form fields and the spinner.
   Components do not redefine them.
4. No UI component library or CSS framework without a new ADR.
5. The font is loaded from one place.
6. Component styles stay within the `anyComponentStyle` budget in `angular.json`.

## Consequences

- Easier: a palette change touches one file; screens look the same.
- Harder: no tool blocks a hex color yet; reviewers check for them.
- Migration when next touched: replace a component's hex colors with tokens; drop the local `.notice`
  rules in `client-data-step`; move `.notice-info`, the spinner and the buttons to `styles.css`; remove
  one of the two font loads; turn the inline `style="margin-top: 24px;"` in `cotizador` (lines 68 and
  78) into a class.

## Security and privacy impact

Google Fonts receives the advisor's IP address and browser details whenever the font is fetched. The
stylesheet is not pinned and has no integrity attribute. Serving the font files from `web/public/` would remove that third
party. No Content Security Policy is set today: none in `index.html` and no response headers policy in
`terraform/modules/web_hosting/main.tf`, tracked for its own spec. When one is added, `style-src` must
allow the `<style>` elements Angular adds for component styles (a nonce through `CSP_NONCE`, or
`'unsafe-inline'`), plus the font origins if the font stays remote. Option A adds no third-party code.
