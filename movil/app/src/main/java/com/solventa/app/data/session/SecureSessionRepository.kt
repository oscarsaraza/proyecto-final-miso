package com.solventa.app.data.session

import com.solventa.app.domain.auth.DeviceCredential
import com.solventa.app.domain.auth.SessionTokens
import javax.crypto.Cipher

data class BoundAccount(val email: String, val name: String)

// Los tokens solo viven en memoria. Lo que se guarda, cifrado con la llave que exige huella, es la
// credencial del teléfono de cada cuenta que activó la huella (HU-MOV-03, HU-MOV-12).
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

    fun boundAccounts(): List<BoundAccount> = store.readAll().map { BoundAccount(it.accountEmail, it.accountName) }

    fun hasStoredSession(): Boolean = store.readAll().isNotEmpty()

    fun isBound(email: String): Boolean = find(email) != null

    fun storedDeviceId(email: String): String? = find(email)?.deviceId

    fun encryptionCipher(): Cipher = crypto.encryptionCipher()

    /** Si la llave fue invalidada (huella nueva en el teléfono) se pierden todas las cuentas vinculadas. */
    fun decryptionCipher(email: String): Cipher? {
        val stored = find(email) ?: return null
        return crypto.decryptionCipher(stored.iv) ?: run {
            store.clear()
            null
        }
    }

    fun save(credential: DeviceCredential, authenticatedCipher: Cipher, accountEmail: String, accountName: String) {
        val plaintext = credential.toBytes()
        try {
            store.write(
                EncryptedSession(
                    ciphertext = authenticatedCipher.doFinal(plaintext),
                    iv = authenticatedCipher.iv,
                    deviceId = credential.deviceId,
                    accountEmail = accountEmail,
                    accountName = accountName,
                )
            )
        } finally {
            plaintext.fill(0)
        }
    }

    fun unlock(email: String, authenticatedCipher: Cipher): DeviceCredential {
        val stored = checkNotNull(find(email)) { "No hay huella vinculada para la cuenta" }
        val plaintext = authenticatedCipher.doFinal(stored.ciphertext)
        try {
            return DeviceCredential.fromBytes(plaintext)
        } finally {
            plaintext.fill(0)
        }
    }

    fun unbind(email: String) {
        store.remove(email)
        if (!hasStoredSession()) crypto.deleteKey()
    }

    fun unbindAll() {
        store.clear()
        crypto.deleteKey()
    }

    fun clear() {
        endSession()
        unbindAll()
    }

    private fun find(email: String): EncryptedSession? = store.readAll().firstOrNull { it.accountEmail == email }
}
