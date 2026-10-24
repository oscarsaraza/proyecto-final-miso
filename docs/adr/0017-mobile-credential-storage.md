# ADR 0017 · Mobile: credentials protected by the Keystore and biometrics; tokens only in memory

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-10-22 |
| Story | none |
| Deciders | The team (to be confirmed) |

## Context

Paths are under `movil/app/src/main/java/com/solventa/app/`. Today:

- What is stored is a device credential per bound account (`DeviceCredential`: device id and device
  secret, issued by `POST auth/devices`). The password and the tokens are not written to app storage.
- `data/session/KeystoreSessionCrypto` creates one AES-256 key in `AndroidKeyStore`, alias
  `solventa_session_key`, GCM without padding. It requires user authentication with `AUTH_BIOMETRIC_STRONG`
  on every use (timeout 0) and is invalidated by a new biometric enrollment. All bound accounts share this
  key; each account has its own ciphertext and IV. StrongBox is not requested.
- `data/auth/AndroidBiometricAuthenticator` unlocks the cipher only through `BiometricPrompt` with
  `BIOMETRIC_STRONG` and a `CryptoObject`. A success without a cipher is an error.
- When decryption finds the key invalidated, the key is deleted and `SecureSessionRepository` clears every
  bound account. The user signs in again with password and code.
- `SharedPreferencesSessionStore` writes to the private preferences `solventa_session` (`MODE_PRIVATE`)
  the ciphertext and IV in Base64, plus the device id, email and full name in plain text.
- `SecureSessionRepository.activeSession` keeps the access and refresh tokens in memory only. Logout clears
  them and revokes the refresh token on the server. There is no token refresh call.
- `save` and `unlock` fill the plaintext byte arrays with zeros. `SessionTokens` and `DeviceCredential`
  mask their secrets in `toString()`.
- The manifest sets `android:allowBackup="false"`. `androidx.biometric` is 1.2.0-alpha05, an alpha
  release. JVM tests replace the Keystore with `FakeSessionCrypto`, an in-memory AES key.

Known gaps, each checked in the code, tracked for their own spec:

1. Password, one-time code, recovery code, new password and confirmation are in `rememberSaveable`
   (`ui/auth/AlternativeLoginScreen.kt`, `ui/auth/PasswordRecoveryScreen.kt`).
2. No `FLAG_SECURE` on any window.
3. No `android:dataExtractionRules`.
4. The server's `debug_code` is shown on screen without a `BuildConfig.DEBUG` guard.
5. The release build has `isMinifyEnabled = false`.
6. No `src/androidTest`: the Keystore and the biometric prompt are not tested on a device.
7. One key for all accounts, not one per account.
8. `domain/model/UserSession` is an unused data class with a `token` field; its generated `toString()`
   would print it.

## Options considered

| Option | Pros | Cons |
|---|---|---|
| A. Keystore key bound to strong biometrics, `CryptoObject`, tokens in memory | The secret is usable only after a strong biometric; the key never leaves the Keystore; no tokens at rest; no extra dependency | A prompt on every start; a new enrollment drops every bound account; process death ends the session; Keystore behavior varies by device |
| B. `EncryptedSharedPreferences` | Simple key-value encryption | Jetpack Security Crypto is deprecated; its default master key needs no user authentication, so no biometric binding; a new dependency |
| C. Server session only, password and code on every start | Nothing secret on the phone | An SMS code and its cost on every start; no biometric sign-in (HU-MOV-03) |

## Decision

Option A, as today, following `sdd/rules/mobile.md`.

1. A secret stored on the phone is encrypted with an `AndroidKeyStore` AES-256-GCM key that requires
   `BIOMETRIC_STRONG` on every use and is invalidated by new enrollments.
2. The key is unlocked only through `BiometricPrompt` with a `CryptoObject`.
3. Only ciphertext and IV go to private preferences. Nothing sensitive goes in plain preferences, saved UI
   state, logs or the clipboard.
4. Access and refresh tokens live only in memory and are cleared on logout.
5. Plaintext byte arrays are zeroed after use. Models with secrets mask them in `toString()`.
6. New code uses one key per purpose and per account.
7. Keystore and biometric behavior is proven by instrumented tests on a device.

## Consequences

- Easier: a lost phone exposes no usable secret without the owner's biometric. Per the comment in
  `AuthViewModel.resetPassword`, a password reset makes the server unlink the account's devices.
- Harder: per-account keys mean managing one alias per account. Device tests need an emulator or device
  with an enrolled fingerprint.
- Migration: the eight gaps are fixed in their own spec, not here. Until then, new code follows the rules.

## Security and privacy impact

- Email and full name of each bound account are stored in plain text in app-private preferences, to show
  the account picker. They are out of cloud backup. On Android 12 and later, `allowBackup="false"` does
  not stop device-to-device transfer, so they can be copied until gap 3 is fixed. The ciphertext is useless
  without the key, which never leaves the Keystore.
- Zeroing covers byte arrays only. The secret and the tokens are also Kotlin `String`s, which cannot be
  wiped.
- Gap 1 puts passwords and codes in saved state. Gap 2 lets screenshots and the recents thumbnail capture
  them. Gap 4 shows a one-time code on screen in any build whose server sends `debug_code`.
- Residual risk until the hardening spec closes is accepted by the team through `risk-acceptance`, not by
  this ADR.
