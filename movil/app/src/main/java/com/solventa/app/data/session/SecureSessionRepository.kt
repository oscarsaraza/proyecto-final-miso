package com.solventa.app.data.session

import com.solventa.app.domain.auth.DeviceCredential
import com.solventa.app.domain.auth.SessionTokens
import javax.crypto.Cipher

// Los tokens solo viven en memoria. Lo que se guarda, cifrado con la llave que exige huella,
// es la credencial del teléfono vinculado (HU-MOV-03, HU-MOV-12).
class SecureSessionRepository(
    private val crypto: SessionCrypto,
    private val store: EncryptedSessionStore,
) {
    var activeSession: SessionTokens? = null
        private set

    fun startSession(tokens: SessionTokens) {
        activeSession = tokens
    }

    fun endSession() {
        activeSession = null
    }

    fun hasStoredSession(): Boolean = store.read() != null

    fun storedDeviceId(): String? = store.read()?.deviceId

    fun encryptionCipher(): Cipher = crypto.encryptionCipher()

    fun decryptionCipher(): Cipher? {
        val stored = store.read() ?: return null
        return crypto.decryptionCipher(stored.iv) ?: run {
            store.clear()
            null
        }
    }

    fun save(credential: DeviceCredential, authenticatedCipher: Cipher) {
        val plaintext = credential.toBytes()
        try {
            store.write(EncryptedSession(authenticatedCipher.doFinal(plaintext), authenticatedCipher.iv, credential.deviceId))
        } finally {
            plaintext.fill(0)
        }
    }

    fun unlock(authenticatedCipher: Cipher): DeviceCredential {
        val stored = checkNotNull(store.read()) { "No hay huella vinculada" }
        val plaintext = authenticatedCipher.doFinal(stored.ciphertext)
        try {
            return DeviceCredential.fromBytes(plaintext)
        } finally {
            plaintext.fill(0)
        }
    }

    fun unbindDevice() {
        store.clear()
        crypto.deleteKey()
    }

    fun clear() {
        endSession()
        unbindDevice()
    }
}
