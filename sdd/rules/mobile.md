# Mobile rules (OWASP MASVS 2.1)

> Mobile app rules (Android and iOS). Load when editing app code or manifests. Paths: `mobile/**`, `android/**`, `ios/**`, `**/*.kt`, `**/*.swift`, `**/*.dart`, `**/AndroidManifest.xml`, `**/Info.plist`.

- Credentials and tokens in the platform keystore (Android Keystore, iOS Keychain): non-exportable keys,
  user authentication required for credentials, bound to the biometric prompt with a crypto object,
  invalidated on biometric enrollment, one key per purpose and per account. (MASVS-STORAGE-1, CRYPTO-2, AUTH-2)
- Nothing sensitive in plain preferences, saved UI state, logs or the clipboard. (MASVS-STORAGE-2)
- Backups and device-to-device transfer exclude sensitive storage (`allowBackup`, `dataExtractionRules`). (MASVS-STORAGE-2)
- `FLAG_SECURE` (or the iOS equivalent) on screens with passwords, codes or personal data. (MASVS-PLATFORM-3)
- HTTPS only outside local development, per build type; certificate pinning when the risk justifies it. (MASVS-NETWORK-1, -2)
- Release builds: minified, not debuggable, signed, and never showing server debug information. (MASVS-CODE, RESILIENCE)
- Minimal exported components. (MASVS-PLATFORM-1)
- Lost or stolen device: local credentials require biometrics on every use and can be revoked server-side. (MASVS-AUTH-3)
- Real keystore and biometric behavior needs device or instrumented tests; fakes do not prove it.

Interfaces follow `ui-ux` and `accessibility`. Language skills: `code-review-kotlin` and
`secure-coding-kotlin`.
