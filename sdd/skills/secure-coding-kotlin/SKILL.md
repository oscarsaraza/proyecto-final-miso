---
name: secure-coding-kotlin
description: Secure coding patterns for Kotlin on Android (OWASP MASVS) — Keystore keys bound to biometrics, token and credential storage, saved UI state, screenshots, network security per build type, backups and device transfer, release builds, debug-only features, exported components, logs and clipboard. Use when writing or reviewing Android code, manifests or build scripts.
---

# Secure coding — Kotlin and Android

The device is in the user's hands, and possibly in a thief's. Each pattern names the MASVS control and
the weakness it prevents (CWE), and the test that proves it.

## Keys in the Android Keystore (MASVS-CRYPTO-2, MASVS-AUTH-2, CWE-321)

```kotlin
val spec = KeyGenParameterSpec.Builder(alias, KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT)
    .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
    .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
    .setKeySize(256)
    .setUserAuthenticationRequired(true)
    .setUserAuthenticationParameters(0, KeyProperties.AUTH_BIOMETRIC_STRONG)
    .setInvalidatedByBiometricEnrollment(true)
    .build()
KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore").run {
    init(spec)
    generateKey()
}
```

- The `Cipher` is initialized with the key and passed to `BiometricPrompt` in a `CryptoObject`; use only
  the cipher returned in the success callback. A prompt without a crypto object proves nothing to the key.
- One key per purpose and per account; the IV comes from the cipher and is stored next to the ciphertext.
- `KeyPermanentlyInvalidatedException` means new biometrics were enrolled: delete the credential and ask
  for the password again.

Test: instrumented, on a device — a fake cipher proves the logic, not the Keystore.

## Tokens and credentials (MASVS-STORAGE-1, CWE-312)

- Access and refresh tokens in memory, or encrypted with a Keystore key. Never plain
  `SharedPreferences`, DataStore, files or databases without encryption.
- Passwords and codes as `CharArray` or `ByteArray` where the API allows, zeroed after use; `toString()`
  of models holding secrets masks them.

## Saved UI state (MASVS-STORAGE-2, CWE-524)

```kotlin
var password by remember { mutableStateOf("") }
```

Never `rememberSaveable` or `SavedStateHandle` for passwords, codes or tokens: saved state is written to
disk when the process dies.

## Screenshots and recents (MASVS-PLATFORM-3, CWE-200)

```kotlin
window.setFlags(WindowManager.LayoutParams.FLAG_SECURE, WindowManager.LayoutParams.FLAG_SECURE)
```

In `onCreate` when most screens show credentials or personal data; otherwise per screen, adding the flag
in a `DisposableEffect` and clearing it in `onDispose`.

## Network (MASVS-NETWORK-1, MASVS-NETWORK-2, CWE-319)

- The main `network_security_config.xml` sets `cleartextTrafficPermitted="false"`. Cleartext for an
  emulator host lives only in `src/debug/res/xml/network_security_config.xml`.
- The API base URL is set per build type (`buildConfigField` in `debug` and `release`); release is HTTPS only.
- Certificate pinning only when the risk justifies it, with a backup pin and an expiration date.
- Connect and read timeouts on every connection; responses are validated before use.

## Backups and device transfer (MASVS-STORAGE-2, CWE-530)

`android:allowBackup="false"` does not stop device-to-device transfer on Android 12 and later: also set
`android:dataExtractionRules` excluding the stores that hold credentials, from both `cloud-backup` and
`device-transfer`.

## Release builds (MASVS-RESILIENCE-2, MASVS-RESILIENCE-3, MASVS-RESILIENCE-4)

```kotlin
release {
    isMinifyEnabled = true
    isShrinkResources = true
    proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
}
```

Not debuggable, signed with a key outside the repository, and logs stripped by R8 rules.

## Debug-only features (CWE-489)

Anything that shows server debug data, test accounts or codes is behind `BuildConfig.DEBUG` — and the
server must not send it in the first place.

## Components and intents (MASVS-PLATFORM-1, MASVS-CODE-4, CWE-926)

`android:exported="false"` unless another app must start the component; explicit intents;
`PendingIntent.FLAG_IMMUTABLE`; deep link parameters validated like any external input. No `WebView`
for authentication; if one is needed, JavaScript and file access off.

## Logs and clipboard (MASVS-STORAGE-2, CWE-532)

No `Log` calls with tokens, codes, credentials or personal data. Do not copy secrets to the clipboard;
when unavoidable, mark the clip sensitive (`ClipDescription.EXTRA_IS_SENSITIVE`).

## Lost or stolen device (MASVS-AUTH-3)

Local credentials need biometrics on every use, and the server can revoke a device's credential.

## Review checklist

- [ ] Keystore keys bound to strong biometrics with a crypto object; invalidated on enrollment; one per purpose.
- [ ] No tokens or credentials in plain storage; no secrets in saved UI state.
- [ ] `FLAG_SECURE` on screens with credentials or personal data.
- [ ] Cleartext only in the debug source set; HTTPS base URL in release.
- [ ] `dataExtractionRules` excludes credential stores.
- [ ] Release minified, shrunk and not debuggable; debug features behind `BuildConfig.DEBUG`.
- [ ] Minimal exported components; immutable pending intents; validated deep links.
- [ ] No sensitive logs or clipboard use.
- [ ] Keystore and biometric behavior proven by instrumented tests.
