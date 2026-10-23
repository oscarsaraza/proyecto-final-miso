# ADR 0013 · Mobile: MVVM with domain, data and ui layers per feature

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-10-22 |
| Story | none |
| Deciders | The team (to be confirmed) |

## Context

The insured's app is Kotlin 2.1.0 with Jetpack Compose (BOM 2024.11.00), minSdk 33, in
`movil/app/src/main/java/com/solventa/app/`. This ADR replaces ADR 0003; dependency injection and
navigation now have their own ADRs (0014, 0015).

- `MainActivity` is the only activity. `SolventaApplication` builds the data objects by hand.
- `domain/auth` holds the ports `AuthApi` and `BiometricAuthenticator`, sealed results (`LoginResult`,
  `OtpResult`, `ResetResult`, `BiometricResult`), `SessionTokens` and `DeviceCredential`, with no Android
  imports. `domain/model` holds `Policy` and `UserSession`; nothing uses them.
- `data/auth` holds `HttpAuthApi` and `AndroidBiometricAuthenticator`; `data/session` the Keystore crypto,
  the preferences store and `SecureSessionRepository`. `data/local/EncryptedStorageManager` is a
  placeholder that throws `NotImplementedError` (HU-MOV-05).
- `ui/auth` holds three screens, two dialogs, password widgets and one `AuthViewModel` of 523 lines for
  four stories (HU-MOV-01, -02, -03, -12), with one `AuthUiState` in a `MutableStateFlow` changed with
  `update {}`. `ui/theme/Theme.kt` holds the Material 3 theme.
- The layers leak: `AuthViewModel` takes the concrete `SecureSessionRepository`, and `AuthViewModel` and
  `BiometricLoginScreen` import `BoundAccount` from `data/session`.

Next stories add features; a comment in `MainActivity.kt` says the policy wallet (HU-MOV-04) replaces
the home placeholder.

## Options considered

| Option | Pros | Cons |
|---|---|---|
| A. MVVM with `domain`, `data` and `ui` layers per feature | Matches the code; ViewModels tested with fakes of domain interfaces; few files | ViewModels grow if flows are not split |
| B. MVI with reducers | Explicit, testable state transitions | More ceremony (intents, reducers, effects); a new pattern for the team |
| C. Full clean architecture with a use-case class per action | Very explicit boundaries | Many one-method classes; most would only forward to a port |

## Decision

Option A.

```
movil/app/src/main/java/com/solventa/app/
  SolventaApplication.kt        dependency container (ADR 0014)
  MainActivity.kt               the single activity; hosts the screens (ADR 0015)
  domain/<feature>/             interfaces (ports), models and sealed results; no Android imports
  domain/model/                 models shared by two or more features
  data/<feature>/               implementations: HTTP, Keystore, storage, biometrics
  ui/<feature>/
    <Feature>ViewModel.kt       one per flow, with its UiState
    <Name>Screen.kt             one per screen: stateful entry, stateless content, previews
  ui/components/                composables shared by two or more features
  ui/theme/
```

1. Dependencies go `ui` → `domain` ← `data`. `data` implements domain interfaces; `ui` never imports `data`.
2. A ViewModel depends on domain interfaces only.
3. One ViewModel per flow, with one immutable `UiState` exposed as a `StateFlow` and changed only with
   `update {}`.
4. Past about 400 lines a ViewModel is split by sub-flow. `AuthViewModel` splits into biometric sign-in,
   alternative sign-in and password recovery.
5. Use-case classes only when two or more ViewModels share the same logic.

## Consequences

- Easier: a feature is three folders, and reviews know where code goes. `AuthViewModelTest` already tests
  the ViewModel with fakes.
- Harder: after the split, three ViewModels share the session. That needs a domain port, and maybe the
  first use case.
- Migration when next touched, not as a rewrite:
  - Add a domain interface for the session repository and move `BoundAccount` to `domain/auth`.
  - Split `AuthViewModel` when the next authentication story changes it.
  - Today `SolventaMobileRoot` collects the state and the screens are content only; each screen gets its
    own entry with navigation (ADR 0015). `ui/components/` does not exist yet.
  - Move `Policy` and `UserSession` into their feature, or delete them. Implement `data/local` in
    HU-MOV-05, or remove it with Room 2.6.1 and SQLCipher 4.5.4, which ship today and nothing calls.

## Security and privacy impact

- Keystore, biometric, HTTP and storage code stays in `data`, behind domain interfaces, so a review of
  sensitive code starts in `data/`.
- JVM fakes prove only the logic: `FakeSessionCrypto` uses an in-memory AES key. The real Keystore and
  biometric prompt have no tests on a device (ADR 0017).
- `UiState` lives in ViewModel memory, not in saved state. Screen form fields are a separate gap (ADR 0017).
- Unused Room and SQLCipher add code to the APK that nothing calls.
