---
name: ui-ux
description: How to build user interfaces on web and mobile — start from the prototype and existing components, design tokens, layout and responsiveness, the states every screen needs, forms, feedback, copy, formatting, navigation and consistency, with a review checklist. Use when designing, building or reviewing a screen, a flow or a component.
---

# UI and UX

A screen is done when a person can complete the task without help, on a small screen, with errors, slow
networks and assistive technology. Accessibility rules are in `accessibility`; both apply together.

## Before building

1. Find the prototype or design for the screen and the components that already exist. Reuse before
   creating; a new component needs a reason.
2. List the screen's states (below) and its data from the spec's data contract. Write them in the spec's
   Design under **Screens**.
3. Agree on the copy for titles, actions, errors and empty states before coding it.

## Design tokens

Colors, typography, spacing, radii and elevation come from tokens: CSS custom properties on the web,
`MaterialTheme` on Android. No hard-coded hex colors, font sizes or one-off spacing; when a value is
missing, add a token. Light and dark themes both work wherever the platform offers them.

## Layout

- Mobile first. Web content reflows at 320 CSS px without horizontal scrolling and works at 200% zoom.
- A spacing scale, aligned to a grid; related elements close, unrelated ones apart.
- Readable line length (about 60–80 characters); content in a max-width container.
- Android: respect system insets, scroll when content does not fit, and survive the largest font size.
- One primary action per screen, visually distinct; destructive actions never styled as the primary one.

## The states of a screen

| State | What the user sees |
|---|---|
| Loading | A skeleton or a progress indicator after about 300 ms; the layout does not jump when data arrives |
| Empty | Why it is empty and the next action |
| Error | What happened in plain language and how to recover (retry, edit, contact); entered data is kept |
| Partial | What loaded, and what failed with its own retry |
| Success | Confirmation of the result and what happens next |
| Offline or slow | A clear message; actions are not lost silently |
| Session expired or no permission | A path back to sign in, returning to the same place |

No silent failures: every request that can fail has a visible outcome.

## Forms

- Visible labels, never placeholder-only. Placeholders show a format example at most.
- The right input type, keyboard, `autocomplete` and `inputmode`; group related fields.
- Show requirements before the user types (for example password rules), not only after failing them.
- Validate on blur and on submit; show the message next to the field, saying how to fix it.
- On submit errors, keep every value and move focus to the first problem.
- Prevent double submission while a request is in flight, and say what is happening ("Validando…").
- Confirm destructive or irreversible actions, naming the consequence; offer undo where possible.
- Ask only for data the spec needs; never ask twice for what the user already gave.

## Feedback and timing

- Pressed and focus states on every control.
- Long operations show progress and can be left without losing work.
- Countdowns (lockouts, code expiry) show the remaining time without announcing every second.
- Never optimistic updates for money, policies or anything irreversible.

## Copy

- The product's language and register (Spanish, formal "usted" in this product); plain words, short sentences.
- One term per concept across the product (a glossary in the design notes keeps them consistent).
- Errors say what happened and what to do, without codes, blame or technical detail.
- Security-sensitive messages are deliberately generic: "Correo o contraseña incorrectos", never which one.
- Buttons say the action ("Pagar", "Emitir póliza"), not "OK".

## Formatting

Money, numbers and dates in the product's locale with one shared formatter per type; time zones explicit
when they matter; identifiers and amounts never truncated without a way to see them in full.

## Navigation

- Every screen has a clear title and a way back; back never loses entered data without a warning.
- Multi-step flows show the current step and the total, and let the user review before confirming.
- Deep links and refresh land on a valid state.

## Review checklist

- [ ] Built from the prototype and existing components; tokens only, no hard-coded styles.
- [ ] Works at 320 CSS px, 200% zoom and the largest font; light and dark.
- [ ] Every state designed: loading, empty, error, partial, success, offline, expired session.
- [ ] Forms: visible labels, requirements up front, inline errors, data kept, double submit prevented.
- [ ] Destructive actions confirmed; no optimistic updates for irreversible operations.
- [ ] Copy plain, consistent and actionable; security messages generic.
- [ ] Locale formatting for money and dates.
- [ ] `accessibility` checklist passed.
