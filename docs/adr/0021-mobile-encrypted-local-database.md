# ADR 0021 · Mobile: an encrypted local database per account with Room and SQLCipher

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-10-23 |
| Story | HU-MOV-04 |
| Deciders | The team (to be confirmed) |

## Context

Paths are under `movil/app/src/main/java/com/solventa/app/`.

- HU-MOV-04 keeps a copy of the policyholder's active policies on the phone so the wallet works without a
  network. The copy is personal data (CONFIDENTIAL): policy number, plan, holder name, coverages and
  validity. HA-16 asks to protect personal data stored on the device.
- Until now the app stored only the device credential of each bound account, encrypted with a Keystore key
  that needs biometrics (ADR 0017). `data/local/EncryptedStorageManager` was a placeholder for HU-MOV-05.
- `movil/gradle/libs.versions.toml` already listed Room 2.6.1 and `net.zetetic:android-database-sqlcipher`
  4.5.4, unused. That artifact is deprecated; its replacement is `net.zetetic:sqlcipher-android`.
- The phone can hold several accounts (HU-MOV-01). Each one must see only its own copy.
- The wallet opens without a network only after the account's biometric unlock (HU-MOV-04, AC-12). The
  database itself must open without a biometric prompt, because the prompt already unlocked the session
  credential and a second prompt for the same action adds nothing.

## Options considered

| Option | Pros | Cons |
|---|---|---|
| A. Room with SQLCipher, one database per account, passphrase wrapped by a per-account Keystore key | Whole file encrypted with page HMAC; Room DAOs and transactions; deleting an account is deleting a file and a key; no cross-account rows | Native library (larger APK); Room needs KSP; the database opens per operation |
| B. Room without encryption, relying on the app sandbox | Simplest; no native code | Data in clear on rooted phones, backups or forensic copies; does not meet HA-16 |
| C. Encrypted JSON file per account with Keystore AES-GCM | No new dependency; small data | Hand-written persistence, no queries or transactions; every later feature (claims, payments) re-implements it |
| D. One shared SQLCipher database with an account column | One file and one key | One key opens every account's data; isolation depends on every query filtering by account |

## Decision

Option A.

1. Local data that identifies a person lives in Room over SQLCipher (`net.zetetic:sqlcipher-android`
   through `SupportOpenHelperFactory`), never in plain SQLite, files or preferences.
2. One database per account, named `wallet_<id>.db`, where `<id>` is the first 32 hex characters of the
   SHA-256 of the normalized email. The email itself is not used in file names or key aliases.
3. Each database has a random 32-byte passphrase from `SecureRandom`. It is stored only wrapped with
   AES-256-GCM by an `AndroidKeyStore` key per account (`solventa_wallet_<id>`), non-exportable and usable
   only while the phone is unlocked (`setUnlockedDeviceRequired`). The passphrase is in clear only in memory
   while one operation runs, then zero-filled.
4. If the key or the database no longer opens, the copy is deleted and downloaded again when there is a
   network. Recovery beyond that is HU-MOV-05.
5. The copy of an account is deleted with its key on logout, on a 401 from the backend and when the server
   no longer recognizes the phone for that account.
6. Room schemas are not exported (`exportSchema = false`) while the copy is a cache that can be rebuilt
   from the backend; a feature that stores data only on the phone exports them and writes migrations.
7. Storage code lives in `data/<feature>/` behind a domain port (`PolicyStore`), as in ADR 0013.

## Consequences

- Easier: later features add entities to their own Room database with the same key scheme; deleting an
  account's data is one call.
- Harder: the SQLCipher native library adds several megabytes per ABI; JVM unit tests cannot open the
  database, so encryption is tested with instrumented tests on an emulator
  (`src/androidTest/.../EncryptedPolicyStoreTest`).
- Build: the KSP plugin (2.1.0-1.0.29) and `room-compiler` join the build.
- Migration: `EncryptedStorageManager` is removed; HU-MOV-05 builds invalid-key handling on this store.

## Security and privacy impact

- A copied database file is unreadable without the account's Keystore key, which never leaves the device.
- While the phone is locked the key cannot be used, so the copy cannot be opened.
- A compromised phone with the app open could read the passphrase or the screen from memory (RISK-02 in
  the HU-MOV-04 spec).
- `allowBackup` stays `false`, so neither the database nor the wrapped passphrase goes to backups.
