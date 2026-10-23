# Cryptography and key management

> Approved algorithms, key management and common confusions. Load when a change hashes, encrypts, signs, tokenizes or manages keys.

## Do not confuse

| Mechanism | Purpose | Reversible | Example |
|---|---|---|---|
| Password hash | Store passwords so they cannot be recovered and guessing is expensive | No | Argon2id |
| Hash | Integrity, or an identifier of a high-entropy value | No | SHA-256 of a 256-bit random secret |
| MAC | Integrity and authenticity with a shared key | No | HMAC-SHA256, JWT HS256 |
| Authenticated encryption | Confidentiality and integrity of data that must be recovered | With the key | AES-256-GCM, ChaCha20-Poly1305 |
| Digital signature | Authenticity verifiable by third parties with a public key | No | Ed25519, ECDSA P-256, RSA-PSS |
| Tokenization | Replace a datum with a reference meaningless outside its issuer | Issuer only | Payment gateway token |

HS256 is a MAC, not a signature: whoever verifies can also issue. Base64 is not encryption. A hash of
low-entropy data (ID numbers, phones, 6-digit codes) is reversed by brute force: use a keyed MAC or encryption.

## Algorithms

| Use | Approved |
|---|---|
| Transport | TLS 1.3, TLS 1.2 minimum; validate certificates; no plaintext outside local development |
| At rest | The managed service's encryption with a customer-managed KMS key and rotation |
| Field or app level | AES-256-GCM or ChaCha20-Poly1305 through a maintained library; a unique nonce per key (NIST SP 800-38D) |
| Passwords | Argon2id (m=19 MiB, t=2, p=1 minimum); scrypt (N=2^17, r=8, p=1) or PBKDF2-HMAC-SHA256 600,000 iterations if FIPS is required; bcrypt only for legacy, cost ≥ 10, rejecting input over 72 bytes |
| MAC | HMAC-SHA256 or stronger, one key per purpose |
| Signatures | Ed25519, ECDSA P-256, RSA-PSS ≥ 3072 bits |
| Randomness | `secrets` (Python), `SecureRandom` (JVM), `crypto.getRandomValues` (web) |

Forbidden: MD5 and SHA-1 for security, DES/3DES, RC4, ECB, CBC without a MAC, SSL and TLS 1.0/1.1,
reversible password encryption, custom schemes, XOR. The validator rejects them in CRY blocks.

## Keys

- In a secrets manager (cloud KMS-backed) or the platform keystore (Android Keystore, iOS Keychain);
  injected as secrets, never as plain environment variables, defaults in code or Terraform state.
- One key per purpose and per environment. Rotation planned; revocation and the leak procedure documented.
- The application refuses to start outside development when a key is missing or has a default value.
- Mobile keys: non-exportable, user authentication required when they protect credentials, invalidated
  on biometric enrollment, StrongBox or Secure Enclave when available, one key per account when accounts share a device.
