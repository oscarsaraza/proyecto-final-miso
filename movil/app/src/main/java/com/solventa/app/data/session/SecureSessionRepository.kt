package com.solventa.app.data.session

import com.solventa.app.domain.auth.SessionTokens
import javax.crypto.Cipher

// Guardar y desbloquear exigen un Cipher ya autenticado por BiometricPrompt (HU-MOV-03).
class SecureSessionRepository(
    private val crypto: SessionCrypto,
    private val store: EncryptedSessionStore,
) {
    var activeSession: SessionTokens? = null
        private set

    fun startSession(tokens: SessionTokens) {
        activeSession = tokens
    }

    fun hasStoredSession(): Boolean = store.read() != null

    fun encryptionCipher(): Cipher = crypto.encryptionCipher()

    fun decryptionCipher(): Cipher? {
        val stored = store.read() ?: return null
        return crypto.decryptionCipher(stored.iv) ?: run {
            store.clear()
            null
        }
    }

    fun save(tokens: SessionTokens, authenticatedCipher: Cipher) {
        val plaintext = tokens.toBytes()
        try {
            store.write(EncryptedSession(authenticatedCipher.doFinal(plaintext), authenticatedCipher.iv))
        } finally {
            plaintext.fill(0)
        }
        activeSession = tokens
    }

    fun unlock(authenticatedCipher: Cipher): SessionTokens {
        val stored = checkNotNull(store.read()) { "No hay sesión guardada" }
        val plaintext = authenticatedCipher.doFinal(stored.ciphertext)
        try {
            return SessionTokens.fromBytes(plaintext).also { activeSession = it }
        } finally {
            plaintext.fill(0)
        }
    }

    fun clear() {
        activeSession = null
        store.clear()
        crypto.deleteKey()
    }
}
