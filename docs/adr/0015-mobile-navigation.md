# ADR 0015 · Mobile: screen switching by UI state in one activity

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-10-22 |
| Story | none |
| Deciders | The team (to be confirmed) |

## Context

Paths are under `movil/app/src/main/java/com/solventa/app/`.

- `MainActivity` extends `FragmentActivity`, because `BiometricPrompt` needs one. It is the only activity.
- `SolventaMobileRoot` in `MainActivity.kt` collects `AuthViewModel.uiState` and picks one screen with
  `when`: `isAuthenticated` → `HomePlaceholder`, `showPasswordRecovery` → `PasswordRecoveryScreen`,
  `showAlternativeAccess` → `AlternativeLoginScreen`, otherwise `BiometricLoginScreen`. Two dialogs show on
  the flags `offerBiometricEnrollment` and `showLogoutConfirmation`.
- Back: `AlternativeLoginScreen` and `PasswordRecoveryScreen` declare a `BackHandler` that calls a
  ViewModel action. The biometric screen and the home placeholder use the system default.
- State: `AuthUiState` lives in ViewModel memory; there is no `SavedStateHandle`. After process death the
  app opens on the biometric screen with a fresh state and no tokens. The screens keep their form fields in
  `rememberSaveable`, including the password, the one-time code and the new password.
- The app has one feature, authentication. A comment in `MainActivity.kt` says the policy wallet
  (HU-MOV-04) replaces `HomePlaceholder`. `movil/gradle/libs.versions.toml` has no navigation library.
- `SolventaMobileRootTest`, in `src/test/.../MainActivityTest.kt`, drives the screen switching with
  Robolectric Compose tests.

## Options considered

| Option | Pros | Cons |
|---|---|---|
| A. Switch screens on UI state in one activity | No dependency; the auth flow is one state machine owned by its ViewModel; already tested | No back stack; each screen writes its own `BackHandler`; the order of `when` decides between flags; no deep links; does not scale past one feature |
| B. Navigation Compose now | AndroidX standard; back stack; type-safe routes; deep links; a ViewModel per destination | A new dependency (type-safe routes also need the Kotlin serialization plugin); restructures a working flow before a second feature exists |
| C. A third-party library (Voyager, Decompose, Compose Destinations) | Some generate routes or add lifecycle-aware components | Smaller communities than AndroidX; another dependency to evaluate and keep current; non-standard API for the team |

## Decision

Option A now, with a planned move to Navigation Compose.

1. While the app has a single feature, `MainActivity` keeps choosing the screen from the `UiState` in
   `SolventaMobileRoot`. New authentication screens add a branch, not a new activity.
2. Every screen other than the start screen declares a `BackHandler` that calls a ViewModel action.
3. With the second feature (policies, payments, claims), the app adopts Navigation Compose. It is a new
   dependency, evaluated, through its own ADR, with type-safe routes and the back stack. Authentication
   becomes one nested graph.
4. Back behavior and process death keep sensitive values out of saved state. Passwords, one-time codes,
   tokens and keys never go into `rememberSaveable`, `SavedStateHandle`, route arguments or deep links.

## Consequences

- Easier: no new dependency now; the auth flow stays in one ViewModel; tests drive it through state.
- Harder: until the move, back and deep links are manual, and the order of `when` must stay correct.
- Migration: the spec of the second feature (HU-MOV-04 or whichever comes first) includes the navigation
  ADR and moves the auth screens behind routes. Nothing changes before that. The `rememberSaveable`
  password and code fields are fixed in their own spec (ADR 0017).

## Security and privacy impact

- Today a process death clears the in-memory session, so the user must authenticate again.
- The password, one-time code, new password and confirmation fields are in `rememberSaveable`. They go
  into the activity's saved instance state, which the system keeps outside the app process. This is a
  known gap, listed in ADR 0017.
- Back on the biometric screen and the home placeholder uses the system default. On Android 12 and later
  (minSdk is 33), that moves the root activity to the background without finishing it. The session stays
  open in memory, and there is no inactivity timeout.
- With Navigation, route arguments are saved with the back stack. Rule 4 keeps secrets out of them. Deep
  links into signed-in screens must check for an active session.
