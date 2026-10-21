package com.solventa.app.data.session

import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

// Sustituye al Keystore, que no existe en la JVM de pruebas, con una llave AES-GCM en memoria.
class FakeSessionCrypto : SessionCrypto {
    var key: SecretKey? = null
        private set
    var invalidated = false

    override fun encryptionCipher(): Cipher {
        val currentKey = key ?: KeyGenerator.getInstance("AES").apply { init(256) }.generateKey().also { key = it }
        return Cipher.getInstance("AES/GCM/NoPadding").apply { init(Cipher.ENCRYPT_MODE, currentKey) }
    }

    override fun decryptionCipher(iv: ByteArray): Cipher? {
        if (invalidated) {
            key = null
            return null
        }
        val currentKey = key ?: return null
        return Cipher.getInstance("AES/GCM/NoPadding").apply {
            init(Cipher.DECRYPT_MODE, currentKey, GCMParameterSpec(128, iv))
        }
    }

    override fun deleteKey() {
        key = null
    }
}

class InMemorySessionStore : EncryptedSessionStore {
    val sessions = mutableListOf<EncryptedSession>()

    override fun readAll(): List<EncryptedSession> = sessions.toList()
    override fun write(session: EncryptedSession) {
        sessions.removeAll { it.accountEmail == session.accountEmail }
        sessions.add(session)
    }
    override fun remove(accountEmail: String) {
        sessions.removeAll { it.accountEmail == accountEmail }
    }
    override fun clear() {
        sessions.clear()
    }
}
