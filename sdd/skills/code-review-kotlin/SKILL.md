---
name: code-review-kotlin
description: Kotlin and Android conventions and review checklist — Kotlin style, layers, ViewModel and UI state, coroutines, Jetpack Compose, resources and tests with JUnit, Robolectric and coroutine test dispatchers. Use when writing or reviewing Kotlin, Gradle Kotlin scripts or Android resources.
---

# Kotlin and Android — conventions and review

Applies to `*.kt`, `*.kts` and Android resources and manifests. Follow it when writing; when reviewing,
`code-review` gives the process and this skill gives what to check. Secure patterns are in
`secure-coding-kotlin`; screens also follow `ui-ux` and `accessibility`.

References: Kotlin coding conventions (https://kotlinlang.org/docs/coding-conventions.html), Android
Kotlin style guide (https://developer.android.com/kotlin/style-guide), Compose API guidelines
(https://developer.android.com/develop/ui/compose/api-guidelines).

## Kotlin

- Official code style (`kotlin.code.style=official`). Adding ktlint or detekt is a dependency change
  (`dependency-review`); Android lint ships with the build (`./gradlew lintDebug`).
- No `!!`; model absence with nullable types and handle it. `lateinit` only for framework-injected fields.
- Immutable by default: `val`, read-only collections, `data class` copies.
- Domain outcomes are `sealed` types (`Success`, `InvalidCredentials`, `Locked(until)`…), not exceptions
  thrown across layers. `when` over sealed types is exhaustive, without `else`.

## Layers

- `domain/`: interfaces and result types, without Android imports.
- `data/`: implementations (HTTP, storage, keystore, biometrics).
- `ui/`: composables and ViewModels. Dependencies reach a ViewModel through its constructor.

## ViewModel and state

- One immutable `UiState` per screen in a `MutableStateFlow`, exposed as `StateFlow`, changed only with
  `update { it.copy(…) }`.
- One-off events (navigate, show a message) are part of the state and acknowledged, or a dedicated channel; never lost.
- Messages are `@StringRes` in the state; the ViewModel does not build user-facing text.
- Collect state in a lifecycle-aware way.

## Coroutines

- Work starts in `viewModelScope`; no `GlobalScope`, no `runBlocking` in production code.
- I/O runs on an injected dispatcher (`Dispatchers.IO` by default) so tests can replace it.
- Respect cancellation: `suspendCancellableCoroutine` registers `invokeOnCancellation`; do not swallow
  `CancellationException`.
- Network calls have connect and read timeouts.

## Compose

- Screens split into a stateful entry point (reads the ViewModel) and stateless composables (state and
  callbacks as parameters). State is hoisted.
- The first optional parameter of a composable is `modifier: Modifier = Modifier`, applied to the root.
- `remember` for UI state; `rememberSaveable` only for non-sensitive values. Side effects in
  `LaunchedEffect` or `DisposableEffect` with explicit keys.
- Text from `stringResource`; colors and type from `MaterialTheme`; no hard-coded colors or `sp` sizes.
- A `@Preview` per meaningful state (default, loading, error), light and dark.

## Resources and build

- User-facing strings in `res/values/strings.xml` (Spanish in this product); no string literals in UI code.
- Versions in the version catalog (`gradle/libs.versions.toml`); no versions inline in build scripts.

## Tests

- JVM tests in `src/test`: JUnit with `kotlinx-coroutines-test` (`runTest`, a test dispatcher set as
  `Main`), hand-written fakes for `domain` interfaces, Robolectric for Android framework and Compose UI
  tests, a mock web server for HTTP.
- Compose tests find nodes as a user would — text, content description, role — or a `testTag`.
- Keystore, biometrics and real device behavior need instrumented tests in `src/androidTest` on a
  device or emulator; a fake proves the logic only.

## Review checklist

- [ ] No `!!`; sealed results handled exhaustively; no exceptions across layers.
- [ ] `domain` free of Android; dependencies through constructors.
- [ ] One immutable `UiState`; updates with `update {}`; no user text built in the ViewModel.
- [ ] Coroutines in `viewModelScope`; injected dispatchers; cancellation respected; timeouts set.
- [ ] Stateless composables with `modifier`; no sensitive value in `rememberSaveable`.
- [ ] Strings, colors and type from resources and the theme; previews for each state.
- [ ] Tests cover the state transitions, including errors and cancellation.

## In this repository

- Architecture: ADRs [0013](../../../docs/adr/0013-mobile-mvvm-layers.md) (MVVM layers: `domain/<feature>`,
  `data/<feature>`, `ui/<feature>`), [0014](../../../docs/adr/0014-mobile-dependency-injection.md) (DI),
  [0015](../../../docs/adr/0015-mobile-navigation.md) (navigation),
  [0016](../../../docs/adr/0016-mobile-networking.md) (HTTP) and
  [0017](../../../docs/adr/0017-mobile-credential-storage.md) (credentials). Check new code against them. Manual dependency injection in
  `SolventaApplication`; ViewModels built with `viewModelFactory`.
- One activity (`MainActivity`, a `FragmentActivity` for the biometric prompt); screens switch on UI state.
- Networking with `HttpURLConnection` and `org.json` in `data/auth/HttpAuthApi.kt`; sealed results in `domain/auth/`.
- Theme in `ui/theme/Theme.kt` (Material 3, light and dark, from `prototipos/movil`).
- Tests: `movil/app/src/test/` with Robolectric Compose tests and fakes in `SessionTestDoubles.kt`; no
  `androidTest` yet. No ktlint, detekt or lint in CI; Kover for coverage.
- Commands: `cd movil && ./gradlew testDebugUnitTest` and `./gradlew lintDebug`.
