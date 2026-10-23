# ADR 0014 · Mobile: manual dependency injection in the Application class

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-10-22 |
| Story | none |
| Deciders | The team (to be confirmed) |

## Context

The app wires its objects by hand (paths under `movil/app/src/main/java/com/solventa/app/`):

- `SolventaApplication.kt` (17 lines) has two `by lazy` properties: `sessionRepository`, a
  `SecureSessionRepository(KeystoreSessionCrypto(), SharedPreferencesSessionStore(this))`, and `authApi`,
  an `HttpAuthApi(BuildConfig.API_BASE_URL)` typed as the domain interface `AuthApi`.
- `MainActivity` gets `AuthViewModel` with `by viewModels { viewModelFactory { initializer { … } } }`. The
  initializer casts `application as SolventaApplication` and passes both objects to the constructor.
- `AndroidBiometricAuthenticator` needs a `FragmentActivity`. `MainActivity.onCreate` builds it and
  `SolventaMobileRoot` passes it as a parameter to ViewModel methods (`authenticateWithBiometrics`,
  `authenticateWithPassword`, `enableBiometricUnlock`). The ViewModel does not keep it.
- Tests build objects through constructors, for example
  `AuthViewModel(SecureSessionRepository(FakeSessionCrypto(), InMemorySessionStore()), api)`.
- `movil/gradle/libs.versions.toml` has no Hilt, Dagger, Koin, KSP or kapt. MockK 1.13.13 is a test
  dependency, but no test imports it.

## Options considered

| Option | Pros | Cons |
|---|---|---|
| A. Manual DI in `SolventaApplication` | No dependency or code generation; the graph is one readable file; checked at compile time | Wiring grows with each feature; scopes and factories are written by hand |
| B. Hilt | Android standard; scopes; `@HiltViewModel`; test modules replace bindings | Dagger plus an annotation processor; slower builds; generated code; new to the team |
| C. Koin | Kotlin DSL; no code generation; small | Bindings resolved at runtime, so a missing one fails in use, not at build; a new dependency |

## Decision

Option A.

1. `SolventaApplication` is the container. It builds each `data` implementation once, with `by lazy`,
   and exposes it typed as its domain interface.
2. A ViewModel receives its dependencies through its constructor, built in its
   `viewModelFactory { initializer { … } }`. ViewModels and composables never reach into the Application.
3. An object that needs an activity is built by the activity and passed as a parameter. It is never kept
   in the Application or in a ViewModel field, so the activity does not leak.
4. Tests pass fakes through constructors. No DI framework or mocking library is needed for that.
5. Adopting a DI framework needs a new ADR. The trigger is a graph that no longer fits one readable class,
   or scopes per navigation graph that are hard to write by hand.

## Consequences

- Easier: no build plugins; anyone reads the whole graph in one file; tests stay as they are.
- Harder: each feature adds wiring lines and a factory block. With Navigation (ADR 0015) a small factory
  helper per feature may be needed.
- Migration when next touched:
  - `sessionRepository` is exposed as the concrete `SecureSessionRepository`. Type it as the domain session
    interface once that exists (ADR 0013).
  - Remove MockK, or use it, the next time test dependencies change.

## Security and privacy impact

- The container is the one place that chooses the implementations of sensitive ports: the Keystore
  crypto, the session store and the API base URL. A reviewer checks one file to confirm that production
  uses `KeystoreSessionCrypto` and not a fake. Fakes live only in `src/test`.
- Application-scoped objects live as long as the process. `SecureSessionRepository` keeps the tokens in
  memory until logout or process death (ADR 0017). Anything sensitive added to the container gets the same
  lifetime.
- No framework means no generated code or reflection to review, and no new library in the supply chain.
