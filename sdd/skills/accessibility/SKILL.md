---
name: accessibility
description: Build and verify accessible interfaces — WCAG 2.2 level AA on the web (semantics, names, keyboard, focus, forms, contrast, targets, live regions) and the Android accessibility guidelines in Jetpack Compose (content descriptions, semantics, touch targets, font scaling, TalkBack), with automated and manual tests. Use when building or reviewing a screen or component, or writing an ACCESSIBILITY test case.
---

# Accessibility

The target is **WCAG 2.2 level AA** (https://www.w3.org/TR/WCAG22/) on the web and the Android
accessibility guidelines (https://developer.android.com/guide/topics/ui/accessibility) on mobile.
Numbers in parentheses are WCAG success criteria. Automated checks find only part of the problems; every
ACCESSIBILITY test case includes a manual keyboard and screen reader pass.

## Web (Angular)

### Semantics first

- Native elements: `<button>` for actions, `<a href>` for navigation, `<label>`, `<fieldset>` and
  `<legend>`, headings in order, landmarks (`header`, `nav`, `main`, `footer`), lists for lists (1.3.1).
- ARIA only when no native element exists, and then the whole pattern from the ARIA Authoring Practices
  (https://www.w3.org/WAI/ARIA/apg/): tabs need `tablist`, `tab`, `tabpanel`, `aria-controls`,
  `aria-selected` and arrow-key handling; a dialog needs `role="dialog"`, `aria-modal`, a label, a focus
  trap and Escape.
- `<html lang="es">` (3.1.1) and a unique page title per route (2.4.2).

### Names

Every control has an accessible name that includes its visible text (2.5.3, 4.1.2). Icon-only buttons
have `aria-label`; decorative icons have `aria-hidden="true"`; images that inform have `alt` (1.1.1).

### Keyboard and focus

- Everything works with the keyboard alone, in a logical order, without traps (2.1.1, 2.1.2, 2.4.3).
- Focus is always visible (2.4.7), with at least 3:1 contrast, and never hidden behind sticky headers or
  banners (2.4.11). Never remove the outline without an equally visible replacement.
- Move focus on purpose: to the new heading after a route or step change, to the first invalid field or
  an error summary after a failed submit, into a dialog when it opens and back to its trigger when it closes.

### Forms

- `<label for>` on every field; help and error text linked with `aria-describedby`; `aria-invalid="true"`
  on invalid fields; required fields marked in text, not only with color (1.3.1, 3.3.2).
- Errors identified in text and with a suggestion to fix them (3.3.1, 3.3.3).
- `autocomplete` on personal data fields (1.3.5); `autocomplete="one-time-code"` on code fields.
- Do not ask again for information already given in the same flow (3.3.7).
- Authentication without memory or puzzle tests: allow paste and password managers, show-password
  toggles, codes that can be copied (3.3.8).

### Perception

- Text contrast 4.5:1, large text 3:1 (1.4.3); borders of inputs, focus rings and icons that convey
  meaning 3:1 (1.4.11).
- Never color alone: a step indicator says "Paso 2 de 4" and marks the current step with
  `aria-current="step"`; errors carry an icon and text (1.4.1).
- Reflow at 320 CSS px (1.4.10), 200% text resize (1.4.4), user text spacing (1.4.12).
- Targets at least 24×24 CSS px or spaced apart (2.5.8); an alternative to every drag (2.5.7).
- Respect `prefers-reduced-motion`; nothing flashes more than three times per second (2.3.1).

### Dynamic content

Status messages in `role="status"` (polite), errors that need attention in `role="alert"`, without
moving focus (4.1.3). Countdowns announce at meaningful moments, not every second. Time limits can be
turned off, adjusted or extended unless they are essential, as an expiring one-time code is; then the
remaining time is shown (2.2.1).

## Android (Compose)

- **Content descriptions:** meaningful icons and images have `contentDescription` from string resources;
  decorative ones `null`. Do not include the role ("botón") in the description; the role is announced.
- **Semantics:** `Modifier.semantics { heading() }` on titles; `mergeDescendants = true` for rows read as
  one item; `stateDescription` for custom toggles; `Role` on custom clickable elements;
  `liveRegion = LiveRegionMode.Polite` on status and error text; text fields with `isError` and an
  error message in `supportingText`.
- **Touch targets:** at least 48×48 dp; Material components do it by default, custom clickables use
  `Modifier.minimumInteractiveComponentSize()` or padding.
- **Text scaling:** sizes in `sp` from the theme; layouts grow with the font up to 200% without clipping;
  no fixed heights on text containers.
- **Contrast:** the same ratios as the web, in light and dark themes.
- **Order and focus:** TalkBack reads in a logical order; after navigation, focus lands on the screen title.
- **Input:** keyboard types and IME actions on every field; credentials support autofill.
- **Alternatives:** biometric sign-in always has a non-biometric path; gestures have a button alternative.

## Testing

| Check | Web | Android |
|---|---|---|
| Automated rules | An accessibility rules engine in component or end-to-end tests; template accessibility lint rules if a linter is adopted (both are dependencies: `dependency-review`) | `./gradlew lintDebug` accessibility checks; Compose tests asserting semantics; Accessibility Test Framework checks in instrumented tests |
| Keyboard | Tab through the flow: order, visible focus, no traps, Escape closes | External keyboard or switch access on the main flow |
| Screen reader | NVDA or VoiceOver: names, roles, states, announcements | TalkBack: order, descriptions, announcements |
| Zoom and text | 200% zoom and 320 px width | Largest font and display size |
| Contrast | Measured with a contrast checker in both themes | Same |

Record them as test cases with Level `ACCESSIBILITY`, Automation `MANUAL` for the passes a person does,
and the findings as evidence.

## Review checklist

- [ ] Native semantics; ARIA patterns complete; language and titles set.
- [ ] Every control named; decorative content hidden.
- [ ] Keyboard-operable with visible, unobscured focus; focus moved on route, step, error and dialog changes.
- [ ] Field errors linked, described in text and focused; paste and password managers allowed.
- [ ] Contrast 4.5:1 and 3:1; nothing conveyed by color alone; reflow, zoom and text spacing work.
- [ ] Targets 24×24 CSS px on the web and 48×48 dp on Android.
- [ ] Status and errors announced politely or assertively as appropriate.
- [ ] Compose: descriptions, headings, merged rows, live regions, `sp` sizes, largest font.
- [ ] Automated checks run and the manual passes recorded.
